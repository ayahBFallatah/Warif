#!/usr/bin/env python3
"""
Green Engine Database Backup Script
Creates automated backups of the PostgreSQL database
"""

import os
import sys
import subprocess
import datetime
import logging
import gzip
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_name = os.getenv("DB_NAME", "green_engine")
        self.db_user = os.getenv("DB_USER", "green_user")
        self.db_password = os.getenv("DB_PASSWORD", "password")
        self.db_port = os.getenv("DB_PORT", "5432")
        
        self.backup_dir = Path(os.getenv("BACKUP_DIR", "infrastructure/postgres/backups"))
        self.retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self):
        """Create a database backup"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"green_engine_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        logger.info(f"Creating database backup: {backup_path}")
        
        try:
            # Set environment variable for password
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            # Create backup using pg_dump
            cmd = [
                'pg_dump',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '--verbose',
                '--no-password',
                '--format=custom',
                '--compress=9',
                '--file', str(backup_path)
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Backup created successfully: {backup_path}")
                
                # Compress the backup
                compressed_path = self._compress_backup(backup_path)
                
                # Get backup size
                size_mb = compressed_path.stat().st_size / (1024 * 1024)
                logger.info(f"📊 Backup size: {size_mb:.2f} MB")
                
                return compressed_path
            else:
                logger.error(f"❌ Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Backup error: {e}")
            return None
    
    def _compress_backup(self, backup_path):
        """Compress the backup file"""
        compressed_path = backup_path.with_suffix('.sql.gz')
        
        logger.info(f"Compressing backup: {compressed_path}")
        
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file
        backup_path.unlink()
        
        logger.info(f"✅ Backup compressed: {compressed_path}")
        return compressed_path
    
    def restore_backup(self, backup_path):
        """Restore database from backup"""
        logger.info(f"Restoring database from backup: {backup_path}")
        
        try:
            # Set environment variable for password
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            # Check if backup is compressed
            if backup_path.suffix == '.gz':
                # Decompress first
                decompressed_path = backup_path.with_suffix('')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(decompressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = decompressed_path
            else:
                restore_file = backup_path
            
            # Restore using pg_restore
            cmd = [
                'pg_restore',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '--verbose',
                '--no-password',
                '--clean',
                '--if-exists',
                str(restore_file)
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Database restored successfully from {backup_path}")
                return True
            else:
                logger.error(f"❌ Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Restore error: {e}")
            return False
        finally:
            # Clean up decompressed file if it was created
            if backup_path.suffix == '.gz' and 'decompressed_path' in locals():
                decompressed_path.unlink()
    
    def list_backups(self):
        """List available backups"""
        backups = []
        for backup_file in self.backup_dir.glob("green_engine_backup_*.sql.gz"):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': backup_file,
                'size_mb': stat.st_size / (1024 * 1024),
                'created': datetime.datetime.fromtimestamp(stat.st_ctime)
            })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        logger.info(f"Cleaning up backups older than {self.retention_days} days")
        
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
        removed_count = 0
        
        for backup_file in self.backup_dir.glob("green_engine_backup_*.sql.gz"):
            if datetime.datetime.fromtimestamp(backup_file.stat().st_ctime) < cutoff_date:
                logger.info(f"Removing old backup: {backup_file.name}")
                backup_file.unlink()
                removed_count += 1
        
        logger.info(f"✅ Removed {removed_count} old backups")
        return removed_count
    
    def get_backup_status(self):
        """Get backup status and statistics"""
        backups = self.list_backups()
        
        if not backups:
            return {
                'total_backups': 0,
                'latest_backup': None,
                'total_size_mb': 0,
                'oldest_backup': None
            }
        
        total_size = sum(backup['size_mb'] for backup in backups)
        
        return {
            'total_backups': len(backups),
            'latest_backup': backups[0]['created'].isoformat(),
            'total_size_mb': total_size,
            'oldest_backup': backups[-1]['created'].isoformat()
        }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Green Engine Database Backup Tool")
    parser.add_argument("action", choices=["backup", "restore", "list", "cleanup", "status"], 
                       help="Action to perform")
    parser.add_argument("--backup-file", help="Backup file for restore action")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    backup_tool = DatabaseBackup()
    
    if args.action == "backup":
        backup_path = backup_tool.create_backup()
        if backup_path:
            print(f"✅ Backup created: {backup_path}")
            sys.exit(0)
        else:
            print("❌ Backup failed")
            sys.exit(1)
    
    elif args.action == "restore":
        if not args.backup_file:
            print("❌ --backup-file is required for restore action")
            sys.exit(1)
        
        backup_path = Path(args.backup_file)
        if not backup_path.exists():
            print(f"❌ Backup file not found: {backup_path}")
            sys.exit(1)
        
        if backup_tool.restore_backup(backup_path):
            print("✅ Database restored successfully")
            sys.exit(0)
        else:
            print("❌ Restore failed")
            sys.exit(1)
    
    elif args.action == "list":
        backups = backup_tool.list_backups()
        if backups:
            print(f"\n📋 Available backups ({len(backups)} total):")
            print("-" * 80)
            for backup in backups:
                print(f"  {backup['filename']}")
                print(f"    Size: {backup['size_mb']:.2f} MB")
                print(f"    Created: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                print()
        else:
            print("📋 No backups found")
    
    elif args.action == "cleanup":
        removed_count = backup_tool.cleanup_old_backups()
        print(f"✅ Cleaned up {removed_count} old backups")
    
    elif args.action == "status":
        status = backup_tool.get_backup_status()
        print(f"\n📊 Backup Status:")
        print(f"  Total backups: {status['total_backups']}")
        print(f"  Total size: {status['total_size_mb']:.2f} MB")
        if status['latest_backup']:
            print(f"  Latest backup: {status['latest_backup']}")
            print(f"  Oldest backup: {status['oldest_backup']}")
        else:
            print("  No backups available")

if __name__ == "__main__":
    main()
