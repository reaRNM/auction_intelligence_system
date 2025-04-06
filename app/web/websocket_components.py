import streamlit as st
from typing import Dict, Any, Optional, Callable
import asyncio
from datetime import datetime
import plotly.graph_objects as go
from .websocket_client import get_websocket_client

def auction_monitor(auction_id: str):
    """Display real-time auction monitoring component."""
    client = get_websocket_client()
    
    # Subscribe to auction updates
    if "auction_subscriptions" not in st.session_state:
        st.session_state.auction_subscriptions = set()
    
    if auction_id not in st.session_state.auction_subscriptions:
        asyncio.run(client.subscribe_auction(auction_id))
        st.session_state.auction_subscriptions.add(auction_id)
    
    # Get auction data from session state
    if "auctions" in st.session_state and auction_id in st.session_state.auctions:
        auction = st.session_state.auctions[auction_id]
        
        # Display auction details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Current Price",
                f"${auction['current_price']:,.2f}",
                f"${auction['current_price'] - auction.get('previous_price', auction['current_price']):,.2f}"
            )
        
        with col2:
            st.metric(
                "Time Remaining",
                auction.get("time_remaining", "N/A"),
                auction.get("time_remaining_delta", "")
            )
        
        with col3:
            st.metric(
                "Bid Count",
                auction.get("bid_count", 0),
                auction.get("bid_count_delta", 0)
            )
        
        # Quick bid section
        st.subheader("Quick Bid")
        bid_col1, bid_col2 = st.columns([3, 1])
        
        with bid_col1:
            bid_amount = st.number_input(
                "Bid Amount ($)",
                min_value=auction["current_price"] + 1,
                step=1.0,
                format="%.2f"
            )
        
        with bid_col2:
            if st.button("Place Bid"):
                if "user" in st.session_state:
                    asyncio.run(client.place_bid(
                        auction_id,
                        bid_amount,
                        st.session_state.user["id"]
                    ))
                else:
                    st.error("Please log in to place a bid")
        
        # Bid history chart
        if "bid_history" in auction:
            st.subheader("Bid History")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[datetime.fromisoformat(bid["timestamp"]) for bid in auction["bid_history"]],
                y=[bid["amount"] for bid in auction["bid_history"]],
                mode="lines+markers",
                name="Bid Amount"
            ))
            
            fig.update_layout(
                title="Bid History",
                xaxis_title="Time",
                yaxis_title="Amount ($)",
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)

def profit_calculator():
    """Display real-time profit calculator component."""
    st.subheader("Profit Calculator")
    
    # Input fields
    col1, col2 = st.columns(2)
    
    with col1:
        purchase_price = st.number_input(
            "Purchase Price ($)",
            min_value=0.0,
            step=1.0,
            format="%.2f"
        )
        
        shipping_cost = st.number_input(
            "Shipping Cost ($)",
            min_value=0.0,
            step=1.0,
            format="%.2f"
        )
    
    with col2:
        platform_fee = st.slider(
            "Platform Fee (%)",
            min_value=0.0,
            max_value=15.0,
            value=10.0,
            step=0.1
        )
        
        target_profit = st.slider(
            "Target Profit (%)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=1.0
        )
    
    # Calculate and display results
    total_cost = purchase_price + shipping_cost
    platform_fee_amount = total_cost * (platform_fee / 100)
    target_selling_price = total_cost * (1 + target_profit / 100)
    potential_profit = target_selling_price - total_cost - platform_fee_amount
    
    st.subheader("Results")
    result_col1, result_col2, result_col3 = st.columns(3)
    
    with result_col1:
        st.metric(
            "Total Cost",
            f"${total_cost:,.2f}",
            "Including shipping"
        )
    
    with result_col2:
        st.metric(
            "Target Price",
            f"${target_selling_price:,.2f}",
            f"Platform fee: ${platform_fee_amount:,.2f}"
        )
    
    with result_col3:
        st.metric(
            "Potential Profit",
            f"${potential_profit:,.2f}",
            f"{target_profit:.1f}% ROI"
        )
    
    # Market comparison chart
    if "market_data" in st.session_state:
        st.subheader("Market Comparison")
        
        fig = go.Figure()
        fig.add_trace(go.Box(
            y=st.session_state.market_data["prices"],
            name="Market Prices",
            boxpoints="all"
        ))
        
        fig.add_trace(go.Scatter(
            y=[target_selling_price],
            mode="markers",
            name="Target Price",
            marker=dict(
                size=12,
                symbol="star",
                color="red"
            )
        ))
        
        fig.update_layout(
            title="Price Distribution",
            yaxis_title="Price ($)",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)

def listing_wizard():
    """Display eBay listing creation wizard component."""
    st.subheader("Create New Listing")
    
    # Basic information
    title = st.text_input("Listing Title")
    description = st.text_area("Description")
    
    # Price and quantity
    col1, col2 = st.columns(2)
    
    with col1:
        price = st.number_input(
            "Price ($)",
            min_value=0.0,
            step=1.0,
            format="%.2f"
        )
    
    with col2:
        quantity = st.number_input(
            "Quantity",
            min_value=1,
            step=1
        )
    
    # Image upload
    st.subheader("Images")
    uploaded_files = st.file_uploader(
        "Upload Images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Display image previews
        cols = st.columns(min(len(uploaded_files), 4))
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 4]:
                st.image(file, use_column_width=True)
    
    # Shipping options
    st.subheader("Shipping Options")
    shipping_method = st.selectbox(
        "Shipping Method",
        ["Standard", "Express", "Economy"]
    )
    
    shipping_cost = st.number_input(
        "Shipping Cost ($)",
        min_value=0.0,
        step=1.0,
        format="%.2f"
    )
    
    # Listing preview
    if st.button("Preview Listing"):
        st.subheader("Listing Preview")
        
        preview_col1, preview_col2 = st.columns([2, 1])
        
        with preview_col1:
            if uploaded_files:
                st.image(uploaded_files[0], use_column_width=True)
            
            st.markdown(f"### {title}")
            st.markdown(description)
        
        with preview_col2:
            st.metric("Price", f"${price:,.2f}")
            st.metric("Quantity", quantity)
            st.metric("Shipping", f"${shipping_cost:,.2f}")
            st.metric("Total", f"${price + shipping_cost:,.2f}")
    
    # Create listing button
    if st.button("Create Listing"):
        if "user" in st.session_state:
            # Prepare listing data
            listing_data = {
                "title": title,
                "description": description,
                "price": price,
                "quantity": quantity,
                "shipping_method": shipping_method,
                "shipping_cost": shipping_cost,
                "created_at": datetime.now().isoformat()
            }
            
            # Create listing
            client = get_websocket_client()
            asyncio.run(client.update_listing(
                "new",
                listing_data,
                st.session_state.user["id"]
            ))
            
            st.success("Listing created successfully!")
        else:
            st.error("Please log in to create a listing")

def real_time_notifications():
    """Display real-time notifications component."""
    if "notifications" not in st.session_state:
        st.session_state.notifications = []
    
    # Display notifications
    for notification in st.session_state.notifications:
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.info(notification["message"])
            
            with col2:
                if st.button("Dismiss", key=f"dismiss_{notification['id']}"):
                    st.session_state.notifications.remove(notification)
                    st.experimental_rerun()
    
    # Clear all button
    if st.session_state.notifications:
        if st.button("Clear All"):
            st.session_state.notifications = []
            st.experimental_rerun()

def add_notification(message: str, notification_type: str = "info"):
    """Add a new notification."""
    if "notifications" not in st.session_state:
        st.session_state.notifications = []
    
    notification = {
        "id": len(st.session_state.notifications),
        "message": message,
        "type": notification_type,
        "timestamp": datetime.now().isoformat()
    }
    
    st.session_state.notifications.append(notification)
    st.experimental_rerun() 