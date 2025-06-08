"""
Trading Bot Service - Handles automated trade execution
"""
import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import aiohttp
from django.utils import timezone
from django.db import transaction

from .models import TradingBot, TradeExecution, ConnectedWallet
from cryptography.fernet import Fernet
import json

logger = logging.getLogger(__name__)


class TradingBotService:
    """Service for executing automated trades based on mirror activity"""
    
    def __init__(self):
        self.active_bots = {}
        self.encryption_key = Fernet.generate_key()  # In production, use a secure key management system
        self.cipher = Fernet(self.encryption_key)
        
        # Platform endpoints (example configuration)
        self.platform_endpoints = {
            'raydium': 'https://api.raydium.io/v2',
            'jupiter': 'https://price.jup.ag/v4',
            'pump': 'https://api.pump.fun',
            'orca': 'https://api.orca.so',
        }
    
    async def execute_trade(self, bot_id: int, trade_data: Dict) -> TradeExecution:
        """Execute a trade for a specific trading bot"""
        try:
            bot = await self._get_bot(bot_id)
            if not bot or not bot.is_active:
                raise ValueError("Trading bot not found or inactive")
            
            # Check risk limits
            await self._check_risk_limits(bot, trade_data)
            
            # Create trade execution record
            execution = await self._create_execution_record(bot, trade_data)
            
            # Calculate trade parameters based on copy mode
            trade_params = await self._calculate_trade_params(bot, trade_data)
            
            # Execute the trade
            result = await self._execute_platform_trade(bot, trade_params, execution)
            
            # Update execution record
            await self._update_execution_record(execution, result)
            
            # Update bot statistics
            await self._update_bot_stats(bot, execution)
            
            return execution
            
        except Exception as e:
            logger.error(f"Trade execution failed: {str(e)}")
            if 'execution' in locals():
                execution.status = 'failed'
                execution.error_message = str(e)
                await self._save_execution(execution)
            raise
    
    async def _get_bot(self, bot_id: int) -> Optional[TradingBot]:
        """Get trading bot by ID"""
        try:
            return TradingBot.objects.select_related('wallet', 'platform').get(id=bot_id)
        except TradingBot.DoesNotExist:
            return None
    
    async def _check_risk_limits(self, bot: TradingBot, trade_data: Dict):
        """Check if trade meets risk management criteria"""
        # Check daily loss limit
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_executions = TradeExecution.objects.filter(
            bot=bot,
            created_at__gte=today_start,
            status='success'
        )
        
        daily_loss = sum(
            abs(exec.realized_pnl) for exec in today_executions 
            if exec.realized_pnl and exec.realized_pnl < 0
        )
        
        if daily_loss >= bot.daily_loss_limit:
            raise ValueError(f"Daily loss limit reached: ${daily_loss}")
        
        # Check trade size limits
        trade_amount = Decimal(str(trade_data.get('amount', 0)))
        if trade_amount < bot.min_trade_size:
            raise ValueError(f"Trade size below minimum: {trade_amount} < {bot.min_trade_size}")
        
        if trade_amount > bot.max_trade_size:
            raise ValueError(f"Trade size above maximum: {trade_amount} > {bot.max_trade_size}")
    
    async def _create_execution_record(self, bot: TradingBot, trade_data: Dict) -> TradeExecution:
        """Create initial trade execution record"""
        execution = TradeExecution(
            bot=bot,
            original_tx_hash=trade_data.get('tx_hash', ''),
            token_address=trade_data.get('token_address', ''),
            token_symbol=trade_data.get('token', ''),
            trade_type=trade_data.get('type', ''),
            amount=Decimal(str(trade_data.get('amount', 0))),
            price=Decimal(str(trade_data.get('price', 0))),
            total_value=Decimal(str(trade_data.get('total', 0))),
            status='pending'
        )
        await self._save_execution(execution)
        return execution
    
    async def _calculate_trade_params(self, bot: TradingBot, trade_data: Dict) -> Dict:
        """Calculate trade parameters based on bot configuration"""
        original_amount = Decimal(str(trade_data.get('amount', 0)))
        original_value = Decimal(str(trade_data.get('total', 0)))
        
        if bot.copy_mode == 'exact':
            # Copy exact amount
            trade_amount = original_amount
        elif bot.copy_mode == 'proportional':
            # Calculate proportional amount based on wallet balance
            wallet_balance = await self._get_wallet_balance(bot.wallet)
            proportion = min(wallet_balance / original_value, Decimal('1.0'))
            trade_amount = original_amount * proportion
        elif bot.copy_mode == 'fixed':
            # Use fixed amount configured in bot
            trade_amount = bot.max_trade_size
        else:
            trade_amount = original_amount
        
        # Apply trade size limits
        trade_amount = max(min(trade_amount, bot.max_trade_size), bot.min_trade_size)
        
        return {
            'token_address': trade_data.get('token_address'),
            'token_symbol': trade_data.get('token'),
            'type': trade_data.get('type'),
            'amount': trade_amount,
            'price': Decimal(str(trade_data.get('price', 0))),
            'slippage': bot.slippage_tolerance,
            'gas_multiplier': bot.gas_limit_multiplier,
        }
    
    async def _execute_platform_trade(self, bot: TradingBot, params: Dict, execution: TradeExecution) -> Dict:
        """Execute trade on the specified platform"""
        platform = bot.platform.name.lower()
        
        # Update execution status
        execution.status = 'executing'
        await self._save_execution(execution)
        
        # Apply delay if configured
        if bot.delay_seconds > 0:
            await asyncio.sleep(bot.delay_seconds)
        
        # Platform-specific execution
        if platform == 'raydium':
            result = await self._execute_raydium_trade(bot, params)
        elif platform == 'jupiter':
            result = await self._execute_jupiter_trade(bot, params)
        elif platform == 'pump':
            result = await self._execute_pump_trade(bot, params)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return result
    
    async def _execute_raydium_trade(self, bot: TradingBot, params: Dict) -> Dict:
        """Execute trade on Raydium"""
        # This is a simplified example - actual implementation would interact with Raydium's API
        async with aiohttp.ClientSession() as session:
            # Decrypt wallet private key
            private_key = self._decrypt_private_key(bot.wallet.private_key_encrypted)
            
            # Prepare transaction
            tx_data = {
                'wallet': bot.wallet.address,
                'token': params['token_address'],
                'amount': str(params['amount']),
                'type': params['type'],
                'slippage': str(params['slippage']),
            }
            
            # In production, this would sign and submit the transaction to Solana
            # For now, return mock successful result
            return {
                'success': True,
                'tx_hash': f"mock_tx_{datetime.now().timestamp()}",
                'executed_price': float(params['price']) * 1.001,  # Simulate slight slippage
                'executed_amount': float(params['amount']),
                'gas_used': 0.005,  # SOL
            }
    
    async def _execute_jupiter_trade(self, bot: TradingBot, params: Dict) -> Dict:
        """Execute trade on Jupiter aggregator"""
        # Similar implementation for Jupiter
        return {
            'success': True,
            'tx_hash': f"mock_jupiter_tx_{datetime.now().timestamp()}",
            'executed_price': float(params['price']) * 1.002,
            'executed_amount': float(params['amount']),
            'gas_used': 0.004,
        }
    
    async def _execute_pump_trade(self, bot: TradingBot, params: Dict) -> Dict:
        """Execute trade on Pump.fun"""
        # Similar implementation for Pump.fun
        return {
            'success': True,
            'tx_hash': f"mock_pump_tx_{datetime.now().timestamp()}",
            'executed_price': float(params['price']) * 1.003,
            'executed_amount': float(params['amount']),
            'gas_used': 0.006,
        }
    
    async def _update_execution_record(self, execution: TradeExecution, result: Dict):
        """Update execution record with trade result"""
        if result.get('success'):
            execution.status = 'success'
            execution.execution_tx_hash = result.get('tx_hash')
            execution.executed_price = Decimal(str(result.get('executed_price', 0)))
            execution.executed_amount = Decimal(str(result.get('executed_amount', 0)))
            execution.gas_used = Decimal(str(result.get('gas_used', 0)))
            execution.executed_at = timezone.now()
            
            # Calculate P&L if this is a sell order
            if execution.trade_type == 'sell':
                # Look for corresponding buy order
                buy_execution = TradeExecution.objects.filter(
                    bot=execution.bot,
                    token_address=execution.token_address,
                    trade_type='buy',
                    status='success',
                    executed_at__lt=execution.created_at
                ).order_by('-executed_at').first()
                
                if buy_execution:
                    execution.entry_price = buy_execution.executed_price
                    execution.exit_price = execution.executed_price
                    execution.realized_pnl = (
                        (execution.exit_price - execution.entry_price) * 
                        execution.executed_amount
                    )
        else:
            execution.status = 'failed'
            execution.error_message = result.get('error', 'Unknown error')
        
        await self._save_execution(execution)
    
    async def _update_bot_stats(self, bot: TradingBot, execution: TradeExecution):
        """Update bot statistics after trade execution"""
        with transaction.atomic():
            bot.total_trades += 1
            
            if execution.status == 'success':
                bot.successful_trades += 1
                
                if execution.realized_pnl:
                    if execution.realized_pnl > 0:
                        bot.total_profit += execution.realized_pnl
                    else:
                        bot.total_loss += abs(execution.realized_pnl)
            else:
                bot.failed_trades += 1
            
            bot.save()
    
    async def _get_wallet_balance(self, wallet: ConnectedWallet) -> Decimal:
        """Get current wallet balance"""
        # In production, this would query the blockchain for actual balance
        # For now, return the stored balance
        return wallet.balance
    
    def _decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt wallet private key"""
        # In production, use secure key management
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    async def _save_execution(self, execution: TradeExecution):
        """Save execution record to database"""
        execution.save()
    
    def start_monitoring(self, bot_id: int):
        """Start monitoring for a specific bot"""
        self.active_bots[bot_id] = True
        logger.info(f"Started monitoring for bot {bot_id}")
    
    def stop_monitoring(self, bot_id: int):
        """Stop monitoring for a specific bot"""
        if bot_id in self.active_bots:
            del self.active_bots[bot_id]
            logger.info(f"Stopped monitoring for bot {bot_id}")


# Global instance
trading_bot_service = TradingBotService() 