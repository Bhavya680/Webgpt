from rest_framework import serializers
from .models import Bot, ScrapedPage


class BotSerializer(serializers.ModelSerializer):
    bot_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Bot
        fields = '__all__'


class ScrapedPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapedPage
        fields = '__all__'


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    bot_id = serializers.CharField()
