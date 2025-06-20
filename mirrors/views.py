from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Mirror, Target, TradingBot, ConnectedWallet, TradingPlatform, TradeExecution, Agent
from .forms import MirrorForm, TargetForm, TradingBotForm, ConnectedWalletForm, AgentForm
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
import json
from django.views.decorators.http import require_http_methods

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

# Agent Management Views
@login_required
def create_agent(request, agent_type):
    """Create a new agent of specified type"""
    # Only Shadow agents are fully functional for now
    if agent_type not in ['shadow', 'hawk', 'hunter', 'mirror']:
        return redirect('horizon:command_center')
    
    if request.method == 'POST':
        form = AgentForm(request.POST)
        if form.is_valid():
            agent = form.save(commit=False)
            agent.pilot = request.user
            agent.agent_type = agent_type  # Set the agent type
            
            # Auto-generate name if not provided
            if not agent.name:
                agent.name = Agent.generate_agent_name(agent_type, request.user)
            
            # Process active_days from form
            active_days = form.cleaned_data.get('active_days', [])
            if active_days:
                agent.active_days = [int(day) for day in active_days]
            else:
                agent.active_days = list(range(7))  # All days by default
            
            agent.save()
            messages.success(request, f'{agent.name} created successfully!')
            
            # If this is a Shadow agent and it's active, start monitoring
            if agent_type == 'shadow' and agent.is_active:
                import asyncio
                from .solana_monitor import start_agent_monitoring
                
                def start_monitoring():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(start_agent_monitoring(agent.id))
                    finally:
                        loop.close()
                
                import threading
                monitor_thread = threading.Thread(target=start_monitoring)
                monitor_thread.daemon = True
                monitor_thread.start()
                messages.info(request, f'{agent.name} is now monitoring Solana network')
            
            return redirect('horizon:command_center')
        else:
            # Debug form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Initialize form with agent_type
        form = AgentForm(initial={'agent_type': agent_type})
    
    context = {
        'form': form,
        'agent_type': agent_type,
    }
    
    return render(request, 'mirrors/create_agent.html', context)

@login_required
def edit_agent(request, agent_id):
    """Edit existing agent"""
    agent = get_object_or_404(Agent, id=agent_id, pilot=request.user)
    
    # Only Shadow agents are fully implemented for now
    if agent.agent_type != 'shadow':
        messages.info(request, f'{agent.agent_type.title()} agent editing is coming soon!')
        return redirect('horizon:command_center')
    
    if request.method == 'POST':
        # Update agent with form data
        agent.name = request.POST.get('name', agent.name)
        
        # Active days
        active_days = []
        for i in range(7):
            if request.POST.get(f'day_{i}'):
                active_days.append(i)
        agent.active_days = active_days
        
        # Active hours
        agent.active_hours_start = request.POST.get('active_hours_start', agent.active_hours_start)
        agent.active_hours_end = request.POST.get('active_hours_end', agent.active_hours_end)
        
        # Transaction limits
        max_transactions_hour = request.POST.get('max_transactions_hour')
        max_transactions_day = request.POST.get('max_transactions_day')
        agent.max_transactions_hour = int(max_transactions_hour) if max_transactions_hour else None
        agent.max_transactions_day = int(max_transactions_day) if max_transactions_day else None
        agent.scan_frequency = request.POST.get('scan_frequency', agent.scan_frequency)
        
        # Value filters
        min_transaction_value = request.POST.get('min_transaction_value')
        max_transaction_value = request.POST.get('max_transaction_value')
        min_wallet_balance = request.POST.get('min_wallet_balance')
        agent.min_transaction_value = float(min_transaction_value) if min_transaction_value else agent.min_transaction_value
        agent.max_transaction_value = float(max_transaction_value) if max_transaction_value else None
        agent.min_wallet_balance = float(min_wallet_balance) if min_wallet_balance else None
        
        # Token filters
        agent.token_filter_type = request.POST.get('token_filter_type', agent.token_filter_type)
        agent.excluded_tokens = request.POST.get('excluded_tokens', agent.excluded_tokens)
        agent.included_tokens = request.POST.get('included_tokens', agent.included_tokens)
        
        # Database retention
        max_retention_days = request.POST.get('max_retention_days')
        agent.max_retention_days = int(max_retention_days) if max_retention_days else agent.max_retention_days
        
        agent.save()
        messages.success(request, f'{agent.name} updated successfully!')
        return redirect('horizon:command_center')
    
    context = {
        'agent': agent,
        'days_of_week': [
            (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
            (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
        ]
    }
    
    return render(request, 'mirrors/edit_agent.html', context)

@login_required
def delete_agent(request, agent_id):
    """Delete agent"""
    if request.method == 'POST':
        agent = get_object_or_404(Agent, id=agent_id, pilot=request.user)
        agent_name = agent.name
        agent.delete()
        return JsonResponse({'success': True, 'message': f'{agent_name} deleted successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@require_http_methods(["POST"])
def toggle_agent(request, agent_id):
    """Toggle agent active status and manage Solana monitoring"""
    try:
        agent = get_object_or_404(Agent, id=agent_id, pilot=request.user)
        
        # Toggle the status
        agent.is_active = not agent.is_active
        agent.save()
        
        # Start/stop Solana monitoring for Shadow agents
        if agent.agent_type == 'shadow':
            import asyncio
            from .solana_monitor import start_agent_monitoring, stop_agent_monitoring
            
            if agent.is_active:
                # Start monitoring asynchronously
                def start_monitoring():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(start_agent_monitoring(agent.id))
                    finally:
                        loop.close()
                
                import threading
                monitor_thread = threading.Thread(target=start_monitoring)
                monitor_thread.daemon = True
                monitor_thread.start()
                
                message = f"Agent {agent.name} activated and connected to Solana network"
            else:
                # Stop monitoring asynchronously
                def stop_monitoring():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(stop_agent_monitoring(agent.id))
                    finally:
                        loop.close()
                
                import threading
                monitor_thread = threading.Thread(target=stop_monitoring)
                monitor_thread.daemon = True
                monitor_thread.start()
                
                message = f"Agent {agent.name} deactivated and disconnected from Solana network"
        else:
            # For non-Shadow agents (placeholders)
            status = "activated" if agent.is_active else "deactivated"
            message = f"Agent {agent.name} {status}"
        
        return JsonResponse({
            'success': True,
            'is_active': agent.is_active,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def agent_transactions(request, agent_id):
    """View agent transactions with real-time updates"""
    agent = get_object_or_404(Agent, id=agent_id, pilot=request.user)
    
    # Only Shadow agents have transactions
    if agent.agent_type != 'shadow':
        messages.info(request, f'{agent.agent_type.title()} agents do not track transactions yet.')
        return redirect('horizon:command_center')
    
    # Get agent stats
    stats = agent.get_transaction_stats()
    
    # Get recent transactions
    transactions = agent.transactions.order_by('-timestamp')[:50]
    
    context = {
        'agent': agent,
        'stats': stats,
        'transactions': transactions,
    }
    
    return render(request, 'mirrors/agent_transactions.html', context)