from typing import Dict, List, Optional
import logging
from datetime import datetime
from .base_shipping import BaseShipping
from .usps_shipping import USPSShipping
from .ups_shipping import UPSShipping
from .fedex_shipping import FedExShipping
from .risk_engine import RiskEngine

logger = logging.getLogger(__name__)

class ShippingService:
    """Main shipping service that coordinates all shipping operations."""
    
    def __init__(self):
        """Initialize the shipping service."""
        # Initialize carrier services
        self.carriers = {
            "usps": USPSShipping(),
            "ups": UPSShipping(),
            "fedex": FedExShipping()
        }
        
        # Initialize risk engine
        self.risk_engine = RiskEngine()
    
    def get_shipping_options(self,
                           origin: Dict[str, str],
                           destination: Dict[str, str],
                           package: Dict[str, float],
                           item_fragility: float = 0.0) -> List[Dict]:
        """Get shipping options from all carriers.
        
        Args:
            origin: Origin address dictionary
            destination: Destination address dictionary
            package: Package details dictionary
            item_fragility: Item fragility score (0-10)
            
        Returns:
            List of shipping options with rates and risk assessments
        """
        try:
            all_options = []
            
            # Get rates from each carrier
            for carrier_name, carrier in self.carriers.items():
                rates = carrier.calculate_rate(origin, destination, package)
                
                for rate in rates:
                    # Calculate distance (simplified)
                    distance = self._calculate_distance(origin, destination)
                    
                    # Predict damage risk
                    damage_prob, importance = self.risk_engine.predict_damage_risk(
                        item_fragility,
                        carrier_name,
                        distance
                    )
                    
                    # Calculate cost risk
                    cost_risk = self.risk_engine.calculate_cost_risk(
                        rate["cost"],
                        distance,
                        package["weight"],
                        self._is_holiday_season()
                    )
                    
                    # Add risk assessments to rate
                    rate.update({
                        "damage_risk": {
                            "probability": damage_prob,
                            "feature_importance": importance
                        },
                        "cost_risk": cost_risk
                    })
                    
                    all_options.append(rate)
            
            # Sort options by total cost
            all_options.sort(key=lambda x: x["cost_risk"]["total_cost"])
            
            return all_options
            
        except Exception as e:
            logger.error(f"Failed to get shipping options: {e}")
            return []
    
    def get_optimal_package(self,
                          item_dimensions: Dict[str, float],
                          item_fragility: float = 0.0) -> Dict:
        """Get optimal package size and padding recommendations.
        
        Args:
            item_dimensions: Item dimensions dictionary
            item_fragility: Item fragility score (0-10)
            
        Returns:
            Dictionary containing package recommendations
        """
        try:
            # Calculate optimal box size with padding
            padding = self._calculate_padding(item_fragility)
            box_size = self.carriers["usps"].optimize_box_size(
                item_dimensions,
                padding
            )
            
            # Calculate dimensional weight
            dim_weight = self.carriers["usps"].calculate_dim_weight(box_size)
            
            return {
                "box_dimensions": box_size,
                "padding": padding,
                "dimensional_weight": dim_weight,
                "recommendations": {
                    "packing_material": self._get_packing_material(item_fragility),
                    "special_handling": item_fragility > 7,
                    "insurance_recommended": item_fragility > 5
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get optimal package: {e}")
            return {}
    
    def train_risk_model(self, training_data: Dict) -> Dict:
        """Train the damage risk prediction model.
        
        Args:
            training_data: Dictionary containing training data
            
        Returns:
            Dictionary containing training results
        """
        try:
            # Convert training data to DataFrame
            df = pd.DataFrame(training_data)
            
            # Train model
            self.risk_engine.train_damage_model(df)
            
            return {
                "status": "success",
                "message": "Risk model trained successfully",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to train risk model: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_distance(self, origin: Dict[str, str], destination: Dict[str, str]) -> float:
        """Calculate shipping distance between origin and destination.
        
        Args:
            origin: Origin address dictionary
            destination: Destination address dictionary
            
        Returns:
            Distance in miles
        """
        # TODO: Implement actual distance calculation using geocoding
        # For now, return a dummy value
        return 100.0
    
    def _is_holiday_season(self) -> bool:
        """Check if current date is during holiday season.
        
        Returns:
            True if during holiday season, False otherwise
        """
        now = datetime.now()
        # Consider November 15 to December 31 as holiday season
        return (now.month == 11 and now.day >= 15) or now.month == 12
    
    def _calculate_padding(self, fragility: float) -> float:
        """Calculate required padding based on fragility score.
        
        Args:
            fragility: Item fragility score (0-10)
            
        Returns:
            Padding in inches
        """
        # Base padding of 1 inch
        base_padding = 1.0
        
        # Add 0.5 inches per fragility point above 5
        extra_padding = max(0, fragility - 5) * 0.5
        
        return base_padding + extra_padding
    
    def _get_packing_material(self, fragility: float) -> List[str]:
        """Get recommended packing materials based on fragility score.
        
        Args:
            fragility: Item fragility score (0-10)
            
        Returns:
            List of recommended packing materials
        """
        materials = ["bubble wrap"]
        
        if fragility > 5:
            materials.append("packing peanuts")
        
        if fragility > 7:
            materials.append("double boxing")
            materials.append("fragile stickers")
        
        return materials 