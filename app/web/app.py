import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from .websocket_client import init_websocket, get_websocket_client
from .websocket_components import (
    auction_monitor,
    profit_calculator,
    listing_wizard,
    real_time_notifications,
    add_notification
)

# Initialize Firebase
cred = credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Page configuration
st.set_page_config(
    page_title="Auction Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
    }
    
    /* Accessibility improvements */
    .stButton>button {
        min-height: 44px;
        padding: 0.5rem 1rem;
    }
    
    /* Loading states */
    .stSpinner {
        color: #FF4B4B;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .stColumns {
            flex-direction: column;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Initialize WebSocket connection
init_websocket()

# Sidebar navigation
with st.sidebar:
    st.title("Auction Intelligence")
    
    # User authentication
    if st.session_state.user:
        st.write(f"Welcome, {st.session_state.user['email']}")
        if st.button("Logout"):
            st.session_state.user = None
            st.experimental_rerun()
    else:
        st.write("Please log in to continue")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            try:
                user = auth.get_user_by_email(email)
                st.session_state.user = {
                    "id": user.uid,
                    "email": user.email
                }
                add_notification("Successfully logged in!", "success")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
    
    # Navigation
    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Auctions", "Research", "Listings"]
    )
    
    # Dark mode toggle
    st.sidebar.markdown("---")
    dark_mode = st.sidebar.toggle("Dark Mode", value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.experimental_rerun()

# Main content
if page == "Dashboard":
    st.title("Dashboard")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Active Auctions",
            len(st.session_state.get("auctions", {})),
            "+2 today"
        )
    
    with col2:
        st.metric(
            "Total Value",
            "$12,345.67",
            "+$1,234.56"
        )
    
    with col3:
        st.metric(
            "Profit Potential",
            "$2,345.67",
            "+$234.56"
        )
    
    with col4:
        st.metric(
            "Active Listings",
            "12",
            "+3 this week"
        )
    
    # Recent activity
    st.subheader("Recent Activity")
    activity_tab1, activity_tab2 = st.tabs(["Auctions", "Listings"])
    
    with activity_tab1:
        if "auctions" in st.session_state:
            for auction_id, auction in list(st.session_state.auctions.items())[:5]:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**{auction.get('title', 'Untitled')}**")
                        st.write(f"Current bid: ${auction.get('current_price', 0):,.2f}")
                    
                    with col2:
                        st.write(f"Time left: {auction.get('time_remaining', 'N/A')}")
                    
                    with col3:
                        if st.button("View", key=f"view_auction_{auction_id}"):
                            st.session_state.selected_auction = auction_id
                            st.experimental_rerun()
    
    with activity_tab2:
        if "listings" in st.session_state:
            for listing_id, listing in list(st.session_state.listings.items())[:5]:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**{listing.get('title', 'Untitled')}**")
                        st.write(f"Price: ${listing.get('price', 0):,.2f}")
                    
                    with col2:
                        st.write(f"Views: {listing.get('views', 0)}")
                    
                    with col3:
                        if st.button("Edit", key=f"edit_listing_{listing_id}"):
                            st.session_state.selected_listing = listing_id
                            st.experimental_rerun()
    
    # Performance charts
    st.subheader("Performance")
    perf_tab1, perf_tab2 = st.tabs(["Profit Trend", "Category Analysis"])
    
    with perf_tab1:
        # Sample data
        dates = pd.date_range(start="2024-01-01", end="2024-03-14", freq="D")
        profits = pd.Series([100, 150, 200, 180, 220, 250, 300, 280, 320, 350])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=profits,
            mode="lines+markers",
            name="Daily Profit"
        ))
        
        fig.update_layout(
            title="Profit Trend",
            xaxis_title="Date",
            yaxis_title="Profit ($)",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with perf_tab2:
        # Sample data
        categories = ["Electronics", "Clothing", "Home", "Sports", "Other"]
        values = [30, 25, 20, 15, 10]
        
        fig = px.pie(
            values=values,
            names=categories,
            title="Sales by Category"
        )
        
        st.plotly_chart(fig, use_container_width=True)

elif page == "Auctions":
    st.title("Auctions")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category = st.selectbox(
            "Category",
            ["All", "Electronics", "Clothing", "Home", "Sports", "Other"]
        )
    
    with col2:
        price_range = st.slider(
            "Price Range ($)",
            min_value=0,
            max_value=1000,
            value=(0, 1000)
        )
    
    with col3:
        time_filter = st.selectbox(
            "Time Remaining",
            ["All", "Ending Soon", "New Listings"]
        )
    
    # Auction grid
    if "auctions" in st.session_state:
        for auction_id, auction in st.session_state.auctions.items():
            with st.container():
                auction_monitor(auction_id)

elif page == "Research":
    st.title("Research")
    
    # Research form
    with st.form("research_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            product_name = st.text_input("Product Name")
            category = st.selectbox(
                "Category",
                ["Electronics", "Clothing", "Home", "Sports", "Other"]
            )
        
        with col2:
            upc = st.text_input("UPC (Optional)")
            condition = st.selectbox(
                "Condition",
                ["New", "Like New", "Used", "Refurbished"]
            )
        
        submitted = st.form_submit_button("Research")
        
        if submitted:
            # Simulate research
            st.session_state.market_data = {
                "prices": [100, 120, 110, 130, 125, 115, 135, 140, 130, 125]
            }
    
    # Research results
    if "market_data" in st.session_state:
        st.subheader("Market Analysis")
        
        # Price distribution
        fig = go.Figure()
        fig.add_trace(go.Box(
            y=st.session_state.market_data["prices"],
            name="Market Prices",
            boxpoints="all"
        ))
        
        fig.update_layout(
            title="Price Distribution",
            yaxis_title="Price ($)",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Profit calculator
        profit_calculator()

elif page == "Listings":
    st.title("Listings")
    
    # Listing tabs
    listing_tab1, listing_tab2, listing_tab3 = st.tabs([
        "Active Listings",
        "Create Listing",
        "Sold Items"
    ])
    
    with listing_tab1:
        if "listings" in st.session_state:
            for listing_id, listing in st.session_state.listings.items():
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**{listing.get('title', 'Untitled')}**")
                        st.write(f"Price: ${listing.get('price', 0):,.2f}")
                    
                    with col2:
                        st.write(f"Views: {listing.get('views', 0)}")
                        st.write(f"Watchers: {listing.get('watchers', 0)}")
                    
                    with col3:
                        if st.button("Edit", key=f"edit_listing_{listing_id}"):
                            st.session_state.selected_listing = listing_id
                            st.experimental_rerun()
    
    with listing_tab2:
        listing_wizard()
    
    with listing_tab3:
        st.write("Sold items will appear here")

# Real-time notifications
real_time_notifications() 