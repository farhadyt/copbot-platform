from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mirrors.models import Mirror, Target
from pulse.models import Echo

@login_required
def command_center(request):
    """Main dashboard - Command Center"""
    context = {
        'mirrors': Mirror.objects.filter(pilot=request.user),
        'total_mirrors': Mirror.objects.filter(pilot=request.user).count(),
        'active_mirrors': Mirror.objects.filter(pilot=request.user, state='hunting').count(),
        'recent_echoes': Echo.objects.filter(mirror__pilot=request.user).order_by('-pulsed_at')[:10],
    }
    return render(request, 'horizon/command_center.html', context)