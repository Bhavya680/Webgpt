from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import uuid
from core.models import Bot

@login_required
def dashboard_index(request):
    # Hardcoded to empty list to show Empty State UI per instructions
    bots = []
    # bots = Bot.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard/code.html', {'bots': bots})

@login_required
def bot_detail(request, bot_id):
    bot = get_object_or_404(Bot, bot_id=bot_id, user=request.user)
    return render(request, 'dashboard/bot_detail.html', {'bot': bot})

@login_required
@require_POST
def mock_create_bot(request):
    bot_name = request.POST.get('bot_name', '')
    website_url = request.POST.get('website_url', '')
    welcome_message = request.POST.get('welcome_message', '')
    bot_color = request.POST.get('bot_color', '')
    
    # Generate dummy ID
    mock_id = str(uuid.uuid4())[:8]
    
    # Terminal Logging Logic
    print("========== NEW BOT TRIGGERED ==========")
    print(f"Mock Bot ID: {mock_id}")
    print(f"Name: {bot_name}")
    print(f"URL: {website_url}")
    print(f"Welcome Message: {welcome_message}")
    print(f"Color: {bot_color}")
    print("=======================================")
    
    return redirect('dashboard_index')
