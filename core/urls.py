from django.urls import path
from .views import CreateBotView, BotStatusView, ChatView, HealthCheckView

urlpatterns = [
    path('bots/', CreateBotView.as_view()),
    path('bots/<uuid:bot_id>/', BotStatusView.as_view()),
    path('chat/', ChatView.as_view()),
    path('health/', HealthCheckView.as_view()),
]
