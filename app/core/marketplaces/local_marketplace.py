from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path

from src.services.marketplaces.base_marketplace import BaseMarketplace

class LocalMarketplace(BaseMarketplace):
    """Local marketplace service implementation."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the local marketplace service."""
        super().__init__()
        
        # Set up database path
        if db_path is None:
            db_path = os.path.join(os.getenv("DATA_DIR", "data"), "local_marketplace.db")
        
        self.db_path = db_path
        
        # Create database directory if it doesn't exist
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create listings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                condition TEXT,
                quantity INTEGER NOT NULL,
                images TEXT,
                attributes TEXT,
                shipping REAL,
                status TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                listing_id TEXT PRIMARY KEY,
                views INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                impressions INTEGER DEFAULT 0,
                conversion_rate REAL DEFAULT 0.0,
                average_position REAL DEFAULT 0.0,
                cost_per_click REAL DEFAULT 0.0,
                total_cost REAL DEFAULT 0.0,
                revenue REAL DEFAULT 0.0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (listing_id) REFERENCES listings (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_listing_analytics(self, listing_id: str) -> Dict:
        """Get analytics data for a specific local listing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get analytics data
        cursor.execute("""
            SELECT * FROM analytics
            WHERE listing_id = ?
        """, (listing_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "views": row[1],
                "clicks": row[2],
                "impressions": row[3],
                "conversion_rate": row[4],
                "average_position": row[5],
                "cost_per_click": row[6],
                "total_cost": row[7],
                "revenue": row[8],
                "raw_data": {
                    "listing_id": row[0],
                    "updated_at": row[9]
                }
            }
        else:
            return {
                "views": 0,
                "clicks": 0,
                "impressions": 0,
                "conversion_rate": 0.0,
                "average_position": 0.0,
                "cost_per_click": 0.0,
                "total_cost": 0.0,
                "revenue": 0.0,
                "raw_data": {}
            }
    
    def update_listing(self, listing_id: str, data: Dict) -> Dict:
        """Update a local listing with new data."""
        if not self._validate_listing_data(data):
            raise ValueError("Invalid listing data")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update listing
        cursor.execute("""
            UPDATE listings
            SET title = ?,
                description = ?,
                price = ?,
                category = ?,
                condition = ?,
                quantity = ?,
                images = ?,
                attributes = ?,
                shipping = ?,
                status = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            data["title"],
            data.get("description"),
            data["price"],
            data.get("category"),
            data.get("condition"),
            data["quantity"],
            json.dumps(data.get("images", [])),
            json.dumps(data.get("attributes", {})),
            data.get("shipping", 0.0),
            data.get("status", "active"),
            self._format_timestamp(datetime.utcnow()),
            listing_id
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_listing_details(listing_id)
    
    def create_listing(self, data: Dict) -> Dict:
        """Create a new local listing."""
        if not self._validate_listing_data(data):
            raise ValueError("Invalid listing data")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate listing ID
        listing_id = f"LOCAL_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create listing
        cursor.execute("""
            INSERT INTO listings (
                id, title, description, price, category, condition,
                quantity, images, attributes, shipping, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing_id,
            data["title"],
            data.get("description"),
            data["price"],
            data.get("category"),
            data.get("condition"),
            data["quantity"],
            json.dumps(data.get("images", [])),
            json.dumps(data.get("attributes", {})),
            data.get("shipping", 0.0),
            data.get("status", "active"),
            self._format_timestamp(datetime.utcnow()),
            self._format_timestamp(datetime.utcnow())
        ))
        
        # Create analytics entry
        cursor.execute("""
            INSERT INTO analytics (
                listing_id, updated_at
            ) VALUES (?, ?)
        """, (
            listing_id,
            self._format_timestamp(datetime.utcnow())
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_listing_details(listing_id)
    
    def delete_listing(self, listing_id: str) -> bool:
        """Delete a local listing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete listing and analytics
        cursor.execute("DELETE FROM analytics WHERE listing_id = ?", (listing_id,))
        cursor.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_listing_details(self, listing_id: str) -> Dict:
        """Get detailed information about a local listing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get listing details
        cursor.execute("""
            SELECT * FROM listings
            WHERE id = ?
        """, (listing_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "price": row[3],
                "category": row[4],
                "condition": row[5],
                "quantity": row[6],
                "images": json.loads(row[7]),
                "attributes": json.loads(row[8]),
                "shipping": row[9],
                "status": row[10],
                "created_at": self._parse_timestamp(row[11]),
                "updated_at": self._parse_timestamp(row[12])
            }
        else:
            raise ValueError(f"Listing not found: {listing_id}")
    
    def search_listings(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Search for local listings matching the query."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        sql = "SELECT * FROM listings WHERE title LIKE ?"
        params = [f"%{query}%"]
        
        if filters:
            if "price_range" in filters:
                sql += " AND price BETWEEN ? AND ?"
                params.extend([
                    filters["price_range"]["min"],
                    filters["price_range"]["max"]
                ])
            
            if "condition" in filters:
                sql += " AND condition = ?"
                params.append(filters["condition"])
        
        # Add pagination
        sql += " LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute search
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        # Get total count
        count_sql = "SELECT COUNT(*) FROM listings WHERE title LIKE ?"
        count_params = [f"%{query}%"]
        
        if filters:
            if "price_range" in filters:
                count_sql += " AND price BETWEEN ? AND ?"
                count_params.extend([
                    filters["price_range"]["min"],
                    filters["price_range"]["max"]
                ])
            
            if "condition" in filters:
                count_sql += " AND condition = ?"
                count_params.append(filters["condition"])
        
        cursor.execute(count_sql, count_params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": [
                {
                    "id": row[0],
                    "title": row[1],
                    "price": row[3],
                    "category": row[4],
                    "condition": row[5],
                    "quantity": row[6],
                    "images": json.loads(row[7]),
                    "shipping": row[9],
                    "status": row[10]
                }
                for row in rows
            ]
        }
    
    def get_market_data(
        self,
        category: str,
        filters: Optional[Dict] = None,
        time_range: Optional[str] = None
    ) -> Dict:
        """Get market data for a specific local category."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        sql = "SELECT * FROM listings WHERE category = ?"
        params = [category]
        
        if time_range:
            end_time = datetime.utcnow()
            if time_range == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = end_time - timedelta(days=30)
            elif time_range == "90d":
                start_time = end_time - timedelta(days=90)
            else:
                start_time = end_time - timedelta(days=30)
            
            sql += " AND created_at BETWEEN ? AND ?"
            params.extend([
                self._format_timestamp(start_time),
                self._format_timestamp(end_time)
            ])
        
        # Execute query
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        conn.close()
        
        if rows:
            # Calculate statistics
            prices = [row[3] for row in rows]
            total_listings = len(prices)
            average_price = sum(prices) / total_listings
            
            # Get price range
            price_range = {
                "min": min(prices),
                "max": max(prices),
                "median": sorted(prices)[len(prices)//2]
            }
            
            # Get popular filters
            conditions = {}
            for row in rows:
                condition = row[5]
                if condition:
                    conditions[condition] = conditions.get(condition, 0) + 1
            
            popular_filters = [
                {"name": "condition", "values": conditions}
            ]
            
            # Calculate trends
            trends = self._calculate_trends(rows)
            
            return {
                "category": category,
                "total_listings": total_listings,
                "average_price": average_price,
                "price_range": price_range,
                "popular_filters": popular_filters,
                "trends": trends,
                "raw_data": {
                    "items": [
                        {
                            "id": row[0],
                            "title": row[1],
                            "price": row[3],
                            "category": row[4],
                            "condition": row[5],
                            "quantity": row[6],
                            "images": json.loads(row[7]),
                            "shipping": row[9],
                            "status": row[10],
                            "created_at": self._parse_timestamp(row[11])
                        }
                        for row in rows
                    ]
                }
            }
        else:
            return {
                "category": category,
                "total_listings": 0,
                "average_price": 0.0,
                "price_range": {
                    "min": 0.0,
                    "max": 0.0,
                    "median": 0.0
                },
                "popular_filters": [],
                "trends": {
                    "daily": {},
                    "overall": {
                        "price_trend": "neutral",
                        "price_change_percent": 0.0,
                        "volume_trend": "neutral",
                        "volume_change_percent": 0.0
                    }
                },
                "raw_data": {
                    "items": []
                }
            }
    
    def _calculate_trends(self, items: List) -> Dict:
        """Calculate market trends from items."""
        # Group items by day
        daily_data = {}
        for item in items:
            created_at = self._parse_timestamp(item[11])
            day = created_at.date().isoformat()
            
            if day not in daily_data:
                daily_data[day] = {
                    "count": 0,
                    "total_price": 0.0,
                    "prices": []
                }
            
            price = item[3]
            daily_data[day]["count"] += 1
            daily_data[day]["total_price"] += price
            daily_data[day]["prices"].append(price)
        
        # Calculate daily statistics
        trends = {
            "daily": {
                day: {
                    "count": data["count"],
                    "average_price": data["total_price"] / data["count"],
                    "price_range": {
                        "min": min(data["prices"]),
                        "max": max(data["prices"]),
                        "median": sorted(data["prices"])[len(data["prices"])//2]
                    }
                }
                for day, data in daily_data.items()
            }
        }
        
        # Calculate overall trends
        all_prices = [price for data in daily_data.values() for price in data["prices"]]
        if all_prices:
            trends["overall"] = {
                "price_trend": "up" if all_prices[-1] > all_prices[0] else "down",
                "price_change_percent": ((all_prices[-1] - all_prices[0]) / all_prices[0] * 100),
                "volume_trend": "up" if daily_data[list(daily_data.keys())[-1]]["count"] > daily_data[list(daily_data.keys())[0]]["count"] else "down",
                "volume_change_percent": ((daily_data[list(daily_data.keys())[-1]]["count"] - daily_data[list(daily_data.keys())[0]]["count"]) / daily_data[list(daily_data.keys())[0]]["count"] * 100)
            }
        else:
            trends["overall"] = {
                "price_trend": "neutral",
                "price_change_percent": 0.0,
                "volume_trend": "neutral",
                "volume_change_percent": 0.0
            }
        
        return trends 