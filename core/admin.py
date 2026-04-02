from django.contrib import admin
from .models import Bot, ScrapedPage, BotConfig, TrainingStatus


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'bot_id', 'user', 'created_at']


@admin.register(ScrapedPage)
class ScrapedPageAdmin(admin.ModelAdmin):
    list_display = ['url', 'bot', 'status', 'scraped_at']


@admin.register(BotConfig)
class BotConfigAdmin(admin.ModelAdmin):
    list_display = ['bot', 'bot_color']


@admin.register(TrainingStatus)
class TrainingStatusAdmin(admin.ModelAdmin):
    list_display = ['bot', 'status_message', 'pages_scraped', 'total_pages']
