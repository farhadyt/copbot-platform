from django.contrib import admin
from .models import Echo, Pulse, ExchangeConnection, TradeExecution

@admin.register(Echo)
class EchoAdmin(admin.ModelAdmin):
    list_display = ['beacon_symbol', 'echo_type', 'magnitude', 'frequency', 'detected_platform', 'realized_pnl', 'phase', 'pulsed_at']
    list_filter = ['echo_type', 'phase', 'detected_platform', 'pulsed_at']
    search_fields = ['beacon_symbol', 'beacon_address', 'platform_tx_hash']
    readonly_fields = ['pulsed_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('mirror', 'origin_target', 'echo_type', 'beacon_address', 'beacon_symbol')
        }),
        ('Trade Details', {
            'fields': ('magnitude', 'frequency', 'resonance', 'detected_platform', 'platform_tx_hash')
        }),
        ('P&L Analysis', {
            'fields': ('entry_price', 'exit_price', 'realized_pnl', 'pnl_percentage')
        }),
        ('Execution', {
            'fields': ('phase', 'sync_hash', 'energy_cost', 'drift', 'amplitude_gain', 'gain_percentage')
        }),
        ('Timestamps', {
            'fields': ('pulsed_at',)
        }),
    )

@admin.register(ExchangeConnection)
class ExchangeConnectionAdmin(admin.ModelAdmin):
    list_display = ['mirror', 'exchange', 'copy_percentage', 'is_active', 'is_testnet', 'created_at']
    list_filter = ['exchange', 'is_active', 'is_testnet', 'created_at']
    search_fields = ['mirror__codename']
    
    fieldsets = (
        ('Connection Info', {
            'fields': ('mirror', 'exchange', 'api_key', 'api_secret', 'is_testnet')
        }),
        ('Trading Settings', {
            'fields': ('copy_percentage', 'min_trade_amount', 'max_trade_amount')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )
    
    readonly_fields = ['created_at']

@admin.register(TradeExecution)
class TradeExecutionAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'side', 'quantity', 'price', 'status', 'exchange_connection', 'created_at']
    list_filter = ['side', 'status', 'exchange_connection__exchange', 'created_at']
    search_fields = ['symbol', 'exchange_order_id']
    readonly_fields = ['created_at', 'executed_at']
    
    fieldsets = (
        ('Order Details', {
            'fields': ('echo', 'exchange_connection', 'exchange_order_id', 'symbol', 'side')
        }),
        ('Trade Info', {
            'fields': ('quantity', 'price', 'filled_quantity', 'avg_price', 'commission')
        }),
        ('Status & Errors', {
            'fields': ('status', 'error_message', 'retry_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'executed_at')
        }),
    )

@admin.register(Pulse)
class PulseAdmin(admin.ModelAdmin):
    list_display = ['mirror', 'timestamp', 'sync_latency', 'echo_count', 'success_count', 'total_amplitude']
    list_filter = ['mirror', 'timestamp']
    readonly_fields = ['timestamp']
