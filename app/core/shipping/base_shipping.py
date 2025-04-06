from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class BaseShipping(ABC):
    """Base class for shipping services."""
    
    def __init__(self):
        """Initialize the shipping service."""
        self.carrier_name = None
        self.base_url = None
        self.api_key = None
    
    @abstractmethod
    def calculate_rate(self, 
                      origin: Dict[str, str],
                      destination: Dict[str, str],
                      package: Dict[str, float],
                      service: Optional[str] = None) -> Dict:
        """Calculate shipping rate.
        
        Args:
            origin: Origin address dictionary with keys [address, city, state, zip]
            destination: Destination address dictionary with keys [address, city, state, zip]
            package: Package details dictionary with keys [weight, length, width, height]
            service: Optional specific service to calculate rate for
            
        Returns:
            Dictionary containing rate information
        """
        pass
    
    def calculate_dim_weight(self, length: float, width: float, height: float) -> float:
        """Calculate dimensional weight.
        
        Args:
            length: Package length in inches
            width: Package width in inches
            height: Package height in inches
            
        Returns:
            Dimensional weight in pounds
        """
        # Standard dim weight divisor (varies by carrier)
        divisor = 166.0  # USPS standard
        
        # Calculate volume in cubic inches
        volume = length * width * height
        
        # Calculate dim weight
        dim_weight = volume / divisor
        
        # Round up to nearest pound
        return np.ceil(dim_weight)
    
    def optimize_box_size(self, 
                         item_length: float,
                         item_width: float,
                         item_height: float,
                         padding: float = 2.0) -> Tuple[float, float, float]:
        """Optimize box size for item.
        
        Args:
            item_length: Item length in inches
            item_width: Item width in inches
            item_height: Item height in inches
            padding: Padding to add in inches
            
        Returns:
            Tuple of (box_length, box_width, box_height)
        """
        # Add padding to each dimension
        box_length = item_length + (padding * 2)
        box_width = item_width + (padding * 2)
        box_height = item_height + (padding * 2)
        
        # Round up to nearest inch
        return (
            np.ceil(box_length),
            np.ceil(box_width),
            np.ceil(box_height)
        )
    
    def format_output(self, 
                     carrier: str,
                     service: str,
                     cost: float,
                     delivery_days: int,
                     insurance: float,
                     risk_score: float) -> Dict:
        """Format shipping rate output.
        
        Args:
            carrier: Carrier name
            service: Service name
            cost: Shipping cost
            delivery_days: Estimated delivery days
            insurance: Insurance amount
            risk_score: Risk score (0-10)
            
        Returns:
            Formatted output dictionary
        """
        return {
            "name": f"{carrier} {service}",
            "cost": round(cost, 2),
            "delivery_days": delivery_days,
            "insurance": round(insurance, 2),
            "risk_score": round(risk_score, 1)
        } 