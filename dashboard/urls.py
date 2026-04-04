from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_index, name='dashboard_index'),
    path('bots/<uuid:bot_id>/', views.bot_detail, name='bot_detail'),
    path('bots/<uuid:bot_id>/pages/', views.bot_pages_view, name='bot_pages'),
    path('bots/<uuid:bot_id>/chat/', views.bot_chat_view, name='bot_chat'),
    path('api/bots/<uuid:bot_id>/chat/', views.bot_chat_api, name='bot_chat_api'),
    path('bots/<uuid:bot_id>/rescrape/', views.rescrape_bot, name='rescrape_bot'),
    path('bots/create/', views.create_bot, name='create_bot'),
    path('bots/<uuid:bot_id>/training/', views.bot_training_view, name='bot_training'),
    path('bots/<uuid:bot_id>/success/', views.bot_training_success, name='bot_training_success'),
    path('api/bots/<uuid:bot_id>/status/', views.bot_training_status_api, name='bot_status_api'),
    path('bots/<uuid:bot_id>/settings/', views.bot_settings_view, name='bot_settings'),
    path('bots/<uuid:bot_id>/delete/', views.bot_delete_view, name='bot_delete'),
    path('bots/<uuid:bot_id>/widget/', views.bot_widget_view, name='bot_widget'),
]
