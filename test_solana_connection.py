import asyncio
import websockets
import json

async def test_solana_connection():
    """Test connection to Solana WebSocket endpoints"""
    
    endpoints = [
        "wss://api.mainnet-beta.solana.com",
        "wss://solana-mainnet.g.alchemy.com/v2/demo",
        "wss://rpc.ankr.com/solana_ws",
        "wss://api.devnet.solana.com",
    ]
    
    for ws_url in endpoints:
        print(f"\n🔍 Testing connection to: {ws_url}")
        
        try:
            # Connect with timeout
            websocket = await asyncio.wait_for(
                websockets.connect(ws_url, ping_interval=30, ping_timeout=10),
                timeout=10.0
            )
            print(f"✅ Connected successfully!")
            
            # Test with getHealth method
            test_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth"
            }
            
            await websocket.send(json.dumps(test_message))
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            print(f"📋 Health check response: {response_data}")
            
            # Test subscription capability
            subscribe_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "logsSubscribe",
                "params": [
                    {"mentions": ["11111111111111111111111111111111"]},  # System program
                    {"commitment": "confirmed"}
                ]
            }
            
            await websocket.send(json.dumps(subscribe_message))
            sub_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            sub_data = json.loads(sub_response)
            
            if "result" in sub_data:
                print(f"✅ Subscription supported! ID: {sub_data['result']}")
                
                # Unsubscribe
                unsub_message = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "logsUnsubscribe",
                    "params": [sub_data["result"]]
                }
                await websocket.send(json.dumps(unsub_message))
            else:
                print(f"❌ Subscription not supported: {sub_data}")
            
            await websocket.close()
            
        except asyncio.TimeoutError:
            print(f"❌ Connection timeout")
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
    
    print("\n\n📊 Summary:")
    print("If all endpoints failed, check your internet connection.")
    print("If some worked, use those in your application.")

if __name__ == "__main__":
    print("🚀 Testing Solana WebSocket Endpoints...")
    asyncio.run(test_solana_connection()) 