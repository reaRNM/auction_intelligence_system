from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from src.services.marketplaces.base_marketplace import BaseMarketplace

class AmazonMarketplace(BaseMarketplace):
    """Amazon marketplace service implementation."""
    
    def __init__(self):
        """Initialize the Amazon marketplace service."""
        super().__init__()
        
        # Initialize API clients
        self.selling_api = boto3.client(
            "sellingpartnerapi",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        
        self.catalog_api = boto3.client(
            "catalogapi",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
    
    def get_listing_analytics(self, listing_id: str) -> Dict:
        """Get analytics data for a specific Amazon listing."""
        try:
            # Get listing details
            response = self.selling_api.get_catalog_item(
                MarketplaceId=os.getenv("AMAZON_MARKETPLACE_ID"),
                ASIN=listing_id
            )
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                item = response["Item"]
                
                # Get advertising data
                ad_data = self._get_advertising_data(listing_id)
                
                # Get sales data
                sales_data = self._get_sales_data(listing_id)
                
                return {
                    "views": ad_data.get("impressions", 0),
                    "clicks": ad_data.get("clicks", 0),
                    "impressions": ad_data.get("impressions", 0),
                    "conversion_rate": sales_data.get("conversion_rate", 0.0),
                    "average_position": ad_data.get("average_position", 0.0),
                    "cost_per_click": ad_data.get("cost_per_click", 0.0),
                    "total_cost": ad_data.get("total_cost", 0.0),
                    "revenue": sales_data.get("revenue", 0.0),
                    "raw_data": {
                        "item": item,
                        "advertising": ad_data,
                        "sales": sales_data
                    }
                }
            else:
                raise ClientError(
                    {"Error": {"Code": "InvalidRequest", "Message": "Failed to get listing details"}},
                    "get_catalog_item"
                )
                
        except ClientError as e:
            raise Exception(f"Amazon API error: {str(e)}")
    
    def update_listing(self, listing_id: str, data: Dict) -> Dict:
        """Update an Amazon listing with new data."""
        try:
            if not self._validate_listing_data(data):
                raise ValueError("Invalid listing data")
            
            # Format data for Amazon API
            amazon_data = self._format_listing_data(data)
            
            # Prepare API request
            request = {
                "MarketplaceId": os.getenv("AMAZON_MARKETPLACE_ID"),
                "ASIN": listing_id,
                "Item": {
                    "Title": amazon_data["title"],
                    "Description": amazon_data["description"],
                    "Price": amazon_data["price"],
                    "Category": amazon_data["category"],
                    "Condition": amazon_data["condition"],
                    "Quantity": amazon_data["quantity"],
                    "Images": amazon_data["images"],
                    "Attributes": amazon_data["attributes"],
                    "Shipping": amazon_data["shipping"]
                }
            }
            
            # Update listing
            response = self.selling_api.update_catalog_item(**request)
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                return self.get_listing_details(listing_id)
            else:
                raise ClientError(
                    {"Error": {"Code": "InvalidRequest", "Message": "Failed to update listing"}},
                    "update_catalog_item"
                )
                
        except ClientError as e:
            raise Exception(f"Amazon API error: {str(e)}")
    
    def create_listing(self, data: Dict) -> Dict:
        """Create a new Amazon listing."""
        try:
            if not self._validate_listing_data(data):
                raise ValueError("Invalid listing data")
            
            # Format data for Amazon API
            amazon_data = self._format_listing_data(data)
            
            # Prepare API request
            request = {
                "MarketplaceId": os.getenv("AMAZON_MARKETPLACE_ID"),
                "Item": {
                    "Title": amazon_data["title"],
                    "Description": amazon_data["description"],
                    "Price": amazon_data["price"],
                    "Category": amazon_data["category"],
                    "Condition": amazon_data["condition"],
                    "Quantity": amazon_data["quantity"],
                    "Images": amazon_data["images"],
                    "Attributes": amazon_data["attributes"],
                    "Shipping": amazon_data["shipping"]
                }
            }
            
            # Create listing
            response = self.selling_api.create_catalog_item(**request)
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                return self.get_listing_details(response["ASIN"])
            else:
                raise ClientError(
                    {"Error": {"Code": "InvalidRequest", "Message": "Failed to create listing"}},
                    "create_catalog_item"
                )
                
        except ClientError as e:
            raise Exception(f"Amazon API error: {str(e)}")
    
    def delete_listing(self, listing_id: str) -> bool:
        """Delete an Amazon listing."""
        try:
            # Delete listing
            response = self.selling_api.delete_catalog_item(
                MarketplaceId=os.getenv("AMAZON_MARKETPLACE_ID"),
                ASIN=listing_id
            )
            
            return response["ResponseMetadata"]["HTTPStatusCode"] == 200
            
        except ClientError as e:
            raise Exception(f"Amazon API error: {str(e)}")
    
    def get_listing_details(self, listing_id: str) -> Dict:
        """Get detailed information about an Amazon listing."""
        try:
            response = self.selling_api.get_catalog_item(
                MarketplaceId=os.getenv("AMAZON_MARKETPLACE_ID"),
                ASIN=listing_id
            )
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                item = response["Item"]
                return {
                    "id": item["ASIN"],
                    "title": item["Title"],
                    "description": item["Description"],
                    "price": float(item["Price"]),
                    "category": item["Category"],
                    "condition": item["Condition"],
                    "quantity": int(item["Quantity"]),
                    "images": item["Images"],
                    "attributes": item["Attributes"],
                    "shipping": item["Shipping"],
                    "status": item["Status"],
                    "created_at": self._parse_timestamp(item["CreatedAt"]),
                    "updated_at": self._parse_timestamp(item["UpdatedAt"])
                }
            else:
                raise ClientError(
                    {"Error": {"Code": "InvalidRequest", "Message": "Failed to get listing details"}},
                    "get_catalog_item"
                )
                
        except ClientError as e:
            raise Exception(f"Amazon API error: {str(e)}")
    
    def search_listings(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Search for Amazon listings matching the query."""
        try:
            # Prepare search request
            request = {
                "MarketplaceId": os.getenv("AMAZON_MARKETPLACE_ID"),
                "Keywords": query,
                "Page": page,
                "PageSize": page_size
            }
            
            # Add filters
            if filters:
                request["Filters"] = {}
                
                if "price_range" in filters:
                    request["Filters"]["PriceRange"] = {
                        "Min": filters["price_range"]["min"],
                        "Max": filters["price_range"]["max"]
                    }
                
                if "condition" in filters:
                    request["Filters"]["Condition"] = filters["condition"]
            
            # Execute search
            response = self.catalog_api.search_catalog_items(**request)
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                search_result = response["Items"]
                return {
                    "total": int(response["TotalResults"]),
                    "page": page,
                    "page_size": page_size,
                    "results": [
                        {
                            "id": item["ASIN"],
                            "title": item["Title"],
                            "price": float(item["Price"]),
                            "url": item["DetailPageURL"],
                            "image_url": item["ImageURL"],
                            "condition": item["Condition"],
                            "location": item["Location"],
                            "shipping": float(item["ShippingCost"])
                        }
                        for item in search_result
                    ]
                }
            else:
                raise ClientError(
                    {"Error": {"Code": "InvalidRequest", "Message": "Failed to search listings"}},
                    "search_catalog_items"
                )
                
        except ClientError as e:
            raise Exception(f"Amazon API error: {str(e)}")
    
    def get_market_data(
        self,
        category: str,
        filters: Optional[Dict] = None,
        time_range: Optional[str] = None
    ) -> Dict:
        """Get market data for a specific Amazon category."""
        try:
            # Prepare search request
            request = {
                "MarketplaceId": os.getenv("AMAZON_MARKETPLACE_ID"),
                "Category": category,
                "PageSize": 100
            }
            
            # Add time range filter
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
                
                request["TimeRange"] = {
                    "Start": self._format_timestamp(start_time),
                    "End": self._format_timestamp(end_time)
                }
            
            # Execute search
            response = self.catalog_api.get_category_items(**request)
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                items = response["Items"]
                
                # Calculate statistics
                prices = [float(item["Price"]) for item in items]
                total_listings = len(prices)
                average_price = sum(prices) / total_listings if total_listings > 0 else 0.0
                
                # Get price range
                price_range = {
                    "min": min(prices) if prices else 0.0,
                    "max": max(prices) if prices else 0.0,
                    "median": sorted(prices)[len(prices)//2] if prices else 0.0
                }
                
                # Get popular filters
                conditions = {}
                locations = {}
                for item in items:
                    conditions[item["Condition"]] = conditions.get(item["Condition"], 0) + 1
                    locations[item["Location"]] = locations.get(item["Location"], 0) + 1
                
                popular_filters = [
                    {"name": "condition", "values": conditions},
                    {"name": "location", "values": locations}
                ]
                
                # Calculate trends
                trends = self._calculate_trends(items)
                
                return {
                    "category": category,
                    "total_listings": total_listings,
                    "average_price": average_price,
                    "price_range": price_range,
                    "popular_filters": popular_filters,
                    "trends": trends,
                    "raw_data": {
                        "items": items
                    }
                }
            else:
                raise ClientError(
                    {"Error": {"Code": "InvalidRequest", "Message": "Failed to get market data"}},
                    "get_category_items"
                )
                
        except ClientError as e:
            raise Exception(f"Amazon API error: {str(e)}")
    
    def _get_advertising_data(self, listing_id: str) -> Dict:
        """Get advertising data for a listing."""
        try:
            response = self.selling_api.get_advertising_data(
                MarketplaceId=os.getenv("AMAZON_MARKETPLACE_ID"),
                ASIN=listing_id
            )
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                ad_data = response["AdvertisingData"]
                return {
                    "impressions": int(ad_data["Impressions"]),
                    "clicks": int(ad_data["Clicks"]),
                    "average_position": float(ad_data["AveragePosition"]),
                    "cost_per_click": float(ad_data["CostPerClick"]),
                    "total_cost": float(ad_data["TotalCost"])
                }
            else:
                return {
                    "impressions": 0,
                    "clicks": 0,
                    "average_position": 0.0,
                    "cost_per_click": 0.0,
                    "total_cost": 0.0
                }
                
        except ClientError:
            return {
                "impressions": 0,
                "clicks": 0,
                "average_position": 0.0,
                "cost_per_click": 0.0,
                "total_cost": 0.0
            }
    
    def _get_sales_data(self, listing_id: str) -> Dict:
        """Get sales data for a listing."""
        try:
            response = self.selling_api.get_sales_data(
                MarketplaceId=os.getenv("AMAZON_MARKETPLACE_ID"),
                ASIN=listing_id
            )
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                sales_data = response["SalesData"]
                return {
                    "revenue": float(sales_data["Revenue"]),
                    "units_sold": int(sales_data["UnitsSold"]),
                    "conversion_rate": float(sales_data["ConversionRate"])
                }
            else:
                return {
                    "revenue": 0.0,
                    "units_sold": 0,
                    "conversion_rate": 0.0
                }
                
        except ClientError:
            return {
                "revenue": 0.0,
                "units_sold": 0,
                "conversion_rate": 0.0
            }
    
    def _calculate_trends(self, items: List) -> Dict:
        """Calculate market trends from items."""
        # Group items by day
        daily_data = {}
        for item in items:
            created_at = self._parse_timestamp(item["CreatedAt"])
            day = created_at.date().isoformat()
            
            if day not in daily_data:
                daily_data[day] = {
                    "count": 0,
                    "total_price": 0.0,
                    "prices": []
                }
            
            price = float(item["Price"])
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
        trends["overall"] = {
            "price_trend": "up" if all_prices[-1] > all_prices[0] else "down",
            "price_change_percent": ((all_prices[-1] - all_prices[0]) / all_prices[0] * 100) if all_prices else 0.0,
            "volume_trend": "up" if daily_data[list(daily_data.keys())[-1]]["count"] > daily_data[list(daily_data.keys())[0]]["count"] else "down",
            "volume_change_percent": ((daily_data[list(daily_data.keys())[-1]]["count"] - daily_data[list(daily_data.keys())[0]]["count"]) / daily_data[list(daily_data.keys())[0]]["count"] * 100) if daily_data else 0.0
        }
        
        return trends 