from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime, timedelta
import re
from .base_compliance import BaseComplianceService, ComplianceType, ComplianceStatus

logger = logging.getLogger(__name__)

class AuctionLawsComplianceService(BaseComplianceService):
    """Service for handling auction laws compliance."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize auction laws compliance service.
        
        Args:
            config: Configuration dictionary containing:
                - bid_pattern_threshold: Threshold for bid pattern detection
                - suspicious_patterns: List of suspicious bidding patterns
                - tax_nexus_states: List of states with tax nexus
                - tax_rates: Dictionary of state tax rates
                - resale_cert_required: List of categories requiring resale certificates
        """
        super().__init__(config)
        self.bid_pattern_threshold = config.get('bid_pattern_threshold', 0.8)
        self.suspicious_patterns = config.get('suspicious_patterns', [
            'bid_rotation',
            'bid_suppression',
            'market_allocation'
        ])
        self.tax_nexus_states = config.get('tax_nexus_states', [])
        self.tax_rates = config.get('tax_rates', {})
        self.resale_cert_required = config.get('resale_cert_required', [])
    
    def _check_auction_laws(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check auction laws compliance.
        
        Args:
            data: Data to check for compliance, containing:
                - bids: List of bid information
                - seller_info: Seller information
                - buyer_info: Buyer information
                - item_info: Item information
                - location: Transaction location
                
        Returns:
            Dict containing check results
        """
        try:
            results = {
                'status': ComplianceStatus.PASSED.value,
                'checks': {}
            }
            
            # Check for bid rigging
            bid_rigging_result = self._check_bid_rigging(data.get('bids', []))
            results['checks']['bid_rigging'] = bid_rigging_result
            
            # Check resale certificates
            resale_cert_result = self._check_resale_certificates(
                data.get('item_info', {}),
                data.get('buyer_info', {})
            )
            results['checks']['resale_certificates'] = resale_cert_result
            
            # Check sales tax nexus
            tax_nexus_result = self._check_sales_tax_nexus(
                data.get('location', {}),
                data.get('seller_info', {})
            )
            results['checks']['sales_tax_nexus'] = tax_nexus_result
            
            # Update overall status
            if any(check['status'] == ComplianceStatus.FAILED.value 
                  for check in results['checks'].values()):
                results['status'] = ComplianceStatus.FAILED.value
            elif any(check['status'] == ComplianceStatus.WARNING.value 
                    for check in results['checks'].values()):
                results['status'] = ComplianceStatus.WARNING.value
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to check auction laws compliance: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_bid_rigging(self, bids: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for bid rigging patterns.
        
        Args:
            bids: List of bid information
            
        Returns:
            Dict containing check results
        """
        try:
            if not bids:
                return {
                    'status': ComplianceStatus.PASSED.value,
                    'message': 'No bids to analyze'
                }
            
            # Analyze bid patterns
            patterns = self._analyze_bid_patterns(bids)
            
            # Check for suspicious patterns
            suspicious_found = []
            for pattern in self.suspicious_patterns:
                if patterns.get(pattern, 0) > self.bid_pattern_threshold:
                    suspicious_found.append(pattern)
            
            if suspicious_found:
                return {
                    'status': ComplianceStatus.FAILED.value,
                    'message': f'Suspicious bidding patterns detected: {", ".join(suspicious_found)}',
                    'patterns': patterns
                }
            
            return {
                'status': ComplianceStatus.PASSED.value,
                'message': 'No suspicious bidding patterns detected',
                'patterns': patterns
            }
            
        except Exception as e:
            logger.error(f"Failed to check bid rigging: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_resale_certificates(self, item_info: Dict[str, Any], 
                                 buyer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check resale certificate requirements.
        
        Args:
            item_info: Item information
            buyer_info: Buyer information
            
        Returns:
            Dict containing check results
        """
        try:
            category = item_info.get('category')
            if not category:
                return {
                    'status': ComplianceStatus.WARNING.value,
                    'message': 'Item category not specified'
                }
            
            # Check if category requires resale certificate
            if category in self.resale_cert_required:
                cert_info = buyer_info.get('resale_certificate')
                if not cert_info:
                    return {
                        'status': ComplianceStatus.FAILED.value,
                        'message': f'Resale certificate required for category: {category}'
                    }
                
                # Validate certificate
                if not self._validate_resale_certificate(cert_info):
                    return {
                        'status': ComplianceStatus.FAILED.value,
                        'message': 'Invalid resale certificate'
                    }
            
            return {
                'status': ComplianceStatus.PASSED.value,
                'message': 'Resale certificate requirements met'
            }
            
        except Exception as e:
            logger.error(f"Failed to check resale certificates: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_sales_tax_nexus(self, location: Dict[str, Any], 
                             seller_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check sales tax nexus requirements.
        
        Args:
            location: Transaction location
            seller_info: Seller information
            
        Returns:
            Dict containing check results
        """
        try:
            state = location.get('state')
            if not state:
                return {
                    'status': ComplianceStatus.WARNING.value,
                    'message': 'Transaction state not specified'
                }
            
            # Check if state has tax nexus
            if state in self.tax_nexus_states:
                # Get tax rate
                tax_rate = self.tax_rates.get(state, 0)
                
                # Check seller's tax registration
                tax_reg = seller_info.get('tax_registration', {})
                if state not in tax_reg:
                    return {
                        'status': ComplianceStatus.FAILED.value,
                        'message': f'Sales tax registration required for state: {state}'
                    }
                
                return {
                    'status': ComplianceStatus.PASSED.value,
                    'message': f'Sales tax nexus requirements met for {state}',
                    'tax_rate': tax_rate
                }
            
            return {
                'status': ComplianceStatus.PASSED.value,
                'message': f'No sales tax nexus for state: {state}'
            }
            
        except Exception as e:
            logger.error(f"Failed to check sales tax nexus: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _analyze_bid_patterns(self, bids: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze bidding patterns.
        
        Args:
            bids: List of bid information
            
        Returns:
            Dict containing pattern scores
        """
        try:
            patterns = {
                'bid_rotation': 0.0,
                'bid_suppression': 0.0,
                'market_allocation': 0.0
            }
            
            if len(bids) < 2:
                return patterns
            
            # Sort bids by timestamp
            sorted_bids = sorted(bids, key=lambda x: x['timestamp'])
            
            # Analyze bid rotation
            bidders = set(bid['bidder_id'] for bid in bids)
            if len(bidders) > 1:
                rotation_score = self._calculate_rotation_score(sorted_bids)
                patterns['bid_rotation'] = rotation_score
            
            # Analyze bid suppression
            suppression_score = self._calculate_suppression_score(sorted_bids)
            patterns['bid_suppression'] = suppression_score
            
            # Analyze market allocation
            allocation_score = self._calculate_allocation_score(sorted_bids)
            patterns['market_allocation'] = allocation_score
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze bid patterns: {e}")
            return {
                'bid_rotation': 0.0,
                'bid_suppression': 0.0,
                'market_allocation': 0.0
            }
    
    def _calculate_rotation_score(self, bids: List[Dict[str, Any]]) -> float:
        """Calculate bid rotation score.
        
        Args:
            bids: List of sorted bid information
            
        Returns:
            Float score between 0 and 1
        """
        try:
            if len(bids) < 2:
                return 0.0
            
            # Count bidder rotations
            rotations = 0
            prev_bidder = bids[0]['bidder_id']
            
            for bid in bids[1:]:
                if bid['bidder_id'] != prev_bidder:
                    rotations += 1
                    prev_bidder = bid['bidder_id']
            
            # Calculate score
            max_rotations = len(bids) - 1
            return rotations / max_rotations if max_rotations > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate rotation score: {e}")
            return 0.0
    
    def _calculate_suppression_score(self, bids: List[Dict[str, Any]]) -> float:
        """Calculate bid suppression score.
        
        Args:
            bids: List of sorted bid information
            
        Returns:
            Float score between 0 and 1
        """
        try:
            if len(bids) < 2:
                return 0.0
            
            # Calculate bid increments
            increments = []
            prev_bid = bids[0]['amount']
            
            for bid in bids[1:]:
                increment = (bid['amount'] - prev_bid) / prev_bid
                increments.append(increment)
                prev_bid = bid['amount']
            
            # Calculate score based on increment patterns
            if not increments:
                return 0.0
            
            avg_increment = sum(increments) / len(increments)
            return min(1.0, avg_increment * 10)  # Scale and cap at 1.0
            
        except Exception as e:
            logger.error(f"Failed to calculate suppression score: {e}")
            return 0.0
    
    def _calculate_allocation_score(self, bids: List[Dict[str, Any]]) -> float:
        """Calculate market allocation score.
        
        Args:
            bids: List of sorted bid information
            
        Returns:
            Float score between 0 and 1
        """
        try:
            if len(bids) < 2:
                return 0.0
            
            # Group bids by bidder
            bidder_bids = {}
            for bid in bids:
                bidder_id = bid['bidder_id']
                if bidder_id not in bidder_bids:
                    bidder_bids[bidder_id] = []
                bidder_bids[bidder_id].append(bid)
            
            # Calculate bidder concentration
            total_bids = len(bids)
            concentration = max(len(bids) / total_bids for bids in bidder_bids.values())
            
            return concentration
            
        except Exception as e:
            logger.error(f"Failed to calculate allocation score: {e}")
            return 0.0
    
    def _validate_resale_certificate(self, cert_info: Dict[str, Any]) -> bool:
        """Validate resale certificate.
        
        Args:
            cert_info: Certificate information
            
        Returns:
            bool indicating if certificate is valid
        """
        try:
            # Check required fields
            required_fields = ['certificate_number', 'issue_date', 'expiry_date']
            if not all(field in cert_info for field in required_fields):
                return False
            
            # Check expiry date
            expiry_date = datetime.fromisoformat(cert_info['expiry_date'])
            if expiry_date < datetime.now():
                return False
            
            # Validate certificate number format
            cert_number = cert_info['certificate_number']
            if not re.match(r'^[A-Z0-9]{8,12}$', cert_number):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate resale certificate: {e}")
            return False
    
    def _generate_auction_laws_doc(self) -> Dict[str, Any]:
        """Generate auction laws documentation.
        
        Returns:
            Dict containing documentation
        """
        try:
            doc = {
                'title': 'Auction Laws Compliance Documentation',
                'sections': [
                    {
                        'title': 'Bid Rigging Detection',
                        'content': {
                            'description': 'Automated detection of suspicious bidding patterns',
                            'patterns': self.suspicious_patterns,
                            'threshold': self.bid_pattern_threshold
                        }
                    },
                    {
                        'title': 'Resale Certificates',
                        'content': {
                            'description': 'Requirements for resale certificates',
                            'categories': self.resale_cert_required
                        }
                    },
                    {
                        'title': 'Sales Tax Nexus',
                        'content': {
                            'description': 'State tax nexus requirements',
                            'states': self.tax_nexus_states,
                            'rates': self.tax_rates
                        }
                    }
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            return doc
            
        except Exception as e:
            logger.error(f"Failed to generate auction laws documentation: {e}")
            return {
                'title': 'Auction Laws Compliance Documentation',
                'error': str(e)
            } 