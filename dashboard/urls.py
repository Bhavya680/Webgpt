from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_index, name='dashboard_index'),
    path('bots/<uuid:bot_id>/', views.bot_detail, name='bot_detail'),
    path('bots/create/mock/', views.mock_create_bot, name='mock_create_bot'),
]
