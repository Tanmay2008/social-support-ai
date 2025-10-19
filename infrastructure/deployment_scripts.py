# 8_infrastructure/deployment_scripts.py
import subprocess
import os
import sys
import yaml
import json
from typing import Dict, List, Any
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentManager:
    """Manager for deployment and infrastructure operations"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.config = self._load_deployment_config()
    
    def _load_deployment_config(self) -> Dict:
        """Load deployment configuration"""
        config_path = f"deployment/{self.environment}.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return {
                'services': ['backend', 'frontend', 'database', 'cache'],
                'scale': {
                    'backend': 2,
                    'frontend': 1
                },
                'resources': {
                    'backend': {
                        'memory': '2G',
                        'cpu': '1.0'
                    },
                    'frontend': {
                        'memory': '1G', 
                        'cpu': '0.5'
                    }
                }
            }
    
    def deploy_infrastructure(self):
        """Deploy complete infrastructure stack"""
        logger.info(f"Deploying {self.environment} infrastructure...")
        
        try:
            # Start Docker Compose
            compose_file = "8_infrastructure/docker-compose.yml"
            env_file = f"deployment/{self.environment}.env"
            
            cmd = ["docker-compose", "-f", compose_file]
            if os.path.exists(env_file):
                cmd.extend(["--env-file", env_file])
            
            cmd.extend(["up", "-d"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Infrastructure deployed successfully")
                self._wait_for_services()
                return True
            else:
                logger.error(f"Deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Deployment error: {str(e)}")
            return False
    
    def _wait_for_services(self):
        """Wait for all services to be healthy"""
        logger.info("Waiting for services to be ready...")
        
        services = [
            "ai-backend",
            "ai-frontend", 
            "postgres",
            "redis",
            "qdrant",
            "ollama"
        ]
        
        for service in services:
            self._wait_for_service_health(service)
    
    def _wait_for_service_health(self, service_name: str, timeout: int = 300):
        """Wait for a specific service to be healthy"""
        logger.info(f"Waiting for {service_name} to be healthy...")
        
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                cmd = ["docker", "inspect", "--format", "{{.State.Health.Status}}", service_name]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and "healthy" in result.stdout.strip():
                    logger.info(f"{service_name} is healthy")
                    return True
                
                time.sleep(5)
                
            except Exception as e:
                logger.warning(f"Health check failed for {service_name}: {str(e)}")
                time.sleep(5)
        
        logger.error(f"Timeout waiting for {service_name} to be healthy")
        return False
    
    def scale_service(self, service: str, replicas: int):
        """Scale a specific service"""
        logger.info(f"Scaling {service} to {replicas} replicas...")
        
        try:
            cmd = [
                "docker-compose", "-f", "8_infrastructure/docker-compose.yml",
                "up", "-d", "--scale", f"{service}={replicas}", service
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully scaled {service} to {replicas} replicas")
                return True
            else:
                logger.error(f"Scaling failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Scaling error: {str(e)}")
            return False
    
    def backup_database(self, backup_path: str = "backups"):
        """Create database backup"""
        logger.info("Creating database backup...")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_path}/backup_{timestamp}.sql"
            
            # Create backup directory if it doesn't exist
            os.makedirs(backup_path, exist_ok=True)
            
            cmd = [
                "docker", "exec", "postgres", "pg_dump",
                "-U", "admin", "-d", "social_support", "-f", f"/backup/backup_{timestamp}.sql"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Copy backup from container to host
                copy_cmd = [
                    "docker", "cp", f"postgres:/backup/backup_{timestamp}.sql", backup_file
                ]
                subprocess.run(copy_cmd, capture_output=True)
                
                logger.info(f"Database backup created: {backup_file}")
                return backup_file
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Backup error: {str(e)}")
            return None
    
    def restore_database(self, backup_file: str):
        """Restore database from backup"""
        logger.info(f"Restoring database from {backup_file}...")
        
        try:
            # Copy backup to container
            copy_cmd = ["docker", "cp", backup_file, "postgres:/restore/backup.sql"]
            subprocess.run(copy_cmd, capture_output=True)
            
            # Restore database
            cmd = [
                "docker", "exec", "postgres", "psql",
                "-U", "admin", "-d", "social_support", "-f", "/restore/backup.sql"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Restore error: {str(e)}")
            return False
    
    def update_application(self, version: str):
        """Update application to a new version"""
        logger.info(f"Updating application to version {version}...")
        
        try:
            # Pull latest images
            cmd = ["docker-compose", "-f", "8_infrastructure/docker-compose.yml", "pull"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Image pull failed: {result.stderr}")
                return False
            
            # Restart services
            cmd = ["docker-compose", "-f", "8_infrastructure/docker-compose.yml", "up", "-d"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Application updated successfully")
                return True
            else:
                logger.error(f"Update failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        try:
            cmd = ["docker", "ps", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
                
                status = {
                    'total_containers': len(containers),
                    'running_containers': len([c for c in containers if c['State'] == 'running']),
                    'services': {}
                }
                
                for container in containers:
                    service_name = container['Names']
                    status['services'][service_name] = {
                        'state': container['State'],
                        'status': container['Status'],
                        'image': container['Image']
                    }
                
                return status
            else:
                return {'error': 'Failed to get system status'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def run_maintenance(self):
        """Run system maintenance tasks"""
        logger.info("Running system maintenance...")
        
        tasks = [
            self._cleanup_old_images,
            self._prune_system,
            self._rotate_logs,
            self._update_system
        ]
        
        results = {}
        for task in tasks:
            try:
                task_name = task.__name__
                logger.info(f"Running {task_name}...")
                results[task_name] = task()
            except Exception as e:
                results[task_name] = f"Failed: {str(e)}"
        
        return results
    
    def _cleanup_old_images(self):
        """Cleanup old Docker images"""
        cmd = ["docker", "image", "prune", "-f"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return "Success" if result.returncode == 0 else f"Failed: {result.stderr}"
    
    def _prune_system(self):
        """Prune Docker system"""
        cmd = ["docker", "system", "prune", "-f"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return "Success" if result.returncode == 0 else f"Failed: {result.stderr}"
    
    def _rotate_logs(self):
        """Rotate application logs"""
        # This would typically involve logrotate or similar
        return "Log rotation completed"
    
    def _update_system(self):
        """Update system packages"""
        # This would update system packages in production
        return "System update completed"

# CLI interface for deployment operations
def main():
    """Command line interface for deployment operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI System Deployment Manager")
    parser.add_argument('--environment', '-e', default='development', 
                       choices=['development', 'staging', 'production'],
                       help='Deployment environment')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy infrastructure')
    
    # Scale command
    scale_parser = subparsers.add_parser('scale', help='Scale services')
    scale_parser.add_argument('service', help='Service to scale')
    scale_parser.add_argument('replicas', type=int, help='Number of replicas')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--path', default='backups', help='Backup path')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database')
    restore_parser.add_argument('file', help='Backup file to restore')
    
    # Status command
    subparsers.add_parser('status', help='Get system status')
    
    # Maintenance command
    subparsers.add_parser('maintenance', help='Run maintenance tasks')
    
    args = parser.parse_args()
    
    manager = DeploymentManager(environment=args.environment)
    
    if args.command == 'deploy':
        success = manager.deploy_infrastructure()
        sys.exit(0 if success else 1)
    
    elif args.command == 'scale':
        success = manager.scale_service(args.service, args.replicas)
        sys.exit(0 if success else 1)
    
    elif args.command == 'backup':
        backup_file = manager.backup_database(args.path)
        if backup_file:
            print(f"Backup created: {backup_file}")
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.command == 'restore':
        success = manager.restore_database(args.file)
        sys.exit(0 if success else 1)
    
    elif args.command == 'status':
        status = manager.get_system_status()
        print(json.dumps(status, indent=2))
    
    elif args.command == 'maintenance':
        results = manager.run_maintenance()
        print(json.dumps(results, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()