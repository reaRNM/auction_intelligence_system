from typing import Dict, List, Optional
import logging
import os
import requests
from datetime import datetime
import json
from dotenv import load_dotenv

from .base_generator import BaseGenerator

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EbayGenerator(BaseGenerator):
    """eBay-specific listing generator."""
    
    def __init__(self):
        """Initialize the eBay listing generator."""
        super().__init__()
        self.api_key = os.getenv("EBAY_API_KEY")
        self.base_url = "https://api.ebay.com/sell/inventory/v1"
    
    def generate_listing(self,
                        product_data: Dict,
                        media_files: List[str],
                        strategy: Dict) -> Dict:
        """Generate a complete eBay listing.
        
        Args:
            product_data: Product information dictionary
            media_files: List of media file paths
            strategy: Listing strategy dictionary
            
        Returns:
            Dictionary containing listing details
        """
        try:
            # Get keywords for title optimization
            keywords = self._get_keywords(product_data)
            
            # Generate title
            title = self.optimize_title(product_data, keywords)
            
            # Generate description
            description = self.generate_description(product_data)
            
            # Process media
            media_options = {
                "remove_background": True,
                "color_correction": True,
                "add_watermark": True,
                "generate_video": strategy.get("include_video", False)
            }
            processed_media = self.process_media(media_files, media_options)
            
            # Calculate price
            price_strategy = self.calculate_price(product_data, strategy)
            
            # Calculate promotion settings
            promotion_settings = self._calculate_promotion_settings(strategy)
            
            # Calculate optimization metrics
            optimization_notes = self._calculate_optimization_metrics(
                title,
                keywords,
                price_strategy
            )
            
            # Format output
            return {
                "listing_details": {
                    "title": title,
                    "category": product_data.get("category", ""),
                    "condition": product_data.get("condition", ""),
                    "description": description,
                    "price_strategy": price_strategy
                },
                "media_assets": processed_media,
                "promotion_settings": promotion_settings,
                "optimization_notes": optimization_notes
            }
            
        except Exception as e:
            logger.error(f"eBay listing generation failed: {e}")
            return {}
    
    def _get_keywords(self, product_data: Dict) -> List[str]:
        """Get relevant keywords for product.
        
        Args:
            product_data: Product information dictionary
            
        Returns:
            List of relevant keywords
        """
        try:
            # Extract keywords from product data
            keywords = []
            
            # Add brand and model
            brand = product_data.get("brand", "")
            model = product_data.get("model", "")
            if brand:
                keywords.append(brand)
            if model:
                keywords.append(model)
            
            # Add features
            features = product_data.get("features", [])
            keywords.extend(features)
            
            # Add category
            category = product_data.get("category", "")
            if category:
                keywords.append(category)
            
            # Remove duplicates and empty strings
            keywords = list(set(filter(None, keywords)))
            
            return keywords
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def _calculate_promotion_settings(self, strategy: Dict) -> Dict:
        """Calculate promotion settings.
        
        Args:
            strategy: Listing strategy dictionary
            
        Returns:
            Dictionary containing promotion settings
        """
        try:
            # Get base promotion settings
            promoted_percentage = strategy.get("promoted_percentage", 5.0)
            markdown_rules = strategy.get("markdown_rules", {})
            
            # Calculate markdown schedule
            markdown_schedule = []
            for days, discount in markdown_rules.items():
                markdown_schedule.append({
                    "days": int(days),
                    "discount": float(discount)
                })
            
            return {
                "promoted_listings": {
                    "percentage": promoted_percentage,
                    "duration": "30"  # 30 days
                },
                "markdown_manager": {
                    "enabled": bool(markdown_schedule),
                    "schedule": markdown_schedule
                }
            }
            
        except Exception as e:
            logger.error(f"Promotion settings calculation failed: {e}")
            return {
                "promoted_listings": {"percentage": 0.0, "duration": "30"},
                "markdown_manager": {"enabled": False, "schedule": []}
            }
    
    def _calculate_optimization_metrics(self,
                                      title: str,
                                      keywords: List[str],
                                      price_strategy: Dict) -> Dict:
        """Calculate listing optimization metrics.
        
        Args:
            title: Listing title
            keywords: List of keywords
            price_strategy: Price strategy dictionary
            
        Returns:
            Dictionary containing optimization metrics
        """
        try:
            # Calculate keyword score
            keyword_score = self._calculate_keyword_score(title, keywords)
            
            # Calculate competitiveness
            competitiveness = self._calculate_competitiveness(price_strategy)
            
            # Estimate views
            estimated_views = self._estimate_views(keyword_score, competitiveness)
            
            return {
                "keyword_score": f"{keyword_score}/100",
                "competitiveness": competitiveness,
                "estimated_views": estimated_views
            }
            
        except Exception as e:
            logger.error(f"Optimization metrics calculation failed: {e}")
            return {
                "keyword_score": "0/100",
                "competitiveness": "Low",
                "estimated_views": "0-0/day"
            }
    
    def _calculate_keyword_score(self, title: str, keywords: List[str]) -> int:
        """Calculate keyword optimization score.
        
        Args:
            title: Listing title
            keywords: List of keywords
            
        Returns:
            Keyword score from 0 to 100
        """
        try:
            score = 0
            
            # Check title length
            if 30 <= len(title) <= 80:
                score += 30
            
            # Check keyword usage
            keyword_count = sum(1 for keyword in keywords if keyword.lower() in title.lower())
            score += min(keyword_count * 10, 40)
            
            # Check title structure
            if " - " in title:
                score += 15
            
            if "(" in title and ")" in title:
                score += 15
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Keyword score calculation failed: {e}")
            return 0
    
    def _calculate_competitiveness(self, price_strategy: Dict) -> str:
        """Calculate price competitiveness.
        
        Args:
            price_strategy: Price strategy dictionary
            
        Returns:
            Competitiveness level string
        """
        try:
            if price_strategy["type"] == "Auction":
                return "Medium"
            
            # Compare price to market average
            price = price_strategy["price"]
            market_avg = price_strategy.get("market_average", price)
            
            if price < market_avg * 0.9:
                return "High"
            elif price > market_avg * 1.1:
                return "Low"
            else:
                return "Medium"
            
        except Exception as e:
            logger.error(f"Competitiveness calculation failed: {e}")
            return "Low"
    
    def _estimate_views(self, keyword_score: int, competitiveness: str) -> str:
        """Estimate daily listing views.
        
        Args:
            keyword_score: Keyword optimization score
            competitiveness: Competitiveness level
            
        Returns:
            Estimated views range string
        """
        try:
            # Base views on keyword score
            base_views = keyword_score * 2
            
            # Adjust for competitiveness
            if competitiveness == "High":
                base_views *= 1.5
            elif competitiveness == "Low":
                base_views *= 0.5
            
            # Calculate range
            min_views = int(base_views * 0.8)
            max_views = int(base_views * 1.2)
            
            return f"{min_views}-{max_views}/day"
            
        except Exception as e:
            logger.error(f"View estimation failed: {e}")
            return "0-0/day" 