#!/usr/bin/env python3
# ZFS Assistant - System Integration (Pacman Hooks & Systemd Timers)
# Author: GitHub Copilot

import os
import subprocess
import tempfile
from typing import Dict, List, Tuple
from .logger import (
    OperationType, get_logger,
    log_info, log_error, log_success, log_warning
)
from .common import PACMAN_HOOK_PATH, SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH


class SystemIntegration:
    """Handles system integration features like pacman hooks and systemd timers."""
      def __init__(self, privilege_manager, config):
        self.logger = get_logger()
        self.privilege_manager = privilege_manager
        self.config = config
        self.pacman_hook_path = PACMAN_HOOK_PATH
    
    def setup_pacman_hook(self, enable: bool = True) -> Tuple[bool, str]:
        """Setup or remove pacman hook to create ZFS snapshots before package operations."""
        try:
            if enable:
                log_info("Setting up pacman hook for ZFS snapshots")
                
                # Create hook content
                hook_content = """[Trigger]
Operation = Install
Operation = Upgrade
Operation = Remove
Type = Package
Target = *

[Action]
Description = Creating ZFS snapshot before pacman transaction...
When = PreTransaction
Exec = ~/.local/bin/zfs-assistant-pacman-hook.py
Depends = python
"""
                # Create the hook script content
                script_content = self._get_pacman_hook_script_content()
                
                # Create script in user's home directory
                local_bin_dir = os.path.expanduser("~/.local/bin")
                os.makedirs(local_bin_dir, exist_ok=True)
                
                with open(PACMAN_SCRIPT_PATH, 'w') as f:
                    f.write(script_content)
                os.chmod(PACMAN_SCRIPT_PATH, 0o755)
                
                # Install the hook with elevated privileges
                success, result = privilege_manager.create_script_privileged(
                    self.pacman_hook_path, hook_content, executable=False
                )
                if not success:
                    return False, f"Error installing pacman hook: {result}"
                
                log_success("Pacman hook installed successfully")
                return True, "Pacman hook installed successfully"
                
            else:
                log_info("Removing pacman hook")
                
                # Remove user script
                if os.path.exists(PACMAN_SCRIPT_PATH):
                    os.remove(PACMAN_SCRIPT_PATH)
                
                # Remove pacman hook with elevated privileges
                success, result = privilege_manager.remove_files_privileged([self.pacman_hook_path])
                
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
        
        config_file = os.path.expanduser("~/.config/zfs-assistant/config.json")
        
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
    
    def setup_systemd_timers(self, schedules: Dict[str, bool]) -> Tuple[bool, str]:
        """Setup systemd timers for automated snapshots."""
        try:
            log_info("Setting up systemd timers for automated snapshots", {
                'schedules': schedules
            })
            
            # Create the snapshot script
            script_content = self._get_systemd_script_content()
            
            # Create script in user's home directory
            local_bin_dir = os.path.expanduser("~/.local/bin")
            os.makedirs(local_bin_dir, exist_ok=True)
            
            with open(SYSTEMD_SCRIPT_PATH, 'w') as f:
                f.write(script_content)
            os.chmod(SYSTEMD_SCRIPT_PATH, 0o755)
            
            # Create systemd service directory
            user_systemd_dir = os.path.expanduser("~/.config/systemd/user")
            os.makedirs(user_systemd_dir, exist_ok=True)
            
            # Create the service file
            service_content = """[Unit]
Description=ZFS Snapshot %i Job
After=zfs.target

[Service]
Type=oneshot
ExecStart=~/.local/bin/zfs-assistant-systemd.py %i
"""
            service_path = os.path.join(user_systemd_dir, "zfs-snapshot@.service")
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            # Clean up existing timer files
            self._cleanup_existing_timers(user_systemd_dir)
            
            # Create new timer files based on schedules
            self._create_optimized_timers(user_systemd_dir, schedules)
            
            # Reload systemd daemon
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
            
            log_success("Systemd timers set up successfully")
            return True, "Systemd timers set up successfully"
            
        except Exception as e:
            error_msg = f"Error setting up systemd timers: {str(e)}"
            log_error(error_msg)
            return False, error_msg
    
    def _cleanup_existing_timers(self, user_systemd_dir: str):
        """Clean up existing timer files."""
        timer_patterns = [
            "zfs-snapshot-hourly*.timer",
            "zfs-snapshot-daily*.timer", 
            "zfs-snapshot-weekly.timer",
            "zfs-snapshot-monthly.timer"
        ]
        
        for pattern in timer_patterns:
            import glob                for timer_file in glob.glob(os.path.join(user_systemd_dir, pattern)):
                    try:
                        # systemctl --user commands don't need pkexec
                        timer_name = os.path.basename(timer_file)
                        subprocess.run(['systemctl', '--user', 'stop', timer_name], check=False)
                        subprocess.run(['systemctl', '--user', 'disable', timer_name], check=False)
                        
                        # Remove file
                        os.remove(timer_file)
                    except:
                        pass
    
    def _create_optimized_timers(self, user_systemd_dir: str, schedules: Dict[str, bool]):
        """Create optimized timer files that group multiple times into single timers."""
        
        # Handle hourly schedule with custom hours
        if schedules.get("hourly", False):
            self._create_hourly_timers(user_systemd_dir)
        
        # Handle daily schedule with custom days
        if schedules.get("daily", False):
            self._create_daily_timers(user_systemd_dir)
        
        # Handle weekly schedule
        if schedules.get("weekly", False):
            self._create_weekly_timer(user_systemd_dir)
        
        # Handle monthly schedule
        if schedules.get("monthly", False):
            self._create_monthly_timer(user_systemd_dir)
      def _create_hourly_timers(self, user_systemd_dir: str):
        """Create hourly timers."""
        hourly_schedule = self.config.get("hourly_schedule", list(range(24)))
        
        if not hourly_schedule:
            hourly_schedule = list(range(24))  # Default to all hours
        
        # Group hours for efficiency (e.g., every 4 hours, every 6 hours, etc.)
        if len(hourly_schedule) == 24:
            # All hours selected - use simple hourly timer
            timer_content = """[Unit]
Description=Take hourly ZFS snapshots

[Timer]
OnCalendar=*-*-* *:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
            timer_path = os.path.join(user_systemd_dir, "zfs-snapshot-hourly.timer")
            with open(timer_path, 'w') as f:
                f.write(timer_content)
            
            # systemctl --user commands don't need pkexec
            subprocess.run(['systemctl', '--user', 'enable', 'zfs-snapshot-hourly.timer'], check=True)
            subprocess.run(['systemctl', '--user', 'start', 'zfs-snapshot-hourly.timer'], check=True)
        else:            # Create timer for specific hours
            hour_list = ','.join(f"{hour:02d}" in sorted(hourly_schedule))
            timer_content = f"""[Unit]
Description=Take hourly ZFS snapshots at selected hours

[Timer]
OnCalendar=*-*-* {hour_list}:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
            timer_path = os.path.join(user_systemd_dir, "zfs-snapshot-hourly-custom.timer")
            with open(timer_path, 'w') as f:
                f.write(timer_content)
            
            # systemctl --user commands don't need pkexec
            subprocess.run(['systemctl', '--user', 'enable', 'zfs-snapshot-hourly-custom.timer'], check=True)
            subprocess.run(['systemctl', '--user', 'start', 'zfs-snapshot-hourly-custom.timer'], check=True)
    
    def _create_daily_timers(self, user_systemd_dir: str):
        """Create daily timers."""
        daily_schedule = self.config.get("daily_schedule", list(range(7)))
        
        if not daily_schedule:
            daily_schedule = list(range(7))  # Default to all days
        
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        if len(daily_schedule) == 7:
            # All days selected - use simple daily timer
            timer_content = """[Unit]
Description=Take daily ZFS snapshots

[Timer]
OnCalendar=*-*-* 00:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""            timer_path = os.path.join(user_systemd_dir, "zfs-snapshot-daily.timer")
            with open(timer_path, 'w') as f:
                f.write(timer_content)
            
            # systemctl --user commands don't need pkexec
            subprocess.run(['systemctl', '--user', 'enable', 'zfs-snapshot-daily.timer'], check=True)
            subprocess.run(['systemctl', '--user', 'start', 'zfs-snapshot-daily.timer'], check=True)
        
        else:
            # Create timer for specific days
            selected_days = [days_of_week[day] for day in sorted(daily_schedule)]
            day_list = ','.join(selected_days)
            
            timer_content = f"""[Unit]
Description=Take daily ZFS snapshots on selected days

[Timer]
OnCalendar={day_list} *-*-* 00:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
            timer_path = os.path.join(user_systemd_dir, "zfs-snapshot-daily-custom.timer")            with open(timer_path, 'w') as f:
                f.write(timer_content)
            
            # systemctl --user commands don't need pkexec
            subprocess.run(['systemctl', '--user', 'enable', 'zfs-snapshot-daily-custom.timer'], check=True)
            subprocess.run(['systemctl', '--user', 'start', 'zfs-snapshot-daily-custom.timer'], check=True)
    
    def _create_weekly_timer(self, user_systemd_dir: str):
        """Create weekly timer."""
        timer_content = """[Unit]
Description=Take weekly ZFS snapshots

[Timer]
OnCalendar=Mon *-*-* 00:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
        timer_path = os.path.join(user_systemd_dir, "zfs-snapshot-weekly.timer")        with open(timer_path, 'w') as f:
            f.write(timer_content)
        
        # systemctl --user commands don't need pkexec
        subprocess.run(['systemctl', '--user', 'enable', 'zfs-snapshot-weekly.timer'], check=True)
        subprocess.run(['systemctl', '--user', 'start', 'zfs-snapshot-weekly.timer'], check=True)
    
    def _create_monthly_timer(self, user_systemd_dir: str):
        """Create monthly timer."""
        timer_content = """[Unit]
Description=Take monthly ZFS snapshots

[Timer]
OnCalendar=*-*-01 00:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
        timer_path = os.path.join(user_systemd_dir, "zfs-snapshot-monthly.timer")        with open(timer_path, 'w') as f:
            f.write(timer_content)
        
        # systemctl --user commands don't need pkexec
        subprocess.run(['systemctl', '--user', 'enable', 'zfs-snapshot-monthly.timer'], check=True)
        subprocess.run(['systemctl', '--user', 'start', 'zfs-snapshot-monthly.timer'], check=True)
    
    def _get_systemd_script_content(self) -> str:
        """Get the content for the systemd timer script."""
        return """#!/usr/bin/env python3
import subprocess
import datetime
import json
import os
import sys
from pathlib import Path

# Import logging system
sys.path.insert(0, '/usr/lib/python3/site-packages')
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
    
    def log_info(msg, details=None): print(f"[INFO] {msg}")
    def log_error(msg, details=None): print(f"[ERROR] {msg}")
    def log_success(msg, details=None): print(f"[SUCCESS] {msg}")
    def log_warning(msg, details=None): print(f"[WARNING] {msg}")
    
    logger = MockLogger()

def create_scheduled_snapshot(interval):
    try:
        config_file = os.path.expanduser("~/.config/zfs-assistant/config.json")
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        try:
            logger = get_logger()
        except:
            logger = MockLogger()
        
        log_info(f"Starting scheduled {interval} snapshot operation")
        
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
        
        # Create snapshots using batch execution
        batch_commands = []
        for dataset in datasets:
            snapshot_name = f"{dataset}@{prefix}-{interval}-{timestamp}"
            batch_commands.append(['zfs', 'snapshot', snapshot_name])
        
        if batch_commands:
            script_lines = ["#!/bin/bash", "set -e"]
            for dataset in datasets:
                snapshot_name = f"{dataset}@{prefix}-{interval}-{timestamp}"
                script_lines.append(f"zfs snapshot '{snapshot_name}'")
            
            script_content = '\\n'.join(script_lines)
              try:
                # Esegui con privilegi (necessario per i comandi zfs)
                result = subprocess.run(['pkexec', 'bash', '-c', script_content], 
                                      check=True, capture_output=True, text=True)
                
                log_success(f"Created {len(datasets)} {interval} snapshots")
                for dataset in datasets:
                    logger.log_snapshot_operation('create', dataset, f"{prefix}-{interval}-{timestamp}", True)
                logger.end_operation(operation_id, True)
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to create snapshots: {e.stderr if e.stderr else str(e)}"
                log_error(error_msg)
                logger.end_operation(operation_id, False, {'error': error_msg})
    
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
    
    def disable_schedule(self, schedule_type: str) -> Tuple[bool, str]:
        """Disable and remove timers for a specific schedule type."""
        try:
            log_info(f"Disabling {schedule_type} schedule")
            
            user_systemd_dir = os.path.expanduser("~/.config/systemd/user")
            
            # Define timer file patterns for each schedule type
            timer_patterns = {
                "hourly": ["zfs-snapshot-hourly*.timer"],
                "daily": ["zfs-snapshot-daily*.timer"],
                "weekly": ["zfs-snapshot-weekly.timer"],
                "monthly": ["zfs-snapshot-monthly.timer"]
            }
            
            if schedule_type not in timer_patterns:
                return False, f"Unknown schedule type: {schedule_type}"
            
            # Stop, disable, and remove timer files
            import glob
            removed_timers = []
            
            for pattern in timer_patterns[schedule_type]:
                for timer_file in glob.glob(os.path.join(user_systemd_dir, pattern)):                    timer_name = os.path.basename(timer_file)
                    
                    try:
                        # systemctl --user commands don't need pkexec
                        subprocess.run(['systemctl', '--user', 'stop', timer_name], check=False)
                        subprocess.run(['systemctl', '--user', 'disable', timer_name], check=False)
                        
                        # Remove file
                        os.remove(timer_file)
                        removed_timers.append(timer_name)
                        
                    except Exception as e:
                        log_warning(f"Error removing timer {timer_name}: {str(e)}")
              # Reload systemd daemon (user service doesn't need pkexec)
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
            
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
