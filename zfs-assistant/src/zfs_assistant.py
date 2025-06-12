#!/usr/bin/env python3
# ZFS Assistant - Main Coordinator Class
# Author: GitHub Copilot
# Refactored to use modular architecture

import os
import json
from pathlib import Path

# Try relative imports first, fall back to absolute imports if run as a script
try:    from .common import (
        CONFIG_DIR, CONFIG_FILE, LOG_FILE, PACMAN_HOOK_PATH, 
        SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
        DEFAULT_CONFIG, get_timestamp
    )
    from .models import ZFSSnapshot
    from .logger import (
        ZFSLogger, OperationType, LogLevel, get_logger,
        log_info, log_error, log_success, log_warning
    )
    from .privilege_manager import PrivilegeManager
    from .zfs_core import ZFSCore
    from .zfs_backup import ZFSBackup
    from .system_integration import SystemIntegration
    from .system_maintenance import SystemMaintenance
except ImportError:
    # For direct script execution
    import sys
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    try:
        # Try with src as a direct submodule        from src.common import (
            CONFIG_DIR, CONFIG_FILE, LOG_FILE, PACMAN_HOOK_PATH, 
            SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
            DEFAULT_CONFIG, get_timestamp
        )
        from src.models import ZFSSnapshot
        from src.logger import (
            ZFSLogger, OperationType, LogLevel, get_logger,
            log_info, log_error, log_success, log_warning
        )
        from src.privilege_manager import PrivilegeManager
        from src.zfs_core import ZFSCore
        from src.zfs_backup import ZFSBackup
        from src.system_integration import SystemIntegration
        from src.system_maintenance import SystemMaintenance
    except ImportError:
        # Last resort, use direct file paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)        from common import (
            CONFIG_DIR, CONFIG_FILE, LOG_FILE, PACMAN_HOOK_PATH, 
            SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
            DEFAULT_CONFIG, get_timestamp
        )
        from models import ZFSSnapshot
        from logger import (
            ZFSLogger, OperationType, LogLevel, get_logger,
            log_info, log_error, log_success, log_warning
        )
        from privilege_manager import PrivilegeManager
        from zfs_core import ZFSCore
        from zfs_backup import ZFSBackup
        from system_integration import SystemIntegration
        from system_maintenance import SystemMaintenance


class ZFSAssistant:
    """
    Main coordinator class for ZFS Assistant.
    This class delegates operations to specialized modules for better maintainability.
    """
    
    def __init__(self):
        """Initialize ZFS Assistant with all specialized modules"""
        # Basic configuration
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self.pacman_hook_path = PACMAN_HOOK_PATH
        self.default_config = DEFAULT_CONFIG
        self.config = self.load_config()
        
        # Initialize logger
        self.logger = get_logger()
        
        # Initialize specialized modules
        self.privilege_manager = PrivilegeManager()
        self.zfs_core = ZFSCore(self.privilege_manager, self.config)
        self.zfs_backup = ZFSBackup(self.privilege_manager, self.config)
        self.system_integration = SystemIntegration(self.privilege_manager, self.config)
        self.system_maintenance = SystemMaintenance(self.privilege_manager, self.config)
        
        log_info("ZFS Assistant initialized with modular architecture", {
            'config_dir': str(self.config_dir),
            'config_file': str(self.config_file),
            'managed_datasets': self.config.get('datasets', []),
            'auto_snapshot_enabled': self.config.get('auto_snapshot', True),
            'pacman_integration_enabled': self.config.get('pacman_integration', True)
        })
    
    # ==================== Configuration Management ====================
    
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
            log_error(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Update config in all modules
            self.zfs_core.update_config(self.config)
            self.zfs_backup.update_config(self.config)
            self.system_integration.update_config(self.config)
            self.system_maintenance.update_config(self.config)
            
            return True
        except Exception as e:
            log_error(f"Error saving config: {e}")
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
    
    # ==================== ZFS Dataset Operations ====================
    
    def get_datasets(self):
        """Get available ZFS datasets with their properties"""
        return self.zfs_core.get_datasets()
    
    def get_dataset_properties(self, dataset_name):
        """Get properties for a specific dataset"""
        return self.zfs_core.get_dataset_properties(dataset_name)
    
    def get_snapshots(self, dataset):
        """Get all snapshots for a dataset"""
        return self.zfs_core.get_snapshots(dataset)
    
    # ==================== Snapshot Operations ====================
    
    def create_snapshot(self, dataset, name=None):
        """Create a ZFS snapshot for the specified dataset"""
        return self.zfs_core.create_snapshot(dataset, name)
    
    def delete_snapshot(self, snapshot_full_name):
        """Delete a ZFS snapshot"""
        return self.zfs_core.delete_snapshot(snapshot_full_name)
    
    def rollback_snapshot(self, snapshot_full_name, force=False):
        """Rollback to a ZFS snapshot"""
        return self.zfs_core.rollback_snapshot(snapshot_full_name, force)
    
    def clone_snapshot(self, snapshot_full_name, target_name):
        """Clone a ZFS snapshot to a new dataset"""
        return self.zfs_core.clone_snapshot(snapshot_full_name, target_name)
    
    def cleanup_snapshots(self):
        """Clean up snapshots based on retention policy"""
        return self.zfs_core.cleanup_snapshots()
    
    # ==================== Backup Operations ====================
    
    def send_snapshot(self, snapshot_full_name, target_pool, incremental_snapshot=None):
        """Send snapshot to target pool"""
        return self.zfs_backup.send_snapshot(snapshot_full_name, target_pool, incremental_snapshot)
    
    def get_latest_common_snapshot(self, source_dataset, target_pool):
        """Get the latest common snapshot between source and target"""
        return self.zfs_backup.get_latest_common_snapshot(source_dataset, target_pool)
    
    def perform_backup(self, dataset, target_pool):
        """Perform backup of a dataset to target pool"""
        return self.zfs_backup.perform_backup(dataset, target_pool)
    
    def run_scheduled_backup(self):
        """Run scheduled backup operations based on configuration"""
        return self.zfs_backup.run_scheduled_backup()
    
    # ==================== System Integration ====================
    
    def setup_pacman_hook(self, enabled):
        """Setup or remove pacman hook for pre-transaction snapshots"""
        return self.system_integration.setup_pacman_hook(enabled)
    
    def setup_systemd_timers(self, schedules):
        """Setup systemd timers for automated snapshots"""
        return self.system_integration.setup_systemd_timers(schedules)
    
    # ==================== System Maintenance ====================
    
    def run_system_update(self):
        """Run system update using pacman -Syu"""
        return self.system_maintenance.run_system_update()
    
    def clean_package_cache(self):
        """Clean package cache using pacman -Scc"""
        return self.system_maintenance.clean_package_cache()
    
    def remove_orphaned_packages(self):
        """Remove orphaned packages"""
        return self.system_maintenance.remove_orphaned_packages()
    
    def perform_system_maintenance(self, create_snapshot_before=True, run_update=True, 
                                   clean_cache=True, remove_orphans=True):
        """Perform comprehensive system maintenance"""
        return self.system_maintenance.perform_system_maintenance(
            create_snapshot_before, run_update, clean_cache, remove_orphans
        )
    
    def create_system_update_snapshot(self, snapshot_type="sysupdate"):
        """Create snapshots for all managed datasets before system updates"""
        return self.system_maintenance.create_system_update_snapshot(snapshot_type)
    
    # ==================== Legacy/Compatibility Methods ====================
    
    def run_pkexec_command(self, cmd):
        """Legacy method for running privileged commands - delegates to PrivilegeManager.
        This method is maintained for backwards compatibility.
        New code should use PrivilegeManager directly."""
        return self.privilege_manager.run_pkexec_command(cmd)
    
    def run_batch_pkexec_commands(self, commands):
        """Legacy method for running multiple privileged commands - delegates to PrivilegeManager.
        This method is maintained for backwards compatibility.
        New code should use PrivilegeManager directly."""
        return self.privilege_manager.run_batch_pkexec_commands(commands)
    
    def create_batch_snapshots(self, datasets, snapshot_name):
        """Create snapshots for multiple datasets in a single batch operation"""
        return self.zfs_core.create_batch_snapshots(datasets, snapshot_name)


# ==================== Legacy Functions for Compatibility ====================

# These functions maintain compatibility with existing systemd scripts and pacman hooks

def create_pre_pacman_snapshot():
    """Legacy function for pacman hook compatibility"""
    try:
        # Use the system integration module for pacman hook operations
        from .system_integration import SystemIntegration
        from .privilege_manager import PrivilegeManager
        
        # Load config
        config_file = os.path.expanduser("~/.config/zfs-assistant/config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = DEFAULT_CONFIG
        
        # Create managers
        privilege_manager = PrivilegeManager()
        
        # Create snapshots using the ZFS core module
        from .zfs_core import ZFSCore
        zfs_core = ZFSCore(privilege_manager, config)
        
        datasets = config.get("datasets", [])
        if not datasets:
            log_error("No datasets configured for snapshots")
            return
        
        timestamp = get_timestamp()
        prefix = config.get("prefix", "zfs-assistant")
          # Build batch commands for all datasets
        snapshot_commands = []
        snapshot_name = f"{prefix}-pkgop-{timestamp}"
        
        for dataset in datasets:
            snapshot_full_name = f"{dataset}@{snapshot_name}"
            snapshot_commands.append(['zfs', 'snapshot', snapshot_full_name])
        
        # Execute all snapshot creation commands in batch to reduce pkexec prompts
        log_info(f"Creating snapshots for {len(datasets)} datasets in batch")
        success, batch_result = privilege_manager.run_batch_privileged_commands(snapshot_commands)
        
        if success:
            log_success(f"Created {len(datasets)} pre-pacman snapshots successfully")
        else:
            log_error(f"Batch snapshot creation failed: {batch_result}")
            # Log individual failures for troubleshooting
            for dataset in datasets:
                log_error(f"Failed to create snapshot for {dataset} as part of batch operation")
            
    except Exception as e:
        log_error(f"Error in pacman hook script: {str(e)}")


def create_scheduled_snapshot(interval):
    """Legacy function for systemd timer compatibility"""
    try:
        # Load config
        config_file = os.path.expanduser("~/.config/zfs-assistant/config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            log_error(f"Configuration file not found: {config_file}")
            return
        
        # Create ZFS Assistant instance and delegate to ZFS core
        privilege_manager = PrivilegeManager()
        zfs_core = ZFSCore(privilege_manager, config)
        
        # Create scheduled snapshot
        success, message = zfs_core.create_scheduled_snapshot(interval)
        if success:
            log_success(f"Scheduled {interval} snapshot completed: {message}")
        else:
            log_error(f"Scheduled {interval} snapshot failed: {message}")
            
    except Exception as e:
        log_error(f"Error creating {interval} snapshot: {str(e)}")


# Entry point for systemd script compatibility
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: zfs-assistant-systemd.py <interval>")
        sys.exit(1)
    
    interval = sys.argv[1]
    create_scheduled_snapshot(interval)
