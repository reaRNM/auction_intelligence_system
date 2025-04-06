from typing import Dict, List, Optional
import logging
import os
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

from .base_shipping import BaseShipping

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class USPSShipping(BaseShipping):
    """USPS shipping service implementation."""
    
    def __init__(self):
        """Initialize the USPS shipping service."""
        super().__init__()
        self.carrier_name = "USPS"
        self.base_url = "https://secure.shippingapis.com/ShippingAPI.dll"
        self.api_key = os.getenv("USPS_API_KEY")
        
        # USPS service codes
        self.services = {
            "priority": "PRIORITY",
            "priority_cubic": "PRIORITY_CUBIC",
            "first_class": "FIRST_CLASS",
            "parcel_select": "PARCEL_SELECT"
        }
    
    def calculate_rate(self, 
                      origin: Dict[str, str],
                      destination: Dict[str, str],
                      package: Dict[str, float],
                      service: Optional[str] = None) -> Dict:
        """Calculate USPS shipping rate.
        
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
            
            # Build XML request
            xml_request = self._build_rate_request(
                origin,
                destination,
                weight,
                service
            )
            
            # Make API request
            response = requests.get(
                self.base_url,
                params={
                    "API": "RateV4",
                    "XML": xml_request
                }
            )
            response.raise_for_status()
            
            # Parse response
            rates = self._parse_rate_response(response.text)
            
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
            logger.error(f"USPS rate calculation failed: {e}")
            return {"carrier_options": []}
    
    def _build_rate_request(self, 
                          origin: Dict[str, str],
                          destination: Dict[str, str],
                          weight: float,
                          service: Optional[str] = None) -> str:
        """Build USPS rate request XML.
        
        Args:
            origin: Origin address dictionary
            destination: Destination address dictionary
            weight: Package weight in pounds
            service: Optional specific service
            
        Returns:
            XML request string
        """
        # Create root element
        root = ET.Element("RateV4Request")
        root.set("USERID", self.api_key)
        
        # Add package element
        package = ET.SubElement(root, "Package")
        package.set("ID", "1")
        
        # Add service element if specified
        if service and service in self.services:
            ET.SubElement(package, "Service").text = self.services[service]
        
        # Add dimensions
        dimensions = ET.SubElement(package, "Dimensions")
        ET.SubElement(dimensions, "Length").text = str(package["length"])
        ET.SubElement(dimensions, "Width").text = str(package["width"])
        ET.SubElement(dimensions, "Height").text = str(package["height"])
        
        # Add weight
        weight_elem = ET.SubElement(package, "Weight")
        weight_elem.text = str(weight)
        
        # Add origin address
        origin_elem = ET.SubElement(package, "Origin")
        ET.SubElement(origin_elem, "Address1").text = origin["address"]
        ET.SubElement(origin_elem, "City").text = origin["city"]
        ET.SubElement(origin_elem, "State").text = origin["state"]
        ET.SubElement(origin_elem, "Zip5").text = origin["zip"]
        
        # Add destination address
        dest_elem = ET.SubElement(package, "Destination")
        ET.SubElement(dest_elem, "Address1").text = destination["address"]
        ET.SubElement(dest_elem, "City").text = destination["city"]
        ET.SubElement(dest_elem, "State").text = destination["state"]
        ET.SubElement(dest_elem, "Zip5").text = destination["zip"]
        
        return ET.tostring(root, encoding="unicode")
    
    def _parse_rate_response(self, xml_response: str) -> List[Dict]:
        """Parse USPS rate response XML.
        
        Args:
            xml_response: XML response string
            
        Returns:
            List of rate dictionaries
        """
        rates = []
        
        try:
            root = ET.fromstring(xml_response)
            
            for package in root.findall(".//Package"):
                for postage in package.findall(".//Postage"):
                    rate = {
                        "service": postage.find("MailService").text,
                        "cost": float(postage.find("Rate").text),
                        "days": int(postage.find("CommitmentDays").text or "0"),
                        "insurance": float(postage.find("Insurance").text or "0"),
                        "risk": self._calculate_risk_score(package)
                    }
                    rates.append(rate)
            
        except Exception as e:
            logger.error(f"Failed to parse USPS response: {e}")
        
        return rates
    
    def _calculate_risk_score(self, package: ET.Element) -> float:
        """Calculate risk score for package.
        
        Args:
            package: Package XML element
            
        Returns:
            Risk score from 0 to 10
        """
        # Base risk score
        risk = 5.0
        
        # Adjust based on dimensions
        dimensions = package.find(".//Dimensions")
        if dimensions is not None:
            length = float(dimensions.find("Length").text)
            width = float(dimensions.find("Width").text)
            height = float(dimensions.find("Height").text)
            
            # Increase risk for larger packages
            if length * width * height > 1728:  # > 1 cubic foot
                risk += 2.0
            
            # Increase risk for elongated packages
            if max(length, width, height) / min(length, width, height) > 3:
                risk += 1.0
        
        # Adjust based on weight
        weight = float(package.find(".//Weight").text)
        if weight > 10:  # > 10 pounds
            risk += 1.0
        
        # Cap risk score at 10
        return min(risk, 10.0) 