from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mirrors.models import Mirror, Target, Agent
from pulse.models import Echo

@login_required
def command_center(request):
    """Enhanced Command Center with transaction statistics"""
    # Get agents by type for the current user
    shadow_agents = Agent.objects.filter(pilot=request.user, agent_type='shadow')
    hawk_agents = Agent.objects.filter(pilot=request.user, agent_type='hawk')
    hunter_agents = Agent.objects.filter(pilot=request.user, agent_type='hunter')
    mirror_agents = Agent.objects.filter(pilot=request.user, agent_type='mirror')
    
    # Add transaction statistics for Shadow agents
    for agent in shadow_agents:
        agent.transaction_stats = agent.get_transaction_stats()
    
    # Calculate totals
    total_agents = shadow_agents.count() + hawk_agents.count() + hunter_agents.count() + mirror_agents.count()
    active_agents = Agent.objects.filter(pilot=request.user, is_active=True).count()
    
    context = {
        'shadow_agents': shadow_agents,
        'hawk_agents': hawk_agents,
        'hunter_agents': hunter_agents,
        'mirror_agents': mirror_agents,
        'total_agents': total_agents,
        'active_agents': active_agents,
        
        # Legacy stats (can be removed later)
        'mirrors': Mirror.objects.filter(pilot=request.user),
        'total_mirrors': Mirror.objects.filter(pilot=request.user).count(),
        'active_mirrors': Mirror.objects.filter(pilot=request.user, state='hunting').count(),
        'recent_echoes': Echo.objects.filter(mirror__pilot=request.user).order_by('-pulsed_at')[:10],
    }
    return render(request, 'horizon/command_center.html', context)