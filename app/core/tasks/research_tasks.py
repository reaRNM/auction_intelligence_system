from typing import Dict, List, Optional
import logging
from celery import shared_task
from datetime import datetime
from sqlalchemy.orm import Session

from ..research.research_service import ResearchService
from ..database import get_db
from ..models import ResearchLog

logger = logging.getLogger(__name__)

@shared_task
def research_product(upc: Optional[str] = None,
                    brand: Optional[str] = None,
                    model: Optional[str] = None,
                    category: Optional[str] = None,
                    asin: Optional[str] = None,
                    ebay_id: Optional[str] = None) -> Dict:
    """Celery task to research a product.
    
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
    research_service = ResearchService()
    db = next(get_db())
    
    try:
        # Research product
        result = research_service.research_product(
            upc=upc,
            brand=brand,
            model=model,
            category=category,
            asin=asin,
            ebay_id=ebay_id
        )
        
        # Log research
        log = ResearchLog(
            upc=upc,
            brand=brand,
            model=model,
            category=category,
            asin=asin,
            ebay_id=ebay_id,
            data=result,
            created_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        
        return result
        
    except Exception as e:
        logger.error(f"Product research failed: {e}")
        raise
    
    finally:
        db.close()

@shared_task
def train_models(price_data: List[Dict], return_data: List[Dict]) -> Dict:
    """Celery task to train research models.
    
    Args:
        price_data: List of dictionaries containing price training data
        return_data: List of dictionaries containing return training data
        
    Returns:
        Dictionary containing training results
    """
    research_service = ResearchService()
    
    try:
        # Train models
        research_service.train_models(price_data, return_data)
        
        # Get model stats
        stats = research_service.get_research_stats()
        
        return {
            "status": "success",
            "models_trained": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@shared_task
def update_economic_indicators(gdp_growth: float,
                             inflation_rate: float,
                             unemployment_rate: float) -> Dict:
    """Celery task to update economic indicators.
    
    Args:
        gdp_growth: GDP growth rate
        inflation_rate: Inflation rate
        unemployment_rate: Unemployment rate
        
    Returns:
        Dictionary containing update results
    """
    research_service = ResearchService()
    
    try:
        # Update indicators
        research_service.update_economic_indicators(
            gdp_growth=gdp_growth,
            inflation_rate=inflation_rate,
            unemployment_rate=unemployment_rate
        )
        
        # Get updated stats
        stats = research_service.get_research_stats()
        
        return {
            "status": "success",
            "indicators_updated": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to update economic indicators: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@shared_task
def get_research_stats() -> Dict:
    """Celery task to get research service statistics.
    
    Returns:
        Dictionary containing research statistics
    """
    research_service = ResearchService()
    
    try:
        stats = research_service.get_research_stats()
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get research stats: {e}")
        return {
            "status": "error",
            "error": str(e)
        } 