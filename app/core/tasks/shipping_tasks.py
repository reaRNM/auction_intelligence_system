from typing import Dict, List, Optional
import logging
from celery import shared_task
from datetime import datetime
from ..shipping.shipping_service import ShippingService
from ..database import get_db
from ..models import ShippingLog

logger = logging.getLogger(__name__)

@shared_task(name="shipping-get-rates")
def get_shipping_rates(origin: Dict[str, str],
                      destination: Dict[str, str],
                      package: Dict[str, float],
                      item_fragility: float = 0.0) -> List[Dict]:
    """Get shipping rates from all carriers.
    
    Args:
        origin: Origin address dictionary
        destination: Destination address dictionary
        package: Package details dictionary
        item_fragility: Item fragility score (0-10)
        
    Returns:
        List of shipping options with rates and risk assessments
    """
    try:
        # Initialize shipping service
        shipping_service = ShippingService()
        
        # Get shipping options
        options = shipping_service.get_shipping_options(
            origin,
            destination,
            package,
            item_fragility
        )
        
        # Log the request
        db = get_db()
        log = ShippingLog(
            timestamp=datetime.now(),
            origin=origin,
            destination=destination,
            package=package,
            item_fragility=item_fragility,
            options=options
        )
        db.add(log)
        db.commit()
        
        return options
        
    except Exception as e:
        logger.error(f"Failed to get shipping rates: {e}")
        return []

@shared_task(name="shipping-get-package")
def get_package_recommendations(item_dimensions: Dict[str, float],
                              item_fragility: float = 0.0) -> Dict:
    """Get package size and padding recommendations.
    
    Args:
        item_dimensions: Item dimensions dictionary
        item_fragility: Item fragility score (0-10)
        
    Returns:
        Dictionary containing package recommendations
    """
    try:
        # Initialize shipping service
        shipping_service = ShippingService()
        
        # Get package recommendations
        recommendations = shipping_service.get_optimal_package(
            item_dimensions,
            item_fragility
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Failed to get package recommendations: {e}")
        return {}

@shared_task(name="shipping-train-model")
def train_risk_model(training_data: Dict) -> Dict:
    """Train the damage risk prediction model.
    
    Args:
        training_data: Dictionary containing training data
        
    Returns:
        Dictionary containing training results
    """
    try:
        # Initialize shipping service
        shipping_service = ShippingService()
        
        # Train model
        results = shipping_service.train_risk_model(training_data)
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to train risk model: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@shared_task(name="shipping-get-stats")
def get_shipping_stats() -> Dict:
    """Get shipping service statistics.
    
    Returns:
        Dictionary containing shipping statistics
    """
    try:
        # Get database connection
        db = get_db()
        
        # Get recent shipping logs
        recent_logs = db.query(ShippingLog).order_by(
            ShippingLog.timestamp.desc()
        ).limit(100).all()
        
        # Calculate statistics
        total_requests = len(recent_logs)
        avg_fragility = sum(log.item_fragility for log in recent_logs) / total_requests if total_requests > 0 else 0
        
        carrier_stats = {}
        for log in recent_logs:
            for option in log.options:
                carrier = option["carrier"]
                if carrier not in carrier_stats:
                    carrier_stats[carrier] = {
                        "count": 0,
                        "total_cost": 0,
                        "total_risk": 0
                    }
                carrier_stats[carrier]["count"] += 1
                carrier_stats[carrier]["total_cost"] += option["cost"]
                carrier_stats[carrier]["total_risk"] += option["damage_risk"]["probability"]
        
        # Calculate averages
        for carrier in carrier_stats:
            stats = carrier_stats[carrier]
            stats["avg_cost"] = stats["total_cost"] / stats["count"]
            stats["avg_risk"] = stats["total_risk"] / stats["count"]
        
        return {
            "total_requests": total_requests,
            "avg_fragility": avg_fragility,
            "carrier_stats": carrier_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get shipping stats: {e}")
        return {} 