from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta
import requests
from ebaysdk.finding import Connection as FindingAPI
from ebaysdk.trading import Connection as TradingAPI
from ebaysdk.exception import ConnectionError

from src.services.marketplaces.base_marketplace import BaseMarketplace

class EbayMarketplace(BaseMarketplace):
    """eBay marketplace service implementation."""
    
    def __init__(self):
        """Initialize the eBay marketplace service."""
        super().__init__()
        
        # Initialize API clients
        self.finding_api = FindingAPI(
            appid=os.getenv("EBAY_APP_ID"),
            config_file=None
        )
        self.trading_api = TradingAPI(
            appid=os.getenv("EBAY_APP_ID"),
            devid=os.getenv("EBAY_DEV_ID"),
            certid=os.getenv("EBAY_CERT_ID"),
            token=os.getenv("EBAY_AUTH_TOKEN"),
            config_file=None
        )
    
    def get_listing_analytics(self, listing_id: str) -> Dict:
        """Get analytics data for a specific eBay listing."""
        try:
            # Get listing details
            response = self.trading_api.execute(
                "GetItem",
                {"ItemID": listing_id}
            )
            
            if response.reply.Ack == "Success":
                item = response.reply.Item
                
                # Get view and click data
                views = int(item.ViewItemURLForNaturalSearch)
                clicks = int(item.ViewItemURLForNaturalSearch)
                
                # Calculate conversion rate
                conversion_rate = clicks / views if views > 0 else 0.0
                
                # Get advertising data
                ad_data = self._get_advertising_data(listing_id)
                
                return {
                    "views": views,
                    "clicks": clicks,
                    "impressions": ad_data.get("impressions", 0),
                    "conversion_rate": conversion_rate,
                    "average_position": ad_data.get("average_position", 0.0),
                    "cost_per_click": ad_data.get("cost_per_click", 0.0),
                    "total_cost": ad_data.get("total_cost", 0.0),
                    "revenue": float(item.SellingStatus.CurrentPrice.value),
                    "raw_data": {
                        "item": item.dict(),
                        "advertising": ad_data,
                    }
                }
            else:
                raise ConnectionError(f"Failed to get listing details: {response.reply.Errors}")
                
        except ConnectionError as e:
            raise Exception(f"eBay API error: {str(e)}")
    
    def update_listing(self, listing_id: str, data: Dict) -> Dict:
        """Update an eBay listing with new data."""
        try:
            if not self._validate_listing_data(data):
                raise ValueError("Invalid listing data")
            
            # Format data for eBay API
            ebay_data = self._format_listing_data(data)
            
            # Prepare API request
            request = {
                "Item": {
                    "ItemID": listing_id,
                    "Title": ebay_data["title"],
                    "Description": ebay_data["description"],
                    "StartPrice": ebay_data["price"],
                    "CategoryID": ebay_data["category"],
                    "ConditionID": ebay_data["condition"],
                    "Quantity": ebay_data["quantity"],
                    "PictureDetails": {
                        "PictureURL": ebay_data["images"]
                    },
                    "ItemSpecifics": ebay_data["attributes"],
                    "ShippingDetails": ebay_data["shipping"],
                }
            }
            
            # Update listing
            response = self.trading_api.execute("ReviseItem", request)
            
            if response.reply.Ack == "Success":
                return self.get_listing_details(listing_id)
            else:
                raise ConnectionError(f"Failed to update listing: {response.reply.Errors}")
                
        except ConnectionError as e:
            raise Exception(f"eBay API error: {str(e)}")
    
    def create_listing(self, data: Dict) -> Dict:
        """Create a new eBay listing."""
        try:
            if not self._validate_listing_data(data):
                raise ValueError("Invalid listing data")
            
            # Format data for eBay API
            ebay_data = self._format_listing_data(data)
            
            # Prepare API request
            request = {
                "Item": {
                    "Title": ebay_data["title"],
                    "Description": ebay_data["description"],
                    "StartPrice": ebay_data["price"],
                    "CategoryID": ebay_data["category"],
                    "ConditionID": ebay_data["condition"],
                    "Quantity": ebay_data["quantity"],
                    "PictureDetails": {
                        "PictureURL": ebay_data["images"]
                    },
                    "ItemSpecifics": ebay_data["attributes"],
                    "ShippingDetails": ebay_data["shipping"],
                    "ListingDuration": "GTC",  # Good Till Cancelled
                    "ListingType": "FixedPriceItem",
                }
            }
            
            # Create listing
            response = self.trading_api.execute("AddFixedPriceItem", request)
            
            if response.reply.Ack == "Success":
                return self.get_listing_details(response.reply.ItemID)
            else:
                raise ConnectionError(f"Failed to create listing: {response.reply.Errors}")
                
        except ConnectionError as e:
            raise Exception(f"eBay API error: {str(e)}")
    
    def delete_listing(self, listing_id: str) -> bool:
        """Delete an eBay listing."""
        try:
            # End listing
            request = {
                "ItemID": listing_id,
                "EndingReason": "Other"
            }
            
            response = self.trading_api.execute("EndItem", request)
            
            return response.reply.Ack == "Success"
            
        except ConnectionError as e:
            raise Exception(f"eBay API error: {str(e)}")
    
    def get_listing_details(self, listing_id: str) -> Dict:
        """Get detailed information about an eBay listing."""
        try:
            response = self.trading_api.execute(
                "GetItem",
                {"ItemID": listing_id}
            )
            
            if response.reply.Ack == "Success":
                item = response.reply.Item
                return {
                    "id": item.ItemID,
                    "title": item.Title,
                    "description": item.Description,
                    "price": float(item.SellingStatus.CurrentPrice.value),
                    "category": item.PrimaryCategory.CategoryID,
                    "condition": item.ConditionID,
                    "quantity": int(item.Quantity),
                    "images": [pic.PictureURL for pic in item.PictureDetails.PictureURL],
                    "attributes": item.ItemSpecifics.NameValueList,
                    "shipping": item.ShippingDetails.dict(),
                    "status": item.SellingStatus.ListingStatus,
                    "created_at": self._parse_timestamp(item.ListingDetails.StartTime),
                    "updated_at": self._parse_timestamp(item.ListingDetails.EndTime),
                }
            else:
                raise ConnectionError(f"Failed to get listing details: {response.reply.Errors}")
                
        except ConnectionError as e:
            raise Exception(f"eBay API error: {str(e)}")
    
    def search_listings(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Search for eBay listings matching the query."""
        try:
            # Prepare search request
            request = {
                "keywords": query,
                "paginationInput": {
                    "pageNumber": page,
                    "entriesPerPage": page_size
                },
                "sortOrder": "BestMatch"
            }
            
            # Add filters
            if filters:
                if "price_range" in filters:
                    request["itemFilter"] = [{
                        "name": "CurrentPrice",
                        "minValue": filters["price_range"]["min"],
                        "maxValue": filters["price_range"]["max"]
                    }]
                
                if "condition" in filters:
                    request["itemFilter"].append({
                        "name": "Condition",
                        "value": filters["condition"]
                    })
            
            # Execute search
            response = self.finding_api.execute("findItemsAdvanced", request)
            
            if response.reply.Ack == "Success":
                search_result = response.reply.searchResult
                return {
                    "total": int(search_result._count),
                    "page": page,
                    "page_size": page_size,
                    "results": [
                        {
                            "id": item.itemId,
                            "title": item.title,
                            "price": float(item.sellingStatus.currentPrice.value),
                            "url": item.viewItemURL,
                            "image_url": item.galleryURL,
                            "condition": item.condition.conditionId,
                            "location": item.location,
                            "shipping": item.shippingInfo.shippingServiceCost.value if hasattr(item.shippingInfo, "shippingServiceCost") else 0.0,
                        }
                        for item in search_result.item
                    ]
                }
            else:
                raise ConnectionError(f"Failed to search listings: {response.reply.errorMessage}")
                
        except ConnectionError as e:
            raise Exception(f"eBay API error: {str(e)}")
    
    def get_market_data(
        self,
        category: str,
        filters: Optional[Dict] = None,
        time_range: Optional[str] = None
    ) -> Dict:
        """Get market data for a specific eBay category."""
        try:
            # Prepare search request
            request = {
                "categoryId": category,
                "sortOrder": "EndTimeSoonest",
                "paginationInput": {
                    "entriesPerPage": 100
                }
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
                
                request["itemFilter"] = [{
                    "name": "EndTimeFrom",
                    "value": self._format_timestamp(start_time)
                }, {
                    "name": "EndTimeTo",
                    "value": self._format_timestamp(end_time)
                }]
            
            # Execute search
            response = self.finding_api.execute("findItemsAdvanced", request)
            
            if response.reply.Ack == "Success":
                items = response.reply.searchResult.item
                
                # Calculate statistics
                prices = [float(item.sellingStatus.currentPrice.value) for item in items]
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
                    conditions[item.condition.conditionId] = conditions.get(item.condition.conditionId, 0) + 1
                    locations[item.location] = locations.get(item.location, 0) + 1
                
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
                        "items": [item.dict() for item in items]
                    }
                }
            else:
                raise ConnectionError(f"Failed to get market data: {response.reply.errorMessage}")
                
        except ConnectionError as e:
            raise Exception(f"eBay API error: {str(e)}")
    
    def _get_advertising_data(self, listing_id: str) -> Dict:
        """Get advertising data for a listing."""
        try:
            response = self.trading_api.execute(
                "GetPromotionalSaleDetails",
                {"ItemID": listing_id}
            )
            
            if response.reply.Ack == "Success":
                promo = response.reply.PromotionalSaleDetails
                return {
                    "impressions": int(promo.ImpressionCount),
                    "average_position": float(promo.AveragePosition),
                    "cost_per_click": float(promo.CostPerClick),
                    "total_cost": float(promo.TotalCost)
                }
            else:
                return {
                    "impressions": 0,
                    "average_position": 0.0,
                    "cost_per_click": 0.0,
                    "total_cost": 0.0
                }
                
        except ConnectionError:
            return {
                "impressions": 0,
                "average_position": 0.0,
                "cost_per_click": 0.0,
                "total_cost": 0.0
            }
    
    def _calculate_trends(self, items: List) -> Dict:
        """Calculate market trends from items."""
        # Group items by day
        daily_data = {}
        for item in items:
            end_time = self._parse_timestamp(item.listingInfo.endTime)
            day = end_time.date().isoformat()
            
            if day not in daily_data:
                daily_data[day] = {
                    "count": 0,
                    "total_price": 0.0,
                    "prices": []
                }
            
            price = float(item.sellingStatus.currentPrice.value)
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