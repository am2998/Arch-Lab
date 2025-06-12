#!/usr/bin/env python3
# ZFS Assistant - Core ZFS operations
# Author: GitHub Copilot

import os
import json
import subprocess
import datetime
import tempfile
from pathlib import Path

# Try relative imports first, fall back to absolute imports if run as a script
try:
    from .common import (
        CONFIG_DIR, CONFIG_FILE, LOG_FILE, PACMAN_HOOK_PATH, 
        SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
        DEFAULT_CONFIG, run_command, get_timestamp
    )
    from .models import ZFSSnapshot
    from .logger import (
        ZFSLogger, OperationType, LogLevel, get_logger,
        log_info, log_error, log_success, log_warning
    )
except ImportError:
    # For direct script execution
    import sys
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    try:
        # Try with src as a direct submodule
        from src.common import (
            CONFIG_DIR, CONFIG_FILE, LOG_FILE, PACMAN_HOOK_PATH, 
            SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
            DEFAULT_CONFIG, run_command, get_timestamp
        )
        from src.models import ZFSSnapshot
        from src.logger import (
            ZFSLogger, OperationType, LogLevel, get_logger,
            log_info, log_error, log_success, log_warning
        )
    except ImportError:
        # Last resort, use direct file paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        from common import (
            CONFIG_DIR, CONFIG_FILE, LOG_FILE, PACMAN_HOOK_PATH, 
            SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
            DEFAULT_CONFIG, run_command, get_timestamp
        )
        from models import ZFSSnapshot
        from logger import (
            ZFSLogger, OperationType, LogLevel, get_logger,
            log_info, log_error, log_success, log_warning
        )

class ZFSAssistant:
    """
    Class for managing ZFS operations and configuration
    """
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self.pacman_hook_path = PACMAN_HOOK_PATH
        self.default_config = DEFAULT_CONFIG
        self.config = self.load_config()
        
        # Initialize comprehensive logging
        self.logger = get_logger()
        log_info("ZFS Assistant initialized", {
            'config_dir': str(self.config_dir),
            'config_file': str(self.config_file),
            'managed_datasets': self.config.get('datasets', []),
            'auto_snapshot_enabled': self.config.get('auto_snapshot', True),
            'pacman_integration_enabled': self.config.get('pacman_integration', True)
        })

    # Helper method to run pkexec commands
    def run_pkexec_command(self, cmd):
        """Run a command with pkexec"""
        try:
            # Check if the command already includes pkexec
            has_pkexec = cmd[0] == 'pkexec' if cmd else False
            
            # If cmd already includes pkexec, use it as is
            # Otherwise, prepend pkexec to the command
            if not has_pkexec:
                cmd = ['pkexec'] + cmd
                
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, result
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr
            if "Permission denied" in error_msg or "authorization failed" in error_msg:
                return False, "Permission denied. ZFS operations require administrative privileges."
            return False, f"Error executing command: {error_msg}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def load_config(self):
        """Load configuration from file or create with defaults if it doesn't exist"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
            
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default config file
                with open(self.config_file, 'w') as f:
                    json.dump(self.default_config, f, indent=2)
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
            
    def export_config(self, filename):
        """Export configuration to a file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True, f"Configuration exported to {filename}"
        except Exception as e:
            return False, f"Error exporting configuration: {e}"
            
    def import_config(self, filename):
        """Import configuration from a file"""
        try:
            with open(filename, 'r') as f:
                imported_config = json.load(f)
                
            # Validate imported config
            if not isinstance(imported_config, dict):
                return False, "Invalid configuration format"
                
            # Make sure required fields exist, use defaults if missing
            required_fields = ["auto_snapshot", "snapshot_retention", "datasets", "prefix"]
            for field in required_fields:
                if field not in imported_config:
                    imported_config[field] = self.default_config[field]
            
            # Update config
            self.config = imported_config
            self.save_config()
            
            return True, "Configuration imported successfully"
        except json.JSONDecodeError:
            return False, "Invalid JSON format in configuration file"
        except Exception as e:
            return False, f"Error importing configuration: {e}"

    def get_datasets(self):
        """Get available ZFS datasets with their properties"""
        try:
            # First get the dataset names
            result = subprocess.run(['zfs', 'list', '-H', '-o', 'name'], 
                                    capture_output=True, text=True, check=True)
            dataset_names = result.stdout.strip().split('\n')
            
            # Filter out top-level zpools (those that don't have a '/' in their name)
            dataset_names = [name for name in dataset_names if '/' in name]
            
            # Now get properties for each dataset
            datasets = []
            for name in dataset_names:
                properties = self.get_dataset_properties(name)
                datasets.append({
                    'name': name,
                    'properties': properties
                })
            
            return datasets
        except subprocess.CalledProcessError as e:
            # This is a read-only operation, so we don't need elevated privileges,
            # but users might still encounter permission issues
            print(f"Error getting datasets: {e.stderr}")
            return []
        except Exception as e:
            print(f"Error getting datasets: {e}")
            return []
    
    def get_dataset_properties(self, dataset_name):
        """Get properties for a specific dataset"""
        try:
            properties = {}
            # Get common properties
            props_to_get = [
                'used', 'available', 'referenced', 'mountpoint', 
                'compression', 'compressratio', 'readonly', 'encryption',
                'quota', 'reservation', 'recordsize', 'type'
            ]
            
            for prop in props_to_get:
                result = subprocess.run(
                    ['zfs', 'get', '-H', '-o', 'value', prop, dataset_name],
                    capture_output=True, text=True, check=False
                )
                if result.returncode == 0:
                    properties[prop] = result.stdout.strip()
            
            return properties
        except Exception as e:
            print(f"Error getting properties for {dataset_name}: {e}")
            return {}

    def get_snapshots(self, dataset=None):
        """Get ZFS snapshots for a dataset or all snapshots if dataset is None"""
        try:
            cmd = ['zfs', 'list', '-H', '-t', 'snapshot', '-o', 'name,creation,used,referenced', '-s', 'creation']
            
            if dataset:
                cmd.append(f"{dataset}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            
            snapshots = []
            for line in lines:
                if line:  # Skip empty lines
                    snapshot = ZFSSnapshot.from_zfs_list(line)
                    if snapshot:
                        snapshots.append(snapshot)
            
            return snapshots
        except subprocess.CalledProcessError as e:
            # This is a read-only operation, so we don't need elevated privileges,
            # but users might still encounter permission issues
            print(f"Error getting snapshots: {e.stderr}")
            return []
        except Exception as e:
            print(f"Error getting snapshots: {e}")
            return []
            
    def cleanup_snapshots(self):
        """Clean up snapshots based on retention policy"""
        try:
            # Check if auto_snapshot is disabled - for manual cleanups we'll still proceed
            auto_snapshot_disabled = not self.config.get("auto_snapshot", True)
            
            retention = self.config.get("snapshot_retention", {})
            prefix = self.config.get("prefix", "zfs-assistant")
            
            log_info("Starting snapshot cleanup based on retention policy", {
                'retention_policy': retention,
                'prefix': prefix,
                'auto_snapshot_disabled': auto_snapshot_disabled,
                'operation': 'cleanup'
            })
            
            # Start operation tracking
            operation_id = self.logger.start_operation(OperationType.SNAPSHOT_CLEANUP, {
                'retention_policy': retention,
                'prefix': prefix
            })
            
            # Get all snapshots for managed datasets
            managed_datasets = self.config.get("datasets", [])
            snapshots_by_type = {
                "hourly": [],
                "daily": [],
                "weekly": [],
                "monthly": []
            }
            
            log_info(f"Scanning {len(managed_datasets)} datasets for snapshots", {
                'datasets': managed_datasets
            })
            
            success_count = 0
            error_count = 0
            errors = []
            
            for dataset in managed_datasets:
                # Get all snapshots for this dataset
                all_snapshots = self.get_snapshots(dataset)
                log_info(f"Found {len(all_snapshots)} snapshots in dataset: {dataset}")
                
                # Group snapshots by type
                for snapshot in all_snapshots:
                    for snap_type in snapshots_by_type.keys():
                        if f"{prefix}-{snap_type}-" in snapshot.name:
                            snapshots_by_type[snap_type].append(snapshot)
            
            # Log snapshot counts by type
            for snap_type, snapshots in snapshots_by_type.items():
                count = len(snapshots)
                retention_count = retention.get(snap_type, 0)
                to_delete_count = max(0, count - retention_count) if retention_count > 0 else 0
                log_info(f"Snapshot type '{snap_type}': {count} found, {retention_count} to keep, {to_delete_count} to delete")
            
            # Apply retention policy
            for snap_type, snapshots in snapshots_by_type.items():
                # Sort snapshots by creation time (newest first)
                sorted_snapshots = sorted(
                    snapshots, 
                    key=lambda x: x.creation_date if isinstance(x.creation_date, datetime.datetime) else datetime.datetime.now(),
                    reverse=True
                )
                
                # Keep only the number specified in the retention policy
                keep_count = retention.get(snap_type, 0)
                to_delete = sorted_snapshots[keep_count:] if keep_count > 0 else []
                
                # Delete excess snapshots
                for snapshot in to_delete:
                    log_info(f"Deleting excess {snap_type} snapshot: {snapshot.full_name}")
                    success, message = self.delete_snapshot(snapshot.full_name)
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(message)
            
            result_message = f"Cleanup completed: {success_count} snapshots deleted"
            if error_count > 0:
                result_message += f", {error_count} errors"
                if errors:
                    # Check if any permission errors occurred
                    if any("Permission denied" in err for err in errors):
                        result_message += "\nSome operations failed due to insufficient permissions. " \
                                         "ZFS operations require administrative privileges."
                    result_message += f"\nErrors: {'; '.join(errors[:5])}"
                    if len(errors) > 5:
                        result_message += f" and {len(errors) - 5} more"
            
            # Log final results
            if error_count == 0:
                log_success(result_message, {
                    'snapshots_deleted': success_count,
                    'errors': error_count
                })
                self.logger.end_operation(operation_id, True, {
                    'snapshots_deleted': success_count,
                    'message': result_message
                })
            else:
                log_warning(result_message, {
                    'snapshots_deleted': success_count,
                    'errors': error_count,
                    'error_messages': errors[:5]
                })
                self.logger.end_operation(operation_id, False, {
                    'snapshots_deleted': success_count,
                    'errors': error_count,
                    'error_messages': errors
                })
            
            return success_count > 0 or error_count == 0, result_message
        except Exception as e:
            error_msg = f"Error during snapshot cleanup: {str(e)}"
            log_error(error_msg, {
                'exception': str(e)
            })
            if 'operation_id' in locals():
                self.logger.end_operation(operation_id, False, {'error': error_msg})
            return False, error_msg

    def create_snapshot(self, dataset, name=None):
        """Create a ZFS snapshot for the specified dataset"""
        try:
            if not name:
                timestamp = get_timestamp()
                name = f"{self.config['prefix']}-{timestamp}"
            
            snapshot_name = f"{dataset}@{name}"
            
            log_info(f"Creating snapshot: {snapshot_name}", {
                'dataset': dataset,
                'snapshot_name': name,
                'full_snapshot_name': snapshot_name,
                'operation': 'create'
            })
            
            # Use cached pkexec authorization
            success, result = self.run_pkexec_command(['zfs', 'snapshot', snapshot_name])
            if not success:
                log_error(f"Failed to create snapshot: {snapshot_name}", {
                    'error': result,
                    'dataset': dataset,
                    'snapshot_name': name
                })
                return False, result
            
            log_success(f"Successfully created snapshot: {snapshot_name}", {
                'dataset': dataset,
                'snapshot_name': name,
                'full_snapshot_name': snapshot_name
            })
            
            self.logger.log_snapshot_operation('create', dataset, name, True)
            return True, name
        except Exception as e:
            error_msg = f"Error creating snapshot: {str(e)}"
            log_error(error_msg, {
                'dataset': dataset,
                'snapshot_name': name,
                'exception': str(e)
            })
            return False, error_msg

    def delete_snapshot(self, snapshot_full_name):
        """Delete a ZFS snapshot by its full name (dataset@snapshot)"""
        try:
            # Parse dataset and snapshot name
            dataset, snapshot_name = snapshot_full_name.split('@', 1)
            
            log_info(f"Deleting snapshot: {snapshot_full_name}", {
                'dataset': dataset,
                'snapshot_name': snapshot_name,
                'full_snapshot_name': snapshot_full_name,
                'operation': 'delete'
            })
            
            # Use cached pkexec authorization
            success, result = self.run_pkexec_command(['zfs', 'destroy', snapshot_full_name])
            if not success:
                log_error(f"Failed to delete snapshot: {snapshot_full_name}", {
                    'error': result,
                    'dataset': dataset,
                    'snapshot_name': snapshot_name
                })
                self.logger.log_snapshot_operation('delete', dataset, snapshot_name, False, {'error': result})
                return False, result
            
            log_success(f"Successfully deleted snapshot: {snapshot_full_name}", {
                'dataset': dataset,
                'snapshot_name': snapshot_name,
                'full_snapshot_name': snapshot_full_name
            })
            
            self.logger.log_snapshot_operation('delete', dataset, snapshot_name, True)
            return True, f"Snapshot {snapshot_full_name} deleted"
        except Exception as e:
            error_msg = f"Error deleting snapshot: {str(e)}"
            log_error(error_msg, {
                'snapshot_full_name': snapshot_full_name,
                'exception': str(e)
            })
            return False, error_msg

    def rollback_snapshot(self, snapshot_full_name, force=False):
        """Rollback to a ZFS snapshot"""
        try:
            # Parse dataset and snapshot name for logging
            dataset, snapshot_name = snapshot_full_name.split('@', 1)
            
            log_info(f"Rolling back to snapshot: {snapshot_full_name}", {
                'dataset': dataset,
                'snapshot_name': snapshot_name,
                'full_snapshot_name': snapshot_full_name,
                'force': force,
                'operation': 'rollback'
            })
            
            cmd = ['zfs', 'rollback']
            if force:
                cmd.append('-r')
            cmd.append(snapshot_full_name)
            
            # Use cached pkexec authorization
            success, result = self.run_pkexec_command(cmd)
            if not success:
                log_error(f"Failed to rollback to snapshot: {snapshot_full_name}", {
                    'error': result,
                    'dataset': dataset,
                    'snapshot_name': snapshot_name,
                    'force': force
                })
                return False, result
            
            log_success(f"Successfully rolled back to snapshot: {snapshot_full_name}", {
                'dataset': dataset,
                'snapshot_name': snapshot_name,
                'force': force
            })
            return True, f"Rolled back to snapshot {snapshot_full_name}"
        except Exception as e:
            error_msg = f"Error rolling back to snapshot: {str(e)}"
            log_error(error_msg, {
                'snapshot_full_name': snapshot_full_name,
                'force': force,
                'exception': str(e)
            })
            return False, error_msg

    def clone_snapshot(self, snapshot_full_name, target_name):
        """Clone a ZFS snapshot to a new dataset"""
        try:
            # Parse dataset and snapshot name for logging
            dataset, snapshot_name = snapshot_full_name.split('@', 1)
            
            log_info(f"Cloning snapshot: {snapshot_full_name} to {target_name}", {
                'source_dataset': dataset,
                'snapshot_name': snapshot_name,
                'source_full_name': snapshot_full_name,
                'target_name': target_name,
                'operation': 'clone'
            })
            
            # Use cached pkexec authorization
            success, result = self.run_pkexec_command(['zfs', 'clone', snapshot_full_name, target_name])
            if not success:
                log_error(f"Failed to clone snapshot: {snapshot_full_name} to {target_name}", {
                    'error': result,
                    'source_dataset': dataset,
                    'snapshot_name': snapshot_name,
                    'target_name': target_name
                })
                return False, result
            
            log_success(f"Successfully cloned snapshot: {snapshot_full_name} to {target_name}", {
                'source_dataset': dataset,
                'snapshot_name': snapshot_name,
                'target_name': target_name
            })
            return True, f"Cloned snapshot {snapshot_full_name} to {target_name}"
        except Exception as e:
            error_msg = f"Error cloning snapshot: {str(e)}"
            log_error(error_msg, {
                'snapshot_full_name': snapshot_full_name,
                'target_name': target_name,
                'exception': str(e)
            })
            return False, error_msg

    def setup_pacman_hook(self, enable=True):
        """Setup or remove pacman hook to create ZFS snapshots before package operations"""
        if enable:
            hook_content = """[Trigger]
Operation = Install
Operation = Upgrade
Operation = Remove
Type = Package
Target = *

[Action]
Description = Creating ZFS snapshot before pacman transaction...
When = PreTransaction
Exec = /usr/bin/python /usr/local/bin/zfs-assistant-pacman-hook.py
Depends = python
"""
            # Create the hook script with comprehensive logging
            script_content = """#!/usr/bin/env python3
import subprocess
import datetime
import json
import os
import sys

# Try to import the logging system, fallback if not available
try:
    from logger import ZFSLogger, OperationType, LogLevel
    HAS_LOGGING = True
except ImportError:
    HAS_LOGGING = False
    # Fallback logger functions
    def log_operation_start(op_type, details):
        print(f"Starting operation: {details}")
    
    def log_message(level, message, details=None):
        print(f"[{level}] {message}")
        if details:
            print(f"  Details: {details}")
    
    def log_operation_end(op_type, success, details=None, error_message=None):
        status = "SUCCESS" if success else "FAILED"
        print(f"Operation completed: {status}")
        if error_message:
            print(f"  Error: {error_message}")

def create_pre_pacman_snapshot():
    logger = None
    operation_started = False
    
    try:
        # Initialize logger if available
        if HAS_LOGGING:
            logger = ZFSLogger()
            logger.log_operation_start(OperationType.PACMAN_INTEGRATION, "Pre-package transaction snapshot creation")
            operation_started = True
        else:
            log_operation_start("PACMAN_INTEGRATION", "Pre-package transaction snapshot creation")
            operation_started = True
        
        config_file = os.path.expanduser("~/.config/zfs-assistant/config.json")
        
        # Load configuration
        if not os.path.exists(config_file):
            error_msg = f"Configuration file not found: {config_file}"
            if logger:
                logger.log_error("Configuration file not found", {'config_file': config_file})
                logger.log_operation_end(OperationType.PACMAN_INTEGRATION, False, error_message=error_msg)
            else:
                log_message("ERROR", error_msg)
                log_operation_end("PACMAN_INTEGRATION", False, error_message=error_msg)
            return
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if logger:
            logger.log_info("Configuration loaded successfully", {'config_file': config_file})
        else:
            log_message("INFO", f"Configuration loaded from {config_file}")
        
        if not config.get("pacman_integration", True):
            if logger:
                logger.log_info("Pacman integration disabled, skipping snapshot creation")
                logger.log_operation_end(OperationType.PACMAN_INTEGRATION, True, "Pacman integration disabled")
            else:
                log_message("INFO", "Pacman integration disabled, skipping snapshot creation")
                log_operation_end("PACMAN_INTEGRATION", True, "Pacman integration disabled")
            return
        
        datasets = config.get("datasets", [])
        if not datasets:
            if logger:
                logger.log_warning("No datasets configured for snapshots")
                logger.log_operation_end(OperationType.PACMAN_INTEGRATION, True, "No datasets configured")
            else:
                log_message("WARNING", "No datasets configured for snapshots")
                log_operation_end("PACMAN_INTEGRATION", True, "No datasets configured")
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = config.get("prefix", "zfs-assistant")
        
        if logger:
            logger.log_info("Starting pacman hook snapshot creation", {
                'timestamp': timestamp,
                'prefix': prefix,
                'dataset_count': len(datasets)
            })
        else:
            log_message("INFO", f"Creating snapshots for {len(datasets)} datasets with timestamp {timestamp}")
        
        # Try to cache authorization with a single pkexec call
        try:
            subprocess.run(['pkexec', 'true'], check=True, capture_output=True)
            if logger:
                logger.log_info("pkexec authorization cached successfully")
            else:
                log_message("INFO", "pkexec authorization cached")
        except Exception as e:
            if logger:
                logger.log_warning("Failed to cache pkexec authorization", {'error': str(e)})
            else:
                log_message("WARNING", f"Failed to cache pkexec authorization: {e}")
        
        success_count = 0
        failed_count = 0
        
        for dataset in datasets:
            snapshot_name = f"{dataset}@{prefix}-pkgop-{timestamp}"
            
            try:
                if logger:
                    logger.log_info("Creating pacman hook snapshot", {
                        'dataset': dataset,
                        'snapshot_name': snapshot_name
                    })
                else:
                    log_message("INFO", f"Creating snapshot: {snapshot_name}")
                
                result = subprocess.run(['pkexec', 'zfs', 'snapshot', snapshot_name], 
                                      check=True, capture_output=True, text=True)
                
                success_count += 1
                if logger:
                    logger.log_snapshot_operation("create", dataset, snapshot_name, True)
                    logger.log_success("Pacman hook snapshot created successfully", {
                        'dataset': dataset,
                        'snapshot_name': snapshot_name
                    })
                else:
                    log_message("SUCCESS", f"Created snapshot: {snapshot_name}")
                
            except subprocess.CalledProcessError as e:
                failed_count += 1
                error_msg = f"Failed to create snapshot {snapshot_name}: {e.stderr if e.stderr else str(e)}"
                
                if logger:
                    logger.log_snapshot_operation("create", dataset, snapshot_name, False, str(e))
                    logger.log_error("Pacman hook snapshot creation failed", {
                        'dataset': dataset,
                        'snapshot_name': snapshot_name,
                        'error': error_msg,
                        'return_code': e.returncode
                    })
                else:
                    log_message("ERROR", error_msg)
            
            except Exception as e:
                failed_count += 1
                error_msg = f"Unexpected error creating snapshot {snapshot_name}: {str(e)}"
                
                if logger:
                    logger.log_snapshot_operation("create", dataset, snapshot_name, False, str(e))
                    logger.log_error("Unexpected error in pacman hook snapshot creation", {
                        'dataset': dataset,
                        'snapshot_name': snapshot_name,
                        'error': error_msg
                    })
                else:
                    log_message("ERROR", error_msg)
        
        # Log final results
        total_count = success_count + failed_count
        operation_success = failed_count == 0
        
        if logger:
            logger.log_info("Pacman hook snapshot operation completed", {
                'total_datasets': total_count,
                'successful_snapshots': success_count,
                'failed_snapshots': failed_count,
                'operation_success': operation_success
            })
            
            if operation_success:
                logger.log_success("All pacman hook snapshots created successfully")
            else:
                logger.log_warning(f"Pacman hook snapshot operation completed with {failed_count} failures")
            
            logger.log_operation_end(OperationType.PACMAN_INTEGRATION, operation_success)
        else:
            status_msg = f"Pacman hook completed: {success_count} successful, {failed_count} failed"
            log_message("SUCCESS" if operation_success else "WARNING", status_msg)
            log_operation_end("PACMAN_INTEGRATION", operation_success)
    
    except Exception as e:
        error_msg = f"Error in pacman hook script: {str(e)}"
        if logger and operation_started:
            logger.log_error("Critical error in pacman hook execution", {
                'error': error_msg,
                'error_type': type(e).__name__
            })
            logger.log_operation_end(OperationType.PACMAN_INTEGRATION, False, error_message=error_msg)
        else:
            log_message("ERROR", error_msg)
            if operation_started:
                log_operation_end("PACMAN_INTEGRATION", False, error_message=error_msg)
        
        # Exit with error code for pacman to detect failure
        sys.exit(1)

if __name__ == "__main__":
    create_pre_pacman_snapshot()
"""
            try:
                # Create temporary files for both hook and script
                
                # Create temporary hook file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hook') as temp_hook:
                    temp_hook.write(hook_content)
                    temp_hook_path = temp_hook.name
                
                # Create temporary script file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as temp_script:
                    temp_script.write(script_content)
                    temp_script_path = temp_script.name
                
                try:
                    # Ensure hook directory exists with elevated permissions
                    hook_dir = os.path.dirname(self.pacman_hook_path)
                    subprocess.run(['pkexec', 'mkdir', '-p', hook_dir], check=True, capture_output=True)
                    
                    # Copy hook file with elevated permissions
                    subprocess.run(['pkexec', 'cp', temp_hook_path, self.pacman_hook_path], check=True, capture_output=True)
                    
                    # Copy script file with elevated permissions
                    script_path = PACMAN_SCRIPT_PATH
                    subprocess.run(['pkexec', 'cp', temp_script_path, script_path], check=True, capture_output=True)
                    
                    # Make the script executable
                    subprocess.run(['pkexec', 'chmod', '755', script_path], check=True, capture_output=True)
                    
                finally:
                    # Clean up temporary files
                    os.unlink(temp_hook_path)
                    os.unlink(temp_script_path)
                
                return True, "Pacman hook installed successfully"
            except Exception as e:
                return False, f"Error installing pacman hook: {e}"
        else:
            # Remove the hook
            try:
                # Use elevated permissions to remove files
                subprocess.run(['pkexec', 'rm', '-f', self.pacman_hook_path], check=True, capture_output=True)
                subprocess.run(['pkexec', 'rm', '-f', PACMAN_SCRIPT_PATH], check=True, capture_output=True)
                
                return True, "Pacman hook removed successfully"
            except Exception as e:
                return False, f"Error removing pacman hook: {e}"

    def setup_systemd_timers(self, schedules):
        """Setup systemd timers for automated snapshots"""
        try:
            # Create the snapshot script with comprehensive logging
            script_content = """#!/usr/bin/env python3
import subprocess
import datetime
import json
import os
import sys
from pathlib import Path

# Import logging system
sys.path.insert(0, '/usr/lib/python3.13/site-packages')
try:
    from zfs_assistant.logger import (
        ZFSLogger, OperationType, LogLevel, get_logger,
        log_info, log_error, log_success, log_warning
    )
except ImportError:
    # Fallback if package import fails
    class MockLogger:
        def start_operation(self, op_type, details): return "mock_id"
        def end_operation(self, op_id, success, details): pass
        def log_snapshot_operation(self, action, dataset, snapshot, success, details=None): pass
        def log_command(self, command): pass
        def log_backup_operation(self, dataset, snapshot, target_pool, backup_type, success, details=None): pass
    
    def log_info(msg, details=None): print(f"[INFO] {msg}")
    def log_error(msg, details=None): print(f"[ERROR] {msg}")
    def log_success(msg, details=None): print(f"[SUCCESS] {msg}")
    def log_warning(msg, details=None): print(f"[WARNING] {msg}")
    
    logger = MockLogger()

def create_scheduled_snapshot(interval):
    try:
        config_file = os.path.expanduser("~/.config/zfs-assistant/config.json")
        
        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Initialize logger if not using mock
        try:
            logger = get_logger()
        except:
            logger = MockLogger()
        
        log_info(f"Starting scheduled {interval} snapshot operation", {
            'interval': interval,
            'config_file': config_file,
            'operation': 'scheduled_snapshot'
        })
        
        # Start operation tracking
        operation_id = logger.start_operation(OperationType.SNAPSHOT_SCHEDULED, {
            'interval': interval,
            'datasets': config.get("datasets", []),
            'prefix': config.get("prefix", "zfs-assistant")
        })
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = config.get("prefix", "zfs-assistant")
        datasets = config.get("datasets", [])
        
        if not datasets:
            error_msg = "No datasets configured for snapshots"
            log_error(error_msg)
            logger.end_operation(operation_id, False, {'error': error_msg})
            return
        
        log_info(f"Creating {interval} snapshots for {len(datasets)} datasets", {
            'datasets': datasets,
            'timestamp': timestamp,
            'prefix': prefix
        })
        
        # Try to cache authorization with a single pkexec call
        try:
            subprocess.run(['pkexec', 'true'], check=True, capture_output=True)
        except:
            pass
        
        success_count = 0
        error_count = 0
        errors = []
        
        for dataset in datasets:
            snapshot_name = f"{dataset}@{prefix}-{interval}-{timestamp}"
            log_info(f"Creating snapshot: {snapshot_name}", {'dataset': dataset})
            
            try:
                result = subprocess.run(['pkexec', 'zfs', 'snapshot', snapshot_name], 
                                      check=True, capture_output=True, text=True)
                log_success(f"Created {interval} snapshot: {snapshot_name}")
                logger.log_snapshot_operation('create', dataset, f"{prefix}-{interval}-{timestamp}", True)
                success_count += 1
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to create snapshot {snapshot_name}: {e.stderr}"
                log_error(error_msg)
                logger.log_snapshot_operation('create', dataset, f"{prefix}-{interval}-{timestamp}", False, {'error': e.stderr})
                errors.append(error_msg)
                error_count += 1
        
        log_info(f"Snapshot creation completed: {success_count} successful, {error_count} failed")
        
        # Check if we should perform system update after creating snapshots
        update_option = config.get("update_snapshots", "disabled")
        if update_option == "before" and interval in ["daily", "weekly", "monthly"]:
            log_info(f"Running system update after {interval} snapshot...")
            try:
                # Run system update
                update_result = subprocess.run(['pkexec', 'pacman', '-Syu', '--noconfirm'], 
                                             capture_output=True, text=True, check=True)
                log_success("System update completed successfully")
                
                # Clean cache if enabled
                if config.get("clean_cache_after_updates", False):
                    cache_result = subprocess.run(['pkexec', 'pacman', '-Scc', '--noconfirm'],
                                                capture_output=True, text=True, check=True)
                    log_success("Package cache cleaned successfully")
                    
            except subprocess.CalledProcessError as e:
                error_msg = f"Error during system update: {e.stderr}"
                log_error(error_msg)
                errors.append(error_msg)
        
        # Check if we should perform backup after creating snapshots
        if config.get("external_backup_enabled", False) and config.get("backup_frequency", "Manual") == "Follow snapshot schedule":
            target_pool = config.get("external_pool_name", "")
            if target_pool:
                log_info(f"Performing backup to {target_pool}...")
                backup_success_count = 0
                backup_error_count = 0
                
                for dataset in datasets:
                    try:
                        # Find the latest snapshot
                        latest_snap_cmd = ["zfs", "list", "-H", "-t", "snapshot", "-o", "name", "-s", "creation", dataset]
                        result = subprocess.run(latest_snap_cmd, capture_output=True, text=True)
                        if result.returncode != 0:
                            log_error(f"Error getting snapshots for {dataset}")
                            backup_error_count += 1
                            continue
                            
                        snapshots = result.stdout.strip().split('\\n')
                        if not snapshots or snapshots[0] == '':
                            log_warning(f"No snapshots found for {dataset}")
                            continue
                            
                        latest_snapshot = snapshots[-1]
                        log_info(f"Latest snapshot for {dataset}: {latest_snapshot}")
                        
                        # Find common snapshots for incremental backup
                        common_snap_cmd = ["zfs", "list", "-H", "-t", "snapshot", "-o", "name", "-s", "creation", target_pool]
                        result = subprocess.run(common_snap_cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0 and result.stdout.strip():
                            # Look for common snapshots
                            target_snapshots = result.stdout.strip().split('\\n')
                            latest_snap_name = latest_snapshot.split('@')[1]
                            
                            # Check if latest snapshot already exists on target
                            latest_exists = False
                            for target_snap in target_snapshots:
                                if '@' in target_snap and target_snap.split('@')[1] == latest_snap_name:
                                    latest_exists = True
                                    break
                                    
                            if latest_exists:
                                log_info(f"Latest snapshot already exists on target for {dataset}, skipping")
                                continue
                            
                            # Find common snapshot for incremental backup
                            common_snapshot = None
                            for src_snap in reversed(snapshots[:-1]):
                                src_snap_name = src_snap.split('@')[1]
                                for target_snap in target_snapshots:
                                    if '@' in target_snap and target_snap.split('@')[1] == src_snap_name:
                                        common_snapshot = src_snap
                                        break
                                if common_snapshot:
                                    break
                            
                            if common_snapshot:
                                log_info(f"Performing incremental backup from {common_snapshot} to {latest_snapshot}")
                                send_cmd = ["pkexec", "zfs", "send", "-i", common_snapshot, latest_snapshot]
                                receive_cmd = ["pkexec", "zfs", "receive", "-F", target_pool]
                                backup_type = "incremental"
                            else:
                                log_info(f"No common snapshots found, performing full backup of {latest_snapshot}")
                                send_cmd = ["pkexec", "zfs", "send", latest_snapshot]
                                receive_cmd = ["pkexec", "zfs", "receive", "-F", target_pool]
                                backup_type = "full"
                        else:
                            log_info(f"Target pool not found or no snapshots, performing full backup of {latest_snapshot}")
                            send_cmd = ["pkexec", "zfs", "send", latest_snapshot]
                            receive_cmd = ["pkexec", "zfs", "receive", "-F", target_pool]
                            backup_type = "full"
                        
                        # Execute the send/receive
                        send_process = subprocess.Popen(send_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        receive_process = subprocess.Popen(receive_cmd, stdin=send_process.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        send_process.stdout.close()
                        receive_out, receive_err = receive_process.communicate()
                        send_out, send_err = send_process.communicate()
                        
                        if send_process.returncode != 0:
                            error_msg = f"Error in send operation: {send_err.decode('utf-8')}"
                            log_error(error_msg)
                            logger.log_backup_operation(dataset, latest_snapshot.split('@')[1], target_pool, backup_type, False, {'error': error_msg})
                            backup_error_count += 1
                        elif receive_process.returncode != 0:
                            error_msg = f"Error in receive operation: {receive_err.decode('utf-8')}"
                            log_error(error_msg)
                            logger.log_backup_operation(dataset, latest_snapshot.split('@')[1], target_pool, backup_type, False, {'error': error_msg})
                            backup_error_count += 1
                        else:
                            log_success(f"Successfully backed up {latest_snapshot} to {target_pool}")
                            logger.log_backup_operation(dataset, latest_snapshot.split('@')[1], target_pool, backup_type, True)
                            backup_success_count += 1
                            
                    except Exception as e:
                        error_msg = f"Error backing up {dataset}: {str(e)}"
                        log_error(error_msg)
                        errors.append(error_msg)
                        backup_error_count += 1
                
                log_info(f"Backup completed: {backup_success_count} successful, {backup_error_count} failed")
            else:
                log_warning("External backup enabled but no target pool configured")
        
        # End operation tracking
        if error_count == 0 and len(errors) == 0:
            log_success(f"Scheduled {interval} snapshot operation completed successfully")
            logger.end_operation(operation_id, True, {
                'snapshots_created': success_count,
                'message': f"Successfully created {success_count} {interval} snapshots"
            })
        else:
            log_warning(f"Scheduled {interval} snapshot operation completed with errors")
            logger.end_operation(operation_id, False, {
                'snapshots_created': success_count,
                'errors': error_count,
                'error_messages': errors
            })
    
    except Exception as e:
        error_msg = f"Error creating {interval} snapshot: {str(e)}"
        log_error(error_msg)
        if 'operation_id' in locals():
            logger.end_operation(operation_id, False, {'error': error_msg})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: zfs-assistant-systemd.py <interval>")
        sys.exit(1)
    
    interval = sys.argv[1]
    create_scheduled_snapshot(interval)
"""
            # Write the script using elevated permissions
            script_path = SYSTEMD_SCRIPT_PATH
              # Create a temporary file first
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as temp_file:
                temp_file.write(script_content)
                temp_path = temp_file.name
            
            try:
                # Copy the temporary file to the system location with elevated permissions
                subprocess.run(['pkexec', 'cp', temp_path, script_path], check=True, capture_output=True)
                # Make the script executable
                subprocess.run(['pkexec', 'chmod', '755', script_path], check=True, capture_output=True)
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
            
            # Create systemd service directory if it doesn't exist
            user_systemd_dir = os.path.expanduser("~/.config/systemd/user")
            os.makedirs(user_systemd_dir, exist_ok=True)
            
            # Define the base service file content
            service_content = """[Unit]
Description=ZFS Snapshot %i Job
After=zfs.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/zfs-assistant-systemd.py %i
"""
            # Write the service file
            service_path = os.path.join(user_systemd_dir, "zfs-snapshot@.service")
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            # Remove any existing timer files
            timer_files = [
                "zfs-snapshot-hourly.timer",
                "zfs-snapshot-daily.timer",
                "zfs-snapshot-weekly.timer",
                "zfs-snapshot-monthly.timer"
            ]
            
            for timer_file in timer_files:
                timer_path = os.path.join(user_systemd_dir, timer_file)
                if os.path.exists(timer_path):
                    os.remove(timer_path)
              # Define timer templates
            timer_templates = {
                "hourly": {
                    "filename": "zfs-snapshot-hourly.timer",
                    "description": "Take hourly ZFS snapshots",
                    "oncalendar": "*-*-* *:00:00"  # This will be overridden for custom hours
                },
                "daily": {
                    "filename": "zfs-snapshot-daily.timer",
                    "description": "Take daily ZFS snapshots",
                    "oncalendar": "*-*-* 00:00:00"  # This will be overridden for custom days
                },
                "weekly": {
                    "filename": "zfs-snapshot-weekly.timer",
                    "description": "Take weekly ZFS snapshots",
                    "oncalendar": "Mon *-*-* 00:00:00"
                },
                "monthly": {
                    "filename": "zfs-snapshot-monthly.timer",
                    "description": "Take monthly ZFS snapshots",
                    "oncalendar": "*-*-01 00:00:00"
                }
            }
              # Create needed timer files
            for interval, enabled in schedules.items():
                if enabled and interval in timer_templates:
                    template = timer_templates[interval]
                      # Handle multi-hourly schedule
                    if interval == "hourly" and "hourly_schedule" in self.config and self.config["hourly_schedule"]:
                        # Create separate timer for each selected hour
                        selected_hours = self.config["hourly_schedule"]
                        
                        # If no hours are selected but hourly is enabled, use all hours as fallback
                        if not selected_hours:
                            selected_hours = list(range(24))
                        
                        # Remove any existing hourly timer
                        hourly_timer_path = os.path.join(user_systemd_dir, template["filename"])
                        if os.path.exists(hourly_timer_path):
                            os.remove(hourly_timer_path)
                        
                        # Remove existing numbered hourly timers
                        for i in range(24):
                            numbered_timer = f"zfs-snapshot-hourly-{i:02d}.timer"
                            numbered_timer_path = os.path.join(user_systemd_dir, numbered_timer)
                            if os.path.exists(numbered_timer_path):
                                os.remove(numbered_timer_path)
                        
                        # Create new timers for each selected hour
                        for hour in selected_hours:
                            hour_timer_name = f"zfs-snapshot-hourly-{hour:02d}.timer"
                            hour_timer_content = f"""[Unit]
Description=Take hourly ZFS snapshot at {hour:02d}:00

[Timer]
OnCalendar=*-*-* {hour:02d}:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
                            hour_timer_path = os.path.join(user_systemd_dir, hour_timer_name)
                            with open(hour_timer_path, 'w') as f:
                                f.write(hour_timer_content)
                                
                            # Enable and start the timer
                            subprocess.run(['systemctl', '--user', 'enable', hour_timer_name], check=True)
                            subprocess.run(['systemctl', '--user', 'start', hour_timer_name], check=True)
                          # Handle multi-daily schedule
                    elif interval == "daily" and "daily_schedule" in self.config and self.config["daily_schedule"]:
                        # Create separate timer for each selected day
                        selected_days = self.config["daily_schedule"]
                        
                        # If no days are selected but daily is enabled, use all days as fallback
                        if not selected_days:
                            selected_days = list(range(7))
                        
                        # Days of the week in systemd format
                        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                        
                        # Remove any existing daily timer
                        daily_timer_path = os.path.join(user_systemd_dir, template["filename"])
                        if os.path.exists(daily_timer_path):
                            os.remove(daily_timer_path)
                        
                        # Remove existing numbered daily timers
                        for i in range(7):
                            numbered_timer = f"zfs-snapshot-daily-{days_of_week[i]}.timer"
                            numbered_timer_path = os.path.join(user_systemd_dir, numbered_timer)
                            if os.path.exists(numbered_timer_path):
                                os.remove(numbered_timer_path)
                        
                        # Create new timers for each selected day
                        for day_idx in selected_days:
                            if 0 <= day_idx < 7:  # Safety check                                day_name = days_of_week[day_idx]
                                daily_hour = self.config.get("daily_hour", 0)
                                day_timer_name = f"zfs-snapshot-daily-{day_name}.timer"
                                day_timer_content = f"""[Unit]
Description=Take daily ZFS snapshot on {day_name}days at {daily_hour:02d}:00

[Timer]
OnCalendar={day_name} *-*-* {daily_hour:02d}:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
                                day_timer_path = os.path.join(user_systemd_dir, day_timer_name)
                                with open(day_timer_path, 'w') as f:
                                    f.write(day_timer_content)
                                    
                                # Enable and start the timer
                                subprocess.run(['systemctl', '--user', 'enable', day_timer_name], check=True)
                                subprocess.run(['systemctl', '--user', 'start', day_timer_name], check=True)
                    
                    # Handle regular weekly and monthly timers
                    else:
                        timer_content = f"""[Unit]
Description={template["description"]}

[Timer]
OnCalendar={template["oncalendar"]}
Persistent=true

[Install]
WantedBy=timers.target
"""
                        timer_path = os.path.join(user_systemd_dir, template["filename"])
                        with open(timer_path, 'w') as f:
                            f.write(timer_content)
                            
                        # Enable and start the regular timer
                        subprocess.run(['systemctl', '--user', 'enable', template["filename"]], check=True)
                        subprocess.run(['systemctl', '--user', 'start', template["filename"]], check=True)
                
                elif not enabled and interval in timer_templates:
                    # Disable and stop timers for disabled schedules
                    template = timer_templates[interval]
                    
                    if interval == "hourly":
                        # Stop and disable all hourly timers
                        for i in range(24):
                            hour_timer_name = f"zfs-snapshot-hourly-{i:02d}.timer"
                            try:
                                subprocess.run(['systemctl', '--user', 'stop', hour_timer_name], check=False)
                                subprocess.run(['systemctl', '--user', 'disable', hour_timer_name], check=False)
                            except:
                                pass  # Ignore errors
                    
                    elif interval == "daily":
                        # Stop and disable all daily timers
                        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                        for day_name in days_of_week:
                            day_timer_name = f"zfs-snapshot-daily-{day_name}.timer"
                            try:
                                subprocess.run(['systemctl', '--user', 'stop', day_timer_name], check=False)
                                subprocess.run(['systemctl', '--user', 'disable', day_timer_name], check=False)
                            except:
                                pass  # Ignore errors
                    
                    # Also stop and disable the main timer
                    try:
                        subprocess.run(['systemctl', '--user', 'stop', template["filename"]], check=False)
                        subprocess.run(['systemctl', '--user', 'disable', template["filename"]], check=False)
                    except:
                        pass  # Ignore errors
            
            # Reload systemd user daemon
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
            
            return True, "Systemd timers set up successfully"
        except Exception as e:
            return False, f"Error setting up systemd timers: {e}"
    
    def send_snapshot(self, snapshot_full_name, target_pool, incremental_snapshot=None):
        """
        Send a ZFS snapshot to another pool using zfs send/receive
        
        Args:
            snapshot_full_name: Full name of the snapshot to send (dataset@snapshot)
            target_pool: Name of the target pool to receive the snapshot
            incremental_snapshot: Optional base snapshot for incremental send
            
        Returns:
            (success, message) tuple
        """
        try:
            # Parse dataset and snapshot name for logging
            dataset, snapshot_name = snapshot_full_name.split('@', 1)
            
            backup_type = "incremental" if incremental_snapshot else "full"
            log_info(f"Starting {backup_type} backup: {snapshot_full_name} to {target_pool}", {
                'source_dataset': dataset,
                'snapshot_name': snapshot_name,
                'source_full_name': snapshot_full_name,
                'target_pool': target_pool,
                'backup_type': backup_type,
                'incremental_base': incremental_snapshot,
                'operation': 'send_receive'
            })
            
            # Start operation tracking
            operation_id = self.logger.start_operation(OperationType.ZFS_BACKUP, {
                'source_snapshot': snapshot_full_name,
                'target_pool': target_pool,
                'backup_type': backup_type,
                'incremental_base': incremental_snapshot
            })
            
            # Build the command
            if incremental_snapshot:
                # Incremental send
                send_cmd = ['zfs', 'send', '-i', incremental_snapshot, snapshot_full_name]
                log_info(f"Using incremental base: {incremental_snapshot}")
            else:
                # Full send
                send_cmd = ['zfs', 'send', snapshot_full_name]
                
            receive_cmd = ['zfs', 'receive', '-F', target_pool]
            self.logger.log_system_command(' '.join(['pkexec'] + send_cmd), True)
            self.logger.log_system_command(' '.join(['pkexec'] + receive_cmd), True)
            
            # Use cached pkexec authorization for both commands
            success, _ = self.run_pkexec_command(['true'])
            if not success:
                error_msg = "Failed to obtain administrative privileges for ZFS send/receive operation"
                log_error(error_msg)
                self.logger.end_operation(operation_id, False, {'error': error_msg})
                return False, error_msg
                
            # Execute send command with pipe to receive command
            send_process = subprocess.Popen(
                ['pkexec'] + send_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            receive_process = subprocess.Popen(
                ['pkexec'] + receive_cmd,
                stdin=send_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Close the pipe in the send process
            send_process.stdout.close()
            
            # Get output and errors
            receive_stdout, receive_stderr = receive_process.communicate()
            send_stdout, send_stderr = send_process.communicate()
            
            # Check return codes
            if send_process.returncode != 0:
                error_msg = f"Error in send operation: {send_stderr.decode('utf-8')}"
                log_error(error_msg, {
                    'command': ' '.join(['pkexec'] + send_cmd),
                    'return_code': send_process.returncode,
                    'stderr': send_stderr.decode('utf-8')
                })
                self.logger.end_operation(operation_id, False, {'error': error_msg})
                return False, error_msg
                
            if receive_process.returncode != 0:
                error_msg = f"Error in receive operation: {receive_stderr.decode('utf-8')}"
                log_error(error_msg, {
                    'command': ' '.join(['pkexec'] + receive_cmd),
                    'return_code': receive_process.returncode,
                    'stderr': receive_stderr.decode('utf-8')
                })
                self.logger.end_operation(operation_id, False, {'error': error_msg})
                return False, error_msg
            
            # Log successful backup    
            success_msg = f"Successfully sent snapshot {snapshot_full_name} to {target_pool}"
            log_success(success_msg, {
                'source_dataset': dataset,
                'snapshot_name': snapshot_name,
                'target_pool': target_pool,
                'backup_type': backup_type
            })
            
            self.logger.log_backup_operation(dataset, snapshot_name, target_pool, backup_type, True, {
                'incremental_base': incremental_snapshot
            })
            self.logger.end_operation(operation_id, True, {'message': success_msg})
            
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error during ZFS send/receive: {str(e)}"
            log_error(error_msg, {
                'snapshot_full_name': snapshot_full_name,
                'target_pool': target_pool,
                'incremental_snapshot': incremental_snapshot,
                'exception': str(e)
            })
            if 'operation_id' in locals():
                self.logger.end_operation(operation_id, False, {'error': error_msg})
            return False, error_msg
    
    def get_latest_common_snapshot(self, source_dataset, target_pool):
        """
        Find the latest snapshot that exists in both the source dataset and target pool
        for incremental send/receive operations
        
        Args:
            source_dataset: Source dataset name
            target_pool: Target pool name
            
        Returns:
            The name of the latest common snapshot, or None if no common snapshots exist
        """
        try:
            # Get snapshots from source dataset
            source_snapshots = self.get_snapshots(source_dataset)
            source_snapshot_names = {snapshot.name: snapshot for snapshot in source_snapshots}
            
            # Get snapshots from target pool
            target_snapshots = self.get_snapshots(target_pool)
            target_snapshot_names = {snapshot.name: snapshot for snapshot in target_snapshots}
            
            # Find common snapshots
            common_names = set(source_snapshot_names.keys()) & set(target_snapshot_names.keys())
            
            if not common_names:
                return None
                
            # Get the latest common snapshot by creation date
            latest = None
            latest_date = datetime.datetime.min
            
            for name in common_names:
                source_snap = source_snapshot_names[name]
                if isinstance(source_snap.creation_date, datetime.datetime) and source_snap.creation_date > latest_date:
                    latest = source_snap
                    latest_date = source_snap.creation_date
                    
            return latest.full_name if latest else None
            
        except Exception as e:
            print(f"Error finding common snapshots: {e}")
            return None
            
    def perform_backup(self, dataset, target_pool):
        """
        Perform a backup of the specified dataset to the target pool
        
        Args:
            dataset: Dataset to back up
            target_pool: Target pool to receive the backup
            
        Returns:
            (success, message) tuple
        """
        try:
            # Check if target pool exists
            try:
                subprocess.run(['zfs', 'list', target_pool], 
                              check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                return False, f"Target pool '{target_pool}' does not exist or is not accessible"
                
            # Get the latest snapshot for the dataset
            snapshots = self.get_snapshots(dataset)
            if not snapshots:
                return False, f"No snapshots found for dataset {dataset}"
                
            # Sort snapshots by creation date (newest first)
            sorted_snapshots = sorted(
                snapshots, 
                key=lambda x: x.creation_date if isinstance(x.creation_date, datetime.datetime) else datetime.datetime.min,
                reverse=True
            )
            
            latest_snapshot = sorted_snapshots[0]
            
            # Try to find a common snapshot for incremental send
            common_snapshot = self.get_latest_common_snapshot(dataset, target_pool)
            
            if common_snapshot:
                # If latest snapshot is already in the target pool, nothing to do
                if common_snapshot == latest_snapshot.full_name:
                    return True, f"Latest snapshot {latest_snapshot.full_name} already exists in target pool"
                
                # Perform incremental send
                return self.send_snapshot(latest_snapshot.full_name, target_pool, common_snapshot)
            else:
                # Perform full send
                return self.send_snapshot(latest_snapshot.full_name, target_pool)
                
        except Exception as e:
            return False, f"Error performing backup: {str(e)}"
    


    def run_system_update(self):
        """
        Run system update using pacman -Syu
        
        Returns:
            (success, message) tuple
        """
        try:
            log_info("Starting system update", {'command': 'pacman -Syu --noconfirm'})
            
            # Use cached pkexec authorization
            success, result = self.run_pkexec_command(['pacman', '-Syu', '--noconfirm'])
            
            if not success:
                error_msg = f"System update failed: {result}"
                log_error(error_msg, {'command_output': result})
                self.logger.log_system_command(['pacman', '-Syu', '--noconfirm'], False, error=result)
                return False, error_msg
            
            success_msg = "System update completed successfully"
            log_success(success_msg)
            self.logger.log_system_command(['pacman', '-Syu', '--noconfirm'], True)
            return True, success_msg
        except Exception as e:
            error_msg = f"Error during system update: {str(e)}"
            log_error(error_msg, {'exception': str(e)})
            return False, error_msg
    
    def clean_package_cache(self):
        """
        Clean package cache using pacman -Scc
        
        Returns:
            (success, message) tuple
        """
        try:
            log_info("Starting package cache cleanup", {'command': 'pacman -Scc --noconfirm'})
            
            # Use cached pkexec authorization
            success, result = self.run_pkexec_command(['pacman', '-Scc', '--noconfirm'])
            
            if not success:
                error_msg = f"Cache cleaning failed: {result}"
                log_error(error_msg, {'command_output': result})
                self.logger.log_system_command(['pacman', '-Scc', '--noconfirm'], False, error=result)
                return False, error_msg
            
            success_msg = "Package cache cleaned successfully"
            log_success(success_msg)
            self.logger.log_system_command(['pacman', '-Scc', '--noconfirm'], True)
            return True, success_msg
        except Exception as e:
            error_msg = f"Error during cache cleaning: {str(e)}"
            log_error(error_msg, {'exception': str(e)})
            return False, error_msg
    
    def remove_orphaned_packages(self):
        """
        Remove orphaned packages using pacman -Qtdq | pacman -Rns
        
        Returns:
            (success, message) tuple
        """
        try:
            log_info("Starting orphaned package removal")
            
            # First, get orphaned packages
            result = subprocess.run(['pacman', '-Qtdq'], capture_output=True, text=True, check=False)
            
            if result.returncode != 0 or not result.stdout.strip():
                success_msg = "No orphaned packages found"
                log_info(success_msg)
                return True, success_msg
            
            orphaned_packages = result.stdout.strip().split('\n')
            if not orphaned_packages or orphaned_packages == ['']:
                success_msg = "No orphaned packages found"
                log_info(success_msg)
                return True, success_msg
            
            log_info(f"Found {len(orphaned_packages)} orphaned packages", {
                'orphaned_packages': orphaned_packages
            })
            
            # Remove orphaned packages
            cmd = ['pacman', '-Rns', '--noconfirm'] + orphaned_packages
            success, result = self.run_pkexec_command(cmd)
            
            if not success:
                error_msg = f"Failed to remove orphaned packages: {result}"
                log_error(error_msg, {
                    'orphaned_packages': orphaned_packages,
                    'command_output': result
                })
                self.logger.log_system_command(cmd, False, error=result)
                return False, error_msg
            
            success_msg = f"Removed {len(orphaned_packages)} orphaned package(s)"
            log_success(success_msg, {'orphaned_packages': orphaned_packages})
            self.logger.log_system_command(cmd, True)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error removing orphaned packages: {str(e)}"
            log_error(error_msg, {'exception': str(e)})
            return False, error_msg
    
    def perform_system_maintenance(self, create_snapshot_before=True, run_update=True, clean_cache=True, remove_orphans=True):
        """
        Perform comprehensive system maintenance including snapshots, updates, and cleanup
        
        Args:
            create_snapshot_before: Whether to create snapshots before updates
            run_update: Whether to run system update
            clean_cache: Whether to clean package cache
            remove_orphans: Whether to remove orphaned packages
            
        Returns:
            (success, message) tuple with detailed results
        """
        try:
            log_info("Starting comprehensive system maintenance", {
                'create_snapshots': create_snapshot_before,
                'run_update': run_update,
                'clean_cache': clean_cache,
                'remove_orphans': remove_orphans,
                'operation': 'system_maintenance'
            })
            
            # Start operation tracking
            operation_id = self.logger.start_operation(OperationType.SYSTEM_MAINTENANCE, {
                'create_snapshots': create_snapshot_before,
                'run_update': run_update,
                'clean_cache': clean_cache,
                'remove_orphans': remove_orphans
            })
            
            results = []
            overall_success = True
            
            # Get managed datasets
            datasets = self.config.get("datasets", [])
            if not datasets and create_snapshot_before:
                error_msg = "No datasets configured for snapshots"
                log_error(error_msg)
                self.logger.end_operation(operation_id, False, {'error': error_msg})
                return False, error_msg
            
            # Step 1: Create pre-update snapshots if requested
            if create_snapshot_before:
                results.append("=== Pre-Update Snapshots ===")
                log_info("Creating pre-update snapshots", {'datasets': datasets})
                snapshot_success = 0
                snapshot_errors = 0
                
                timestamp = get_timestamp()
                prefix = self.config.get("prefix", "zfs-assistant")
                
                for dataset in datasets:
                    snapshot_name = f"{prefix}-sysupdate-{timestamp}"
                    success, message = self.create_snapshot(dataset, snapshot_name)
                    if success:
                        snapshot_success += 1
                        results.append(f"✓ Created snapshot for {dataset}: {snapshot_name}")
                    else:
                        snapshot_errors += 1
                        overall_success = False
                        results.append(f"✗ Failed snapshot for {dataset}: {message}")
                
                log_info(f"Pre-update snapshots completed: {snapshot_success} successful, {snapshot_errors} failed")
                results.append(f"Snapshots: {snapshot_success} successful, {snapshot_errors} failed")
                results.append("")
            
            # Step 2: Remove orphaned packages if requested
            if remove_orphans:
                results.append("=== Orphaned Package Cleanup ===")
                log_info("Starting orphaned package cleanup")
                success, message = self.remove_orphaned_packages()
                if success:
                    results.append(f"✓ {message}")
                    log_success(f"Orphaned package cleanup completed: {message}")
                else:
                    overall_success = False
                    results.append(f"✗ {message}")
                    log_error(f"Orphaned package cleanup failed: {message}")
                results.append("")
            
            # Step 3: Run system update if requested
            if run_update:
                results.append("=== System Update ===")
                log_info("Starting system update")
                success, message = self.run_system_update()
                if success:
                    results.append(f"✓ {message}")
                    log_success(f"System update completed: {message}")
                else:
                    overall_success = False
                    results.append(f"✗ {message}")
                    log_error(f"System update failed: {message}")
                results.append("")
            
            # Step 4: Clean package cache if requested
            if clean_cache:
                results.append("=== Package Cache Cleanup ===")
                log_info("Starting package cache cleanup")
                success, message = self.clean_package_cache()
                if success:
                    results.append(f"✓ {message}")
                    log_success(f"Package cache cleanup completed: {message}")
                else:
                    overall_success = False
                    results.append(f"✗ {message}")
                    log_error(f"Package cache cleanup failed: {message}")
                results.append("")
            
            # Step 5: Run backup if configured and snapshots were created
            if create_snapshot_before and self.config.get("external_backup_enabled", False):
                backup_frequency = self.config.get("backup_frequency", "Manual")
                if backup_frequency == "Follow snapshot schedule" or backup_frequency == "After system updates":
                    results.append("=== External Backup ===")
                    log_info("Starting external backup")
                    success, message = self.run_scheduled_backup()
                    if success:
                        results.append(f"✓ Backup completed successfully")
                        log_success("External backup completed successfully")
                        # Add detailed backup messages
                        for line in message.split('\n')[1:]:  # Skip the summary line
                            if line.strip():
                                results.append(f"  {line}")
                    else:
                        results.append(f"✗ Backup failed: {message}")
                        log_error(f"External backup failed: {message}")
                    results.append("")
            
            final_message = "\n".join(results)
            status = "System maintenance completed successfully" if overall_success else "System maintenance completed with errors"
            
            # Log final results
            if overall_success:
                log_success(status, {'details': final_message})
                self.logger.end_operation(operation_id, True, {'message': status, 'details': final_message})
            else:
                log_warning(status, {'details': final_message})
                self.logger.end_operation(operation_id, False, {'message': status, 'details': final_message})
            
            return overall_success, f"{status}\n\n{final_message}"
            
        except Exception as e:
            error_msg = f"Error during system maintenance: {str(e)}"
            log_error(error_msg, {'exception': str(e)})
            if 'operation_id' in locals():
                self.logger.end_operation(operation_id, False, {'error': error_msg})
            return False, error_msg
    
    def create_system_update_snapshot(self, snapshot_type="sysupdate"):
        """
        Create snapshots for all managed datasets before system updates
        
        Args:
            snapshot_type: Type identifier for the snapshot (default: "sysupdate")
            
        Returns:
            (success, message) tuple
        """
        try:
            datasets = self.config.get("datasets", [])
            if not datasets:
                return False, "No datasets configured for snapshots"
            
            timestamp = get_timestamp()
            prefix = self.config.get("prefix", "zfs-assistant")
            
            success_count = 0
            error_count = 0
            messages = []
            
            for dataset in datasets:
                snapshot_name = f"{prefix}-{snapshot_type}-{timestamp}"
                success, message = self.create_snapshot(dataset, snapshot_name)
                
                if success:
                    success_count += 1
                    messages.append(f"✓ {dataset}: {snapshot_name}")
                else:
                    error_count += 1
                    messages.append(f"✗ {dataset}: {message}")
            
            summary = f"Created {success_count} snapshots"
            if error_count > 0:
                summary += f", {error_count} errors"
                
            detailed_message = summary + "\n" + "\n".join(messages)
            
            return success_count > 0, detailed_message
            
        except Exception as e:
            return False, f"Error creating system update snapshots: {str(e)}"

    def run_scheduled_backup(self):
        """
        Run scheduled backup operations based on configuration
        
        Returns:
            (success, message) tuple
        """
        if not self.config.get("external_backup_enabled", False):
            return True, "External backup is disabled in configuration"
            
        external_pool = self.config.get("external_pool_name", "")
        if not external_pool:
            return False, "No external pool configured for backup"
            
        try:
            # Get all managed datasets
            datasets = self.config.get("datasets", [])
            if not datasets:
                return False, "No datasets configured for backup"
                
            success_count = 0
            error_count = 0
            messages = []
            
            for dataset in datasets:
                # Perform backup for this dataset
                success, message = self.perform_backup(dataset, external_pool)
                
                if success:
                    success_count += 1
                    messages.append(f"✓ {dataset}: {message}")
                else:
                    error_count += 1
                    messages.append(f"✗ {dataset}: {message}")
            
            summary = f"Backup completed: {success_count} successful"
            if error_count > 0:
                summary += f", {error_count} errors"
                
            detailed_message = summary + "\n" + "\n".join(messages)
            
            return success_count > 0, detailed_message
            
        except Exception as e:
            return False, f"Error during scheduled backup: {str(e)}"
