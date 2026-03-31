from django.urls import path
from .views import (
    CreateBotView, BotStatusView, ChatView, HealthCheckView,
    APILoginView, APISignupView
)

urlpatterns = [
    # API endpoints
    path('bots/', CreateBotView.as_view()),
    path('bots/<uuid:bot_id>/', BotStatusView.as_view()),
    path('chat/', ChatView.as_view()),
    path('health/', HealthCheckView.as_view()),
    
    # Auth API
    path('auth/login/', APILoginView.as_view(), name='api_login'),
    path('auth/signup/', APISignupView.as_view(), name='api_signup'),
]
