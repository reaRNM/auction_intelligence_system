from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime, timedelta
import re
from .base_compliance import BaseComplianceService, ComplianceType, ComplianceStatus

logger = logging.getLogger(__name__)

class DataPrivacyComplianceService(BaseComplianceService):
    """Service for handling data privacy compliance."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize data privacy compliance service.
        
        Args:
            config: Configuration dictionary containing:
                - pii_fields: List of fields containing PII
                - redaction_rules: Rules for PII redaction
                - gdpr_retention_period: Data retention period in days
                - ccpa_optout_methods: List of opt-out methods
                - data_processing_purposes: List of data processing purposes
        """
        super().__init__(config)
        self.pii_fields = config.get('pii_fields', [
            'email', 'phone', 'address', 'ssn', 'dob', 'credit_card'
        ])
        self.redaction_rules = config.get('redaction_rules', {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        })
        self.gdpr_retention_period = config.get('gdpr_retention_period', 30)
        self.ccpa_optout_methods = config.get('ccpa_optout_methods', [
            'email', 'phone', 'web_form', 'toll_free'
        ])
        self.data_processing_purposes = config.get('data_processing_purposes', [
            'auction_participation',
            'payment_processing',
            'shipping',
            'marketing',
            'analytics'
        ])
    
    def _check_data_privacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check data privacy compliance.
        
        Args:
            data: Data to check for compliance, containing:
                - user_data: User information
                - processing_purposes: Data processing purposes
                - consent_status: User consent status
                - optout_status: User opt-out status
                
        Returns:
            Dict containing check results
        """
        try:
            results = {
                'status': ComplianceStatus.PASSED.value,
                'checks': {}
            }
            
            # Check GDPR compliance
            gdpr_result = self._check_gdpr_compliance(
                data.get('user_data', {}),
                data.get('processing_purposes', [])
            )
            results['checks']['gdpr'] = gdpr_result
            
            # Check CCPA compliance
            ccpa_result = self._check_ccpa_compliance(
                data.get('user_data', {}),
                data.get('optout_status', {})
            )
            results['checks']['ccpa'] = ccpa_result
            
            # Check PII redaction
            redaction_result = self._check_pii_redaction(
                data.get('user_data', {})
            )
            results['checks']['pii_redaction'] = redaction_result
            
            # Update overall status
            if any(check['status'] == ComplianceStatus.FAILED.value 
                  for check in results['checks'].values()):
                results['status'] = ComplianceStatus.FAILED.value
            elif any(check['status'] == ComplianceStatus.WARNING.value 
                    for check in results['checks'].values()):
                results['status'] = ComplianceStatus.WARNING.value
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to check data privacy compliance: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_gdpr_compliance(self, user_data: Dict[str, Any], 
                             processing_purposes: List[str]) -> Dict[str, Any]:
        """Check GDPR compliance.
        
        Args:
            user_data: User information
            processing_purposes: Data processing purposes
            
        Returns:
            Dict containing check results
        """
        try:
            results = {
                'status': ComplianceStatus.PASSED.value,
                'checks': {}
            }
            
            # Check data retention
            retention_result = self._check_data_retention(user_data)
            results['checks']['retention'] = retention_result
            
            # Check processing purposes
            purposes_result = self._check_processing_purposes(processing_purposes)
            results['checks']['purposes'] = purposes_result
            
            # Check right to erasure
            erasure_result = self._check_right_to_erasure(user_data)
            results['checks']['erasure'] = erasure_result
            
            # Update status
            if any(check['status'] == ComplianceStatus.FAILED.value 
                  for check in results['checks'].values()):
                results['status'] = ComplianceStatus.FAILED.value
            elif any(check['status'] == ComplianceStatus.WARNING.value 
                    for check in results['checks'].values()):
                results['status'] = ComplianceStatus.WARNING.value
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to check GDPR compliance: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_ccpa_compliance(self, user_data: Dict[str, Any], 
                             optout_status: Dict[str, Any]) -> Dict[str, Any]:
        """Check CCPA compliance.
        
        Args:
            user_data: User information
            optout_status: User opt-out status
            
        Returns:
            Dict containing check results
        """
        try:
            results = {
                'status': ComplianceStatus.PASSED.value,
                'checks': {}
            }
            
            # Check opt-out methods
            optout_result = self._check_optout_methods(optout_status)
            results['checks']['optout_methods'] = optout_result
            
            # Check data categories
            categories_result = self._check_data_categories(user_data)
            results['checks']['data_categories'] = categories_result
            
            # Check disclosure requirements
            disclosure_result = self._check_disclosure_requirements(user_data)
            results['checks']['disclosure'] = disclosure_result
            
            # Update status
            if any(check['status'] == ComplianceStatus.FAILED.value 
                  for check in results['checks'].values()):
                results['status'] = ComplianceStatus.FAILED.value
            elif any(check['status'] == ComplianceStatus.WARNING.value 
                    for check in results['checks'].values()):
                results['status'] = ComplianceStatus.WARNING.value
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to check CCPA compliance: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_pii_redaction(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check PII redaction.
        
        Args:
            user_data: User information
            
        Returns:
            Dict containing check results
        """
        try:
            results = {
                'status': ComplianceStatus.PASSED.value,
                'fields_checked': [],
                'fields_redacted': []
            }
            
            # Check each PII field
            for field in self.pii_fields:
                if field in user_data:
                    results['fields_checked'].append(field)
                    
                    # Check if field needs redaction
                    if self._needs_redaction(user_data[field], field):
                        results['fields_redacted'].append(field)
                        results['status'] = ComplianceStatus.WARNING.value
            
            if results['fields_redacted']:
                results['message'] = f"PII fields need redaction: {', '.join(results['fields_redacted'])}"
            else:
                results['message'] = "All PII fields properly redacted"
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to check PII redaction: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_data_retention(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check data retention compliance.
        
        Args:
            user_data: User information
            
        Returns:
            Dict containing check results
        """
        try:
            last_activity = user_data.get('last_activity')
            if not last_activity:
                return {
                    'status': ComplianceStatus.WARNING.value,
                    'message': 'Last activity date not found'
                }
            
            # Calculate retention period
            last_activity_date = datetime.fromisoformat(last_activity)
            retention_limit = datetime.now() - timedelta(days=self.gdpr_retention_period)
            
            if last_activity_date < retention_limit:
                return {
                    'status': ComplianceStatus.FAILED.value,
                    'message': f'Data exceeds retention period of {self.gdpr_retention_period} days'
                }
            
            return {
                'status': ComplianceStatus.PASSED.value,
                'message': 'Data retention compliant'
            }
            
        except Exception as e:
            logger.error(f"Failed to check data retention: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_processing_purposes(self, purposes: List[str]) -> Dict[str, Any]:
        """Check data processing purposes.
        
        Args:
            purposes: List of processing purposes
            
        Returns:
            Dict containing check results
        """
        try:
            if not purposes:
                return {
                    'status': ComplianceStatus.FAILED.value,
                    'message': 'No processing purposes specified'
                }
            
            # Check if all purposes are valid
            invalid_purposes = [p for p in purposes if p not in self.data_processing_purposes]
            if invalid_purposes:
                return {
                    'status': ComplianceStatus.FAILED.value,
                    'message': f'Invalid processing purposes: {", ".join(invalid_purposes)}'
                }
            
            return {
                'status': ComplianceStatus.PASSED.value,
                'message': 'Processing purposes compliant'
            }
            
        except Exception as e:
            logger.error(f"Failed to check processing purposes: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_right_to_erasure(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check right to erasure compliance.
        
        Args:
            user_data: User information
            
        Returns:
            Dict containing check results
        """
        try:
            # Check if erasure request exists
            erasure_request = user_data.get('erasure_request')
            if erasure_request:
                request_date = datetime.fromisoformat(erasure_request['date'])
                if datetime.now() - request_date > timedelta(days=30):
                    return {
                        'status': ComplianceStatus.FAILED.value,
                        'message': 'Erasure request not processed within 30 days'
                    }
            
            return {
                'status': ComplianceStatus.PASSED.value,
                'message': 'Right to erasure compliant'
            }
            
        except Exception as e:
            logger.error(f"Failed to check right to erasure: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_optout_methods(self, optout_status: Dict[str, Any]) -> Dict[str, Any]:
        """Check CCPA opt-out methods.
        
        Args:
            optout_status: User opt-out status
            
        Returns:
            Dict containing check results
        """
        try:
            if not optout_status:
                return {
                    'status': ComplianceStatus.FAILED.value,
                    'message': 'No opt-out status found'
                }
            
            # Check if all required methods are available
            missing_methods = [m for m in self.ccpa_optout_methods 
                             if m not in optout_status]
            if missing_methods:
                return {
                    'status': ComplianceStatus.FAILED.value,
                    'message': f'Missing opt-out methods: {", ".join(missing_methods)}'
                }
            
            return {
                'status': ComplianceStatus.PASSED.value,
                'message': 'Opt-out methods compliant'
            }
            
        except Exception as e:
            logger.error(f"Failed to check opt-out methods: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_data_categories(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check CCPA data categories.
        
        Args:
            user_data: User information
            
        Returns:
            Dict containing check results
        """
        try:
            # Check if data categories are properly labeled
            categories = user_data.get('data_categories', {})
            if not categories:
                return {
                    'status': ComplianceStatus.FAILED.value,
                    'message': 'No data categories specified'
                }
            
            # Check for required categories
            required_categories = ['personal', 'commercial', 'biometric']
            missing_categories = [c for c in required_categories 
                                if c not in categories]
            if missing_categories:
                return {
                    'status': ComplianceStatus.FAILED.value,
                    'message': f'Missing data categories: {", ".join(missing_categories)}'
                }
            
            return {
                'status': ComplianceStatus.PASSED.value,
                'message': 'Data categories compliant'
            }
            
        except Exception as e:
            logger.error(f"Failed to check data categories: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _check_disclosure_requirements(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check CCPA disclosure requirements.
        
        Args:
            user_data: User information
            
        Returns:
            Dict containing check results
        """
        try:
            # Check if privacy notice is provided
            privacy_notice = user_data.get('privacy_notice')
            if not privacy_notice:
                return {
                    'status': ComplianceStatus.FAILED.value,
                    'message': 'Privacy notice not provided'
                }
            
            # Check if notice is up to date
            notice_date = datetime.fromisoformat(privacy_notice['date'])
            if datetime.now() - notice_date > timedelta(days=365):
                return {
                    'status': ComplianceStatus.WARNING.value,
                    'message': 'Privacy notice may need updating'
                }
            
            return {
                'status': ComplianceStatus.PASSED.value,
                'message': 'Disclosure requirements compliant'
            }
            
        except Exception as e:
            logger.error(f"Failed to check disclosure requirements: {e}")
            return {
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def _needs_redaction(self, value: str, field_type: str) -> bool:
        """Check if a field needs redaction.
        
        Args:
            value: Field value
            field_type: Type of field
            
        Returns:
            bool indicating if redaction is needed
        """
        try:
            if not value or not field_type:
                return False
            
            # Check if field type has a redaction rule
            if field_type not in self.redaction_rules:
                return False
            
            # Check if value matches pattern
            pattern = self.redaction_rules[field_type]
            return bool(re.search(pattern, value))
            
        except Exception as e:
            logger.error(f"Failed to check redaction need: {e}")
            return False
    
    def _generate_data_privacy_doc(self) -> Dict[str, Any]:
        """Generate data privacy documentation.
        
        Returns:
            Dict containing documentation
        """
        try:
            doc = {
                'title': 'Data Privacy Compliance Documentation',
                'sections': [
                    {
                        'title': 'GDPR Compliance',
                        'content': {
                            'description': 'General Data Protection Regulation compliance',
                            'retention_period': self.gdpr_retention_period,
                            'processing_purposes': self.data_processing_purposes
                        }
                    },
                    {
                        'title': 'CCPA Compliance',
                        'content': {
                            'description': 'California Consumer Privacy Act compliance',
                            'optout_methods': self.ccpa_optout_methods
                        }
                    },
                    {
                        'title': 'PII Protection',
                        'content': {
                            'description': 'Personal Identifiable Information protection',
                            'pii_fields': self.pii_fields,
                            'redaction_rules': self.redaction_rules
                        }
                    }
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            return doc
            
        except Exception as e:
            logger.error(f"Failed to generate data privacy documentation: {e}")
            return {
                'title': 'Data Privacy Compliance Documentation',
                'error': str(e)
            } 