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
from .logger import (
    OperationType, get_logger,
    log_info, log_error, log_success, log_warning
)
from .common import (
    CONFIG_DIR, CONFIG_FILE, SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
    PACMAN_HOOK_PATH, run_command, get_timestamp
)


class SystemIntegration:
    """Handles system integration for ZFS Assistant (Pacman hooks and systemd timers)"""
    
    def __init__(self, privilege_manager, config: dict):
        self.privilege_manager = privilege_manager
        self.config = config
        self.logger = get_logger()

    def setup_systemd_timers(self, schedules: Dict[str, bool]) -> Tuple[bool, str]:
        """Setup systemd timers for automated snapshots."""
        try:
            log_info("Setting up systemd timers for automated snapshots", {
                'schedules': schedules
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
        # Create the snapshot script in system location
        script_content = self._get_systemd_script_content()
        system_script_path = "/usr/local/bin/zfs-assistant-systemd.py"
        
        # Create script with elevated privileges
        success, result = self.privilege_manager.create_script_privileged(
            system_script_path, script_content, executable=True
        )
        if not success:
            return False, f"Error creating system script: {result}"
        
        # Create system service file
        service_content = f"""[Unit]
Description=ZFS Snapshot %i Job
After=zfs.target

[Service]
Type=oneshot
ExecStart={system_script_path} %i
User=root
"""
        
        # Create service file with elevated privileges
        service_path = "/etc/systemd/system/zfs-snapshot@.service"
        success, result = self.privilege_manager.create_script_privileged(
            service_path, service_content, executable=False
        )
        if not success:
            return False, f"Error creating system service: {result}"
        
        # Clean up existing system timer files
        self._cleanup_existing_system_timers()
        
        # Create new system timer files based on schedules
        self._create_optimized_system_timers(schedules)
        
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
                "hourly": ["/etc/systemd/system/zfs-snapshot-hourly.timer"],
                "daily": ["/etc/systemd/system/zfs-snapshot-daily.timer"],  # Single daily timer file
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
                "hourly": False,
                "daily": False,
                "weekly": False,
                "monthly": False
            }
            
            # Check if system timer files exist and are active
            timer_patterns = {
                "hourly": ["/etc/systemd/system/zfs-snapshot-hourly.timer"],  # Single hourly timer file
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
                "hourly": bool(self.config.get("hourly_schedule", [])),
                "daily": bool(self.config.get("daily_schedule", [])),
                "weekly": bool(self.config.get("weekly_schedule", False)),
                "monthly": bool(self.config.get("monthly_schedule", False))
            }
    
    def _cleanup_existing_system_timers(self):
        """Clean up existing system timer files."""
        timer_patterns = [
            "/etc/systemd/system/zfs-snapshot-hourly.timer",  # Single hourly timer file
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

    def _create_optimized_system_timers(self, schedules: Dict[str, bool]):
        """Create optimized system timer files based on enabled schedules."""
        try:
            # Hourly snapshots
            if schedules.get("hourly", False):
                hourly_schedule = self.config.get("hourly_schedule", [8, 12, 16, 20])
                log_info(f"Creating hourly timer for hours: {hourly_schedule}")
                
                # Create a single timer file with multiple OnCalendar entries
                timer_content = """[Unit]
Description=ZFS Hourly Snapshot

[Timer]
"""
                
                # Add one OnCalendar line for each selected hour
                for hour in sorted(hourly_schedule):
                    timer_content += f"OnCalendar=*-*-* {hour:02d}:00:00\n"
                
                timer_content += """Persistent=true
Unit=zfs-snapshot@hourly.service

[Install]
WantedBy=timers.target
"""
                timer_path = "/etc/systemd/system/zfs-snapshot-hourly.timer"
                success, result = self.privilege_manager.create_script_privileged(
                    timer_path, timer_content, executable=False
                )
                if success:
                    # Enable and start system timer
                    timer_name = "zfs-snapshot-hourly.timer"
                    enable_success, enable_result = self.privilege_manager.run_privileged_command(['systemctl', 'enable', timer_name])
                    start_success, start_result = self.privilege_manager.run_privileged_command(['systemctl', 'start', timer_name])
                    
                    if enable_success and start_success:
                        log_success(f"Successfully enabled and started {timer_name}")
                    else:
                        log_error(f"Failed to enable/start {timer_name}: enable={enable_result}, start={start_result}")
                else:
                    log_error(f"Failed to create timer file {timer_path}: {result}")

            # Daily snapshots
            if schedules.get("daily", False):
                daily_schedule = self.config.get("daily_schedule", [0, 1, 2, 3, 4])  # Weekdays
                daily_hour = self.config.get("daily_hour", 0)
                weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                
                log_info(f"Creating daily timer for days: {daily_schedule} at hour {daily_hour}")
                
                # Create a single timer file with multiple OnCalendar entries
                selected_days = []
                for day in daily_schedule:
                    if 0 <= day <= 6:
                        selected_days.append(weekdays[day])
                
                # Join day names with commas for the OnCalendar specification
                days_spec = ",".join(selected_days)
                
                timer_content = f"""[Unit]
Description=ZFS Daily Snapshot on {days_spec}

[Timer]
OnCalendar={days_spec} *-*-* {daily_hour:02d}:00:00
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

# Try to import the logging system, fallback if not available
try:
    from logger import ZFSLogger, OperationType, LogLevel
    HAS_LOGGING = True
except ImportError:
    HAS_LOGGING = False
    def log_operation_start(op_type, details): print(f"Starting operation: {details}")
    def log_message(level, message, details=None): print(f"[{level}] {message}")
    def log_operation_end(op_type, success, details=None, error_message=None):
        status = "SUCCESS" if success else "FAILED"
        print(f"Operation completed: {status}")

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
        return """#!/usr/bin/env python3
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
    def log_operation_start(op_type, details): print(f"Starting operation: {details}")
    def log_message(level, message, details=None): print(f"[{level}] {message}")
    def log_operation_end(op_type, success, details=None, error_message=None):
        status = "SUCCESS" if success else "FAILED"
        print(f"Operation completed: {status}")

def create_scheduled_snapshot(interval):
    logger = None
    operation_started = False
    
    try:
        if HAS_LOGGING:
            logger = ZFSLogger()
            logger.log_operation_start(OperationType.SCHEDULED_SNAPSHOT, f"Scheduled {interval} snapshot creation")
            operation_started = True
        else:
            log_operation_start("SCHEDULED_SNAPSHOT", f"Scheduled {interval} snapshot creation")
            operation_started = True
        
        config_file = "/etc/zfs-assistant/config.json"
        
        if not os.path.exists(config_file):
            error_msg = f"Configuration file not found: {config_file}"
            if logger:
                logger.log_error("Configuration file not found", {'config_file': config_file})
                logger.log_operation_end(OperationType.SCHEDULED_SNAPSHOT, False, error_message=error_msg)
            else:
                log_message("ERROR", error_msg)
                log_operation_end("SCHEDULED_SNAPSHOT", False, error_message=error_msg)
            return
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        datasets = config.get("datasets", [])
        if not datasets:
            if logger:
                logger.log_warning("No datasets configured for snapshots")
                logger.log_operation_end(OperationType.SCHEDULED_SNAPSHOT, True, "No datasets configured")
            else:
                log_message("WARNING", "No datasets configured for snapshots")
                log_operation_end("SCHEDULED_SNAPSHOT", True, "No datasets configured")
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = config.get("prefix", "zfs-assistant")
        
        # Create batch script for all snapshots
        batch_commands = []
        for dataset in datasets:
            snapshot_name = f"{dataset}@{prefix}-{interval}-{timestamp}"
            batch_commands.append(['zfs', 'snapshot', snapshot_name])
        
        if batch_commands:
            # Execute all snapshots
            script_lines = ["#!/bin/bash", "set -e"]
            for dataset in datasets:
                snapshot_name = f"{dataset}@{prefix}-{interval}-{timestamp}"
                script_lines.append(f"zfs snapshot '{snapshot_name}'")
            
            script_content = '\\n'.join(script_lines)
            
            try:
                # Execute with elevated privileges (necessary for zfs commands)
                result = subprocess.run(['bash', '-c', script_content], 
                                      check=True, capture_output=True, text=True)
                
                success_count = len(datasets)
                if logger:
                    for dataset in datasets:
                        snapshot_name = f"{prefix}-{interval}-{timestamp}"
                        logger.log_snapshot_operation("create", dataset, snapshot_name, True)
                    logger.log_success(f"All {interval} snapshots created successfully")
                    logger.log_operation_end(OperationType.SCHEDULED_SNAPSHOT, True)
                else:
                    log_message("SUCCESS", f"Created {success_count} {interval} snapshots")
                    log_operation_end("SCHEDULED_SNAPSHOT", True)
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to create {interval} snapshots: {e.stderr if e.stderr else str(e)}"
                if logger:
                    logger.log_error(f"{interval.capitalize()} snapshot creation failed", {'error': error_msg})
                    logger.log_operation_end(OperationType.SCHEDULED_SNAPSHOT, False, error_message=error_msg)
                else:
                    log_message("ERROR", error_msg)
                    log_operation_end("SCHEDULED_SNAPSHOT", False, error_message=error_msg)
                sys.exit(1)
    
    except Exception as e:
        error_msg = f"Error in {interval} snapshot script: {str(e)}"
        if logger and operation_started:
            logger.log_error(f"Critical error in {interval} snapshot execution", {'error': error_msg})
            logger.log_operation_end(OperationType.SCHEDULED_SNAPSHOT, False, error_message=error_msg)
        else:
            log_message("ERROR", error_msg)
            if operation_started:
                log_operation_end("SCHEDULED_SNAPSHOT", False, error_message=error_msg)
        sys.exit(1)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        interval = sys.argv[1]
        create_scheduled_snapshot(interval)
    else:
        print("Usage: zfs-assistant-systemd.py <interval>")
        sys.exit(1)
"""
