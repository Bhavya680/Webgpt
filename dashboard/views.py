from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import Bot

@login_required
def dashboard_index(request):
    bots = Bot.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard/code.html', {'bots': bots})

@login_required
def bot_detail(request, bot_id):
    bot = get_object_or_404(Bot, bot_id=bot_id, user=request.user)
    return render(request, 'dashboard/bot_detail.html', {'bot': bot})
