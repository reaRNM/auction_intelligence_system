from typing import Dict, List, Optional
import logging
import os
import requests
from datetime import datetime
import json
from dotenv import load_dotenv

from .base_shipping import BaseShipping

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FedExShipping(BaseShipping):
    """FedEx shipping service implementation."""
    
    def __init__(self):
        """Initialize the FedEx shipping service."""
        super().__init__()
        self.carrier_name = "FedEx"
        self.base_url = "https://apis-sandbox.fedex.com/rate/v1/rates/quotes"
        self.api_key = os.getenv("FEDEX_API_KEY")
        
        # FedEx service codes
        self.services = {
            "ground": "FEDEX_GROUND",
            "home_delivery": "FEDEX_HOME_DELIVERY",
            "express": "FEDEX_2_DAY",
            "overnight": "FEDEX_OVERNIGHT",
            "priority": "FEDEX_PRIORITY",
            "first_overnight": "FEDEX_FIRST_OVERNIGHT"
        }
    
    def calculate_rate(self, 
                      origin: Dict[str, str],
                      destination: Dict[str, str],
                      package: Dict[str, float],
                      service: Optional[str] = None) -> Dict:
        """Calculate FedEx shipping rate.
        
        Args:
            origin: Origin address dictionary with keys [address, city, state, zip]
            destination: Destination address dictionary with keys [address, city, state, zip]
            package: Package details dictionary with keys [weight, length, width, height]
            service: Optional specific service to calculate rate for
            
        Returns:
            Dictionary containing rate information
        """
        try:
            # Calculate dimensional weight
            dim_weight = self.calculate_dim_weight(
                package["length"],
                package["width"],
                package["height"]
            )
            
            # Use the greater of actual weight and dimensional weight
            weight = max(package["weight"], dim_weight)
            
            # Build request payload
            payload = self._build_rate_request(
                origin,
                destination,
                weight,
                package,
                service
            )
            
            # Make API request
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            
            # Parse response
            rates = self._parse_rate_response(response.json())
            
            # Format output
            return {
                "carrier_options": [
                    self.format_output(
                        carrier=self.carrier_name,
                        service=rate["service"],
                        cost=rate["cost"],
                        delivery_days=rate["days"],
                        insurance=rate["insurance"],
                        risk_score=rate["risk"]
                    )
                    for rate in rates
                ]
            }
            
        except Exception as e:
            logger.error(f"FedEx rate calculation failed: {e}")
            return {"carrier_options": []}
    
    def _build_rate_request(self, 
                          origin: Dict[str, str],
                          destination: Dict[str, str],
                          weight: float,
                          package: Dict[str, float],
                          service: Optional[str] = None) -> Dict:
        """Build FedEx rate request payload.
        
        Args:
            origin: Origin address dictionary
            destination: Destination address dictionary
            weight: Package weight in pounds
            package: Package details dictionary
            service: Optional specific service
            
        Returns:
            Request payload dictionary
        """
        payload = {
            "accountNumber": {
                "value": os.getenv("FEDEX_ACCOUNT_NUMBER")
            },
            "requestedShipment": {
                "shipper": {
                    "address": {
                        "streetLines": [origin["address"]],
                        "city": origin["city"],
                        "stateOrProvinceCode": origin["state"],
                        "postalCode": origin["zip"],
                        "countryCode": "US"
                    }
                },
                "recipient": {
                    "address": {
                        "streetLines": [destination["address"]],
                        "city": destination["city"],
                        "stateOrProvinceCode": destination["state"],
                        "postalCode": destination["zip"],
                        "countryCode": "US"
                    }
                },
                "requestedPackageLineItems": [{
                    "weight": {
                        "value": str(weight),
                        "units": "LB"
                    },
                    "dimensions": {
                        "length": str(package["length"]),
                        "width": str(package["width"]),
                        "height": str(package["height"]),
                        "units": "IN"
                    }
                }]
            }
        }
        
        # Add service type if specified
        if service and service in self.services:
            payload["requestedShipment"]["serviceType"] = self.services[service]
        
        return payload
    
    def _parse_rate_response(self, response: Dict) -> List[Dict]:
        """Parse FedEx rate response.
        
        Args:
            response: Response dictionary
            
        Returns:
            List of rate dictionaries
        """
        rates = []
        
        try:
            for rate in response["output"]["rateReplyDetails"]:
                service = rate["serviceName"]
                cost = float(rate["ratedShipmentDetails"][0]["totalNetCharge"])
                days = int(rate.get("transitTime", "0"))
                insurance = float(rate.get("insurance", {}).get("amount", "0"))
                
                rate_info = {
                    "service": service,
                    "cost": cost,
                    "days": days,
                    "insurance": insurance,
                    "risk": self._calculate_risk_score(rate)
                }
                rates.append(rate_info)
            
        except Exception as e:
            logger.error(f"Failed to parse FedEx response: {e}")
        
        return rates
    
    def _calculate_risk_score(self, rate: Dict) -> float:
        """Calculate risk score for package.
        
        Args:
            rate: Rate information dictionary
            
        Returns:
            Risk score from 0 to 10
        """
        # Base risk score
        risk = 5.0
        
        # Adjust based on service
        service = rate["serviceName"].lower()
        if "overnight" in service:
            risk += 1.0
        elif "ground" in service:
            risk -= 1.0
        
        # Adjust based on transit time
        if rate.get("transitTime", 0) > 3:
            risk += 1.0
        
        # Adjust based on insurance
        insurance = float(rate.get("insurance", {}).get("amount", "0"))
        if insurance > 100:
            risk += 1.0
        
        # Cap risk score at 10
        return min(risk, 10.0) 