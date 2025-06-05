from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Mirror, Target
from .forms import MirrorForm, TargetForm
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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