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

class UPSShipping(BaseShipping):
    """UPS shipping service implementation."""
    
    def __init__(self):
        """Initialize the UPS shipping service."""
        super().__init__()
        self.carrier_name = "UPS"
        self.base_url = "https://onlinetools.ups.com/api/rate/v1"
        self.api_key = os.getenv("UPS_API_KEY")
        
        # UPS service codes
        self.services = {
            "ground": "01",
            "next_day_air": "01",
            "next_day_air_saver": "59",
            "next_day_air_early": "14",
            "2nd_day_air": "02",
            "2nd_day_air_am": "59",
            "3_day_select": "12"
        }
    
    def calculate_rate(self, 
                      origin: Dict[str, str],
                      destination: Dict[str, str],
                      package: Dict[str, float],
                      service: Optional[str] = None) -> Dict:
        """Calculate UPS shipping rate.
        
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
            logger.error(f"UPS rate calculation failed: {e}")
            return {"carrier_options": []}
    
    def _build_rate_request(self, 
                          origin: Dict[str, str],
                          destination: Dict[str, str],
                          weight: float,
                          package: Dict[str, float],
                          service: Optional[str] = None) -> Dict:
        """Build UPS rate request payload.
        
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
            "UPSSecurity": {
                "UsernameToken": {
                    "Username": self.api_key
                }
            },
            "RateRequest": {
                "Request": {
                    "RequestOption": "Shop"
                },
                "Shipment": {
                    "Shipper": {
                        "Address": {
                            "AddressLine": [origin["address"]],
                            "City": origin["city"],
                            "StateProvinceCode": origin["state"],
                            "PostalCode": origin["zip"],
                            "CountryCode": "US"
                        }
                    },
                    "ShipTo": {
                        "Address": {
                            "AddressLine": [destination["address"]],
                            "City": destination["city"],
                            "StateProvinceCode": destination["state"],
                            "PostalCode": destination["zip"],
                            "CountryCode": "US"
                        }
                    },
                    "Package": {
                        "PackagingType": {
                            "Code": "02",  # Customer Packaging
                            "Description": "Package"
                        },
                        "Dimensions": {
                            "UnitOfMeasurement": {
                                "Code": "IN"
                            },
                            "Length": str(package["length"]),
                            "Width": str(package["width"]),
                            "Height": str(package["height"])
                        },
                        "PackageWeight": {
                            "UnitOfMeasurement": {
                                "Code": "LBS"
                            },
                            "Weight": str(weight)
                        }
                    }
                }
            }
        }
        
        # Add service code if specified
        if service and service in self.services:
            payload["RateRequest"]["Shipment"]["Service"] = {
                "Code": self.services[service],
                "Description": service.replace("_", " ").title()
            }
        
        return payload
    
    def _parse_rate_response(self, response: Dict) -> List[Dict]:
        """Parse UPS rate response.
        
        Args:
            response: Response dictionary
            
        Returns:
            List of rate dictionaries
        """
        rates = []
        
        try:
            for rate in response["RateResponse"]["RatedShipment"]:
                service = rate["Service"]["Description"]
                cost = float(rate["TotalCharges"]["MonetaryValue"])
                days = int(rate["GuaranteedDelivery"]["BusinessDaysInTransit"])
                insurance = float(rate.get("Insurance", {}).get("MonetaryValue", "0"))
                
                rate_info = {
                    "service": service,
                    "cost": cost,
                    "days": days,
                    "insurance": insurance,
                    "risk": self._calculate_risk_score(rate)
                }
                rates.append(rate_info)
            
        except Exception as e:
            logger.error(f"Failed to parse UPS response: {e}")
        
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
        service = rate["Service"]["Description"].lower()
        if "next day" in service:
            risk += 1.0
        elif "ground" in service:
            risk -= 1.0
        
        # Adjust based on guaranteed delivery
        if rate.get("GuaranteedDelivery", {}).get("BusinessDaysInTransit", 0) > 3:
            risk += 1.0
        
        # Adjust based on insurance
        insurance = float(rate.get("Insurance", {}).get("MonetaryValue", "0"))
        if insurance > 100:
            risk += 1.0
        
        # Cap risk score at 10
        return min(risk, 10.0) 