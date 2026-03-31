import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webbot.settings')
django.setup()

from core.models import Bot
from django.contrib.auth.models import User

bot = Bot.objects.first()
if bot:
    print(f"BOT_ID: {bot.id}")
    print(f"OWNER: {bot.user.username}")
    # Also create a password for this user if we don't know it, or create a new test user
    user = bot.user
    user.set_password('testpassword123')
    user.save()
    print("USER_PASSWORD: testpassword123")
else:
    print("NO_BOT_FOUND")
    # Let's create one
    user, created = User.objects.get_or_create(username='testuser')
    user.set_password('testpassword123')
    user.save()
    bot = Bot.objects.create(user=user, name='Test Bot', url='https://example.com')
    print(f"CREATED_BOT_ID: {bot.id}")
    print(f"OWNER: {user.username}")
    print("USER_PASSWORD: testpassword123")
