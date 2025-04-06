import asyncio
import json
import logging
import websockets
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import uuid
import firebase_admin
from firebase_admin import firestore

# Initialize Firestore
db = firestore.client()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_service")

class WebSocketService:
    """WebSocket service for real-time updates."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.auction_subscribers: Dict[str, List[str]] = {}
        self.user_subscribers: Dict[str, List[str]] = {}
        self.message_handlers: Dict[str, Callable] = {
            "subscribe_auction": self._handle_subscribe_auction,
            "unsubscribe_auction": self._handle_unsubscribe_auction,
            "subscribe_user": self._handle_subscribe_user,
            "unsubscribe_user": self._handle_unsubscribe_user,
            "place_bid": self._handle_place_bid,
            "update_listing": self._handle_update_listing
        }
    
    async def start(self):
        """Start the WebSocket server."""
        server = await websockets.serve(self._handle_connection, self.host, self.port)
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        await server.wait_closed()
    
    async def _handle_connection(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle a new WebSocket connection."""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        
        try:
            logger.info(f"Client connected: {client_id}")
            
            # Send welcome message
            await self._send_message(websocket, {
                "type": "welcome",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Handle messages
            async for message in websocket:
                await self._process_message(client_id, message)
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling connection: {str(e)}")
        finally:
            # Clean up
            self._remove_client(client_id)
    
    def _remove_client(self, client_id: str):
        """Remove a client and clean up subscriptions."""
        if client_id in self.clients:
            del self.clients[client_id]
        
        # Remove from auction subscribers
        for auction_id, subscribers in self.auction_subscribers.items():
            if client_id in subscribers:
                subscribers.remove(client_id)
                if not subscribers:
                    del self.auction_subscribers[auction_id]
        
        # Remove from user subscribers
        for user_id, subscribers in self.user_subscribers.items():
            if client_id in subscribers:
                subscribers.remove(client_id)
                if not subscribers:
                    del self.user_subscribers[user_id]
    
    async def _process_message(self, client_id: str, message: str):
        """Process a message from a client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](client_id, data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self._send_message(self.clients[client_id], {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                })
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message: {message}")
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": "Invalid JSON message",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": f"Error processing message: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _send_message(self, websocket: websockets.WebSocketServerProtocol, message: Dict[str, Any]):
        """Send a message to a WebSocket client."""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
    
    async def _broadcast_to_subscribers(self, subscriber_ids: List[str], message: Dict[str, Any]):
        """Broadcast a message to multiple subscribers."""
        for client_id in subscriber_ids:
            if client_id in self.clients:
                await self._send_message(self.clients[client_id], message)
    
    async def _handle_subscribe_auction(self, client_id: str, data: Dict[str, Any]):
        """Handle subscription to an auction."""
        auction_id = data.get("auction_id")
        
        if not auction_id:
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": "Missing auction_id",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Add to subscribers
        if auction_id not in self.auction_subscribers:
            self.auction_subscribers[auction_id] = []
        
        if client_id not in self.auction_subscribers[auction_id]:
            self.auction_subscribers[auction_id].append(client_id)
        
        # Get current auction data
        try:
            auction_ref = db.collection("auctions").document(auction_id)
            auction_doc = auction_ref.get()
            
            if auction_doc.exists:
                auction_data = auction_doc.to_dict()
                await self._send_message(self.clients[client_id], {
                    "type": "auction_data",
                    "auction_id": auction_id,
                    "data": auction_data,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                await self._send_message(self.clients[client_id], {
                    "type": "error",
                    "message": f"Auction not found: {auction_id}",
                    "timestamp": datetime.now().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error fetching auction data: {str(e)}")
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": f"Error fetching auction data: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_unsubscribe_auction(self, client_id: str, data: Dict[str, Any]):
        """Handle unsubscription from an auction."""
        auction_id = data.get("auction_id")
        
        if not auction_id:
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": "Missing auction_id",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Remove from subscribers
        if auction_id in self.auction_subscribers and client_id in self.auction_subscribers[auction_id]:
            self.auction_subscribers[auction_id].remove(client_id)
            
            if not self.auction_subscribers[auction_id]:
                del self.auction_subscribers[auction_id]
    
    async def _handle_subscribe_user(self, client_id: str, data: Dict[str, Any]):
        """Handle subscription to a user's updates."""
        user_id = data.get("user_id")
        
        if not user_id:
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": "Missing user_id",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Add to subscribers
        if user_id not in self.user_subscribers:
            self.user_subscribers[user_id] = []
        
        if client_id not in self.user_subscribers[user_id]:
            self.user_subscribers[user_id].append(client_id)
    
    async def _handle_unsubscribe_user(self, client_id: str, data: Dict[str, Any]):
        """Handle unsubscription from a user's updates."""
        user_id = data.get("user_id")
        
        if not user_id:
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": "Missing user_id",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Remove from subscribers
        if user_id in self.user_subscribers and client_id in self.user_subscribers[user_id]:
            self.user_subscribers[user_id].remove(client_id)
            
            if not self.user_subscribers[user_id]:
                del self.user_subscribers[user_id]
    
    async def _handle_place_bid(self, client_id: str, data: Dict[str, Any]):
        """Handle a bid placement."""
        auction_id = data.get("auction_id")
        amount = data.get("amount")
        user_id = data.get("user_id")
        
        if not all([auction_id, amount, user_id]):
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": "Missing required fields: auction_id, amount, user_id",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        try:
            # Update auction in Firestore
            auction_ref = db.collection("auctions").document(auction_id)
            auction_doc = auction_ref.get()
            
            if not auction_doc.exists:
                await self._send_message(self.clients[client_id], {
                    "type": "error",
                    "message": f"Auction not found: {auction_id}",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            auction_data = auction_doc.to_dict()
            current_price = auction_data.get("current_price", 0)
            
            if amount <= current_price:
                await self._send_message(self.clients[client_id], {
                    "type": "error",
                    "message": f"Bid amount must be greater than current price: ${current_price}",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # Update auction
            auction_ref.update({
                "current_price": amount,
                "current_bidder": user_id,
                "last_bid_time": firestore.SERVER_TIMESTAMP,
                "bid_count": firestore.Increment(1)
            })
            
            # Add bid to history
            bid_ref = auction_ref.collection("bids").document()
            bid_ref.set({
                "user_id": user_id,
                "amount": amount,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            
            # Notify subscribers
            bid_update = {
                "type": "bid_update",
                "auction_id": auction_id,
                "amount": amount,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
            if auction_id in self.auction_subscribers:
                await self._broadcast_to_subscribers(self.auction_subscribers[auction_id], bid_update)
            
            # Send confirmation to bidder
            await self._send_message(self.clients[client_id], {
                "type": "bid_confirmation",
                "auction_id": auction_id,
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error placing bid: {str(e)}")
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": f"Error placing bid: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_update_listing(self, client_id: str, data: Dict[str, Any]):
        """Handle a listing update."""
        listing_id = data.get("listing_id")
        updates = data.get("updates", {})
        user_id = data.get("user_id")
        
        if not all([listing_id, updates, user_id]):
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": "Missing required fields: listing_id, updates, user_id",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        try:
            # Update listing in Firestore
            listing_ref = db.collection("listings").document(listing_id)
            listing_doc = listing_ref.get()
            
            if not listing_doc.exists:
                await self._send_message(self.clients[client_id], {
                    "type": "error",
                    "message": f"Listing not found: {listing_id}",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            listing_data = listing_doc.to_dict()
            
            # Verify ownership
            if listing_data.get("user_id") != user_id:
                await self._send_message(self.clients[client_id], {
                    "type": "error",
                    "message": "You don't have permission to update this listing",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # Update listing
            updates["updated_at"] = firestore.SERVER_TIMESTAMP
            listing_ref.update(updates)
            
            # Notify subscribers
            listing_update = {
                "type": "listing_update",
                "listing_id": listing_id,
                "updates": updates,
                "timestamp": datetime.now().isoformat()
            }
            
            if user_id in self.user_subscribers:
                await self._broadcast_to_subscribers(self.user_subscribers[user_id], listing_update)
            
            # Send confirmation
            await self._send_message(self.clients[client_id], {
                "type": "update_confirmation",
                "listing_id": listing_id,
                "timestamp": datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error updating listing: {str(e)}")
            await self._send_message(self.clients[client_id], {
                "type": "error",
                "message": f"Error updating listing: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def notify_auction_update(self, auction_id: str, update_data: Dict[str, Any]):
        """Notify subscribers about an auction update."""
        if auction_id in self.auction_subscribers:
            message = {
                "type": "auction_update",
                "auction_id": auction_id,
                "data": update_data,
                "timestamp": datetime.now().isoformat()
            }
            await self._broadcast_to_subscribers(self.auction_subscribers[auction_id], message)
    
    async def notify_user_update(self, user_id: str, update_data: Dict[str, Any]):
        """Notify subscribers about a user update."""
        if user_id in self.user_subscribers:
            message = {
                "type": "user_update",
                "user_id": user_id,
                "data": update_data,
                "timestamp": datetime.now().isoformat()
            }
            await self._broadcast_to_subscribers(self.user_subscribers[user_id], message)

# Example usage
async def main():
    service = WebSocketService()
    await service.start()

if __name__ == "__main__":
    asyncio.run(main()) 