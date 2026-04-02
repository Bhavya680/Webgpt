from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import uuid
from core.models import Bot, BotConfig, TrainingStatus
from .tasks import train_bot_task

@login_required
def dashboard_index(request):
    bots = Bot.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard/index.html', {'bots': bots})

@login_required
def bot_detail(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id, user=request.user)
    return render(request, 'dashboard/bot_detail.html', {'bot': bot})

@login_required
@require_POST
def create_bot(request):
    bot_name = request.POST.get('bot_name', '')
    website_url = request.POST.get('website_url', '')
    welcome_message = request.POST.get('welcome_message', '')
    bot_color = request.POST.get('bot_color', '#3b82f6')
    
    bot = Bot.objects.create(
        user=request.user,
        name=bot_name,
        url=website_url,
        status='training',
        welcome_message=welcome_message
    )
    
    BotConfig.objects.create(bot=bot, bot_color=bot_color)
    TrainingStatus.objects.create(bot=bot)
    
    train_bot_task.delay(bot.id, website_url)
    
    return redirect('bot_training', bot_id=bot.id)

@login_required
def bot_training_view(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id, user=request.user)
    return render(request, 'dashboard/training.html', {'bot': bot})

@login_required
def bot_training_success(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id, user=request.user)
    return render(request, 'dashboard/training_success.html', {'bot': bot})
@login_required
def bot_training_status_api(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id, user=request.user)
    status = bot.training_status
    
    progress = 0
    if status.total_pages > 0:
        progress = min(int((status.pages_scraped / max(status.total_pages, 1)) * 100), 100)
    
    return JsonResponse({
        'status': bot.status,
        'pages_scraped': status.pages_scraped,
        'chunks_created': status.chunks_created,
        'total_pages': status.total_pages,
        'message': status.status_message,
        'progress': progress
    })

@login_required
def bot_pages_view(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id, user=request.user)
    scraped_pages = bot.pages.all().order_by('id')
    return render(request, 'dashboard/bot_pages.html', {'bot': bot, 'scraped_pages': scraped_pages})

@login_required
@require_POST
def rescrape_bot(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id, user=request.user)
    bot.status = 'training'
    bot.save()
    
    # Reset training status
    status = bot.training_status
    status.pages_scraped = 0
    status.chunks_created = 0
    status.status_message = 'Initializing rescrape...'
    status.completed_at = None
    status.save()
    
    train_bot_task.delay(bot.id, bot.url)
    return redirect('bot_training', bot_id=bot.id)
