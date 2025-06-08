from django.contrib import admin
from .models import Mirror, Target, TradingPlatform, ConnectedWallet, TradingBot, TradeExecution

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