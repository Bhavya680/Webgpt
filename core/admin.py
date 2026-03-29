from django.contrib import admin
from .models import Bot, ScrapedPage


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'bot_id', 'user', 'created_at']


@admin.register(ScrapedPage)
class ScrapedPageAdmin(admin.ModelAdmin):
    list_display = ['url', 'bot', 'status', 'scraped_at']
