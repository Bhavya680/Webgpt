"""
core/views.py

Architecture note
-----------------
LLM inference is delegated to a remote Flask API running on Google Colab,
exposed via an ngrok tunnel. The URL is stored in settings.COLAB_API_URL
(sourced from the .env file).

Local responsibilities (unchanged):
  - ChromaDB vector retrieval  →  top-3 context chunks
  - Prompt construction        →  Gemma-style chat template
  - Bot CRUD + background scraping

Remote responsibilities (new):
  - Actual text generation     →  POST settings.COLAB_API_URL
"""

import logging
import threading
from datetime import datetime

import requests
from django.conf import settings
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer

from .models import Bot, ScrapedPage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared sentence-transformer embedder (Loaded on first use)
# ---------------------------------------------------------------------------
_embedder = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        logger.info("[views] Initializing SentenceTransformer (Lazy Load)...")
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedder


# ---------------------------------------------------------------------------
# Helper: RAG retrieval  (ChromaDB stays 100 % local)
# ---------------------------------------------------------------------------
def _retrieve_context(question: str, bot_id: str, n_results: int = 15) -> list[str]:
    """
    Query the bot's ChromaDB collection and return up to *n_results* text chunks.
    """
    # ... code continues ...
    client = chromadb.PersistentClient(path='./chroma_db/')
    try:
        collection = client.get_collection(name=bot_id)
        if collection.count() == 0:
            return []
    except Exception:
        return []

    q_embedding = _get_embedder().encode([question], convert_to_numpy=True)[0].tolist()
    results = collection.query(query_embeddings=[q_embedding], n_results=n_results)

    documents = (
        results["documents"][0]
        if results and results.get("documents")
        else []
    )
    
    # DEBUG: See what the bot is actually looking at
    print(f"\n[RAG DEBUG] Question: '{question}'")
    print(f"[RAG DEBUG] Retrieved {len(documents)} chunks:")
    for i, doc in enumerate(documents):
        preview = doc.replace('\n', ' ')[:80]
        print(f"  {i+1}. {preview}...")
        
    return documents


# ---------------------------------------------------------------------------
# Helper: prompt construction
# ---------------------------------------------------------------------------
def _build_prompt(question: str, chunks: list[str]) -> str:
    """Build a simplified task-oriented prompt for smaller LLMs like Gemma-2B."""
    context_block = "\n\n".join(chunks)
    
    return (
        "<start_of_turn>user\n"
        "INSTRUCTIONS:\n"
        "You are a helpful web assistant. Use the extracted data below to answer the user question.\n"
        "The data contains [ROW] items and [SITE_NAVIGATION] lists.\n"
        "1. Scan the [ROW] labels (e.g., 'Wins: 47', 'Year: 1990') to find the exact answer.\n"
        "2. If the user asks for a LIST (e.g., 'Top 5'), provide a numbered list.\n"
        "3. Answer in natural language (sentences). Do NOT just repeat the raw data.\n"
        "4. If the data is not in the context, say 'I cannot find that specific information in my current knowledge base.'\n\n"
        "=== EXTRACTED CONTEXT ===\n"
        f"{context_block}\n"
        "=== END CONTEXT ===\n\n"
        f"User Question: {question}\n"
        "<end_of_turn>\n"
        "<start_of_turn>model\n"
    )



# ---------------------------------------------------------------------------
# Helper: remote LLM call  (Colab / ngrok API bridge)
# ---------------------------------------------------------------------------
_OFFLINE_MSG = (
    "The AI server is currently offline or booting up. "
    "Please try again in a minute."
)
_TIMEOUT_SECONDS = 300


def _call_colab_api(prompt: str) -> tuple[str, int]:
    """
    POST the prompt to the remote Colab API and return (answer, http_status).

    Returns a graceful fallback tuple on any network / timeout failure.
    """
    colab_url = settings.COLAB_API_URL
    if not colab_url:
        logger.error("COLAB_API_URL is not configured in .env / settings.py")
        return _OFFLINE_MSG, 503

    try:
        headers = {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
        }
        resp = requests.post(
            colab_url,
            json={"prompt": prompt},
            headers=headers,
            timeout=_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("answer", "No answer returned by the AI server.")
        return answer.strip(), 200

    except requests.exceptions.RequestException as exc:
        logger.warning("Colab API unreachable: %s", exc)
        return _OFFLINE_MSG, 503


# ===========================================================================
# Views
# ===========================================================================

def landing_page(request):
    """Render the SiteBot marketing landing page."""
    return render(request, 'landing.html')


def signup_page(request):
    """Render the SiteBot signup page with Firebase client-side auth."""
    return render(request, 'signup.html')


def login_page(request):
    """Render the SiteBot login page with Firebase client-side auth."""
    return render(request, 'login.html')


class CreateBotView(APIView):
    """POST /api/bots/ — Create a new bot and start background scraping."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name')
        url = request.data.get('url')

        if not name or not url:
            return Response(
                {'error': 'Both "name" and "url" are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bot = Bot.objects.create(user=request.user, name=name, url=url)
        page = ScrapedPage.objects.create(bot=bot, url=url, status='pending')

        def _scrape_and_embed():
            try:
                from ai_engine.scraper import scrape_url
                from ai_engine.embedder import embed_and_store

                text = scrape_url(url)
                embed_and_store(text, str(bot.bot_id))

                page.status = 'success'
                page.save()
                logger.info("[CreateBotView] Scraping complete for bot %s", bot.bot_id)
            except Exception as exc:
                page.status = 'failed'
                page.save()
                logger.error("[CreateBotView] Scraping failed for bot %s: %s", bot.bot_id, exc)

        thread = threading.Thread(target=_scrape_and_embed, daemon=True)
        thread.start()

        return Response(
            {
                'bot_id': str(bot.bot_id),
                'name': bot.name,
                'status': 'processing',
            },
            status=status.HTTP_201_CREATED,
        )


class ChatView(APIView):
    """POST /api/chat/ — RAG retrieval (local) + LLM generation (remote Colab)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message')
        bot_id = request.data.get('bot_id')

        if not message or not bot_id:
            return Response(
                {'error': 'Both "message" and "bot_id" are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bot = Bot.objects.filter(bot_id=bot_id).first()
        if not bot:
            return Response(
                {'error': 'Bot not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── Step 1: Local ChromaDB retrieval ────────────────────────────────
        chunks = _retrieve_context(message, str(bot_id))

        if not chunks:
            return Response(
                {
                    'answer': (
                        "I don't have enough information yet. "
                        "Please wait for the website to finish processing."
                    ),
                    'bot_id': str(bot_id),
                },
                status=status.HTTP_200_OK,
            )

        # ── Step 2: Build RAG prompt ─────────────────────────────────────────
        prompt = _build_prompt(message, chunks)

        # ── Step 3: Remote LLM call with timeout + fallback ──────────────────
        answer, http_status = _call_colab_api(prompt)

        response_body = {'answer': answer, 'bot_id': str(bot_id)}
        drf_status = (
            status.HTTP_200_OK
            if http_status == 200
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(response_body, status=drf_status)


class BotStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, bot_id):
        bot = Bot.objects.filter(bot_id=bot_id).first()
        if not bot:
            return Response(
                {'error': 'Bot not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        pages = bot.pages.all()
        pages_data = [
            {'url': p.url, 'status': p.status, 'scraped_at': p.scraped_at}
            for p in pages
        ]

        return Response(
            {
                'bot_id': str(bot.bot_id),
                'name': bot.name,
                'url': bot.url,
                'created_at': bot.created_at,
                'pages': pages_data,
            },
            status=status.HTTP_200_OK,
        )


from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST as _require_POST
from django.http import JsonResponse as _JsonResponse
import json as _json

# ... existing code ...

class APILoginView(APIView):
    """POST /api/login/ — Handle Django session-based login."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        # In this simplified setup, we assume email = username for lookup
        user = User.objects.filter(email=email).first()
        if not user:
            # Fallback for demouser / admin which might not have email=username
            user = User.objects.filter(username=email.split('@')[0]).first()

        if user:
            authenticated_user = authenticate(request, username=user.username, password=password)
            if authenticated_user:
                login(request, authenticated_user)
                return Response({'message': 'Login successful', 'redirect': '/dashboard/'}, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class APISignupView(APIView):
    """POST /api/signup/ — Handle Django user registration."""
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')

        if not name or not email or not password:
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        username = email.split('@')[0] # Simple username generator
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = name
            user.save()
            
            # Auto-login after signup
            login(request, user)
            return Response({'message': 'User created', 'redirect': '/dashboard/'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class SyncFirebaseUserView(APIView):
    """
    POST /api/auth/sync/
    Called from the frontend AFTER Firebase authenticates the user.
    Creates (or fetches) a matching Django User and logs them into the
    Django session so that request.user is available in all views.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get('email', '').strip().lower()
            firebase_uid = request.data.get('firebase_uid', '').strip()
            display_name = request.data.get('display_name', '').strip()

            if not email:
                return Response({'error': 'email is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Use email as the username — guaranteed unique in Firebase
            user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email}
            )

            # Keep email in sync (in case it was updated)
            if user.email != email:
                user.email = email

            # Populate first_name from Firebase display_name if not already set
            if display_name and not user.first_name:
                parts = display_name.split(' ', 1)
                user.first_name = parts[0]
                if len(parts) > 1:
                    user.last_name = parts[1]

            # Ensure the user has a password set (unusable is fine — Firebase owns auth)
            if not user.has_usable_password():
                user.set_unusable_password()

            user.save()

            # Establish the Django session
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            return Response({
                'status': 'success',
                'created': created,
                'username': user.username,
                'email': user.email,
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.error('[SyncFirebaseUserView] error: %s', exc)
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        colab_url = settings.COLAB_API_URL
        return Response(
            {
                'status': 'ok',
                'colab_api_configured': bool(colab_url),
                'timestamp': datetime.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )
