import asyncio
import json
import logging
import websockets
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import streamlit as st
from queue import Queue
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_client")

class WebSocketClient:
    """WebSocket client for real-time updates in Streamlit."""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.client_id: Optional[str] = None
        self.message_queue: Queue = Queue()
        self.handlers: Dict[str, Callable] = {
            "welcome": self._handle_welcome,
            "auction_data": self._handle_auction_data,
            "bid_update": self._handle_bid_update,
            "listing_update": self._handle_listing_update,
            "user_update": self._handle_user_update,
            "error": self._handle_error
        }
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1  # seconds
    
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            self.reconnect_attempts = 0
            logger.info("Connected to WebSocket server")
            
            # Start message processing
            asyncio.create_task(self._process_messages())
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self.connected = False
            await self._handle_reconnect()
    
    async def _handle_reconnect(self):
        """Handle reconnection attempts."""
        while not self.connected and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Reconnection attempt {self.reconnect_attempts}")
            
            try:
                await asyncio.sleep(self.reconnect_delay)
                await self.connect()
            except Exception as e:
                logger.error(f"Reconnection error: {str(e)}")
        
        if not self.connected:
            logger.error("Max reconnection attempts reached")
            st.error("Failed to connect to real-time updates. Please refresh the page.")
    
    async def _process_messages(self):
        """Process incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type in self.handlers:
                        await self.handlers[message_type](data)
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message: {message}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.connected = False
            await self._handle_reconnect()
        except Exception as e:
            logger.error(f"Error in message processing: {str(e)}")
            self.connected = False
            await self._handle_reconnect()
    
    async def _handle_welcome(self, data: Dict[str, Any]):
        """Handle welcome message."""
        self.client_id = data.get("client_id")
        logger.info(f"Received welcome message. Client ID: {self.client_id}")
    
    async def _handle_auction_data(self, data: Dict[str, Any]):
        """Handle auction data update."""
        auction_id = data.get("auction_id")
        auction_data = data.get("data")
        
        if auction_id and auction_data:
            # Update session state
            if "auctions" not in st.session_state:
                st.session_state.auctions = {}
            
            st.session_state.auctions[auction_id] = auction_data
            st.experimental_rerun()
    
    async def _handle_bid_update(self, data: Dict[str, Any]):
        """Handle bid update."""
        auction_id = data.get("auction_id")
        amount = data.get("amount")
        user_id = data.get("user_id")
        
        if auction_id and amount and user_id:
            # Update session state
            if "auctions" in st.session_state and auction_id in st.session_state.auctions:
                auction = st.session_state.auctions[auction_id]
                auction["current_price"] = amount
                auction["current_bidder"] = user_id
                auction["last_bid_time"] = datetime.now().isoformat()
                
                # Show notification
                st.toast(f"New bid: ${amount:,.2f} on auction {auction_id}")
                st.experimental_rerun()
    
    async def _handle_listing_update(self, data: Dict[str, Any]):
        """Handle listing update."""
        listing_id = data.get("listing_id")
        updates = data.get("updates")
        
        if listing_id and updates:
            # Update session state
            if "listings" not in st.session_state:
                st.session_state.listings = {}
            
            if listing_id in st.session_state.listings:
                st.session_state.listings[listing_id].update(updates)
                st.experimental_rerun()
    
    async def _handle_user_update(self, data: Dict[str, Any]):
        """Handle user update."""
        user_id = data.get("user_id")
        update_data = data.get("data")
        
        if user_id and update_data:
            # Update session state
            if "user_data" not in st.session_state:
                st.session_state.user_data = {}
            
            st.session_state.user_data.update(update_data)
            st.experimental_rerun()
    
    async def _handle_error(self, data: Dict[str, Any]):
        """Handle error message."""
        error_message = data.get("message")
        if error_message:
            st.error(error_message)
            logger.error(f"WebSocket error: {error_message}")
    
    async def subscribe_auction(self, auction_id: str):
        """Subscribe to auction updates."""
        if self.connected and self.websocket:
            message = {
                "type": "subscribe_auction",
                "auction_id": auction_id
            }
            await self.websocket.send(json.dumps(message))
    
    async def unsubscribe_auction(self, auction_id: str):
        """Unsubscribe from auction updates."""
        if self.connected and self.websocket:
            message = {
                "type": "unsubscribe_auction",
                "auction_id": auction_id
            }
            await self.websocket.send(json.dumps(message))
    
    async def subscribe_user(self, user_id: str):
        """Subscribe to user updates."""
        if self.connected and self.websocket:
            message = {
                "type": "subscribe_user",
                "user_id": user_id
            }
            await self.websocket.send(json.dumps(message))
    
    async def unsubscribe_user(self, user_id: str):
        """Unsubscribe from user updates."""
        if self.connected and self.websocket:
            message = {
                "type": "unsubscribe_user",
                "user_id": user_id
            }
            await self.websocket.send(json.dumps(message))
    
    async def place_bid(self, auction_id: str, amount: float, user_id: str):
        """Place a bid on an auction."""
        if self.connected and self.websocket:
            message = {
                "type": "place_bid",
                "auction_id": auction_id,
                "amount": amount,
                "user_id": user_id
            }
            await self.websocket.send(json.dumps(message))
    
    async def update_listing(self, listing_id: str, updates: Dict[str, Any], user_id: str):
        """Update an eBay listing."""
        if self.connected and self.websocket:
            message = {
                "type": "update_listing",
                "listing_id": listing_id,
                "updates": updates,
                "user_id": user_id
            }
            await self.websocket.send(json.dumps(message))
    
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from WebSocket server")

# Streamlit integration
def init_websocket():
    """Initialize WebSocket connection in Streamlit."""
    if "websocket_client" not in st.session_state:
        client = WebSocketClient()
        st.session_state.websocket_client = client
        
        # Start WebSocket connection in a separate thread
        def run_websocket():
            asyncio.run(client.connect())
        
        thread = threading.Thread(target=run_websocket)
        thread.daemon = True
        thread.start()

def get_websocket_client() -> WebSocketClient:
    """Get the WebSocket client instance."""
    if "websocket_client" not in st.session_state:
        init_websocket()
    return st.session_state.websocket_client 