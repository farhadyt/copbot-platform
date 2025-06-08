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

class TradingPlatform(models.Model):
    """Supported trading platforms"""
    name = models.CharField(max_length=50, unique=True)
    api_endpoint = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name.upper()


class ConnectedWallet(models.Model):
    """User's connected wallets for trading"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    address = models.CharField(max_length=200)
    private_key_encrypted = models.TextField()  # Encrypted private key
    platform = models.ForeignKey(TradingPlatform, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'address', 'platform']
    
    def __str__(self):
        return f"{self.address[:8]}...{self.address[-6:]} ({self.platform.name})"


class TradingBot(models.Model):
    """Trading bot configuration for a mirror"""
    COPY_MODES = [
        ('exact', 'Exact Copy'),
        ('proportional', 'Proportional'),
        ('fixed', 'Fixed Amount'),
    ]
    
    mirror = models.OneToOneField(Mirror, on_delete=models.CASCADE, related_name='trading_bot')
    wallet = models.ForeignKey(ConnectedWallet, on_delete=models.CASCADE)
    platform = models.ForeignKey(TradingPlatform, on_delete=models.CASCADE)
    
    # Trading configuration
    is_active = models.BooleanField(default=False)
    copy_mode = models.CharField(max_length=20, choices=COPY_MODES, default='proportional')
    
    # Risk management
    max_trade_size = models.DecimalField(max_digits=20, decimal_places=8, help_text="Maximum trade size in SOL")
    min_trade_size = models.DecimalField(max_digits=20, decimal_places=8, default=0.01)
    daily_loss_limit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Daily loss limit in USD")
    take_profit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.0)
    stop_loss_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=20.0)
    
    # Advanced settings
    slippage_tolerance = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    gas_limit_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1.5)
    delay_seconds = models.IntegerField(default=0, help_text="Delay before copying trade")
    
    # Statistics
    total_trades = models.IntegerField(default=0)
    successful_trades = models.IntegerField(default=0)
    failed_trades = models.IntegerField(default=0)
    total_profit = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_loss = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Bot for {self.mirror.codename} - {self.platform.name}"
    
    @property
    def success_rate(self):
        if self.total_trades == 0:
            return 0
        return (self.successful_trades / self.total_trades) * 100
    
    @property
    def net_profit(self):
        return self.total_profit - self.total_loss


class TradeExecution(models.Model):
    """Record of executed trades by the bot"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executing', 'Executing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    bot = models.ForeignKey(TradingBot, on_delete=models.CASCADE, related_name='executions')
    original_tx_hash = models.CharField(max_length=200)  # Original transaction being copied
    
    # Trade details
    token_address = models.CharField(max_length=200)
    token_symbol = models.CharField(max_length=50)
    trade_type = models.CharField(max_length=10)  # buy/sell
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    total_value = models.DecimalField(max_digits=20, decimal_places=8)
    
    # Execution details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    executed_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    executed_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    execution_tx_hash = models.CharField(max_length=200, null=True, blank=True)
    gas_used = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # P&L tracking
    entry_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.trade_type.upper()} {self.token_symbol} - {self.status}"