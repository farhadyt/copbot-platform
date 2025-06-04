from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Mirror(models.Model):
    """Mirror - our intelligent copy systems"""
    
    MIRROR_TYPES = [
        ('phantom', 'Phantom - Invisible Tracker'),
        ('echo', 'Echo - Perfect Replicator'),  
        ('shadow', 'Shadow - Stealth Hunter'),
        ('prism', 'Prism - Multi-Angle Analyzer'),
        ('nexus', 'Nexus - Neural Network'),
    ]
    
    STATES = [
        ('sleeping', 'Sleeping'),
        ('hunting', 'Hunting'),
        ('paused', 'Paused'),
    ]
    
    pilot = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mirrors')
    codename = models.CharField(max_length=100, unique=True)
    mirror_type = models.CharField(max_length=20, choices=MIRROR_TYPES)
    state = models.CharField(max_length=20, choices=STATES, default='sleeping')
    
    # Neural metrics
    sync_count = models.IntegerField(default=0)
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pulse_frequency = models.IntegerField(default=1000)  # milliseconds
    
    # Limits
    max_echo_size = models.DecimalField(max_digits=20, decimal_places=8, default=100)
    risk_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    gain_target = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    
    awakened_at = models.DateTimeField(auto_now_add=True)
    last_pulse = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-awakened_at']
    
    def __str__(self):
        return f"{self.codename} ({self.get_mirror_type_display()})"
    
    @property
    def is_active(self):
        return self.state == 'hunting'

class Target(models.Model):
    """Targets being tracked by mirrors"""
    
    mirror = models.ForeignKey(Mirror, on_delete=models.CASCADE, related_name='targets')
    beacon_id = models.CharField(max_length=100)  # wallet address
    alias = models.CharField(max_length=50, blank=True)
    
    # Tracking metrics
    echoes_captured = models.IntegerField(default=0)
    perfect_syncs = models.IntegerField(default=0)
    sync_quality = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    is_tracking = models.BooleanField(default=True)
    locked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['mirror', 'beacon_id']
    
    def __str__(self):
        return f"{self.alias or f'Target-{self.beacon_id[:8]}'}"