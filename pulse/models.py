from django.db import models
from mirrors.models import Mirror, Target

class ExchangeConnection(models.Model):
    """Exchange API connections for trading execution"""
    
    EXCHANGE_CHOICES = [
        ('binance', 'Binance'),
        ('okx', 'OKX'),
        ('bybit', 'Bybit'),
        ('kucoin', 'KuCoin'),
        ('mexc', 'MEXC'),
        ('gate', 'Gate.io'),
    ]
    
    mirror = models.ForeignKey(Mirror, on_delete=models.CASCADE, related_name='exchanges')
    exchange = models.CharField(max_length=20, choices=EXCHANGE_CHOICES)
    api_key = models.CharField(max_length=200)
    api_secret = models.CharField(max_length=200)
    
    # Trading settings
    copy_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)  # % of original trade size
    min_trade_amount = models.DecimalField(max_digits=20, decimal_places=8, default=10)
    max_trade_amount = models.DecimalField(max_digits=20, decimal_places=8, default=1000)
    
    is_active = models.BooleanField(default=True)
    is_testnet = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['mirror', 'exchange']
    
    def __str__(self):
        return f"{self.mirror.codename} - {self.get_exchange_display()}"

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
    
    PLATFORMS = [
        ('dexscreener', 'DexScreener'),
        ('gmgn', 'GMGN.ai'),
        ('photon', 'Photon'),
        ('raydium', 'Raydium'),
        ('jupiter', 'Jupiter'),
        ('uniswap', 'Uniswap'),
        ('pancakeswap', 'PancakeSwap'),
        ('pump', 'Pump.fun'),
        ('unknown', 'Unknown'),
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
    
    # Platform info
    detected_platform = models.CharField(max_length=20, choices=PLATFORMS, default='unknown')
    platform_tx_hash = models.CharField(max_length=200, blank=True)
    
    # Sync details
    phase = models.CharField(max_length=20, choices=PHASES, default='pending')
    sync_hash = models.CharField(max_length=150, blank=True)
    energy_cost = models.DecimalField(max_digits=20, decimal_places=8, default=0)  # gas
    drift = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # slippage
    
    # Results
    amplitude_gain = models.DecimalField(max_digits=20, decimal_places=8, null=True)  # profit/loss
    gain_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    # P&L calculations
    entry_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    pnl_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    pulsed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-pulsed_at']
    
    def __str__(self):
        return f"{self.echo_type} {self.beacon_symbol} - {self.phase}"
    
    @property
    def is_profitable(self):
        """Returns True if trade is profitable"""
        return self.realized_pnl and self.realized_pnl > 0
    
    def calculate_pnl(self):
        """Calculate P&L for the trade"""
        if self.entry_price and self.exit_price:
            if self.echo_type == 'acquire':
                # For buy orders, we calculate unrealized P&L based on current price
                self.realized_pnl = (self.exit_price - self.entry_price) * self.magnitude
            else:
                # For sell orders, we calculate realized P&L
                self.realized_pnl = (self.exit_price - self.entry_price) * self.magnitude
            
            if self.entry_price > 0:
                self.pnl_percentage = ((self.exit_price - self.entry_price) / self.entry_price) * 100
            
            self.save()

class TradeExecution(models.Model):
    """Tracks actual trades executed on exchanges"""
    
    EXECUTION_STATUS = [
        ('pending', 'Pending'),
        ('filled', 'Filled'),
        ('partially_filled', 'Partially Filled'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    echo = models.ForeignKey(Echo, on_delete=models.CASCADE, related_name='executions')
    exchange_connection = models.ForeignKey(ExchangeConnection, on_delete=models.CASCADE)
    
    # Order details
    exchange_order_id = models.CharField(max_length=100, blank=True)
    symbol = models.CharField(max_length=20)
    side = models.CharField(max_length=10)  # BUY/SELL
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    
    # Execution results
    filled_quantity = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    avg_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    commission = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    status = models.CharField(max_length=20, choices=EXECUTION_STATUS, default='pending')
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.side} {self.quantity} {self.symbol} @ {self.price}"

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