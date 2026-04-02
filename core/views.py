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

import chromadb
from sentence_transformers import SentenceTransformer

from .models import Bot, ScrapedPage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared sentence-transformer embedder (loaded once at module level)
# ---------------------------------------------------------------------------
_embedder = SentenceTransformer('all-MiniLM-L6-v2')


# ---------------------------------------------------------------------------
# Helper: RAG retrieval  (ChromaDB stays 100 % local)
# ---------------------------------------------------------------------------
def _retrieve_context(question: str, bot_id: str, n_results: int = 5) -> list[str]:
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

    q_embedding = _embedder.encode([question], convert_to_numpy=True)[0].tolist()
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
    """Build a Gemma-style instruction prompt for precision RAG."""
    chunks_block = "\n\n".join(chunks)
    # Final sanitization
    clean_chunks = chunks_block.replace('Â£', '£').replace('Â', '')
    return (
        "<start_of_turn>user\n"
        "SYSTEM INSTRUCTIONS:\n"
        "1. Answer directly and concisely. START YOUR ANSWER with either YES or NO if appropriate.\n"
        "2. For COMPARISONS, state both values and give a clear conclusion.\n"
        "3. LOGIC: 5 stars is the HIGHEST rating. 1 star is the LOWEST.\n\n"
        f"Context:\n{clean_chunks}\n\n"
        f"Question: {question}\n"
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
        
        # SMART ENFORCEMENT: Allow exactly two sentences so logic/conclusions aren't cut off.
        sentences = answer.split(". ")
        if len(sentences) > 2:
            answer = ". ".join(sentences[:2]).strip() + "."
        elif "\n" in answer:
            answer = answer.split("\n")[0]
            
        return answer, 200

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


from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

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
