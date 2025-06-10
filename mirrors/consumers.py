import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from .models import Agent, Transaction
from .solana_monitor import start_agent_monitoring, stop_agent_monitoring

logger = logging.getLogger(__name__)

class AgentConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time agent monitoring and transaction updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_id = None
        self.agent_group_name = None
        
    async def connect(self):
        """Handle WebSocket connection"""
        self.agent_id = self.scope['url_route']['kwargs']['agent_id']
        self.user_id = self.scope['url_route']['kwargs'].get('user_id', None)
        self.agent_group_name = f'agent_{self.agent_id}'
        
        # Join agent group
        await self.channel_layer.group_add(
            self.agent_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection success
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Agent monitoring active',
            'agent_id': self.agent_id
        }))
        
        # Send current agent status
        await self.send_agent_status()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave agent group
        await self.channel_layer.group_discard(
            self.agent_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'get_status':
                await self.send_agent_status()
            elif command == 'get_transactions':
                await self.send_transactions()
            elif command == 'start_monitoring':
                await self.handle_start_monitoring()
            elif command == 'stop_monitoring':
                await self.handle_stop_monitoring()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON received'
            }))
    
    async def send_agent_status(self):
        """Send current agent status and statistics"""
        try:
            agent = await self.get_agent()
            if agent:
                stats = await sync_to_async(agent.get_transaction_stats)()
                
                await self.send(text_data=json.dumps({
                    'type': 'agent_status',
                    'agent': {
                        'id': str(agent.id),
                        'name': agent.name,
                        'agent_type': agent.agent_type,
                        'is_active': agent.is_active,
                        'created_at': agent.created_at.isoformat(),
                    },
                    'stats': stats
                }))
        except Exception as e:
            logger.error(f"Error sending agent status: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error fetching agent status'
            }))
    
    async def send_transactions(self, limit=50):
        """Send recent transactions for the agent"""
        try:
            transactions = await self.get_recent_transactions(limit)
            
            transactions_data = []
            for tx in transactions:
                transactions_data.append({
                    'id': str(tx.id),
                    'wallet_address': tx.wallet_address,
                    'tx_hash': tx.tx_hash,
                    'token_symbol': tx.token_symbol,
                    'amount': str(tx.amount),
                    'price_usd': str(tx.price_usd),
                    'total_value_usd': str(tx.total_value_usd),
                    'tx_type': tx.tx_type,
                    'platform': tx.platform,
                    'timestamp': tx.timestamp.isoformat(),
                    'is_closed': tx.is_closed,
                    'realized_profit_usd': str(tx.realized_profit_usd) if tx.realized_profit_usd else None,
                    'profit_percent': str(tx.profit_percent) if tx.profit_percent else None,
                })
            
            await self.send(text_data=json.dumps({
                'type': 'transactions',
                'data': transactions_data
            }))
            
        except Exception as e:
            logger.error(f"Error sending transactions: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error fetching transactions'
            }))
    
    async def handle_start_monitoring(self):
        """Start Solana monitoring for the agent"""
        try:
            agent = await self.get_agent()
            if agent and agent.agent_type == 'shadow':
                success = await start_agent_monitoring(agent.id)
                
                if success:
                    await self.send(text_data=json.dumps({
                        'type': 'monitoring_started',
                        'message': f'Solana monitoring started for {agent.name}'
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Failed to start Solana monitoring'
                    }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Only Shadow agents support Solana monitoring'
                }))
                
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error starting monitoring'
            }))
    
    async def handle_stop_monitoring(self):
        """Stop Solana monitoring for the agent"""
        try:
            success = await stop_agent_monitoring(self.agent_id)
            
            await self.send(text_data=json.dumps({
                'type': 'monitoring_stopped',
                'message': 'Solana monitoring stopped'
            }))
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error stopping monitoring'
            }))
    
    # Event handlers for group messages
    async def new_transaction(self, event):
        """Handle new transaction notifications"""
        await self.send(text_data=json.dumps({
            'type': 'new_transaction',
            'transaction': event['transaction']
        }))
    
    async def agent_update(self, event):
        """Handle agent status updates"""
        await self.send(text_data=json.dumps({
            'type': 'agent_update',
            'data': event['data']
        }))
    
    # Database helper methods
    @database_sync_to_async
    def get_agent(self):
        try:
            return Agent.objects.get(id=self.agent_id)
        except Agent.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_recent_transactions(self, limit=50):
        try:
            return list(
                Transaction.objects.filter(agent_id=self.agent_id)
                .order_by('-timestamp')[:limit]
            )
        except:
            return []


# Utility function to send transaction updates to agent groups
async def notify_new_transaction(agent_id, transaction_data):
    """Send new transaction notification to agent WebSocket group"""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    if channel_layer:
        await channel_layer.group_send(
            f'agent_{agent_id}',
            {
                'type': 'new_transaction',
                'transaction': transaction_data
            }
        ) 