from django.db import models
from mirrors.models import Mirror, Target

class Echo(models.Model):
    """Echo - replicated actions"""
    
    ECHO_TYPES = [
        ('acquire', 'Acquire'),
        ('release', 'Release'),
    ]
    
    PHASES = [
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
        ('void', 'Void'),
    ]
    
    mirror = models.ForeignKey(Mirror, on_delete=models.CASCADE, related_name='echoes')
    origin_target = models.ForeignKey(Target, on_delete=models.SET_NULL, null=True)
    
    # Echo details
    echo_type = models.CharField(max_length=20, choices=ECHO_TYPES)
    beacon_address = models.CharField(max_length=100)  # token
    beacon_symbol = models.CharField(max_length=20)
    magnitude = models.DecimalField(max_digits=20, decimal_places=8)
    frequency = models.DecimalField(max_digits=20, decimal_places=8)  # price
    resonance = models.DecimalField(max_digits=20, decimal_places=8)  # total value
    
    # Sync details
    phase = models.CharField(max_length=20, choices=PHASES, default='pending')
    sync_hash = models.CharField(max_length=150, blank=True)
    energy_cost = models.DecimalField(max_digits=20, decimal_places=8, default=0)  # gas
    drift = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # slippage
    
    # Results
    amplitude_gain = models.DecimalField(max_digits=20, decimal_places=8, null=True)  # profit/loss
    gain_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    pulsed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-pulsed_at']
    
    def __str__(self):
        return f"{self.echo_type} {self.beacon_symbol} - {self.phase}"

class Pulse(models.Model):
    """System heartbeat and metrics"""
    
    mirror = models.ForeignKey(Mirror, on_delete=models.CASCADE, related_name='pulses')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Vitals
    sync_latency = models.IntegerField()  # milliseconds
    echo_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    
    # Performance
    total_amplitude = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    resonance_quality = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-timestamp']