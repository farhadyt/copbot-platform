import asyncio
import ccxt.async_support as ccxt
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Echo, TradeExecution, ExchangeConnection
import logging

logger = logging.getLogger(__name__)

class TradingService:
    """Service for executing trades on various exchanges"""
    
    def __init__(self):
        self.exchanges = {}
    
    def get_exchange_class(self, exchange_name):
        """Get the appropriate CCXT exchange class"""
        exchange_classes = {
            'binance': ccxt.binance,
            'okx': ccxt.okx,
            'bybit': ccxt.bybit,
            'kucoin': ccxt.kucoin,
            'mexc': ccxt.mexc,
            'gate': ccxt.gate,
        }
        return exchange_classes.get(exchange_name)
    
    async def initialize_exchange(self, exchange_connection):
        """Initialize exchange connection"""
        exchange_class = self.get_exchange_class(exchange_connection.exchange)
        if not exchange_class:
            raise ValueError(f"Unsupported exchange: {exchange_connection.exchange}")
        
        config = {
            'apiKey': exchange_connection.api_key,
            'secret': exchange_connection.api_secret,
            'sandbox': exchange_connection.is_testnet,
            'enableRateLimit': True,
        }
        
        exchange = exchange_class(config)
        self.exchanges[exchange_connection.id] = exchange
        return exchange
    
    async def execute_copy_trade(self, echo, exchange_connection):
        """Execute a copy trade on the specified exchange"""
        try:
            # Initialize exchange if not already done
            if exchange_connection.id not in self.exchanges:
                await self.initialize_exchange(exchange_connection)
            
            exchange = self.exchanges[exchange_connection.id]
            
            # Calculate trade size based on copy percentage
            original_amount = float(echo.magnitude)
            copy_amount = original_amount * (float(exchange_connection.copy_percentage) / 100)
            
            # Apply min/max limits
            copy_amount = max(copy_amount, float(exchange_connection.min_trade_amount))
            copy_amount = min(copy_amount, float(exchange_connection.max_trade_amount))
            
            # Determine trade side
            side = 'buy' if echo.echo_type == 'acquire' else 'sell'
            
            # Create symbol (e.g., WIF/USDT)
            symbol = f"{echo.beacon_symbol}/USDT"
            
            # Create trade execution record
            execution = TradeExecution.objects.create(
                echo=echo,
                exchange_connection=exchange_connection,
                symbol=symbol,
                side=side.upper(),
                quantity=Decimal(str(copy_amount)),
                price=echo.frequency,  # Use detected price
                status='pending'
            )
            
            try:
                # Execute the trade
                if side == 'buy':
                    order = await exchange.create_market_buy_order(symbol, copy_amount)
                else:
                    order = await exchange.create_market_sell_order(symbol, copy_amount)
                
                # Update execution record with results
                execution.exchange_order_id = order['id']
                execution.filled_quantity = Decimal(str(order.get('filled', 0)))
                execution.avg_price = Decimal(str(order.get('average', 0))) if order.get('average') else None
                execution.commission = Decimal(str(order.get('fee', {}).get('cost', 0)))
                execution.status = 'filled' if order.get('status') == 'closed' else 'partially_filled'
                execution.executed_at = timezone.now()
                execution.save()
                
                # Update echo status
                echo.phase = 'synced'
                echo.sync_hash = order['id']
                echo.save()
                
                logger.info(f"Successfully executed copy trade: {side} {copy_amount} {symbol}")
                return True
                
            except Exception as e:
                # Handle trade execution errors
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.save()
                
                echo.phase = 'failed'
                echo.save()
                
                logger.error(f"Failed to execute copy trade: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error in copy trade execution: {e}")
            return False
    
    async def process_pending_trades(self, mirror_id):
        """Process all pending trades for a mirror"""
        pending_echoes = Echo.objects.filter(
            mirror_id=mirror_id,
            phase='pending'
        ).select_related('mirror', 'origin_target')
        
        # Get active exchange connections for this mirror
        exchange_connections = ExchangeConnection.objects.filter(
            mirror_id=mirror_id,
            is_active=True
        )
        
        for echo in pending_echoes:
            for conn in exchange_connections:
                await self.execute_copy_trade(echo, conn)
    
    async def close_all_connections(self):
        """Close all exchange connections"""
        for exchange in self.exchanges.values():
            await exchange.close()
        self.exchanges.clear()

# Global trading service instance
trading_service = TradingService()

async def execute_mirror_trades(mirror_id):
    """Execute all pending trades for a mirror"""
    try:
        await trading_service.process_pending_trades(mirror_id)
    except Exception as e:
        logger.error(f"Error processing mirror trades: {e}")
    finally:
        await trading_service.close_all_connections() 