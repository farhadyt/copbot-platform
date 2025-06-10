from django.contrib import admin
from .models import Mirror, Target, TradingPlatform, ConnectedWallet, TradingBot, TradeExecution, Agent, Transaction
from django.utils.html import format_html

@admin.register(Mirror)
class MirrorAdmin(admin.ModelAdmin):
    list_display = ['codename', 'pilot', 'mirror_type', 'state', 'sync_count', 'awakened_at']
    list_filter = ['mirror_type', 'state', 'awakened_at']
    search_fields = ['codename', 'pilot__username']

@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ['alias', 'beacon_id', 'mirror', 'is_tracking', 'echoes_captured']
    list_filter = ['is_tracking', 'mirror']
    search_fields = ['alias', 'beacon_id']

@admin.register(TradingPlatform)
class TradingPlatformAdmin(admin.ModelAdmin):
    list_display = ['name', 'api_endpoint', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(ConnectedWallet)
class ConnectedWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'address', 'platform', 'balance', 'is_active', 'last_sync']
    list_filter = ['platform', 'is_active']
    search_fields = ['user__username', 'address']
    readonly_fields = ['created_at', 'last_sync']

@admin.register(TradingBot)
class TradingBotAdmin(admin.ModelAdmin):
    list_display = ['mirror', 'platform', 'is_active', 'copy_mode', 'success_rate', 'net_profit', 'total_trades']
    list_filter = ['is_active', 'copy_mode', 'platform']
    search_fields = ['mirror__codename']
    readonly_fields = ['total_trades', 'successful_trades', 'failed_trades', 'total_profit', 'total_loss', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('mirror', 'wallet', 'platform', 'is_active', 'copy_mode')
        }),
        ('Risk Management', {
            'fields': ('max_trade_size', 'min_trade_size', 'daily_loss_limit', 'take_profit_percentage', 'stop_loss_percentage')
        }),
        ('Advanced Settings', {
            'fields': ('slippage_tolerance', 'gas_limit_multiplier', 'delay_seconds')
        }),
        ('Statistics', {
            'fields': ('total_trades', 'successful_trades', 'failed_trades', 'total_profit', 'total_loss', 'created_at', 'updated_at')
        }),
    )

@admin.register(TradeExecution)
class TradeExecutionAdmin(admin.ModelAdmin):
    list_display = ['token_symbol', 'trade_type', 'amount', 'status', 'realized_pnl', 'created_at']
    list_filter = ['status', 'trade_type', 'created_at']
    search_fields = ['token_symbol', 'token_address', 'execution_tx_hash']
    readonly_fields = ['created_at', 'executed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bot', 'bot__mirror')

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'agent_type', 'pilot', 'is_active', 'created_at']
    list_filter = ['agent_type', 'is_active', 'created_at']
    search_fields = ['name', 'pilot__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('pilot', 'agent_type', 'name', 'is_active')
        }),
        ('Schedule', {
            'fields': ('active_days', 'active_hours_start', 'active_hours_end')
        }),
        ('Transaction Limits', {
            'fields': ('max_transactions_hour', 'max_transactions_day', 'scan_frequency')
        }),
        ('Value Filters', {
            'fields': ('min_transaction_value', 'max_transaction_value', 'min_wallet_balance')
        }),
        ('Token Filters', {
            'fields': ('token_filter_type', 'excluded_tokens', 'included_tokens')
        }),
        ('Database Retention', {
            'fields': ('max_retention_days',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'agent', 'wallet_address_short', 'token_symbol', 'amount', 
        'price_usd', 'total_value_usd', 'tx_type', 'platform', 
        'is_closed', 'profit_display', 'timestamp'
    ]
    list_filter = [
        'agent__agent_type', 'tx_type', 'status', 'is_closed', 
        'platform', 'timestamp'
    ]
    search_fields = [
        'wallet_address', 'tx_hash', 'signature', 'token_symbol', 
        'token_address', 'agent__name'
    ]
    readonly_fields = [
        'tx_hash', 'signature', 'timestamp', 'slot', 'created_at', 
        'updated_at', 'realized_profit_usd', 'profit_percent'
    ]
    
    fieldsets = [
        ('Agent & Basic Info', {
            'fields': ('agent', 'wallet_address', 'timestamp')
        }),
        ('Transaction Details', {
            'fields': (
                'tx_hash', 'signature', 'slot', 'status', 'platform'
            )
        }),
        ('Token Information', {
            'fields': (
                'token_symbol', 'token_address', 'amount', 
                'price_usd', 'total_value_usd', 'tx_type'
            )
        }),
        ('Trade Matching & P&L', {
            'fields': (
                'is_closed', 'closed_at', 'linked_transaction', 
                'realized_profit_usd', 'profit_percent'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def wallet_address_short(self, obj):
        """Display shortened wallet address"""
        return f"{obj.wallet_address[:8]}...{obj.wallet_address[-4:]}" if obj.wallet_address else "N/A"
    wallet_address_short.short_description = "Wallet"
    
    def profit_display(self, obj):
        """Display profit with color coding"""
        if not obj.is_closed or not obj.realized_profit_usd:
            return "-"
        
        profit = float(obj.realized_profit_usd)
        color = "green" if profit > 0 else "red"
        return format_html(
            '<span style="color: {};">${:.2f} ({:.1f}%)</span>',
            color, profit, float(obj.profit_percent or 0)
        )
    profit_display.short_description = "P&L"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('agent', 'linked_transaction')