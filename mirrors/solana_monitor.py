import asyncio
import json
import websockets
import logging
import aiohttp
import re
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import Agent, Transaction

logger = logging.getLogger(__name__)

class SolanaMonitor:
    """
    Enhanced Solana WebSocket Monitor for Shadow Agents
    Connects to Solana RPC WebSocket and monitors real-time transactions
    """
    
    # Multiple Solana RPC WebSocket endpoints for redundancy
    SOLANA_WS_URLS = [
        "wss://api.mainnet-beta.solana.com",
        "wss://solana-mainnet.g.alchemy.com/v2/demo",  # Alchemy demo endpoint
        "wss://rpc.ankr.com/solana_ws",  # Fixed Ankr WebSocket endpoint
        "wss://api.devnet.solana.com",  # Fallback to devnet for testing
    ]
    
    # HTTP RPC endpoints for transaction details
    SOLANA_RPC_URLS = [
        "https://api.mainnet-beta.solana.com",
        "https://solana-mainnet.g.alchemy.com/v2/demo",
        "https://rpc.ankr.com/solana",
    ]
    
    # Known DEX program IDs to monitor
    DEX_PROGRAM_IDS = [
        "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium
        "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",  # Jupiter
        "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",  # Orca
        "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP",  # Orca V2
        "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX",  # Serum
        "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",  # PumpFun
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",   # SPL Token Program
    ]
    
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.agent = None
        self.websocket = None
        self.is_monitoring = False
        self.subscription_id = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.processed_signatures = set()  # Track processed transactions
        self.current_ws_url = None
        self.current_rpc_url = None
        
    async def start_monitoring(self):
        """Start monitoring for the agent"""
        try:
            self.agent = await sync_to_async(Agent.objects.get)(id=self.agent_id)
            if not self.agent.is_active:
                logger.info(f"Agent {self.agent.name} is not active, skipping monitoring")
                return False
                
            logger.info(f"🚀 Starting Enhanced Solana monitoring for agent: {self.agent.name}")
            self.is_monitoring = True
            
            # Try connecting to different Solana endpoints
            for ws_url in self.SOLANA_WS_URLS:
                try:
                    logger.info(f"Attempting to connect to: {ws_url}")
                    self.current_ws_url = ws_url
                    # Set corresponding RPC URL
                    if "mainnet-beta" in ws_url:
                        self.current_rpc_url = self.SOLANA_RPC_URLS[0]
                    elif "alchemy" in ws_url:
                        self.current_rpc_url = self.SOLANA_RPC_URLS[1]
                    elif "ankr" in ws_url:
                        self.current_rpc_url = self.SOLANA_RPC_URLS[2]
                    else:
                        self.current_rpc_url = self.SOLANA_RPC_URLS[0]
                        
                    await self._connect_and_monitor(ws_url)
                    break
                except Exception as e:
                    logger.warning(f"Failed to connect to {ws_url}: {e}")
                    continue
            else:
                logger.error("❌ Failed to connect to any Solana WebSocket endpoint")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error starting monitoring for agent {self.agent_id}: {e}")
            return False
    
    async def stop_monitoring(self):
        """Stop monitoring for the agent"""
        logger.info(f"🛑 Stopping Solana monitoring for agent: {self.agent_id}")
        self.is_monitoring = False
        
        if self.websocket and not self.websocket.closed:
            try:
                # Unsubscribe from logs
                if self.subscription_id:
                    await self._unsubscribe()
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        
        self.websocket = None
        self.subscription_id = None
    
    async def _connect_and_monitor(self, ws_url):
        """Connect to Solana WebSocket and start monitoring"""
        try:
            # Remove extra_headers as it's not supported in this websockets version
            self.websocket = await websockets.connect(
                ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            logger.info(f"✅ Connected to Solana WebSocket: {ws_url}")
            
            # Test connection with a simple request
            test_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth"
            }
            await self.websocket.send(json.dumps(test_message))
            test_response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            logger.info(f"Connection test response: {test_response[:100]}...")
            
            # Subscribe to account notifications for DEX programs
            await self._subscribe_to_dex_transactions()
            
            # Start listening for messages
            await self._listen_for_transactions()
            
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            if self.is_monitoring:
                await self._handle_reconnect()
        except asyncio.TimeoutError:
            logger.error("Connection test timeout")
            if self.is_monitoring:
                await self._handle_reconnect()
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if self.is_monitoring:
                await self._handle_reconnect()
    
    async def _subscribe_to_dex_transactions(self):
        """Subscribe to all program logs for broader transaction detection"""
        try:
            # Subscribe to all program logs to catch more transactions
            subscribe_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": [
                    "all",  # Subscribe to ALL logs
                    {
                        "commitment": "confirmed"
                    }
                ]
            }
            
            await self.websocket.send(json.dumps(subscribe_message))
            
            # Wait for subscription confirmation
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            response_data = json.loads(response)
            
            if "result" in response_data:
                self.subscription_id = response_data["result"]
                logger.info(f"✅ Successfully subscribed to ALL program logs with ID: {self.subscription_id}")
                logger.info(f"🔍 Now monitoring for transactions...")
            else:
                logger.error(f"❌ Failed to subscribe to logs: {response_data}")
                raise Exception("Failed to subscribe to Solana logs")
                
        except asyncio.TimeoutError:
            logger.error("Subscription timeout - WebSocket may not support log subscriptions")
            raise
        except Exception as e:
            logger.error(f"Error subscribing to transactions: {e}")
            raise
    
    async def _unsubscribe(self):
        """Unsubscribe from transaction logs"""
        try:
            unsubscribe_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "logsUnsubscribe",
                "params": [self.subscription_id]
            }
            
            await self.websocket.send(json.dumps(unsubscribe_message))
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
    
    async def _listen_for_transactions(self):
        """Listen for incoming transaction data"""
        try:
            logger.info(f"🎯 Starting to listen for SPL Token transactions for agent {self.agent_id}")
            
            # Counter for monitoring
            message_count = 0
            transaction_count = 0
            
            async for message in self.websocket:
                if not self.is_monitoring:
                    break
                
                message_count += 1
                if message_count % 100 == 0:
                    logger.info(f"Processed {message_count} messages, found {transaction_count} transactions")
                    
                try:
                    data = json.loads(message)
                    
                    # Check if this is a transaction log
                    if "params" in data and "result" in data["params"]:
                        result = await self._process_transaction_data(data)
                        if result:
                            transaction_count += 1
                            
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received: {message[:100]}...")
                except Exception as e:
                    logger.error(f"Error processing transaction data: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection lost during listening")
            if self.is_monitoring:
                await self._handle_reconnect()
        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
            if self.is_monitoring:
                await self._handle_reconnect()
    
    async def _process_transaction_data(self, data):
        """Process incoming transaction data and filter for token swaps"""
        try:
            # Check if this is a transaction log notification
            if "params" not in data or "result" not in data["params"]:
                return False
            
            result = data["params"]["result"]
            
            # Extract transaction details
            signature = result.get("signature")
            logs = result.get("logs", [])
            slot = result.get("context", {}).get("slot")
            
            if not signature or not logs:
                return False
            
            # Skip if already processed
            if signature in self.processed_signatures:
                return False
            
            # Log first few logs for debugging
            logger.debug(f"Transaction {signature[:8]}... has {len(logs)} logs")
            if logs:
                logger.debug(f"First log: {logs[0][:100]}...")
                
            # Check if logs contain swap/trade activity
            if self._is_swap_transaction(logs):
                logger.info(f"🎯 Detected potential transaction: {signature}")
                
                # Get detailed transaction information
                token_transfers = await self._get_detailed_transaction_info(signature, slot)
                
                if token_transfers:
                    logger.info(f"📊 Found {len(token_transfers)} token transfers in transaction")
                
                for transfer in token_transfers:
                    # Apply agent filters
                    if await self._should_track_transaction(transfer):
                        # Create transaction record
                        await self._create_transaction_record(transfer)
                        logger.info(f"✅ Saved transaction: {transfer['token_symbol']} {transfer['tx_type']} - ${transfer['total_value_usd']:.2f}")
                    else:
                        logger.debug(f"Filtered out: {transfer['token_symbol']} - ${transfer['total_value_usd']:.2f}")
                
                # Mark as processed
                self.processed_signatures.add(signature)
                
                # Clean up old signatures (keep last 1000)
                if len(self.processed_signatures) > 1000:
                    self.processed_signatures = set(list(self.processed_signatures)[-500:])
                    
                return True
                    
        except Exception as e:
            logger.error(f"Error processing transaction data: {e}")
            
        return False
    
    def _is_swap_transaction(self, logs):
        """Check if transaction logs indicate any significant activity"""
        if not logs:
            return False
            
        # DEX platform indicators
        dex_indicators = [
            "raydium", "jupiter", "orca", "serum", "pumpfun", "meteora",
            "swap", "trade", "exchange", "dex", "amm", "pool"
        ]
        
        # Token program indicators  
        token_indicators = [
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            "transfer", "transferchecked", "mint", "burn",
            "program log", "invoke", "success"
        ]
        
        # Combine all logs into single text for analysis
        log_text = " ".join(logs).lower()
        
        # More inclusive detection - if it has ANY token or DEX activity
        has_dex_activity = any(indicator in log_text for indicator in dex_indicators)
        has_token_activity = any(indicator in log_text for indicator in token_indicators)
        
        # Return True if this looks like any kind of significant transaction
        return has_dex_activity or has_token_activity
    
    async def _get_detailed_transaction_info(self, signature, slot):
        """Get detailed transaction information using HTTP RPC"""
        try:
            rpc_url = self.current_rpc_url
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "commitment": "confirmed",
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "result" in data and data["result"]:
                            return await self._parse_detailed_transaction(data["result"], signature, slot)
                    else:
                        logger.warning(f"RPC request failed with status {response.status}")
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting transaction details for {signature}")
        except Exception as e:
            logger.error(f"Error getting transaction details for {signature}: {e}")
        
        return []
    
    async def _parse_detailed_transaction(self, transaction_data, signature, slot):
        """Parse detailed transaction data to extract token transfers"""
        transfers = []
        
        try:
            meta = transaction_data.get("meta", {})
            transaction = transaction_data.get("transaction", {})
            
            if meta.get("err"):
                logger.debug(f"Transaction {signature} failed, skipping")
                return []
            
            # Get pre and post token balances
            pre_token_balances = meta.get("preTokenBalances", [])
            post_token_balances = meta.get("postTokenBalances", [])
            
            # Track balance changes by account and mint
            balance_changes = {}
            
            # Process pre balances
            for balance in pre_token_balances:
                account = balance.get("accountIndex")
                mint = balance.get("mint")
                owner = balance.get("owner")
                amount = float(balance.get("uiTokenAmount", {}).get("uiAmount", 0))
                
                key = (account, mint)
                if key not in balance_changes:
                    balance_changes[key] = {"pre": 0, "post": 0, "owner": owner, "mint": mint}
                balance_changes[key]["pre"] = amount
            
            # Process post balances
            for balance in post_token_balances:
                account = balance.get("accountIndex")
                mint = balance.get("mint")
                owner = balance.get("owner")
                amount = float(balance.get("uiTokenAmount", {}).get("uiAmount", 0))
                
                key = (account, mint)
                if key not in balance_changes:
                    balance_changes[key] = {"pre": 0, "post": 0, "owner": owner, "mint": mint}
                balance_changes[key]["post"] = amount
            
            # Analyze balance changes to create transfer records
            for (account, mint), change_data in balance_changes.items():
                pre_amount = change_data["pre"]
                post_amount = change_data["post"]
                amount_change = post_amount - pre_amount
                
                # Only process significant changes (> 0.001 tokens)
                if abs(amount_change) > 0.001:
                    token_symbol = await self._get_token_symbol_by_mint(mint)
                    price_usd = await self._get_token_price(token_symbol)
                    
                    transfer = {
                        "signature": signature,
                        "tx_hash": signature,
                        "slot": slot or 0,
                        "timestamp": timezone.now(),
                        "wallet_address": change_data["owner"],
                        "token_symbol": token_symbol,
                        "token_address": mint,
                        "amount": abs(amount_change),
                        "price_usd": price_usd,
                        "total_value_usd": abs(amount_change) * price_usd,
                        "tx_type": "BUY" if amount_change > 0 else "SELL",
                        "platform": self._detect_platform_from_transaction(transaction),
                        "status": "SUCCESS"
                    }
                    
                    transfers.append(transfer)
                    
        except Exception as e:
            logger.error(f"Error parsing detailed transaction {signature}: {e}")
        
        return transfers
    
    async def _should_track_transaction(self, transfer_data):
        """Check if agent should track this transaction based on filters"""
        try:
            agent = await sync_to_async(Agent.objects.get)(id=self.agent_id)
            
            # Check value filters
            total_value = transfer_data["total_value_usd"]
            if agent.min_transaction_value and total_value < agent.min_transaction_value:
                return False
            if agent.max_transaction_value and total_value > agent.max_transaction_value:
                return False
            
            # Check token filters
            token_symbol = transfer_data["token_symbol"]
            if agent.token_filter_type == "exclude":
                excluded = [t.strip().upper() for t in (agent.excluded_tokens or "").split(",") if t.strip()]
                if token_symbol.upper() in excluded:
                    return False
            elif agent.token_filter_type == "include":
                included = [t.strip().upper() for t in (agent.included_tokens or "").split(",") if t.strip()]
                if included and token_symbol.upper() not in included:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking transaction filters: {e}")
            return False
    
    async def _create_transaction_record(self, transfer_data):
        """Create a Transaction record in the database"""
        try:
            # Check if transaction already exists
            exists = await sync_to_async(Transaction.objects.filter(
                tx_hash=transfer_data["tx_hash"],
                wallet_address=transfer_data["wallet_address"],
                token_address=transfer_data["token_address"]
            ).exists)()
            
            if not exists:
                transaction = await sync_to_async(Transaction.objects.create)(
                    agent_id=self.agent_id,
                    wallet_address=transfer_data["wallet_address"],
                    tx_hash=transfer_data["tx_hash"],
                    signature=transfer_data["signature"],
                    token_symbol=transfer_data["token_symbol"],
                    token_address=transfer_data["token_address"],
                    amount=Decimal(str(transfer_data["amount"])),
                    price_usd=Decimal(str(transfer_data["price_usd"])),
                    total_value_usd=Decimal(str(transfer_data["total_value_usd"])),
                    tx_type=transfer_data["tx_type"],
                    platform=transfer_data["platform"],
                    timestamp=transfer_data["timestamp"],
                    slot=transfer_data["slot"],
                    status=transfer_data["status"]
                )
                
                logger.info(f"✅ Created transaction: {transaction.token_symbol} {transaction.tx_type} - ${transaction.total_value_usd}")
                
                # Try to match with existing trades for P&L calculation
                await self._try_match_trades(transaction)
                
                # Send real-time notification to WebSocket clients
                await self._notify_transaction_created(transaction)
                return transaction
                
        except Exception as e:
            logger.error(f"Error creating transaction record: {e}")
        return None
    
    async def _try_match_trades(self, new_transaction):
        """Try to match this transaction with previous trades for P&L calculation"""
        try:
            # Look for opposite trade type with same wallet and token
            opposite_type = "SELL" if new_transaction.tx_type == "BUY" else "BUY"
            
            # Find unmatched transactions of opposite type
            potential_matches = await sync_to_async(list)(
                Transaction.objects.filter(
                    agent=new_transaction.agent,
                    wallet_address=new_transaction.wallet_address,
                    token_address=new_transaction.token_address,
                    tx_type=opposite_type,
                    is_closed=False
                ).order_by('timestamp')
            )
            
            if potential_matches:
                # Match with the earliest unmatched transaction
                match = potential_matches[0]
                await sync_to_async(match.close_trade_with)(new_transaction)
                logger.info(f"🔄 Matched trades: {match.tx_hash[:8]}... <-> {new_transaction.tx_hash[:8]}...")
                
        except Exception as e:
            logger.error(f"Error matching trades: {e}")
    
    async def _notify_transaction_created(self, transaction):
        """Send real-time notification about new transaction"""
        try:
            from .consumers import notify_new_transaction
            
            transaction_data = {
                'id': str(transaction.id),
                'wallet_address': transaction.wallet_address[:8] + "..." + transaction.wallet_address[-4:],
                'tx_hash': transaction.tx_hash,
                'token_symbol': transaction.token_symbol,
                'amount': str(transaction.amount),
                'price_usd': str(transaction.price_usd),
                'total_value_usd': str(transaction.total_value_usd),
                'tx_type': transaction.tx_type,
                'platform': transaction.platform,
                'timestamp': transaction.timestamp.isoformat(),
                'is_closed': transaction.is_closed,
            }
            
            await notify_new_transaction(self.agent_id, transaction_data)
            
        except Exception as e:
            logger.error(f"Error sending transaction notification: {e}")
    
    async def _handle_reconnect(self):
        """Handle WebSocket reconnection with exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"❌ Max reconnection attempts reached for agent {self.agent_id}")
            self.is_monitoring = False
            return
        
        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 60)  # Exponential backoff
        
        logger.info(f"🔄 Reconnecting in {wait_time} seconds (attempt {self.reconnect_attempts})")
        await asyncio.sleep(wait_time)
        
        if self.is_monitoring:
            await self.start_monitoring()
    
    async def _get_token_price(self, token_symbol):
        """Get current token price in USD from CoinGecko API"""
        try:
            # First try with a basic price mapping for common tokens
            price_mapping = {
                "SOL": 100.0,
                "USDC": 1.0,
                "USDT": 1.0,
                "BONK": 0.00002,
                "WIF": 2.8,
                "POPCAT": 1.5,
                "MYRO": 0.12,
                "SAMO": 0.008,
                "JUP": 0.8,
                "RAY": 2.1,
                "ORCA": 3.2,
            }
            
            if token_symbol.upper() in price_mapping:
                return price_mapping[token_symbol.upper()]
            
            # For unknown tokens, try CoinGecko API (with rate limiting)
            # TODO: Implement actual CoinGecko API call with proper rate limiting
            return 0.01  # Default price for unknown tokens
            
        except Exception as e:
            logger.error(f"Error getting token price for {token_symbol}: {e}")
            return 0.01
    
    async def _get_token_symbol_by_mint(self, mint_address):
        """Get token symbol by mint address"""
        # Enhanced token mint address mapping
        known_tokens = {
            "So11111111111111111111111111111111111111112": "SOL",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": "BONK",
            "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm": "WIF",
            "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr": "POPCAT",
            "HhJpBhRRn4g56VsyLuT8DL5Bv31HkXqsrahTTUCZeZg4": "MYRO",
            "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU": "SAMO",
            "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN": "JUP",
            "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R": "RAY",
            "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE": "ORCA",
        }
        
        return known_tokens.get(mint_address, f"TOKEN-{mint_address[:8]}")
    
    def _detect_platform_from_transaction(self, transaction):
        """Detect trading platform from transaction instructions"""
        try:
            instructions = transaction.get("message", {}).get("instructions", [])
            
            # Platform program IDs mapping
            platform_programs = {
                "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium",
                "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter",
                "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca",
                "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP": "Orca",
                "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX": "Serum",
                "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P": "PumpFun",
            }
            
            for instruction in instructions:
                program_id = instruction.get("programId", "")
                if program_id in platform_programs:
                    return platform_programs[program_id]
            
        except Exception as e:
            logger.error(f"Error detecting platform: {e}")
        
        return "Unknown"


# Global monitor instances
active_monitors = {}

async def start_agent_monitoring(agent_id):
    """Start monitoring for a specific agent"""
    try:
        if agent_id in active_monitors:
            logger.info(f"Monitoring already active for agent {agent_id}")
            return True
        
        monitor = SolanaMonitor(agent_id)
        success = await monitor.start_monitoring()
        
        if success:
            active_monitors[agent_id] = monitor
            logger.info(f"✅ Started monitoring for agent {agent_id}")
        else:
            logger.error(f"❌ Failed to start monitoring for agent {agent_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error starting agent monitoring: {e}")
        return False

async def stop_agent_monitoring(agent_id):
    """Stop monitoring for a specific agent"""
    try:
        if agent_id in active_monitors:
            monitor = active_monitors[agent_id]
            await monitor.stop_monitoring()
            del active_monitors[agent_id]
            logger.info(f"🛑 Stopped monitoring for agent {agent_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error stopping agent monitoring: {e}")
        return False

async def restart_agent_monitoring(agent_id):
    """Restart monitoring for a specific agent"""
    try:
        await stop_agent_monitoring(agent_id)
        await asyncio.sleep(2)  # Brief pause
        return await start_agent_monitoring(agent_id)
    except Exception as e:
        logger.error(f"Error restarting agent monitoring: {e}")
        return False

def get_monitoring_status():
    """Get status of all active monitors"""
    return {
        "active_agents": list(active_monitors.keys()),
        "total_active": len(active_monitors)
    } 