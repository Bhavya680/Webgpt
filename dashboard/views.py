import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, logout
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import uuid
from core.models import Bot, BotConfig, TrainingStatus
from core.views import _retrieve_context, _build_prompt, _call_colab_api
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
    
    # Trigger background task
    train_bot_task.delay(bot.id, bot.url)
    
    return redirect('bot_training', bot_id=bot.id)
    
@login_required
def bot_chat_view(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id, user=request.user)
    return render(request, 'dashboard/bot_chat.html', {'bot': bot})

@csrf_exempt
@require_POST
def bot_chat_api(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id)
    
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
            
        chunks = _retrieve_context(message, str(bot.bot_id))
        
        if not chunks:
            return JsonResponse({
                'answer': "I don't have enough information yet. Please wait for the website to finish processing.",
                'status': 'success'
            })
            
        prompt = _build_prompt(message, chunks)
        answer, http_status = _call_colab_api(prompt)
        
        if http_status != 200:
            return JsonResponse({'error': answer}, status=http_status)
            
        return JsonResponse({'answer': answer, 'status': 'success'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def bot_settings_view(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id, user=request.user)
    
    if request.method == 'POST':
        bot_name = request.POST.get('bot_name')
        if bot_name:
            bot.name = bot_name
            
        welcome_msg = request.POST.get('welcome_message')
        if welcome_msg is not None:
            bot.welcome_message = welcome_msg
            
        bot.save()
            
        bot.config.bot_color = request.POST.get('primary_color', bot.config.bot_color)
        
        position = request.POST.get('position')
        if position in ['right', 'left']:
            bot.config.position = position
            
        bot.config.save()
        messages.success(request, 'Bot settings updated successfully!')
        return redirect('bot_settings', bot_id=bot.id)
        
    return render(request, 'dashboard/bot_settings.html', {'bot': bot})

@login_required
@require_POST
def bot_delete_view(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id, user=request.user)
    bot.delete()
    messages.success(request, 'Bot deleted successfully.')
    return redirect('dashboard_index')

@xframe_options_exempt
def bot_widget_view(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id)
    return render(request, 'dashboard/widget.html', {'bot': bot})


@login_required
def profile_settings_view(request):
    """User profile settings — updates name, email, and password."""
    user = request.user

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')

        # Update name fields
        if first_name:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

        # Update email & keep username in sync
        if email and email != user.email:
            from django.contrib.auth.models import User as AuthUser
            if AuthUser.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, 'That email address is already in use.')
                return redirect('profile_settings')
            user.email = email
            user.username = email   # username == email convention enforced at signup

        # Change password (only if both fields provided and current is correct)
        if current_password and new_password:
            if user.check_password(current_password):
                user.set_password(new_password)
                update_session_auth_hash(request, user)  # keep session alive
                messages.success(request, 'Password updated successfully.')
            else:
                messages.error(request, 'Current password is incorrect.')
                user.save()
                return redirect('profile_settings')

        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile_settings')

    total_bots = Bot.objects.filter(user=user).count()
    return render(request, 'dashboard/profile.html', {
        'user': user,
        'total_bots': total_bots,
    })


def user_logout_view(request):
    """Logs the user out of the Django session and redirects to login."""
    logout(request)
    return redirect('login')
