from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CreateBotView, BotStatusView, ChatView, HealthCheckView, landing_page

urlpatterns = [
    # Landing page
    path('', landing_page, name='landing'),

    # Auth placeholders (wired to Django built-ins for now)
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('signup/', landing_page, name='signup'),  # Replace with real signup view later

    # API endpoints
    path('bots/', CreateBotView.as_view()),
    path('bots/<uuid:bot_id>/', BotStatusView.as_view()),
    path('chat/', ChatView.as_view()),
    path('health/', HealthCheckView.as_view()),
]
