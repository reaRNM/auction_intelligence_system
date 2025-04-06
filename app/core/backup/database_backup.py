from typing import Dict, List, Optional, Any
import logging
import os
import subprocess
import hashlib
import json
from datetime import datetime, timedelta
import boto3
import pg8000
from .base_backup import BaseBackupService, BackupType, BackupStatus

logger = logging.getLogger(__name__)

class DatabaseBackupService(BaseBackupService):
    """Service for handling PostgreSQL database backups."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize database backup service.
        
        Args:
            config: Configuration dictionary containing:
                - db_host: Database host
                - db_port: Database port
                - db_name: Database name
                - db_user: Database user
                - db_password: Database password
                - backup_dir: Directory for storing backups
                - s3_bucket: S3 bucket for offsite storage
                - wal_archive_dir: Directory for WAL archives
                - replication_host: Host for replication
                - replication_port: Port for replication
                - replication_user: User for replication
                - replication_password: Password for replication
        """
        super().__init__(config)
        self.db_config = {
            'host': config['db_host'],
            'port': config['db_port'],
            'database': config['db_name'],
            'user': config['db_user'],
            'password': config['db_password']
        }
        self.wal_archive_dir = config['wal_archive_dir']
        self.replication_config = {
            'host': config['replication_host'],
            'port': config['replication_port'],
            'user': config['replication_user'],
            'password': config['replication_password']
        }
        
        # Ensure WAL archive directory exists
        os.makedirs(self.wal_archive_dir, exist_ok=True)
        
        # Initialize S3 client
        self.s3 = boto3.client('s3')
    
    def _create_database_backup(self, backup_id: str, backup_dir: str) -> Dict[str, Any]:
        """Create a database backup.
        
        Args:
            backup_id: Unique backup identifier
            backup_dir: Directory to store backup files
            
        Returns:
            Dict containing backup metadata
        """
        try:
            # Create backup directory
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create database dump
            dump_file = os.path.join(backup_dir, 'database.sql')
            self._create_database_dump(dump_file)
            
            # Archive WAL files
            self._archive_wal_files(backup_dir)
            
            # Setup replication
            self._setup_replication()
            
            # Calculate checksum
            checksum = self._calculate_checksum(dump_file)
            
            # Upload to S3
            s3_key = f"database/{backup_id}/database.sql"
            self.s3.upload_file(dump_file, self.config['s3_bucket'], s3_key)
            
            # Create metadata
            metadata = {
                'backup_id': backup_id,
                'type': BackupType.DATABASE,
                'timestamp': datetime.utcnow().isoformat(),
                'files': {
                    'database.sql': {
                        'path': dump_file,
                        'size': os.path.getsize(dump_file),
                        'checksum': checksum,
                        's3_key': s3_key
                    }
                },
                'status': BackupStatus.COMPLETED,
                'db_config': {
                    'host': self.db_config['host'],
                    'port': self.db_config['port'],
                    'database': self.db_config['database']
                }
            }
            
            # Save metadata
            self._save_backup_metadata(backup_id, metadata)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {str(e)}")
            raise
    
    def _restore_database_backup(self, backup_id: str, backup_dir: str) -> None:
        """Restore a database backup.
        
        Args:
            backup_id: Unique backup identifier
            backup_dir: Directory containing backup files
        """
        try:
            # Load metadata
            metadata = self._load_backup_metadata(backup_id)
            
            # Download from S3 if needed
            dump_file = os.path.join(backup_dir, 'database.sql')
            if not os.path.exists(dump_file):
                s3_key = metadata['files']['database.sql']['s3_key']
                self.s3.download_file(self.config['s3_bucket'], s3_key, dump_file)
            
            # Validate backup
            if not self._validate_backup(backup_id):
                raise ValueError("Backup validation failed")
            
            # Restore database
            self._restore_database_dump(dump_file)
            
            # Restore WAL files if needed
            self._restore_wal_files(backup_dir)
            
        except Exception as e:
            logger.error(f"Failed to restore database backup: {str(e)}")
            raise
    
    def _validate_database_backup(self, backup_id: str, backup_dir: str) -> bool:
        """Validate a database backup.
        
        Args:
            backup_id: Unique backup identifier
            backup_dir: Directory containing backup files
            
        Returns:
            bool indicating if backup is valid
        """
        try:
            # Load metadata
            metadata = self._load_backup_metadata(backup_id)
            
            # Check file existence
            dump_file = os.path.join(backup_dir, 'database.sql')
            if not os.path.exists(dump_file):
                return False
            
            # Verify checksum
            current_checksum = self._calculate_checksum(dump_file)
            if current_checksum != metadata['files']['database.sql']['checksum']:
                return False
            
            # Verify file size
            if os.path.getsize(dump_file) != metadata['files']['database.sql']['size']:
                return False
            
            # Verify database connection
            try:
                with pg8000.connect(**self.db_config) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
            except Exception:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate database backup: {str(e)}")
            return False
    
    def _create_database_dump(self, dump_file: str) -> None:
        """Create a database dump using pg_dump.
        
        Args:
            dump_file: Path to store the dump file
        """
        try:
            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-F', 'c',  # Custom format
                '-f', dump_file,
                self.db_config['database']
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            subprocess.run(cmd, env=env, check=True)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create database dump: {str(e)}")
            raise
    
    def _restore_database_dump(self, dump_file: str) -> None:
        """Restore a database dump using pg_restore.
        
        Args:
            dump_file: Path to the dump file
        """
        try:
            cmd = [
                'pg_restore',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', self.db_config['database'],
                '-c',  # Clean (drop) database objects before recreating
                dump_file
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            subprocess.run(cmd, env=env, check=True)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restore database dump: {str(e)}")
            raise
    
    def _archive_wal_files(self, backup_dir: str) -> None:
        """Archive WAL files.
        
        Args:
            backup_dir: Directory to store WAL archives
        """
        try:
            # Create WAL archive directory
            wal_dir = os.path.join(backup_dir, 'wal')
            os.makedirs(wal_dir, exist_ok=True)
            
            # Get current WAL segment
            with pg8000.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT pg_current_wal_lsn()")
                    current_lsn = cursor.fetchone()[0]
            
            # Archive WAL files
            cmd = [
                'pg_archivecleanup',
                self.wal_archive_dir,
                current_lsn
            ]
            
            subprocess.run(cmd, check=True)
            
            # Copy archived WAL files to backup directory
            for file in os.listdir(self.wal_archive_dir):
                if file.startswith('0000'):
                    src = os.path.join(self.wal_archive_dir, file)
                    dst = os.path.join(wal_dir, file)
                    os.rename(src, dst)
            
        except Exception as e:
            logger.error(f"Failed to archive WAL files: {str(e)}")
            raise
    
    def _restore_wal_files(self, backup_dir: str) -> None:
        """Restore WAL files.
        
        Args:
            backup_dir: Directory containing WAL archives
        """
        try:
            wal_dir = os.path.join(backup_dir, 'wal')
            if not os.path.exists(wal_dir):
                return
            
            # Copy WAL files to archive directory
            for file in os.listdir(wal_dir):
                if file.startswith('0000'):
                    src = os.path.join(wal_dir, file)
                    dst = os.path.join(self.wal_archive_dir, file)
                    os.rename(src, dst)
            
        except Exception as e:
            logger.error(f"Failed to restore WAL files: {str(e)}")
            raise
    
    def _setup_replication(self) -> None:
        """Setup database replication."""
        try:
            # Connect to primary database
            with pg8000.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    # Create replication slot
                    cursor.execute(
                        "SELECT pg_create_physical_replication_slot('replica_slot')"
                    )
                    
                    # Configure replication
                    cursor.execute("""
                        ALTER SYSTEM SET wal_level = replica;
                        ALTER SYSTEM SET max_wal_senders = 10;
                        ALTER SYSTEM SET max_replication_slots = 10;
                    """)
                    
                    # Reload configuration
                    cursor.execute("SELECT pg_reload_conf()")
            
            # Connect to replica database
            with pg8000.connect(**self.replication_config) as conn:
                with conn.cursor() as cursor:
                    # Configure replica
                    cursor.execute("""
                        ALTER SYSTEM SET hot_standby = on;
                        ALTER SYSTEM SET primary_conninfo = %s
                    """, (
                        f"host={self.db_config['host']} "
                        f"port={self.db_config['port']} "
                        f"user={self.db_config['user']} "
                        f"password={self.db_config['password']}"
                    ))
                    
                    # Reload configuration
                    cursor.execute("SELECT pg_reload_conf()")
            
        except Exception as e:
            logger.error(f"Failed to setup replication: {str(e)}")
            raise 