#!/usr/bin/env python3
# ZFS Assistant - System Integration (Pacman Hooks & Systemd Timers)
# Author: GitHub Copilot

import os
import subprocess
import tempfile
import glob
import json
import datetime
from typing import Dict, List, Tuple

# Handle imports for both relative and direct execution
try:
    from ..utils.logger import (
        OperationType, get_logger,
        log_info, log_error, log_success, log_warning
    )
    from ..utils.common import (
        CONFIG_DIR, CONFIG_FILE, SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
        PACMAN_HOOK_PATH, run_command, get_timestamp
    )
except ImportError:
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from utils.logger import (
        OperationType, get_logger,
        log_info, log_error, log_success, log_warning
    )
    from utils.common import (
        CONFIG_DIR, CONFIG_FILE, SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
        PACMAN_HOOK_PATH, run_command, get_timestamp
    )


class SystemIntegration:
    """Handles system integration for ZFS Assistant (Pacman hooks and systemd timers)"""
    
    def __init__(self, privilege_manager, config: dict):
        self.privilege_manager = privilege_manager
        self.config = config
        self.logger = get_logger()

    def update_config(self, config: dict):
        """Update configuration reference when settings are saved"""
        self.config = config

    def setup_systemd_timers(self, schedules: Dict[str, bool]) -> Tuple[bool, str]:
        """Setup systemd timers for automated snapshots."""
        try:
            log_info("Setting up systemd timers for automated snapshots", {
                'schedules': schedules,
                'config_daily': self.config.get("daily_schedule", []),
                'config_weekly': self.config.get("weekly_schedule", False),
                'config_monthly': self.config.get("monthly_schedule", False)
            })
            
            # Application runs with elevated privileges, use system-wide services
            log_info("Using system-wide systemd services")
            return self._setup_system_timers(schedules)
            
        except subprocess.TimeoutExpired as e:
            error_msg = f"Error setting up systemd timers (timeout): {str(e)}"
            log_error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error setting up systemd timers: {str(e)}"
            log_error(error_msg)
            return False, error_msg
    
    def _setup_system_timers(self, schedules: Dict[str, bool]) -> Tuple[bool, str]:
        """Setup system-level systemd timers when running with elevated privileges."""
        # Validate configuration before creating timers
        daily_schedule = self.config.get("daily_schedule", [])
        
        # Check if schedules are enabled but have no days selected
        if schedules.get("daily", False) and not daily_schedule:
            return False, "Daily snapshots enabled but no days selected. Please select at least one day."
        
        # Create the snapshot script in system location
        script_content = self._get_systemd_script_content()
        system_script_path = "/usr/local/bin/zfs-assistant-systemd.py"
        
        # Create script with elevated privileges
        success, result = self.privilege_manager.create_script_privileged(
            system_script_path, script_content, executable=True
        )
        if not success:
            return False, f"Error creating system script: {result}"
        
        # Ensure configuration is available in system location for systemd script
        success, result = self._ensure_system_config()
        if not success:
            log_warning(f"Could not copy config to system location: {result}")
        
        # Create system service file
        service_content = f"""[Unit]
Description=ZFS Snapshot %i Job
After=zfs.target
Wants=zfs.target
After=multi-user.target
Requires=zfs.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {system_script_path} %i
User=root
Group=root
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=/usr/local/lib/python3/dist-packages:/usr/lib/python3/dist-packages
StandardOutput=journal
StandardError=journal
TimeoutStartSec=600
KillMode=process
"""
        
        # Create service file with elevated privileges
        service_path = "/etc/systemd/system/zfs-snapshot@.service"
        success, result = self.privilege_manager.create_script_privileged(
            service_path, service_content, executable=False
        )
        if not success:
            return False, f"Error creating system service: {result}"
        
        # Clean up existing system timer files using the unified method
        self.cleanup_timer_files(include_current_timers=True)
        
        # Create new system timer files based on schedules
        try:
            self._create_optimized_system_timers(schedules)
        except Exception as e:
            return False, f"Error creating timer files: {str(e)}"
        
        # Reload systemd daemon
        success, result = self.privilege_manager.run_privileged_command(['systemctl', 'daemon-reload'])
        if not success:
            return False, f"Error reloading systemd: {result}"
        
        log_success("System systemd timers set up successfully")
        return True, "System systemd timers set up successfully"
    
    def disable_schedule(self, schedule_type: str) -> Tuple[bool, str]:
        """Disable and remove timers for a specific schedule type."""
        try:
            log_info(f"Disabling {schedule_type} schedule")
            
            # Define timer file patterns for each schedule type (system-wide)
            timer_patterns = {
                "daily": ["/etc/systemd/system/zfs-snapshot-daily.timer"], 
                "weekly": ["/etc/systemd/system/zfs-snapshot-weekly.timer"],
                "monthly": ["/etc/systemd/system/zfs-snapshot-monthly.timer"]
            }
            
            if schedule_type not in timer_patterns:
                return False, f"Unknown schedule type: {schedule_type}"
            
            # Stop, disable, and remove timer files
            removed_timers = []
            
            for pattern in timer_patterns[schedule_type]:
                for timer_file in glob.glob(pattern):
                    timer_name = os.path.basename(timer_file)
                    
                    try:
                        # Stop and disable system timer
                        self.privilege_manager.run_privileged_command(['systemctl', 'stop', timer_name])
                        self.privilege_manager.run_privileged_command(['systemctl', 'disable', timer_name])
                        
                        # Remove file
                        success, result = self.privilege_manager.remove_files_privileged([timer_file])
                        if success:
                            removed_timers.append(timer_name)
                        
                    except Exception as e:
                        log_warning(f"Error removing timer {timer_name}: {str(e)}")
            
            # Reload systemd daemon
            success, result = self.privilege_manager.run_privileged_command(['systemctl', 'daemon-reload'])
            if not success:
                log_warning(f"Failed to reload systemd daemon: {result}")
            
            if removed_timers:
                success_msg = f"Disabled {schedule_type} schedule, removed timers: {', '.join(removed_timers)}"
                log_success(success_msg)
                return True, success_msg
            else:
                return True, f"No {schedule_type} timers found to remove"
                
        except Exception as e:
            error_msg = f"Error disabling {schedule_type} schedule: {str(e)}"
            log_error(error_msg)
            return False, error_msg
    
    def get_schedule_status(self) -> Dict[str, bool]:
        """Check actual systemd timer status to determine if schedules are really active."""
        try:
            status = {
                "daily": False,
                "weekly": False,
                "monthly": False
            }
            
            # Check if system timer files exist and are active
            timer_patterns = {
                "daily": ["/etc/systemd/system/zfs-snapshot-daily.timer"],  # Single daily timer file
                "weekly": ["/etc/systemd/system/zfs-snapshot-weekly.timer"],
                "monthly": ["/etc/systemd/system/zfs-snapshot-monthly.timer"]
            }
            
            for schedule_type, patterns in timer_patterns.items():
                for pattern in patterns:
                    timer_files = glob.glob(pattern)
                    for timer_file in timer_files:
                        timer_name = os.path.basename(timer_file)
                        
                        try:
                            # Check if timer is active
                            success, result = self.privilege_manager.run_privileged_command(
                                ['systemctl', 'is-active', timer_name]
                            )
                            
                            if success and hasattr(result, 'stdout') and result.stdout.strip() == "active":
                                status[schedule_type] = True
                                break  # At least one timer of this type is active
                            elif success and isinstance(result, str) and result.strip() == "active":
                                status[schedule_type] = True
                                break  # At least one timer of this type is active
                        except:
                            continue
            
            return status
            
        except Exception as e:
            log_warning(f"Error checking schedule status: {str(e)}")
            # Fallback to config-based status if systemctl check fails
            return {
                "daily": bool(self.config.get("daily_schedule", [])),
                "weekly": bool(self.config.get("weekly_schedule", False)),
                "monthly": bool(self.config.get("monthly_schedule", False))
            }
    
    def _cleanup_existing_system_timers(self):
        """
        Clean up existing system timer files.
        Internal method called during timer setup.
        """
        timer_patterns = [
            "/etc/systemd/system/zfs-snapshot-daily.timer",  # Single daily timer file
            "/etc/systemd/system/zfs-snapshot-weekly.timer",
            "/etc/systemd/system/zfs-snapshot-monthly.timer"
        ]
        
        for pattern in timer_patterns:
            for timer_file in glob.glob(pattern):
                try:
                    timer_name = os.path.basename(timer_file)
                    # Stop and disable system timer
                    self.privilege_manager.run_privileged_command(['systemctl', 'stop', timer_name])
                    self.privilege_manager.run_privileged_command(['systemctl', 'disable', timer_name])
                    
                    # Remove file
                    self.privilege_manager.remove_files_privileged([timer_file])
                except:
                    pass

    def cleanup_timer_files(self, include_current_timers: bool = False) -> Tuple[bool, str]:
        """
        Clean up timer files that might be left from previous installations or 
        after changing schedule configurations.
        
        Args:
            include_current_timers: If True, also clean up current active timers
                                    (daily, weekly, monthly)
                                    
        Returns:
            (success, message) tuple
        """
        try:
            log_info("Cleaning up timer files")
            
            cleaned_files = []
            errors = []
            
            # Clean up current timer files if requested
            if include_current_timers:
                log_info("Cleaning up current timer files")
                current_timer_patterns = [
                    "/etc/systemd/system/zfs-snapshot-daily.timer",
                    "/etc/systemd/system/zfs-snapshot-weekly.timer",
                    "/etc/systemd/system/zfs-snapshot-monthly.timer"
                ]
                
                for pattern in current_timer_patterns:
                    for timer_file in glob.glob(pattern):
                        try:
                            timer_name = os.path.basename(timer_file)
                            # Stop and disable system timer
                            self.privilege_manager.run_privileged_command(
                                ['systemctl', 'stop', timer_name], ignore_errors=True)
                            self.privilege_manager.run_privileged_command(
                                ['systemctl', 'disable', timer_name], ignore_errors=True)
                            
                            # Remove file
                            success, result = self.privilege_manager.remove_files_privileged([timer_file])
                            if success:
                                cleaned_files.append(timer_file)
                            else:
                                errors.append(f"Failed to remove {timer_file}: {result}")
                        except Exception as e:
                            errors.append(f"Error processing {timer_file}: {str(e)}")
            
            # Patterns for older versions or leftover files
            old_timer_patterns = [
                "/etc/systemd/system/zfs-assistant-*.timer",
                "/etc/systemd/system/zfs-snapshot-*.timer", 
                "/etc/systemd/system/zfs-snapshot_*.timer",
                "/usr/lib/systemd/system/zfs-snapshot-*.timer",
                "/usr/local/bin/zfs-snapshot-*.sh"
            ]
            
            for pattern in old_timer_patterns:
                for file_path in glob.glob(pattern):
                    # Skip active timer files that match the current naming convention
                    # unless include_current_timers is True
                    if not include_current_timers and any(file_path.endswith(x) for x in 
                              ["daily.timer", "weekly.timer", "monthly.timer"]):
                        continue
                        
                    try:
                        # If it's a timer, try to stop and disable it first
                        if file_path.endswith(".timer"):
                            timer_name = os.path.basename(file_path)
                            self.privilege_manager.run_privileged_command(
                                ['systemctl', 'stop', timer_name], ignore_errors=True)
                            self.privilege_manager.run_privileged_command(
                                ['systemctl', 'disable', timer_name], ignore_errors=True)
                        
                        # Remove the file
                        success, result = self.privilege_manager.remove_files_privileged([file_path])
                        if success:
                            cleaned_files.append(file_path)
                        else:
                            errors.append(f"Failed to remove {file_path}: {result}")
                    except Exception as e:
                        errors.append(f"Error processing {file_path}: {str(e)}")
            
            # Also clean up old service files
            service_patterns = [
                "/etc/systemd/system/zfs-snapshot-*.service",
                "/usr/lib/systemd/system/zfs-snapshot-*.service"
            ]
            
            for pattern in service_patterns:
                for file_path in glob.glob(pattern):
                    # Skip the current main service file
                    if file_path == "/etc/systemd/system/zfs-snapshot@.service" and not include_current_timers:
                        continue
                        
                    try:
                        service_name = os.path.basename(file_path)
                        self.privilege_manager.run_privileged_command(
                            ['systemctl', 'stop', service_name], ignore_errors=True)
                        self.privilege_manager.run_privileged_command(
                            ['systemctl', 'disable', service_name], ignore_errors=True)
                        
                        success, result = self.privilege_manager.remove_files_privileged([file_path])
                        if success:
                            cleaned_files.append(file_path)
                        else:
                            errors.append(f"Failed to remove {file_path}: {result}")
                    except Exception as e:
                        errors.append(f"Error processing {file_path}: {str(e)}")
            
            # Reload systemd to reflect changes
            self.privilege_manager.run_privileged_command(['systemctl', 'daemon-reload'], ignore_errors=True)
            
            if errors:
                return False, f"Cleaned {len(cleaned_files)} files with {len(errors)} errors: {'; '.join(errors)}"
            
            return True, f"Successfully cleaned up {len(cleaned_files)} timer files"
            
        except Exception as e:
            log_error(f"Error cleaning up timer files: {str(e)}")
            return False, f"Error cleaning up timer files: {str(e)}"
    
    # Alias for backward compatibility
    def cleanup_old_timer_files(self) -> Tuple[bool, str]:
        """Alias for cleanup_timer_files for backward compatibility"""
        return self.cleanup_timer_files(include_current_timers=False)

    def _create_optimized_system_timers(self, schedules: Dict[str, bool]):
        """Create optimized system timer files based on enabled schedules."""
        try:
            # Daily snapshots
            if schedules.get("daily", False):
                daily_schedule = self.config.get("daily_schedule", [0, 1, 2, 3, 4])  # Weekdays
                daily_hour = self.config.get("daily_hour", 0)
                daily_minute = self.config.get("daily_minute", 0)
                weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                
                log_info(f"Creating daily timer for days: {daily_schedule} at {daily_hour:02d}:{daily_minute:02d}")
                
                # Validate that at least one day is selected
                if not daily_schedule:
                    log_error("Daily schedule enabled but no days selected")
                    return
                
                # Create a single timer file with multiple OnCalendar entries
                selected_days = []
                for day in daily_schedule:
                    if 0 <= day <= 6:
                        selected_days.append(weekdays[day])
                
                if not selected_days:
                    log_error("Daily schedule has invalid day indices")
                    return
                
                # Join day names with commas for the OnCalendar specification
                days_spec = ",".join(selected_days)
                
                timer_content = f"""[Unit]
Description=ZFS Daily Snapshot on {days_spec}

[Timer]
OnCalendar={days_spec} *-*-* {daily_hour:02d}:{daily_minute:02d}:00
Persistent=true
Unit=zfs-snapshot@daily.service

[Install]
WantedBy=timers.target
"""
                timer_path = "/etc/systemd/system/zfs-snapshot-daily.timer"
                success, result = self.privilege_manager.create_script_privileged(
                    timer_path, timer_content, executable=False
                )
                if success:
                    # Enable and start system timer
                    timer_name = "zfs-snapshot-daily.timer"
                    enable_success, enable_result = self.privilege_manager.run_privileged_command(['systemctl', 'enable', timer_name])
                    start_success, start_result = self.privilege_manager.run_privileged_command(['systemctl', 'start', timer_name])
                    
                    if enable_success and start_success:
                        log_success(f"Successfully enabled and started {timer_name}")
                    else:
                        log_error(f"Failed to enable/start {timer_name}: enable={enable_result}, start={start_result}")
                else:
                    log_error(f"Failed to create timer file {timer_path}: {result}")

            # Weekly snapshots
            if schedules.get("weekly", False):
                timer_content = """[Unit]
Description=ZFS Weekly Snapshot

[Timer]
OnCalendar=Mon *-*-* 01:00:00
Persistent=true
Unit=zfs-snapshot@weekly.service

[Install]
WantedBy=timers.target
"""
                timer_path = "/etc/systemd/system/zfs-snapshot-weekly.timer"
                success, result = self.privilege_manager.create_script_privileged(
                    timer_path, timer_content, executable=False
                )
                if success:
                    # Enable and start system timer
                    enable_success, enable_result = self.privilege_manager.run_privileged_command(['systemctl', 'enable', 'zfs-snapshot-weekly.timer'])
                    start_success, start_result = self.privilege_manager.run_privileged_command(['systemctl', 'start', 'zfs-snapshot-weekly.timer'])
                    
                    if enable_success and start_success:
                        log_success("Successfully enabled and started zfs-snapshot-weekly.timer")
                    else:
                        log_error(f"Failed to enable/start weekly timer: enable={enable_result}, start={start_result}")
                else:
                    log_error(f"Failed to create weekly timer file: {result}")

            # Monthly snapshots
            if schedules.get("monthly", False):
                timer_content = """[Unit]
Description=ZFS Monthly Snapshot

[Timer]
OnCalendar=*-*-01 02:00:00
Persistent=true
Unit=zfs-snapshot@monthly.service

[Install]
WantedBy=timers.target
"""
                timer_path = "/etc/systemd/system/zfs-snapshot-monthly.timer"
                success, result = self.privilege_manager.create_script_privileged(
                    timer_path, timer_content, executable=False
                )
                if success:
                    # Enable and start system timer
                    enable_success, enable_result = self.privilege_manager.run_privileged_command(['systemctl', 'enable', 'zfs-snapshot-monthly.timer'])
                    start_success, start_result = self.privilege_manager.run_privileged_command(['systemctl', 'start', 'zfs-snapshot-monthly.timer'])
                    
                    if enable_success and start_success:
                        log_success("Successfully enabled and started zfs-snapshot-monthly.timer")
                    else:
                        log_error(f"Failed to enable/start monthly timer: enable={enable_result}, start={start_result}")
                else:
                    log_error(f"Failed to create monthly timer file: {result}")

        except Exception as e:
            log_error(f"Error creating optimized system timers: {str(e)}")
            raise
    
    def setup_pacman_hook(self, enable: bool = True) -> Tuple[bool, str]:
        """Setup or remove pacman hook to create ZFS snapshots before package operations."""
        try:
            if enable:
                log_info("Setting up pacman hook for ZFS snapshots")
                
                # Create hook content - use system-wide script path
                hook_content = """[Trigger]
Operation = Install
Operation = Upgrade
Operation = Remove
Type = Package
Target = *

[Action]
Description = Creating ZFS snapshot before pacman transaction...
When = PreTransaction
Exec = /usr/local/bin/zfs-assistant-pacman-hook.py
Depends = python
"""
                # Create the hook script content
                script_content = self._get_pacman_hook_script_content()
                
                # Create script in system location with elevated privileges
                system_script_path = "/usr/local/bin/zfs-assistant-pacman-hook.py"
                success, result = self.privilege_manager.create_script_privileged(
                    system_script_path, script_content, executable=True
                )
                if not success:
                    return False, f"Error creating system pacman hook script: {result}"
                
                # Install the hook with elevated privileges
                success, result = self.privilege_manager.create_script_privileged(
                    PACMAN_HOOK_PATH, hook_content, executable=False
                )
                if not success:
                    return False, f"Error installing pacman hook: {result}"
                
                log_success("Pacman hook installed successfully")
                return True, "Pacman hook installed successfully"
                
            else:
                log_info("Removing pacman hook")
                
                # Remove system script and hook with elevated privileges
                system_script_path = "/usr/local/bin/zfs-assistant-pacman-hook.py"
                files_to_remove = [PACMAN_HOOK_PATH, system_script_path]
                
                success, result = self.privilege_manager.remove_files_privileged(files_to_remove)
                
                if not success:
                    return False, f"Error removing pacman hook: {result}"
                
                log_success("Pacman hook removed successfully")
                return True, "Pacman hook removed successfully"
                
        except Exception as e:
            error_msg = f"Error managing pacman hook: {str(e)}"
            log_error(error_msg)
            return False, error_msg
    
    def _get_pacman_hook_script_content(self) -> str:
        """Get the content for the pacman hook script."""
        return """#!/usr/bin/env python3

import subprocess
import datetime
import json
import os
import sys

# Add the src directory to Python path to find our modules
sys.path.insert(0, '/etc/zfs-assistant/src')

# Try to import the logging system, fallback if not available
try:
    from logger import ZFSLogger, OperationType, LogLevel
    HAS_LOGGING = True
except ImportError:
    HAS_LOGGING = False
    def log_operation_start(op_type, details): 
        print(f"Starting operation: {details}", flush=True)
    def log_message(level, message, details=None): 
        print(f"[{level}] {message}", flush=True)
    def log_operation_end(success, details=None, error_message=None):
        status = "SUCCESS" if success else "FAILED"
        print(f"Operation completed: {status}", flush=True)

def create_pre_pacman_snapshot():
    logger = None
    operation_started = False
    
    try:
        if HAS_LOGGING:
            logger = ZFSLogger()
            logger.log_operation_start(OperationType.PACMAN_INTEGRATION, "Pre-package transaction snapshot creation")
            operation_started = True
        else:
            log_operation_start("PACMAN_INTEGRATION", "Pre-package transaction snapshot creation")
            operation_started = True
        
        config_file = "/etc/zfs-assistant/config.json"
        
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
        
        # Create batch script for all snapshots
        batch_commands = []
        for dataset in datasets:
            snapshot_name = f"{dataset}@{prefix}-pkgop-{timestamp}"
            batch_commands.append(['zfs', 'snapshot', snapshot_name])
        
        if batch_commands:            # Execute all snapshots using a single pkexec session
            script_lines = ["#!/bin/bash", "set -e"]
            for dataset in datasets:
                snapshot_name = f"{dataset}@{prefix}-pkgop-{timestamp}"
                script_lines.append(f"zfs snapshot '{snapshot_name}'")
            
            script_content = '\\n'.join(script_lines)
            
            try:
                # Esegui con privilegi (necessario per i comandi zfs)
                result = subprocess.run(['pkexec', 'bash', '-c', script_content], 
                                      check=True, capture_output=True, text=True)
                
                success_count = len(datasets)
                if logger:
                    for dataset in datasets:
                        snapshot_name = f"{prefix}-pkgop-{timestamp}"
                        logger.log_snapshot_operation("create", dataset, snapshot_name, True)
                    logger.log_success("All pacman hook snapshots created successfully")
                    logger.log_operation_end(OperationType.PACMAN_INTEGRATION, True)
                else:
                    log_message("SUCCESS", f"Created {success_count} snapshots")
                    log_operation_end("PACMAN_INTEGRATION", True)
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to create snapshots: {e.stderr if e.stderr else str(e)}"
                if logger:
                    logger.log_error("Pacman hook snapshot creation failed", {'error': error_msg})
                    logger.log_operation_end(OperationType.PACMAN_INTEGRATION, False, error_message=error_msg)
                else:
                    log_message("ERROR", error_msg)
                    log_operation_end("PACMAN_INTEGRATION", False, error_message=error_msg)
                sys.exit(1)
    
    except Exception as e:
        error_msg = f"Error in pacman hook script: {str(e)}"
        if logger and operation_started:
            logger.log_error("Critical error in pacman hook execution", {'error': error_msg})
            logger.log_operation_end(OperationType.PACMAN_INTEGRATION, False, error_message=error_msg)
        else:
            log_message("ERROR", error_msg)
            if operation_started:
                log_operation_end("PACMAN_INTEGRATION", False, error_message=error_msg)
        sys.exit(1)

if __name__ == "__main__":
    create_pre_pacman_snapshot()
"""
    
    def _get_systemd_script_content(self) -> str:
        """Get the content for the systemd timer script."""
        return '''#!/usr/bin/env python3

import subprocess
import datetime
import json
import os
import sys

# Add the project root to Python path - use multiple potential locations
project_locations = [
    '/etc/zfs-assistant',
    '/usr/local/share/zfs-assistant', 
    '/opt/zfs-assistant',
    os.path.expanduser('~/.local/share/zfs-assistant')
]

# Find the actual project location
project_root = None
for location in project_locations:
    if os.path.exists(os.path.join(location, 'src')):
        project_root = location
        break

if project_root:
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

# Try to import the logging system, fallback if not available
HAS_LOGGING = False
try:
    from utils.logger import ZFSLogger, OperationType, LogLevel
    HAS_LOGGING = True
except ImportError:
    try:
        from logger import ZFSLogger, OperationType, LogLevel
        HAS_LOGGING = True
    except ImportError:
        HAS_LOGGING = False
        def log_operation_start(op_type, details): 
            print(f"Starting operation: {details}", flush=True)
        def log_message(level, message, details=None): 
            print(f"[{level}] {message}", flush=True)
        def log_operation_end(success, details=None, error_message=None):
            status = "SUCCESS" if success else "FAILED"
            print(f"Operation completed: {status}", flush=True)

def create_scheduled_snapshot(interval):
    logger = None
    operation_started = False


    # Log to main zfs-assistant log file for verification
    try:
        with open("/var/log/zfs-assistant.log", 'a') as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - INFO - ZFS Systemd script started for {interval} snapshots\n")
    except:
        pass
    
    try:
        if HAS_LOGGING:
            logger = ZFSLogger()
            # Start scheduled operation with clear description
            if interval == "daily":
                description = "Daily Snapshot Creation"
            elif interval == "weekly":
                description = "Weekly Snapshot Creation"
            elif interval == "monthly":
                description = "Monthly Snapshot Creation"
            else:
                description = f"{interval.capitalize()} Snapshot Creation"
            
            logger.start_scheduled_operation(OperationType.SCHEDULED_SNAPSHOT, description)
            operation_started = True
        else:
            log_operation_start("SCHEDULED_SNAPSHOT", f"{interval} snapshot creation")
            operation_started = True
        
        # Debug logging to file for troubleshooting - try /var/log first, fallback to /tmp
        debug_log = f"/var/log/zfs-assistant-{interval}.log"
        try:
            os.makedirs(os.path.dirname(debug_log), exist_ok=True)
            with open(debug_log, 'a') as f:
                f.write(f"\n=== {datetime.datetime.now()} ===\n")
                f.write(f"Script started for interval: {interval}\n")
                f.write(f"HAS_LOGGING: {HAS_LOGGING}\n")
                f.write(f"Running as user: {os.getuid()}\n")
        except Exception as e:
            # Fallback to /tmp if /var/log is not writable
            debug_log = f"/tmp/zfs-assistant-{interval}-debug.log"
            try:
                with open(debug_log, 'a') as f:
                    f.write(f"\n=== {datetime.datetime.now()} ===\n")
                    f.write(f"Script started for interval: {interval}\n")
                    f.write(f"HAS_LOGGING: {HAS_LOGGING}\n")
                    f.write(f"Running as user: {os.getuid()}\n")
                    f.write(f"Log fallback reason: {str(e)}\n")
            except:
                # If we can't even write to /tmp, continue without debug logging
                debug_log = None
        
        # Load configuration from multiple potential locations
        config_file = None
        config_locations = [
            "/etc/zfs-assistant/config.json",
            "/usr/local/share/zfs-assistant/config.json",
            "/opt/zfs-assistant/config.json",
            os.path.expanduser("~/.config/zfs-assistant/config.json"),
            os.path.expanduser("~/.local/share/zfs-assistant/config.json")
        ]
        
        # Find the actual config file
        for location in config_locations:
            if os.path.exists(location):
                config_file = location
                break
        
        # Debug: Check if config file exists
        if debug_log:
            with open(debug_log, 'a') as f:
                f.write(f"Searching for config file in locations: {config_locations}\n")
                f.write(f"Found config file: {config_file}\n")
                f.write(f"Config file exists: {config_file and os.path.exists(config_file)}\n")
        
        if not config_file:
            error_msg = f"Configuration file not found in any of these locations: {config_locations}"
            if debug_log:
                with open(debug_log, 'a') as f:
                    f.write(f"ERROR: {error_msg}\n")
            if logger:
                logger.log_essential_message(LogLevel.ERROR, error_msg)
                logger.end_scheduled_operation(False, "Configuration file missing")
            else:
                log_message("ERROR", error_msg)
                log_operation_end(False, "Configuration file missing")
            sys.exit(1)
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if debug_log:
                with open(debug_log, 'a') as f:
                    f.write(f"Config loaded successfully\n")
                    f.write(f"Datasets in config: {config.get('datasets', [])}\n")
        except Exception as e:
            error_msg = f"Error reading config file: {str(e)}"
            if debug_log:
                with open(debug_log, 'a') as f:
                    f.write(f"ERROR reading config: {error_msg}\n")
            if logger:
                logger.log_essential_message(LogLevel.ERROR, error_msg)
                logger.end_scheduled_operation(False, "Config read error")
            else:
                log_message("ERROR", error_msg)
                log_operation_end(False, "Config read error")
            sys.exit(1)
        
        datasets = config.get("datasets", [])
        if not datasets:
            if debug_log:
                with open(debug_log, 'a') as f:
                    f.write("No datasets configured\n")
            if logger:
                logger.log_essential_message(LogLevel.INFO, "No datasets configured for snapshots")
                logger.end_scheduled_operation(True, "No datasets to snapshot")
            else:
                log_message("INFO", "No datasets configured for snapshots")
                log_operation_end(True, "No datasets to snapshot")
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = config.get("prefix", "zfs-assistant")
        
        # Debug logging
        if debug_log:
            with open(debug_log, 'a') as f:
                f.write(f"Creating snapshots with prefix: {prefix}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Datasets to snapshot: {datasets}\n")
        
        
        # Find ZFS command location
        zfs_command = '/usr/bin/zfs'
        if not os.path.exists(zfs_command):
            # Try alternative locations
            for zfs_path in ['/sbin/zfs', '/usr/sbin/zfs', '/usr/local/bin/zfs']:
                if os.path.exists(zfs_path):
                    zfs_command = zfs_path
                    break
        
        if debug_log:
            with open(debug_log, 'a') as f:
                f.write(f"Using ZFS command: {zfs_command}\n")
                f.write(f"ZFS command exists: {os.path.exists(zfs_command)}\n")
        
        # Log essential details
        if logger:
            logger.log_essential_message(LogLevel.INFO, f"Creating {interval} snapshots for {len(datasets)} datasets")
        else:
            log_message("INFO", f"Creating {interval} snapshots for {len(datasets)} datasets")
        
        # Create batch script for all snapshots
        if datasets:
            # Execute all snapshots - use a simpler approach
            success_count = 0
            errors = []
            
            for dataset in datasets:
                snapshot_name = f"{dataset}@{prefix}-{interval}-{timestamp}"
                
                if debug_log:
                    with open(debug_log, 'a') as f:
                        f.write(f"Creating snapshot: {snapshot_name}\n")
                
                try:
                    # Check if we're already running as root (systemd service)
                    if os.getuid() == 0:
                        # Already running as root, execute directly using full path
                        result = subprocess.run([zfs_command, 'snapshot', snapshot_name], 
                                              check=True, capture_output=True, text=True, timeout=120)
                    else:
                        # Use pkexec to run with elevated privileges
                        result = subprocess.run(['pkexec', zfs_command, 'snapshot', snapshot_name], 
                                              check=True, capture_output=True, text=True, timeout=120)
                    
                    success_count += 1
                    
                    if debug_log:
                        with open(debug_log, 'a') as f:
                            f.write(f"Successfully created snapshot: {snapshot_name}\n")
                            if result.stdout:
                                f.write(f"Output: {result.stdout}\n")
                    
                except subprocess.CalledProcessError as e:
                    error_msg = f"Failed to create snapshot {snapshot_name}: {e.stderr if e.stderr else str(e)}"
                    errors.append(error_msg)
                    
                    if debug_log:
                        with open(debug_log, 'a') as f:
                            f.write(f"ERROR creating {snapshot_name}: {error_msg}\n")
                            f.write(f"Return code: {e.returncode}\n")
                            if e.stdout:
                                f.write(f"Stdout: {e.stdout}\n")
                            if e.stderr:
                                f.write(f"Stderr: {e.stderr}\n")
                
                except subprocess.TimeoutExpired as e:
                    error_msg = f"Timeout creating snapshot {snapshot_name}: {str(e)}"
                    errors.append(error_msg)
                    
                    if debug_log:
                        with open(debug_log, 'a') as f:
                            f.write(f"TIMEOUT creating {snapshot_name}: {error_msg}\n")
                
                except Exception as e:
                    error_msg = f"Unexpected error creating snapshot {snapshot_name}: {str(e)}"
                    errors.append(error_msg)
                    
                    if debug_log:
                        with open(debug_log, 'a') as f:
                            f.write(f"UNEXPECTED ERROR creating {snapshot_name}: {error_msg}\n")
            
            # Report results
            if errors:
                combined_error = f"Created {success_count}/{len(datasets)} snapshots. Errors: {'; '.join(errors)}"
                if debug_log:
                    with open(debug_log, 'a') as f:
                        f.write(f"PARTIAL SUCCESS: {combined_error}\n")
                
                if logger:
                    logger.log_essential_message(LogLevel.ERROR, combined_error)
                    logger.end_scheduled_operation(False, combined_error)
                else:
                    log_message("ERROR", combined_error)
                    log_operation_end(False, combined_error)
                
                # Also log error to main zfs-assistant log file
                try:
                    with open("/var/log/zfs-assistant.log", 'a') as f:
                        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - ERROR - {combined_error}\n")
                except:
                    try:
                        with open("/tmp/zfs-assistant-execution.log", 'a') as f:
                            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - ERROR - {combined_error}\n")
                    except:
                        pass
                
                sys.exit(1)
            else:
                success_msg = f"Successfully created {success_count} {interval} snapshots"
                if debug_log:
                    with open(debug_log, 'a') as f:
                        f.write(f"SUCCESS: {success_msg}\n")
                
                if logger:
                    logger.log_essential_message(LogLevel.SUCCESS, success_msg)
                    logger.end_scheduled_operation(True, success_msg)
                else:
                    log_message("SUCCESS", success_msg)
                    log_operation_end(True, success_msg)
                
                # Also log completion to main zfs-assistant log file
                try:
                    with open("/var/log/zfs-assistant.log", 'a') as f:
                        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - SUCCESS - {success_msg}\n")
                except:
                    try:
                        with open("/tmp/zfs-assistant-execution.log", 'a') as f:
                            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - SUCCESS - {success_msg}\n")
                    except:
                        pass
        else:
            if debug_log:
                with open(debug_log, 'a') as f:
                    f.write("No snapshots to create\n")
            if logger:
                logger.log_essential_message(LogLevel.INFO, "No snapshots to create")
                logger.end_scheduled_operation(True, "No snapshots needed")
            else:
                log_message("INFO", "No snapshots to create")
                log_operation_end(True, "No snapshots needed")
    
    except Exception as e:
        error_msg = f"Error in {interval} snapshot script: {str(e)}"
        try:
            if debug_log:
                with open(debug_log, 'a') as f:
                    f.write(f"CRITICAL ERROR: {error_msg}\n")
            else:
                # Try to write to /tmp as last resort
                with open(f"/tmp/zfs-assistant-{interval}-critical.log", 'a') as f:
                    f.write(f"CRITICAL ERROR: {error_msg}\n")
        except:
            pass  # If we can't write to any log, continue anyway
        
        if logger and operation_started:
            logger.log_essential_message(LogLevel.ERROR, error_msg)
            logger.end_scheduled_operation(False, error_msg)
        else:
            log_message("ERROR", error_msg)
            if operation_started:
                log_operation_end(False, error_msg)
        sys.exit(1)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        interval = sys.argv[1]
        create_scheduled_snapshot(interval)
    else:
        print("Usage: zfs-assistant-systemd.py <interval>")
        sys.exit(1)
'''
    
    def _ensure_system_config(self) -> Tuple[bool, str]:
        """Ensure configuration is available in system location for systemd scripts."""
        try:
            # Find the current config file location
            config_locations = [
                CONFIG_FILE,  # From common.py
                os.path.expanduser("~/.config/zfs-assistant/config.json"),
                os.path.expanduser("~/.local/share/zfs-assistant/config.json"),
                "/etc/zfs-assistant/config.json"
            ]
            
            source_config = None
            for location in config_locations:
                if os.path.exists(location):
                    source_config = location
                    break
            
            if not source_config:
                return False, "No configuration file found to copy"
            
            # Target system location
            target_config_dir = "/etc/zfs-assistant"
            target_config_file = os.path.join(target_config_dir, "config.json")
            
            # Read the current config
            try:
                with open(source_config, 'r') as f:
                    config_content = f.read()
            except Exception as e:
                return False, f"Failed to read config file: {str(e)}"
            
            # Create target directory and config file with elevated privileges
            success, result = self.privilege_manager.create_script_privileged(
                target_config_file, config_content, executable=False
            )
            
            if not success:
                return False, f"Failed to create system config: {result}"
            
            log_info(f"Successfully copied config from {source_config} to {target_config_file}")
            return True, f"Config copied to {target_config_file}"
            
        except Exception as e:
            return False, f"Error ensuring system config: {str(e)}"