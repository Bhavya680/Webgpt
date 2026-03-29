import threading
from datetime import datetime

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Bot, ScrapedPage
from .serializers import BotSerializer, ChatRequestSerializer
from ai_engine.rag_engine import get_answer
from ai_engine.model_loader import is_model_loaded

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

        # Create the Bot record
        bot = Bot.objects.create(user=request.user, name=name, url=url)

        # Create a pending ScrapedPage record
        page = ScrapedPage.objects.create(bot=bot, url=url, status='pending')

        # Launch background scraping thread
        def _scrape_and_embed():
            try:
                from ai_engine.scraper import scrape_url
                from ai_engine.embedder import embed_and_store

                text = scrape_url(url)
                embed_and_store(text, str(bot.bot_id))

                page.status = 'success'
                page.save()
                print(f"[CreateBotView] Scraping complete for bot {bot.bot_id}")
            except Exception as exc:
                page.status = 'failed'
                page.save()
                print(f"[CreateBotView] Scraping failed for bot {bot.bot_id}: {exc}")

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message')
        bot_id = request.data.get('bot_id')

        if not message or not bot_id:
            return Response(
                {'error': 'Both "message" and "bot_id" are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        bot = Bot.objects.filter(bot_id=bot_id).first()
        if not bot:
            return Response(
                {'error': 'Bot not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            answer = get_answer(question=message, bot_id=str(bot_id))
            return Response({
                'answer': answer, 
                'bot_id': str(bot_id)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class BotStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, bot_id):
        bot = Bot.objects.filter(bot_id=bot_id).first()
        if not bot:
            return Response(
                {'error': 'Bot not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        pages = bot.pages.all()
        pages_data = [{
            'url': p.url,
            'status': p.status,
            'scraped_at': p.scraped_at
        } for p in pages]

        return Response({
            'bot_id': str(bot.bot_id),
            'name': bot.name,
            'url': bot.url,
            'created_at': bot.created_at,
            'pages': pages_data
        }, status=status.HTTP_200_OK)

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'ok',
            'model_loaded': is_model_loaded(),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_200_OK)
