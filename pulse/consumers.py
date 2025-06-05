import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from mirrors.models import Mirror, Target
from .models import Echo, Pulse, ExchangeConnection
from .trading_service import execute_mirror_trades
import asyncio
from datetime import datetime
import random
import logging

logger = logging.getLogger(__name__)

class MirrorConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time mirror updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mirror_id = None
        self.mirror_group_name = None
        self.monitoring_task = None
        self.trade_positions = {}  # Track positions for P&L calculation
        
    async def connect(self):
        """Handle WebSocket connection"""
        self.mirror_id = self.scope['url_route']['kwargs']['mirror_id']
        self.mirror_group_name = f'mirror_{self.mirror_id}'
        
        # Join mirror group
        await self.channel_layer.group_add(
            self.mirror_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection success
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Neural link established',
            'mirror_id': self.mirror_id
        }))
        
        # Start monitoring if mirror is active
        mirror = await self.get_mirror()
        if mirror and mirror.state == 'hunting':
            self.monitoring_task = asyncio.create_task(self.monitor_targets())
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Cancel monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        # Leave mirror group
        await self.channel_layer.group_discard(
            self.mirror_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        command = data.get('command')
        
        if command == 'start_monitoring':
            await self.handle_start_monitoring()
        elif command == 'stop_monitoring':
            await self.handle_stop_monitoring()
        elif command == 'get_status':
            await self.send_mirror_status()
        elif command == 'execute_trade':
            await self.handle_manual_trade_execution(data)
    
    async def handle_start_monitoring(self):
        """Start monitoring targets"""
        mirror = await self.get_mirror()
        if mirror and mirror.state == 'hunting':
            if not self.monitoring_task or self.monitoring_task.done():
                self.monitoring_task = asyncio.create_task(self.monitor_targets())
                await self.send(text_data=json.dumps({
                    'type': 'monitoring_started',
                    'message': 'Target scanning initiated'
                }))
    
    async def handle_stop_monitoring(self):
        """Stop monitoring targets"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            await self.send(text_data=json.dumps({
                'type': 'monitoring_stopped',
                'message': 'Target scanning terminated'
            }))
    
    async def detect_platform(self, target):
        """Detect which platform the transaction occurred on"""
        # Simulate platform detection based on wallet patterns or APIs
        platforms = [
            'raydium', 'jupiter', 'pump', 'dexscreener', 'gmgn', 
            'photon', 'uniswap', 'pancakeswap'
        ]
        # In real implementation, this would analyze the transaction
        return random.choice(platforms)
    
    def calculate_trade_pnl(self, target_id, token, trade_type, price, amount):
        """Calculate P&L for a trade"""
        position_key = f"{target_id}_{token}"
        
        if position_key not in self.trade_positions:
            self.trade_positions[position_key] = {
                'entry_price': 0,
                'quantity': 0,
                'total_cost': 0
            }
        
        position = self.trade_positions[position_key]
        
        if trade_type == 'acquire':
            # Buy trade - update average entry price
            total_cost = position['total_cost'] + (price * amount)
            total_quantity = position['quantity'] + amount
            
            if total_quantity > 0:
                position['entry_price'] = total_cost / total_quantity
                position['quantity'] = total_quantity
                position['total_cost'] = total_cost
            
            return 0, 0  # No realized P&L on buy
        
        else:
            # Sell trade - calculate P&L
            if position['quantity'] > 0 and position['entry_price'] > 0:
                sell_quantity = min(amount, position['quantity'])
                pnl = (price - position['entry_price']) * sell_quantity
                pnl_percentage = ((price - position['entry_price']) / position['entry_price']) * 100
                
                # Update position
                position['quantity'] -= sell_quantity
                position['total_cost'] -= position['entry_price'] * sell_quantity
                
                if position['quantity'] <= 0:
                    # Position closed
                    position['entry_price'] = 0
                    position['quantity'] = 0
                    position['total_cost'] = 0
                
                return pnl, pnl_percentage
            
            return 0, 0

    async def monitor_targets(self):
        """Main monitoring loop - enhanced with platform detection and P&L"""
        while True:
            try:
                # Get mirror targets
                targets = await self.get_mirror_targets()
                
                for target in targets:
                    # Simulate wallet activity detection with platform info
                    await self.simulate_wallet_activity_enhanced(target)
                
                # Send heartbeat
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat',
                    'timestamp': datetime.now().isoformat(),
                    'targets_monitored': len(targets)
                }))
                
                # Wait before next scan
                await asyncio.sleep(5)  # 5 seconds for testing
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Monitoring error: {str(e)}'
                }))
                await asyncio.sleep(10)
    
    async def simulate_wallet_activity_enhanced(self, target):
        """Enhanced simulation with platform and P&L tracking"""
        import random
        
        # 15% chance of activity
        if random.random() < 0.15:
            # Simulate a trade
            trade_type = random.choice(['acquire', 'release'])
            token = random.choice(['BONK', 'WIF', 'POPCAT', 'MYRO', 'SAMO', 'BOME', 'MEW'])
            amount = round(random.uniform(10, 1000), 2)
            price = round(random.uniform(0.0001, 1), 6)
            total = round(amount * price, 2)
            
            # Detect platform
            platform = await self.detect_platform(target)
            
            # Calculate P&L
            pnl, pnl_percentage = self.calculate_trade_pnl(
                target.id, token, trade_type, price, amount
            )
            
            activity_data = {
                'type': 'wallet_activity',
                'target_id': str(target.id),
                'target_alias': target.alias or f'Target-{target.beacon_id[:8]}',
                'activity': {
                    'type': trade_type,
                    'token': token,
                    'amount': amount,
                    'price': price,
                    'total': total,
                    'platform': platform,
                    'pnl': round(pnl, 2) if pnl != 0 else None,
                    'pnl_percentage': round(pnl_percentage, 2) if pnl_percentage != 0 else None,
                    'timestamp': datetime.now().isoformat(),
                    'tx_hash': f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
                }
            }
            
            # Send to WebSocket
            await self.send(text_data=json.dumps(activity_data))
            
            # Create Echo record with enhanced data
            echo = await self.create_enhanced_echo(target, activity_data['activity'])
            
            # Execute copy trades automatically if exchanges are configured
            if echo:
                asyncio.create_task(self.execute_copy_trades(echo))
    
    async def execute_copy_trades(self, echo):
        """Execute copy trades for the detected activity"""
        try:
            # Check if there are active exchange connections
            connections = await self.get_exchange_connections()
            if connections:
                await execute_mirror_trades(self.mirror_id)
                
                await self.send(text_data=json.dumps({
                    'type': 'trade_executed',
                    'message': f'Copy trade executed for {echo.beacon_symbol}',
                    'echo_id': str(echo.id)
                }))
                
        except Exception as e:
            logger.error(f"Error executing copy trades: {e}")
            await self.send(text_data=json.dumps({
                'type': 'trade_error',
                'message': f'Failed to execute copy trade: {str(e)}'
            }))
    
    async def handle_manual_trade_execution(self, data):
        """Handle manual trade execution request"""
        try:
            echo_id = data.get('echo_id')
            if echo_id:
                echo = await self.get_echo_by_id(echo_id)
                if echo:
                    await self.execute_copy_trades(echo)
        except Exception as e:
            logger.error(f"Error in manual trade execution: {e}")
    
    async def send_mirror_status(self):
        """Send current mirror status with exchange info"""
        mirror = await self.get_mirror()
        if mirror:
            exchanges = await self.get_exchange_connections()
            status_data = {
                'type': 'mirror_status',
                'mirror': {
                    'id': str(mirror.id),
                    'codename': mirror.codename,
                    'state': mirror.state,
                    'sync_count': mirror.sync_count,
                    'success_rate': float(mirror.success_rate)
                },
                'exchanges': [
                    {
                        'exchange': conn.get_exchange_display(),
                        'is_active': conn.is_active,
                        'copy_percentage': float(conn.copy_percentage)
                    } for conn in exchanges
                ]
            }
            await self.send(text_data=json.dumps(status_data))
    
    # Database helper methods
    @database_sync_to_async
    def get_mirror(self):
        try:
            return Mirror.objects.get(id=self.mirror_id)
        except Mirror.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_mirror_targets(self):
        try:
            mirror = Mirror.objects.get(id=self.mirror_id)
            return list(mirror.targets.filter(is_tracking=True))
        except Mirror.DoesNotExist:
            return []
    
    @database_sync_to_async
    def get_exchange_connections(self):
        try:
            return list(ExchangeConnection.objects.filter(
                mirror_id=self.mirror_id,
                is_active=True
            ))
        except:
            return []
    
    @database_sync_to_async
    def get_echo_by_id(self, echo_id):
        try:
            return Echo.objects.get(id=echo_id)
        except Echo.DoesNotExist:
            return None
    
    @database_sync_to_async
    def create_enhanced_echo(self, target, activity):
        """Create Echo record with enhanced data including platform and P&L"""
        return Echo.objects.create(
            mirror_id=self.mirror_id,
            origin_target=target,
            echo_type=activity['type'],
            beacon_address=f"Token_{activity['token']}_Address",  # Simulated
            beacon_symbol=activity['token'],
            magnitude=activity['amount'],
            frequency=activity['price'],
            resonance=activity['total'],
            detected_platform=activity['platform'],
            platform_tx_hash=activity.get('tx_hash', ''),
            entry_price=activity['price'] if activity['type'] == 'acquire' else None,
            exit_price=activity['price'] if activity['type'] == 'release' else None,
            realized_pnl=activity.get('pnl'),
            pnl_percentage=activity.get('pnl_percentage'),
            phase='pending'
        )
    
    # WebSocket event handlers
    async def mirror_update(self, event):
        """Handle mirror update events"""
        await self.send(text_data=json.dumps({
            'type': 'mirror_update',
            'data': event['data']
        }))