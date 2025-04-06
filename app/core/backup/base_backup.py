from typing import Dict, List, Optional, Union, Any
import logging
import os
import subprocess
import hashlib
import json
import datetime
import boto3
from botocore.exceptions import ClientError
import pg8000
import gnupg
import git

logger = logging.getLogger(__name__)

class BackupType:
    """Types of backups."""
    DATABASE = "database"
    RESEARCH_DATA = "research_data"
    CONFIGURATION = "configuration"

class BackupStatus:
    """Status of backup operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"

class BaseBackupService:
    """Base class for backup services."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the backup service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.backup_dir = config.get('backup_dir', '/var/backups/auction_intelligence')
        self.retention_days = config.get('retention_days', 7)
        self.encryption_key = config.get('encryption_key')
        self.checksum_algorithm = 'sha256'
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize GnuPG for encryption if key is provided
        self.gpg = None
        if self.encryption_key:
            try:
                self.gpg = gnupg.GPG()
                self.gpg.import_keys(self.encryption_key)
                logger.info("GPG encryption initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GPG encryption: {e}")
    
    def create_backup(self, backup_type: str, **kwargs) -> Dict[str, Any]:
        """Create a backup.
        
        Args:
            backup_type: Type of backup to create
            **kwargs: Additional arguments for specific backup types
            
        Returns:
            Dictionary with backup information
        """
        try:
            # Generate backup ID
            backup_id = f"{backup_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup directory
            backup_path = os.path.join(self.backup_dir, backup_id)
            os.makedirs(backup_path, exist_ok=True)
            
            # Create backup based on type
            if backup_type == BackupType.DATABASE:
                result = self._create_database_backup(backup_path, **kwargs)
            elif backup_type == BackupType.RESEARCH_DATA:
                result = self._create_research_data_backup(backup_path, **kwargs)
            elif backup_type == BackupType.CONFIGURATION:
                result = self._create_configuration_backup(backup_path, **kwargs)
            else:
                raise ValueError(f"Unsupported backup type: {backup_type}")
            
            # Add metadata
            result['backup_id'] = backup_id
            result['backup_type'] = backup_type
            result['created_at'] = datetime.datetime.now().isoformat()
            result['status'] = BackupStatus.COMPLETED
            
            # Save metadata
            self._save_backup_metadata(result)
            
            # Clean up old backups
            self._cleanup_old_backups(backup_type)
            
            logger.info(f"Backup {backup_id} created successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return {
                'backup_id': backup_id,
                'backup_type': backup_type,
                'created_at': datetime.datetime.now().isoformat(),
                'status': BackupStatus.FAILED,
                'error': str(e)
            }
    
    def restore_backup(self, backup_id: str, **kwargs) -> Dict[str, Any]:
        """Restore a backup.
        
        Args:
            backup_id: ID of the backup to restore
            **kwargs: Additional arguments for specific restore operations
            
        Returns:
            Dictionary with restore information
        """
        try:
            # Load backup metadata
            metadata = self._load_backup_metadata(backup_id)
            if not metadata:
                raise ValueError(f"Backup {backup_id} not found")
            
            # Restore based on type
            if metadata['backup_type'] == BackupType.DATABASE:
                result = self._restore_database_backup(backup_id, **kwargs)
            elif metadata['backup_type'] == BackupType.RESEARCH_DATA:
                result = self._restore_research_data_backup(backup_id, **kwargs)
            elif metadata['backup_type'] == BackupType.CONFIGURATION:
                result = self._restore_configuration_backup(backup_id, **kwargs)
            else:
                raise ValueError(f"Unsupported backup type: {metadata['backup_type']}")
            
            # Add metadata
            result['backup_id'] = backup_id
            result['restored_at'] = datetime.datetime.now().isoformat()
            result['status'] = BackupStatus.COMPLETED
            
            logger.info(f"Backup {backup_id} restored successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return {
                'backup_id': backup_id,
                'restored_at': datetime.datetime.now().isoformat(),
                'status': BackupStatus.FAILED,
                'error': str(e)
            }
    
    def validate_backup(self, backup_id: str) -> Dict[str, Any]:
        """Validate a backup.
        
        Args:
            backup_id: ID of the backup to validate
            
        Returns:
            Dictionary with validation information
        """
        try:
            # Load backup metadata
            metadata = self._load_backup_metadata(backup_id)
            if not metadata:
                raise ValueError(f"Backup {backup_id} not found")
            
            # Validate based on type
            if metadata['backup_type'] == BackupType.DATABASE:
                result = self._validate_database_backup(backup_id)
            elif metadata['backup_type'] == BackupType.RESEARCH_DATA:
                result = self._validate_research_data_backup(backup_id)
            elif metadata['backup_type'] == BackupType.CONFIGURATION:
                result = self._validate_configuration_backup(backup_id)
            else:
                raise ValueError(f"Unsupported backup type: {metadata['backup_type']}")
            
            # Update metadata
            metadata['status'] = BackupStatus.VALIDATED
            metadata['validation_result'] = result
            self._save_backup_metadata(metadata)
            
            logger.info(f"Backup {backup_id} validated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to validate backup: {e}")
            return {
                'backup_id': backup_id,
                'validated_at': datetime.datetime.now().isoformat(),
                'status': BackupStatus.FAILED,
                'error': str(e)
            }
    
    def list_backups(self, backup_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available backups.
        
        Args:
            backup_type: Optional filter by backup type
            
        Returns:
            List of backup metadata
        """
        try:
            backups = []
            
            # List backup directories
            for item in os.listdir(self.backup_dir):
                if os.path.isdir(os.path.join(self.backup_dir, item)):
                    # Load metadata
                    metadata = self._load_backup_metadata(item)
                    if metadata:
                        # Apply filter if specified
                        if backup_type is None or metadata['backup_type'] == backup_type:
                            backups.append(metadata)
            
            # Sort by creation date
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def _create_database_backup(self, backup_path: str, **kwargs) -> Dict[str, Any]:
        """Create a database backup.
        
        Args:
            backup_path: Path to store the backup
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with backup information
        """
        raise NotImplementedError("Subclasses must implement _create_database_backup")
    
    def _create_research_data_backup(self, backup_path: str, **kwargs) -> Dict[str, Any]:
        """Create a research data backup.
        
        Args:
            backup_path: Path to store the backup
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with backup information
        """
        raise NotImplementedError("Subclasses must implement _create_research_data_backup")
    
    def _create_configuration_backup(self, backup_path: str, **kwargs) -> Dict[str, Any]:
        """Create a configuration backup.
        
        Args:
            backup_path: Path to store the backup
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with backup information
        """
        raise NotImplementedError("Subclasses must implement _create_configuration_backup")
    
    def _restore_database_backup(self, backup_id: str, **kwargs) -> Dict[str, Any]:
        """Restore a database backup.
        
        Args:
            backup_id: ID of the backup to restore
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with restore information
        """
        raise NotImplementedError("Subclasses must implement _restore_database_backup")
    
    def _restore_research_data_backup(self, backup_id: str, **kwargs) -> Dict[str, Any]:
        """Restore a research data backup.
        
        Args:
            backup_id: ID of the backup to restore
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with restore information
        """
        raise NotImplementedError("Subclasses must implement _restore_research_data_backup")
    
    def _restore_configuration_backup(self, backup_id: str, **kwargs) -> Dict[str, Any]:
        """Restore a configuration backup.
        
        Args:
            backup_id: ID of the backup to restore
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with restore information
        """
        raise NotImplementedError("Subclasses must implement _restore_configuration_backup")
    
    def _validate_database_backup(self, backup_id: str) -> Dict[str, Any]:
        """Validate a database backup.
        
        Args:
            backup_id: ID of the backup to validate
            
        Returns:
            Dictionary with validation information
        """
        raise NotImplementedError("Subclasses must implement _validate_database_backup")
    
    def _validate_research_data_backup(self, backup_id: str) -> Dict[str, Any]:
        """Validate a research data backup.
        
        Args:
            backup_id: ID of the backup to validate
            
        Returns:
            Dictionary with validation information
        """
        raise NotImplementedError("Subclasses must implement _validate_research_data_backup")
    
    def _validate_configuration_backup(self, backup_id: str) -> Dict[str, Any]:
        """Validate a configuration backup.
        
        Args:
            backup_id: ID of the backup to validate
            
        Returns:
            Dictionary with validation information
        """
        raise NotImplementedError("Subclasses must implement _validate_configuration_backup")
    
    def _save_backup_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save backup metadata.
        
        Args:
            metadata: Backup metadata
        """
        try:
            backup_id = metadata['backup_id']
            metadata_path = os.path.join(self.backup_dir, backup_id, 'metadata.json')
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    def _load_backup_metadata(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Load backup metadata.
        
        Args:
            backup_id: ID of the backup
            
        Returns:
            Backup metadata or None if not found
        """
        try:
            metadata_path = os.path.join(self.backup_dir, backup_id, 'metadata.json')
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to load backup metadata: {e}")
            return None
    
    def _cleanup_old_backups(self, backup_type: str) -> None:
        """Clean up old backups.
        
        Args:
            backup_type: Type of backup to clean up
        """
        try:
            # Get backups of the specified type
            backups = self.list_backups(backup_type)
            
            # Sort by creation date
            backups.sort(key=lambda x: x['created_at'])
            
            # Keep only the most recent backups within retention period
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
            
            for backup in backups:
                backup_date = datetime.datetime.fromisoformat(backup['created_at'])
                
                if backup_date < cutoff_date:
                    # Delete backup
                    backup_path = os.path.join(self.backup_dir, backup['backup_id'])
                    
                    if os.path.exists(backup_path):
                        import shutil
                        shutil.rmtree(backup_path)
                        logger.info(f"Deleted old backup: {backup['backup_id']}")
                
        except Exception as e:
            logger.error(f"Failed to clean up old backups: {e}")
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate checksum of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Checksum string
        """
        try:
            hash_obj = hashlib.new(self.checksum_algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}")
            return ""
    
    def _encrypt_file(self, file_path: str) -> bool:
        """Encrypt a file using GPG.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.gpg:
                logger.warning("GPG encryption not initialized")
                return False
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Encrypt content
            encrypted_data = self.gpg.encrypt(
                file_content,
                recipients=None,  # Use default key
                symmetric=True,
                passphrase=self.encryption_key
            )
            
            # Write encrypted content
            with open(file_path, 'wb') as f:
                f.write(str(encrypted_data).encode())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to encrypt file: {e}")
            return False
    
    def _decrypt_file(self, file_path: str) -> bool:
        """Decrypt a file using GPG.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.gpg:
                logger.warning("GPG encryption not initialized")
                return False
            
            # Read encrypted content
            with open(file_path, 'rb') as f:
                encrypted_content = f.read()
            
            # Decrypt content
            decrypted_data = self.gpg.decrypt(
                encrypted_content,
                passphrase=self.encryption_key
            )
            
            # Write decrypted content
            with open(file_path, 'wb') as f:
                f.write(decrypted_data.data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to decrypt file: {e}")
            return False 