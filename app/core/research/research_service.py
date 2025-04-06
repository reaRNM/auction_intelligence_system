from typing import Dict, List, Optional, Union
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from .amazon_research import AmazonResearch
from .ebay_research import EbayResearch
from .ml_models import PricePredictor, ReturnRiskPredictor

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ResearchService:
    """Service for coordinating product research operations."""
    
    def __init__(self):
        """Initialize the research service."""
        self.amazon_research = AmazonResearch()
        self.ebay_research = EbayResearch()
        self.price_predictor = PricePredictor()
        self.return_risk_predictor = ReturnRiskPredictor()
    
    def research_product(self, 
                        upc: Optional[str] = None,
                        brand: Optional[str] = None,
                        model: Optional[str] = None,
                        category: Optional[str] = None,
                        asin: Optional[str] = None,
                        ebay_id: Optional[str] = None) -> Dict:
        """Research a product using all available sources.
        
        Args:
            upc: Optional UPC to search for
            brand: Optional brand name
            model: Optional model name
            category: Optional category
            asin: Optional Amazon ASIN
            ebay_id: Optional eBay item ID
            
        Returns:
            Dictionary containing research results
        """
        try:
            # Check database for similar items
            similar_items = self.amazon_research.check_database(
                upc=upc,
                brand=brand,
                model=model,
                category=category
            )
            
            # Get Amazon data if ASIN provided
            amazon_data = {}
            if asin:
                amazon_data = self.amazon_research.get_amazon_data(asin)
            
            # Get eBay data if item ID provided
            ebay_data = {}
            if ebay_id:
                ebay_data = self.ebay_research.get_ebay_data(ebay_id)
            
            # Get price prediction
            price_features = {
                "brand": brand,
                "category": category,
                "gdp_growth": float(os.getenv("GDP_GROWTH", "0.0")),
                "inflation_rate": float(os.getenv("INFLATION_RATE", "0.0")),
                "unemployment_rate": float(os.getenv("UNEMPLOYMENT_RATE", "0.0"))
            }
            predicted_price, price_importance = self.price_predictor.predict(price_features)
            
            # Get return risk prediction
            risk_features = {
                "product_type": category,
                "condition": "Used",  # Default to used for auction items
                "seller_rating": 0.0,  # Will be updated if available
                "description": "",  # Will be updated if available
                "returns_accepted": True  # Default to True for auction items
            }
            risk_category, risk_probability = self.return_risk_predictor.predict(risk_features)
            
            # Format output
            return {
                "similar_items": similar_items,
                "amazon_data": amazon_data,
                "ebay_data": ebay_data,
                "predictions": {
                    "price": {
                        "predicted": predicted_price,
                        "importance": price_importance
                    },
                    "return_risk": {
                        "category": risk_category,
                        "probability": risk_probability
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Product research failed: {e}")
            return {}
    
    def train_models(self, price_data: List[Dict], return_data: List[Dict]) -> None:
        """Train the machine learning models.
        
        Args:
            price_data: List of dictionaries containing price training data
            return_data: List of dictionaries containing return training data
        """
        try:
            # Train price predictor
            if price_data:
                price_df = pd.DataFrame(price_data)
                self.price_predictor.train(price_df)
            
            # Train return risk predictor
            if return_data:
                return_df = pd.DataFrame(return_data)
                self.return_risk_predictor.train(return_df)
                
        except Exception as e:
            logger.error(f"Model training failed: {e}")
    
    def update_economic_indicators(self, gdp_growth: float, inflation_rate: float,
                                 unemployment_rate: float) -> None:
        """Update economic indicators for price prediction.
        
        Args:
            gdp_growth: GDP growth rate
            inflation_rate: Inflation rate
            unemployment_rate: Unemployment rate
        """
        try:
            os.environ["GDP_GROWTH"] = str(gdp_growth)
            os.environ["INFLATION_RATE"] = str(inflation_rate)
            os.environ["UNEMPLOYMENT_RATE"] = str(unemployment_rate)
            
        except Exception as e:
            logger.error(f"Failed to update economic indicators: {e}")
    
    def get_research_stats(self) -> Dict:
        """Get statistics about the research service.
        
        Returns:
            Dictionary containing research statistics
        """
        try:
            return {
                "models": {
                    "price_predictor": {
                        "loaded": self.price_predictor.model is not None,
                        "features": self.price_predictor.feature_names
                    },
                    "return_risk_predictor": {
                        "loaded": self.return_risk_predictor.model is not None,
                        "features": self.return_risk_predictor.feature_names
                    }
                },
                "economic_indicators": {
                    "gdp_growth": float(os.getenv("GDP_GROWTH", "0.0")),
                    "inflation_rate": float(os.getenv("INFLATION_RATE", "0.0")),
                    "unemployment_rate": float(os.getenv("UNEMPLOYMENT_RATE", "0.0"))
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get research stats: {e}")
            return {} 