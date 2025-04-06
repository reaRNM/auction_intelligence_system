from celery import shared_task
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.db.config import SessionLocal
from src.models.product import Product, MarketData
from src.services.market_data.ebay_market import EbayMarketData
from src.services.market_data.amazon_market import AmazonMarketData
from src.services.market_data.keepa_market import KeepaMarketData

logger = logging.getLogger(__name__)

@shared_task(
    name="src.services.tasks.product_tasks.update_market_data",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def update_market_data(self) -> Dict[str, int]:
    """Update market data for all products."""
    try:
        db = SessionLocal()
        market_data_sources = [
            EbayMarketData(),
            AmazonMarketData(),
            KeepaMarketData(),
        ]
        
        total_updated = 0
        total_new = 0
        
        # Get all products
        products = db.query(Product).all()
        
        for product in products:
            try:
                for source in market_data_sources:
                    try:
                        # Get market data
                        market_data = source.get_market_data(
                            product.brand,
                            product.model,
                            product.condition,
                        )
                        
                        if market_data:
                            # Create new market data entry
                            new_data = MarketData(
                                product_id=product.id,
                                source=source.name,
                                price=market_data["price"],
                                condition=market_data["condition"],
                                url=market_data.get("url"),
                                seller_rating=market_data.get("seller_rating"),
                                shipping_cost=market_data.get("shipping_cost"),
                                raw_data=market_data.get("raw_data"),
                            )
                            
                            db.add(new_data)
                            total_new += 1
                            
                            # Update product market data
                            update_product_market_data(db, product, market_data)
                            
                    except Exception as e:
                        logger.error(f"Error getting market data from {source.name}: {e}")
                        continue
                
                db.commit()
                total_updated += 1
                
            except Exception as e:
                logger.error(f"Error updating product {product.id}: {e}")
                continue
        
        return {
            "updated": total_updated,
            "new_data_points": total_new,
        }
        
    except Exception as e:
        logger.error(f"Error in update_market_data: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()

@shared_task(
    name="src.services.tasks.product_tasks.analyze_product_trends",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def analyze_product_trends(self, category: Optional[str] = None) -> Dict[str, float]:
    """Analyze product trends for a specific category or all categories."""
    try:
        db = SessionLocal()
        
        # Base query
        query = db.query(Product)
        
        # Filter by category if specified
        if category:
            query = query.filter(Product.category == category)
        
        # Get products with market data from the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        query = query.join(MarketData).filter(MarketData.timestamp >= thirty_days_ago)
        
        products = query.all()
        
        # Calculate metrics
        total_products = len(products)
        total_market_data = sum(len(p.market_data) for p in products)
        
        # Calculate price trends
        price_trends = {}
        for product in products:
            if product.market_data:
                prices = [md.price for md in product.market_data]
                price_trends[product.id] = {
                    "min": min(prices),
                    "max": max(prices),
                    "avg": sum(prices) / len(prices),
                    "volatility": calculate_volatility(prices),
                }
        
        # Calculate average metrics
        avg_min_price = sum(t["min"] for t in price_trends.values()) / total_products if total_products > 0 else 0
        avg_max_price = sum(t["max"] for t in price_trends.values()) / total_products if total_products > 0 else 0
        avg_price = sum(t["avg"] for t in price_trends.values()) / total_products if total_products > 0 else 0
        avg_volatility = sum(t["volatility"] for t in price_trends.values()) / total_products if total_products > 0 else 0
        
        return {
            "total_products": total_products,
            "total_market_data": total_market_data,
            "avg_min_price": avg_min_price,
            "avg_max_price": avg_max_price,
            "avg_price": avg_price,
            "avg_volatility": avg_volatility,
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_product_trends: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()

def update_product_market_data(db: Session, product: Product, market_data: Dict) -> None:
    """Update product market data based on new market data."""
    # Update current market price
    if "price" in market_data:
        product.current_market_price = market_data["price"]
    
    # Update price history
    if not product.price_history:
        product.price_history = []
    
    product.price_history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "price": market_data["price"],
        "source": market_data.get("source"),
    })
    
    # Keep only last 30 days of price history
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    product.price_history = [
        p for p in product.price_history
        if datetime.fromisoformat(p["timestamp"]) >= thirty_days_ago
    ]
    
    # Update min/max/average prices
    if product.price_history:
        prices = [p["price"] for p in product.price_history]
        product.lowest_market_price = min(prices)
        product.highest_market_price = max(prices)
        product.average_market_price = sum(prices) / len(prices)

def calculate_volatility(prices: List[float]) -> float:
    """Calculate price volatility using standard deviation."""
    if not prices:
        return 0.0
    
    mean = sum(prices) / len(prices)
    squared_diff_sum = sum((p - mean) ** 2 for p in prices)
    variance = squared_diff_sum / len(prices)
    return variance ** 0.5  # Standard deviation 