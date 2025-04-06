from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseGenerator(ABC):
    """Base class for listing generators."""
    
    def __init__(self):
        """Initialize the listing generator."""
        self.max_title_length = 80
        self.min_title_length = 30
    
    @abstractmethod
    def generate_listing(self,
                        product_data: Dict,
                        media_files: List[str],
                        strategy: Dict) -> Dict:
        """Generate a complete listing.
        
        Args:
            product_data: Product information dictionary
            media_files: List of media file paths
            strategy: Listing strategy dictionary
            
        Returns:
            Dictionary containing listing details
        """
        pass
    
    def optimize_title(self,
                      product_data: Dict,
                      keywords: List[str]) -> str:
        """Optimize listing title.
        
        Args:
            product_data: Product information dictionary
            keywords: List of relevant keywords
            
        Returns:
            Optimized title string
        """
        try:
            # Extract product details
            brand = product_data.get("brand", "")
            model = product_data.get("model", "")
            condition = product_data.get("condition", "")
            
            # Build title components
            components = []
            
            # Add brand and model
            if brand and model:
                components.append(f"{brand} {model}")
            elif brand:
                components.append(brand)
            elif model:
                components.append(model)
            
            # Add key features
            features = product_data.get("features", [])
            if features:
                key_feature = features[0]  # Use first feature
                components.append(key_feature)
            
            # Add condition
            if condition:
                components.append(f"({condition})")
            
            # Add keywords
            for keyword in keywords[:2]:  # Use top 2 keywords
                if keyword not in " ".join(components):
                    components.append(keyword)
            
            # Join components
            title = " - ".join(components)
            
            # Truncate if too long
            if len(title) > self.max_title_length:
                title = title[:self.max_title_length-3] + "..."
            
            # Ensure minimum length
            if len(title) < self.min_title_length:
                title = title + " - Free Shipping"
            
            return title
            
        except Exception as e:
            logger.error(f"Title optimization failed: {e}")
            return product_data.get("title", "")
    
    def generate_description(self,
                           product_data: Dict,
                           template: Optional[str] = None) -> str:
        """Generate listing description.
        
        Args:
            product_data: Product information dictionary
            template: Optional description template
            
        Returns:
            Generated description string
        """
        try:
            # Use template if provided
            if template:
                description = template
            else:
                description = []
                
                # Add condition disclosure
                condition = product_data.get("condition", "")
                description.append(f"Condition: {condition}")
                
                # Add feature bullet points
                features = product_data.get("features", [])
                if features:
                    description.append("\nFeatures:")
                    for feature in features:
                        description.append(f"• {feature}")
                
                # Add policy statements
                description.append("\nPolicies:")
                description.append("• Free shipping on all orders")
                description.append("• 30-day return policy")
                description.append("• Fast and secure payment")
                
                description = "\n".join(description)
            
            return description
            
        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            return ""
    
    def process_media(self,
                     media_files: List[str],
                     options: Dict) -> Dict:
        """Process media files for listing.
        
        Args:
            media_files: List of media file paths
            options: Processing options dictionary
            
        Returns:
            Dictionary containing processed media assets
        """
        try:
            processed_media = {
                "images": [],
                "video": None
            }
            
            # Process images
            for image_file in media_files:
                if image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    # Apply image enhancements
                    if options.get("remove_background", False):
                        image_file = self._remove_background(image_file)
                    
                    if options.get("color_correction", False):
                        image_file = self._correct_colors(image_file)
                    
                    if options.get("add_watermark", False):
                        image_file = self._add_watermark(image_file)
                    
                    processed_media["images"].append(image_file)
            
            # Generate video if requested
            if options.get("generate_video", False):
                processed_media["video"] = self._generate_product_video(media_files)
            
            return processed_media
            
        except Exception as e:
            logger.error(f"Media processing failed: {e}")
            return {"images": media_files, "video": None}
    
    def calculate_price(self,
                       product_data: Dict,
                       strategy: Dict) -> Dict:
        """Calculate listing price based on strategy.
        
        Args:
            product_data: Product information dictionary
            strategy: Pricing strategy dictionary
            
        Returns:
            Dictionary containing price details
        """
        try:
            base_price = product_data.get("base_price", 0.0)
            price_type = strategy.get("type", "Buy It Now")
            
            if price_type == "Auction":
                # Calculate start price and reserve
                start_price = base_price * 0.8  # 20% below base
                reserve_price = base_price * 0.9  # 10% below base
                
                return {
                    "type": "Auction",
                    "start_price": round(start_price, 2),
                    "reserve_price": round(reserve_price, 2)
                }
            else:
                # Calculate Buy It Now price
                price = base_price
                
                # Apply psychological pricing
                if strategy.get("psychological_pricing", True):
                    price = self._apply_psychological_pricing(price)
                
                # Calculate offer acceptance price
                offer_price = price * 0.95  # 5% below list price
                
                return {
                    "type": "Buy It Now",
                    "price": round(price, 2),
                    "offer_acceptance": round(offer_price, 2)
                }
            
        except Exception as e:
            logger.error(f"Price calculation failed: {e}")
            return {
                "type": "Buy It Now",
                "price": 0.0,
                "offer_acceptance": 0.0
            }
    
    def _remove_background(self, image_file: str) -> str:
        """Remove background from image.
        
        Args:
            image_file: Path to image file
            
        Returns:
            Path to processed image file
        """
        # TODO: Implement background removal
        return image_file
    
    def _correct_colors(self, image_file: str) -> str:
        """Correct colors in image.
        
        Args:
            image_file: Path to image file
            
        Returns:
            Path to processed image file
        """
        # TODO: Implement color correction
        return image_file
    
    def _add_watermark(self, image_file: str) -> str:
        """Add watermark to image.
        
        Args:
            image_file: Path to image file
            
        Returns:
            Path to processed image file
        """
        # TODO: Implement watermarking
        return image_file
    
    def _generate_product_video(self, media_files: List[str]) -> str:
        """Generate product video.
        
        Args:
            media_files: List of media file paths
            
        Returns:
            Path to generated video file
        """
        # TODO: Implement video generation
        return ""
    
    def _apply_psychological_pricing(self, price: float) -> float:
        """Apply psychological pricing.
        
        Args:
            price: Original price
            
        Returns:
            Adjusted price
        """
        # Round to nearest 9
        return round(price - 0.01, 2) 