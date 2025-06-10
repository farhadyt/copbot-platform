import os
import django
import asyncio
import logging
from datetime import datetime
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'copbot.settings')
django.setup()

from mirrors.models import Agent, Transaction
from django.utils import timezone

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_transactions():
    """Create test transactions to verify the system is working"""
    
    # Get the first Shadow agent
    try:
        agent = Agent.objects.filter(agent_type='shadow').first()
        if not agent:
            logger.error("No Shadow agent found. Please create one first.")
            return
            
        logger.info(f"Using agent: {agent.name}")
        
        # Create a few test transactions
        test_transactions = [
            {
                'wallet_address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
                'token_symbol': 'SOL',
                'token_address': 'So11111111111111111111111111111111111111112',
                'amount': Decimal('10.5'),
                'price_usd': Decimal('95.50'),
                'tx_type': 'BUY',
                'platform': 'Raydium',
            },
            {
                'wallet_address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
                'token_symbol': 'BONK',
                'token_address': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
                'amount': Decimal('1000000'),
                'price_usd': Decimal('0.000025'),
                'tx_type': 'BUY',
                'platform': 'Jupiter',
            },
            {
                'wallet_address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
                'token_symbol': 'WIF',
                'token_address': 'EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm',
                'amount': Decimal('50'),
                'price_usd': Decimal('2.35'),
                'tx_type': 'SELL',
                'platform': 'Orca',
            }
        ]
        
        for i, tx_data in enumerate(test_transactions):
            # Generate unique transaction hash
            tx_hash = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}{i}"
            
            transaction = Transaction.objects.create(
                agent=agent,
                wallet_address=tx_data['wallet_address'],
                tx_hash=tx_hash,
                signature=tx_hash,
                token_symbol=tx_data['token_symbol'],
                token_address=tx_data['token_address'],
                amount=tx_data['amount'],
                price_usd=tx_data['price_usd'],
                total_value_usd=tx_data['amount'] * tx_data['price_usd'],
                tx_type=tx_data['tx_type'],
                platform=tx_data['platform'],
                timestamp=timezone.now(),
                slot=1000000 + i,
                status='SUCCESS'
            )
            
            logger.info(f"✅ Created test transaction: {transaction.token_symbol} {transaction.tx_type} - ${transaction.total_value_usd}")
            
            # Wait a bit between transactions
            await asyncio.sleep(1)
            
        logger.info(f"✨ Created {len(test_transactions)} test transactions")
        logger.info("Check the transactions page to see them!")
        
    except Exception as e:
        logger.error(f"Error creating test transactions: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_transactions()) 