import uuid
from django.db import models
from django.contrib.auth.models import User


class Bot(models.Model):
    """A chatbot instance linked to a scraped website."""
    STATUS_CHOICES = [
        ('training', 'Training'),
        ('active', 'Active'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    url = models.URLField()
    bot_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='training')
    welcome_message = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.bot_id})"


class ScrapedPage(models.Model):
    """A page that has been scraped for a specific bot."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='pages')
    url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    chunks_count = models.IntegerField(default=0)
    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.url} — {self.status}"


class BotConfig(models.Model):
    bot = models.OneToOneField(Bot, on_delete=models.CASCADE, related_name='config')
    bot_color = models.CharField(max_length=20, default='#3b82f6')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Config for {self.bot.name}"


class TrainingStatus(models.Model):
    bot = models.OneToOneField(Bot, on_delete=models.CASCADE, related_name='training_status')
    total_pages = models.IntegerField(default=0)
    pages_scraped = models.IntegerField(default=0)
    chunks_created = models.IntegerField(default=0)
    status_message = models.TextField(default='Initializing...')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Training status for {self.bot.name}"
