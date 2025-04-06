from typing import Dict, List, Optional, Any, Union
import logging
import json
import os
from datetime import datetime, timedelta
import hashlib
from enum import Enum
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class ComplianceType(Enum):
    """Types of compliance checks."""
    AUCTION_LAWS = "auction_laws"
    DATA_PRIVACY = "data_privacy"
    PLATFORM_RULES = "platform_rules"

class ComplianceStatus(Enum):
    """Status of compliance checks."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"

class BaseComplianceService:
    """Base class for compliance services."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the compliance service.
        
        Args:
            config: Configuration dictionary containing:
                - audit_log_dir: Directory for audit logs
                - doc_dir: Directory for documentation
                - s3_bucket: S3 bucket for storing logs and docs
                - retention_days: Number of days to retain data
                - override_hours: Number of hours for data retention override
        """
        self.config = config
        self.audit_log_dir = config.get('audit_log_dir', '/var/log/auction_intelligence/compliance')
        self.doc_dir = config.get('doc_dir', '/var/docs/auction_intelligence/compliance')
        self.retention_days = config.get('retention_days', 30)
        self.override_hours = config.get('override_hours', 48)
        
        # Create directories if they don't exist
        os.makedirs(self.audit_log_dir, exist_ok=True)
        os.makedirs(self.doc_dir, exist_ok=True)
        
        # Initialize S3 client
        self.s3 = boto3.client('s3')
    
    def check_compliance(self, compliance_type: ComplianceType, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform compliance check.
        
        Args:
            compliance_type: Type of compliance check
            data: Data to check for compliance
            
        Returns:
            Dict containing compliance check results
        """
        try:
            # Generate check ID
            check_id = f"{compliance_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Perform check based on type
            if compliance_type == ComplianceType.AUCTION_LAWS:
                result = self._check_auction_laws(data)
            elif compliance_type == ComplianceType.DATA_PRIVACY:
                result = self._check_data_privacy(data)
            elif compliance_type == ComplianceType.PLATFORM_RULES:
                result = self._check_platform_rules(data)
            else:
                raise ValueError(f"Unsupported compliance type: {compliance_type}")
            
            # Add metadata
            result['check_id'] = check_id
            result['compliance_type'] = compliance_type.value
            result['timestamp'] = datetime.now().isoformat()
            
            # Log audit
            self._log_audit(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to perform compliance check: {e}")
            return {
                'check_id': check_id,
                'compliance_type': compliance_type.value,
                'timestamp': datetime.now().isoformat(),
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def generate_documentation(self, compliance_type: ComplianceType) -> Dict[str, Any]:
        """Generate compliance documentation.
        
        Args:
            compliance_type: Type of compliance documentation
            
        Returns:
            Dict containing documentation information
        """
        try:
            # Generate doc ID
            doc_id = f"doc_{compliance_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate documentation based on type
            if compliance_type == ComplianceType.AUCTION_LAWS:
                result = self._generate_auction_laws_doc()
            elif compliance_type == ComplianceType.DATA_PRIVACY:
                result = self._generate_data_privacy_doc()
            elif compliance_type == ComplianceType.PLATFORM_RULES:
                result = self._generate_platform_rules_doc()
            else:
                raise ValueError(f"Unsupported compliance type: {compliance_type}")
            
            # Add metadata
            result['doc_id'] = doc_id
            result['compliance_type'] = compliance_type.value
            result['timestamp'] = datetime.now().isoformat()
            
            # Save documentation
            self._save_documentation(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate documentation: {e}")
            return {
                'doc_id': doc_id,
                'compliance_type': compliance_type.value,
                'timestamp': datetime.now().isoformat(),
                'status': ComplianceStatus.ERROR.value,
                'error': str(e)
            }
    
    def request_data_retention_override(self, user_id: str, reason: str) -> Dict[str, Any]:
        """Request data retention override.
        
        Args:
            user_id: ID of the user requesting override
            reason: Reason for override request
            
        Returns:
            Dict containing override information
        """
        try:
            # Generate override ID
            override_id = f"override_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create override record
            override = {
                'override_id': override_id,
                'user_id': user_id,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'expiry': (datetime.now() + timedelta(hours=self.override_hours)).isoformat(),
                'status': 'active'
            }
            
            # Save override
            self._save_override(override)
            
            return override
            
        except Exception as e:
            logger.error(f"Failed to request data retention override: {e}")
            return {
                'override_id': override_id,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    def _check_auction_laws(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check auction laws compliance.
        
        Args:
            data: Data to check for compliance
            
        Returns:
            Dict containing check results
        """
        raise NotImplementedError("Subclasses must implement _check_auction_laws")
    
    def _check_data_privacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check data privacy compliance.
        
        Args:
            data: Data to check for compliance
            
        Returns:
            Dict containing check results
        """
        raise NotImplementedError("Subclasses must implement _check_data_privacy")
    
    def _check_platform_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check platform rules compliance.
        
        Args:
            data: Data to check for compliance
            
        Returns:
            Dict containing check results
        """
        raise NotImplementedError("Subclasses must implement _check_platform_rules")
    
    def _generate_auction_laws_doc(self) -> Dict[str, Any]:
        """Generate auction laws documentation.
        
        Returns:
            Dict containing documentation
        """
        raise NotImplementedError("Subclasses must implement _generate_auction_laws_doc")
    
    def _generate_data_privacy_doc(self) -> Dict[str, Any]:
        """Generate data privacy documentation.
        
        Returns:
            Dict containing documentation
        """
        raise NotImplementedError("Subclasses must implement _generate_data_privacy_doc")
    
    def _generate_platform_rules_doc(self) -> Dict[str, Any]:
        """Generate platform rules documentation.
        
        Returns:
            Dict containing documentation
        """
        raise NotImplementedError("Subclasses must implement _generate_platform_rules_doc")
    
    def _log_audit(self, audit_data: Dict[str, Any]) -> None:
        """Log audit information.
        
        Args:
            audit_data: Audit data to log
        """
        try:
            # Create audit log file
            audit_file = os.path.join(
                self.audit_log_dir,
                f"audit_{audit_data['check_id']}.json"
            )
            
            # Save audit data
            with open(audit_file, 'w') as f:
                json.dump(audit_data, f, indent=2)
            
            # Upload to S3
            s3_key = f"audit/{audit_data['check_id']}.json"
            self.s3.upload_file(audit_file, self.config['s3_bucket'], s3_key)
            
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")
    
    def _save_documentation(self, doc_data: Dict[str, Any]) -> None:
        """Save compliance documentation.
        
        Args:
            doc_data: Documentation data to save
        """
        try:
            # Create documentation file
            doc_file = os.path.join(
                self.doc_dir,
                f"doc_{doc_data['doc_id']}.json"
            )
            
            # Save documentation
            with open(doc_file, 'w') as f:
                json.dump(doc_data, f, indent=2)
            
            # Upload to S3
            s3_key = f"docs/{doc_data['doc_id']}.json"
            self.s3.upload_file(doc_file, self.config['s3_bucket'], s3_key)
            
        except Exception as e:
            logger.error(f"Failed to save documentation: {e}")
    
    def _save_override(self, override_data: Dict[str, Any]) -> None:
        """Save data retention override.
        
        Args:
            override_data: Override data to save
        """
        try:
            # Create override file
            override_file = os.path.join(
                self.audit_log_dir,
                f"override_{override_data['override_id']}.json"
            )
            
            # Save override data
            with open(override_file, 'w') as f:
                json.dump(override_data, f, indent=2)
            
            # Upload to S3
            s3_key = f"overrides/{override_data['override_id']}.json"
            self.s3.upload_file(override_file, self.config['s3_bucket'], s3_key)
            
        except Exception as e:
            logger.error(f"Failed to save override: {e}")
    
    def _cleanup_old_data(self) -> None:
        """Clean up old data based on retention policy."""
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Clean up audit logs
            for file in os.listdir(self.audit_log_dir):
                file_path = os.path.join(self.audit_log_dir, file)
                if os.path.getctime(file_path) < cutoff_date.timestamp():
                    os.remove(file_path)
            
            # Clean up documentation
            for file in os.listdir(self.doc_dir):
                file_path = os.path.join(self.doc_dir, file)
                if os.path.getctime(file_path) < cutoff_date.timestamp():
                    os.remove(file_path)
            
        except Exception as e:
            logger.error(f"Failed to clean up old data: {e}")
    
    def _calculate_hash(self, data: Union[str, bytes]) -> str:
        """Calculate hash of data.
        
        Args:
            data: Data to hash
            
        Returns:
            Hash string
        """
        if isinstance(data, str):
            data = data.encode()
        
        return hashlib.sha256(data).hexdigest() 