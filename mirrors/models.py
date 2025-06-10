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

class Agent(models.Model):
    """New Agent system replacing Mirrors - 4 agent types"""
    
    AGENT_TYPES = [
        ('shadow', 'Shadow'),
        ('hawk', 'Hawk'),
        ('hunter', 'Hunter'),
        ('mirror', 'Mirror'),
    ]
    
    # Agent basic info
    pilot = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agents')
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    # Active days and hours
    active_days = models.JSONField(default=list, help_text="List of active days: 0=Monday, 6=Sunday")
    active_hours_start = models.TimeField(default='00:00')
    active_hours_end = models.TimeField(default='23:59')
    
    # Transaction limits
    max_transactions_hour = models.IntegerField(null=True, blank=True, help_text="Null means unlimited")
    max_transactions_day = models.IntegerField(null=True, blank=True, help_text="Null means unlimited")
    scan_frequency = models.CharField(max_length=50, default="Maximum Fast")
    
    # Value filters
    min_transaction_value = models.DecimalField(max_digits=20, decimal_places=8, default=1.0)
    max_transaction_value = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    min_wallet_balance = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Token filters
    token_filter_type = models.CharField(max_length=20, choices=[
        ('all', 'All Tokens'),
        ('exclude', 'Exclude These Tokens'),
        ('include', 'Only These Tokens'),
    ], default='all')
    excluded_tokens = models.TextField(blank=True, help_text="Comma-separated list of tokens to exclude")
    included_tokens = models.TextField(blank=True, help_text="Comma-separated list of tokens to include")
    
    # Database retention
    max_retention_days = models.IntegerField(default=10, help_text="Keep transaction data for X days")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['pilot', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_agent_type_display()})"
    
    @classmethod
    def generate_agent_name(cls, agent_type, pilot):
        """Generate auto-incrementing agent name like Shadow-1, Hawk-2, etc."""
        count = cls.objects.filter(agent_type=agent_type, pilot=pilot).count()
        return f"{agent_type.title()}-{count + 1}"
    
    def clean_old_transactions(self):
        """Clean old transactions based on database retention policy (FIFO)"""
        if self.agent_type == 'shadow' and self.max_retention_days:
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=self.max_retention_days)
            
            # Get old transactions
            old_transactions = self.transactions.filter(
                timestamp__lt=cutoff_date
            ).order_by('timestamp')
            
            count = old_transactions.count()
            if count > 0:
                old_transactions.delete()
                return count
        
        return 0
    
    def get_transaction_stats(self):
        """Get transaction statistics for this agent"""
        if self.agent_type != 'shadow':
            return {}
        
        total_transactions = self.transactions.count()
        successful_trades = self.transactions.filter(is_closed=True, realized_profit_usd__gt=0).count()
        total_trades = self.transactions.filter(is_closed=True).count()
        
        total_profit = self.transactions.filter(
            is_closed=True, realized_profit_usd__isnull=False
        ).aggregate(
            total=models.Sum('realized_profit_usd')
        )['total'] or 0
        
        return {
            'total_transactions': total_transactions,
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'win_rate': round((successful_trades / total_trades * 100), 2) if total_trades > 0 else 0,
            'total_profit': float(total_profit),
            'is_monitoring': hasattr(self, '_is_monitoring') and self._is_monitoring
        }

class Transaction(models.Model):
    """Transaction records detected by Shadow agents from Solana network"""
    
    TX_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    STATUSES = [
        ('SUCCESS', 'Success'),
        ('FAIL', 'Fail'),
        ('PENDING', 'Pending'),
    ]
    
    # Required fields
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='transactions')
    wallet_address = models.CharField(max_length=200, db_index=True)
    tx_hash = models.CharField(max_length=200, unique=True, db_index=True)
    signature = models.CharField(max_length=200, db_index=True)
    token_symbol = models.CharField(max_length=50)
    token_address = models.CharField(max_length=200, db_index=True)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    price_usd = models.DecimalField(max_digits=20, decimal_places=8)
    total_value_usd = models.DecimalField(max_digits=20, decimal_places=8)
    tx_type = models.CharField(max_length=10, choices=TX_TYPES, default='UNKNOWN')
    platform = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(db_index=True)
    slot = models.BigIntegerField()
    status = models.CharField(max_length=10, choices=STATUSES, default='SUCCESS')
    
    # Trade matching and P&L tracking
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    realized_profit_usd = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    profit_percent = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Linked transaction for P&L calculation
    linked_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_trades')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent', 'timestamp']),
            models.Index(fields=['wallet_address', 'token_address']),
            models.Index(fields=['tx_type', 'is_closed']),
        ]
    
    def __str__(self):
        return f"{self.tx_type} {self.amount} {self.token_symbol} - {self.wallet_address[:8]}..."
    
    @property
    def is_profitable(self):
        """Returns True if transaction is profitable (for closed trades)"""
        return self.is_closed and self.realized_profit_usd and self.realized_profit_usd > 0
    
    def close_trade_with(self, exit_transaction):
        """Close this trade with a matching exit transaction and calculate P&L"""
        if self.tx_type == 'BUY' and exit_transaction.tx_type == 'SELL':
            # Calculate profit from buy to sell
            profit_usd = (exit_transaction.price_usd - self.price_usd) * float(self.amount)
            profit_percent = ((exit_transaction.price_usd - self.price_usd) / self.price_usd) * 100
        elif self.tx_type == 'SELL' and exit_transaction.tx_type == 'BUY':
            # Calculate profit from sell to buy (short position)
            profit_usd = (self.price_usd - exit_transaction.price_usd) * float(self.amount)
            profit_percent = ((self.price_usd - exit_transaction.price_usd) / exit_transaction.price_usd) * 100
        else:
            return False
        
        # Update both transactions
        self.is_closed = True
        self.closed_at = exit_transaction.timestamp
        self.realized_profit_usd = profit_usd
        self.profit_percent = profit_percent
        self.linked_transaction = exit_transaction
        self.save()
        
        exit_transaction.is_closed = True
        exit_transaction.closed_at = exit_transaction.timestamp
        exit_transaction.realized_profit_usd = profit_usd
        exit_transaction.profit_percent = profit_percent
        exit_transaction.linked_transaction = self
        exit_transaction.save()
        
        return True