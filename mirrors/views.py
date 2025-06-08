from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Mirror, Target, TradingBot, ConnectedWallet, TradingPlatform, TradeExecution
from .forms import MirrorForm, TargetForm, TradingBotForm, ConnectedWalletForm
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
import json

@login_required
def create_mirror(request):
    """Deploy new mirror"""
    if request.method == 'POST':
        form = MirrorForm(request.POST)
        if form.is_valid():
            mirror = form.save(commit=False)
            mirror.pilot = request.user
            mirror.save()
            messages.success(request, f'Mirror "{mirror.codename}" deployed successfully!')
            return redirect('mirrors:mirror_detail', pk=mirror.pk)
    else:
        form = MirrorForm()
    
    return render(request, 'mirrors/create_mirror.html', {'form': form})

@login_required
def mirror_detail(request, pk):
    """Mirror control panel"""
    mirror = get_object_or_404(Mirror, pk=pk, pilot=request.user)
    targets = mirror.targets.all()
    
    if request.method == 'POST':
        # Handle mirror actions
        action = request.POST.get('action')
        
        if action == 'activate':
            mirror.state = 'hunting'
            mirror.save()
            messages.success(request, f'{mirror.codename} is now hunting!')
            
            # Send WebSocket update
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'mirror_{mirror.id}',
                {
                    'type': 'mirror_update',
                    'data': {
                        'state': 'hunting',
                        'message': f'{mirror.codename} activated'
                    }
                }
            )
            
        elif action == 'deactivate':
            mirror.state = 'sleeping'
            mirror.save()
            messages.info(request, f'{mirror.codename} is sleeping.')
            
            # Send WebSocket update
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'mirror_{mirror.id}',
                {
                    'type': 'mirror_update',
                    'data': {
                        'state': 'sleeping',
                        'message': f'{mirror.codename} deactivated'
                    }
                }
            )
            
        elif action == 'add_target':
            target_form = TargetForm(request.POST)
            if target_form.is_valid():
                target = target_form.save(commit=False)
                target.mirror = mirror
                target.save()
                messages.success(request, f'Target added to {mirror.codename}')
                
        return redirect('mirrors:mirror_detail', pk=pk)
    
    target_form = TargetForm()
    
    context = {
        'mirror': mirror,
        'targets': targets,
        'target_form': target_form,
    }
    
    return render(request, 'mirrors/mirror_detail.html', context)

@login_required
def mirror_list(request):
    """List all mirrors"""
    mirrors = Mirror.objects.filter(pilot=request.user)
    return render(request, 'mirrors/mirror_list.html', {'mirrors': mirrors})

@login_required
def wallet_detail(request, mirror_pk, wallet_id):
    """Display detailed wallet statistics in a dedicated page"""
    mirror = get_object_or_404(Mirror, pk=mirror_pk, pilot=request.user)
    
    context = {
        'mirror': mirror,
        'wallet_id': wallet_id,
    }
    
    return render(request, 'mirrors/wallet_detail.html', context)

@login_required
def configure_trading_bot(request, pk):
    """Configure trading bot for a mirror"""
    mirror = get_object_or_404(Mirror, pk=pk, pilot=request.user)
    
    # Get or create trading bot
    try:
        trading_bot = mirror.trading_bot
    except TradingBot.DoesNotExist:
        trading_bot = None
    
    if request.method == 'POST':
        # Get user's wallets for the form
        user_wallets = ConnectedWallet.objects.filter(user=request.user, is_active=True)
        
        if trading_bot:
            form = TradingBotForm(request.POST, instance=trading_bot)
        else:
            form = TradingBotForm(request.POST)
        
        # Limit wallet choices to user's wallets
        form.fields['wallet'].queryset = user_wallets
        
        if form.is_valid():
            bot = form.save(commit=False)
            bot.mirror = mirror
            bot.save()
            messages.success(request, f'Trading bot configured for {mirror.codename}!')
            return redirect('mirrors:mirror_detail', pk=pk)
    else:
        user_wallets = ConnectedWallet.objects.filter(user=request.user, is_active=True)
        
        if trading_bot:
            form = TradingBotForm(instance=trading_bot)
        else:
            form = TradingBotForm()
        
        form.fields['wallet'].queryset = user_wallets
    
    context = {
        'mirror': mirror,
        'form': form,
        'trading_bot': trading_bot,
        'has_wallets': user_wallets.exists(),
    }
    
    return render(request, 'mirrors/configure_bot.html', context)

@login_required
def manage_wallets(request):
    """Manage connected wallets"""
    wallets = ConnectedWallet.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = ConnectedWalletForm(request.POST)
        if form.is_valid():
            wallet = form.save(commit=False)
            wallet.user = request.user
            # In production, encrypt the private key properly
            wallet.save()
            messages.success(request, f'Wallet connected successfully!')
            return redirect('mirrors:manage_wallets')
    else:
        form = ConnectedWalletForm()
    
    context = {
        'wallets': wallets,
        'form': form,
        'platforms': TradingPlatform.objects.filter(is_active=True),
    }
    
    return render(request, 'mirrors/manage_wallets.html', context)

@login_required
def toggle_trading_bot(request, pk):
    """Toggle trading bot on/off"""
    if request.method == 'POST':
        mirror = get_object_or_404(Mirror, pk=pk, pilot=request.user)
        
        try:
            trading_bot = mirror.trading_bot
            trading_bot.is_active = not trading_bot.is_active
            trading_bot.save()
            
            status = 'activated' if trading_bot.is_active else 'deactivated'
            messages.success(request, f'Trading bot {status}!')
            
            # Send WebSocket update
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'mirror_{mirror.id}',
                {
                    'type': 'bot_status_update',
                    'data': {
                        'bot_active': trading_bot.is_active,
                        'message': f'Trading bot {status}'
                    }
                }
            )
            
            return JsonResponse({'success': True, 'active': trading_bot.is_active})
            
        except TradingBot.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Trading bot not configured'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def bot_executions(request, pk):
    """View trading bot execution history"""
    mirror = get_object_or_404(Mirror, pk=pk, pilot=request.user)
    
    try:
        trading_bot = mirror.trading_bot
        executions = trading_bot.executions.all()[:100]  # Last 100 executions
    except TradingBot.DoesNotExist:
        executions = []
        trading_bot = None
    
    context = {
        'mirror': mirror,
        'trading_bot': trading_bot,
        'executions': executions,
    }
    
    return render(request, 'mirrors/bot_executions.html', context)