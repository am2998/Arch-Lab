#!/usr/bin/env python3
# ZFS Assistant - Core ZFS operations
# Author: GitHub Copilot

import os
import json
import subprocess
import datetime
from pathlib import Path

# Try relative imports first, fall back to absolute imports if run as a script
try:
    from .common import (
        CONFIG_DIR, CONFIG_FILE, PACMAN_HOOK_PATH, 
        SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
        DEFAULT_CONFIG, run_command, get_timestamp
    )
    from .models import ZFSSnapshot
except ImportError:
    # For direct script execution
    import sys
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    try:
        # Try with src as a direct submodule
        from src.common import (
            CONFIG_DIR, CONFIG_FILE, PACMAN_HOOK_PATH, 
            SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
            DEFAULT_CONFIG, run_command, get_timestamp
        )
        from src.models import ZFSSnapshot
    except ImportError:
        # Last resort, use direct file paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        from common import (
            CONFIG_DIR, CONFIG_FILE, PACMAN_HOOK_PATH, 
            SYSTEMD_SCRIPT_PATH, PACMAN_SCRIPT_PATH,
            DEFAULT_CONFIG, run_command, get_timestamp
        )
        from models import ZFSSnapshot

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
            
            # Now get properties for each dataset
            datasets = []
            for name in dataset_names:
                properties = self.get_dataset_properties(name)
                datasets.append({
                    'name': name,
                    'properties': properties
                })
            
            return datasets
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
        except Exception as e:
            print(f"Error getting snapshots: {e}")
            return []
            
    def cleanup_snapshots(self):
        """Clean up snapshots based on retention policy"""
        try:
            if not self.config.get("auto_snapshot", True):
                return True, "Auto-snapshot is disabled, skipping cleanup"
                
            retention = self.config.get("snapshot_retention", {})
            prefix = self.config.get("prefix", "zfs-assistant")
            
            # Get all snapshots for managed datasets
            managed_datasets = self.config.get("datasets", [])
            snapshots_by_type = {
                "hourly": [],
                "daily": [],
                "weekly": [],
                "monthly": []
            }
            
            success_count = 0
            error_count = 0
            errors = []
            
            for dataset in managed_datasets:
                # Get all snapshots for this dataset
                all_snapshots = self.get_snapshots(dataset)
                
                # Group snapshots by type
                for snapshot in all_snapshots:
                    for snap_type in snapshots_by_type.keys():
                        if f"{prefix}-{snap_type}-" in snapshot.name:
                            snapshots_by_type[snap_type].append(snapshot)
            
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
                    result_message += f"\nErrors: {'; '.join(errors[:5])}"
                    if len(errors) > 5:
                        result_message += f" and {len(errors) - 5} more"
            
            return success_count > 0 or error_count == 0, result_message
        except Exception as e:
            return False, f"Error during snapshot cleanup: {e}"

    def create_snapshot(self, dataset, name=None):
        """Create a ZFS snapshot for the specified dataset"""
        try:
            if not name:
                timestamp = get_timestamp()
                name = f"{self.config['prefix']}-{timestamp}"
            
            snapshot_name = f"{dataset}@{name}"
            result = subprocess.run(['zfs', 'snapshot', snapshot_name], 
                                    capture_output=True, text=True, check=True)
            return True, name
        except subprocess.CalledProcessError as e:
            return False, f"Error creating snapshot: {e.stderr}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_snapshot(self, snapshot_full_name):
        """Delete a ZFS snapshot by its full name (dataset@snapshot)"""
        try:
            result = subprocess.run(['zfs', 'destroy', snapshot_full_name],
                                    capture_output=True, text=True, check=True)
            return True, f"Snapshot {snapshot_full_name} deleted"
        except subprocess.CalledProcessError as e:
            return False, f"Error deleting snapshot: {e.stderr}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def rollback_snapshot(self, snapshot_full_name, force=False):
        """Rollback to a ZFS snapshot"""
        try:
            cmd = ['zfs', 'rollback']
            if force:
                cmd.append('-r')
            cmd.append(snapshot_full_name)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, f"Rolled back to snapshot {snapshot_full_name}"
        except subprocess.CalledProcessError as e:
            return False, f"Error rolling back: {e.stderr}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def clone_snapshot(self, snapshot_full_name, target_name):
        """Clone a ZFS snapshot to a new dataset"""
        try:
            result = subprocess.run(['zfs', 'clone', snapshot_full_name, target_name],
                                    capture_output=True, text=True, check=True)
            return True, f"Cloned snapshot {snapshot_full_name} to {target_name}"
        except subprocess.CalledProcessError as e:
            return False, f"Error cloning snapshot: {e.stderr}"
        except Exception as e:
            return False, f"Error: {str(e)}"

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
            # Create the hook script
            script_content = """#!/usr/bin/env python3
import subprocess
import datetime
import json
import os

def create_pre_pacman_snapshot():
    try:        config_file = os.path.expanduser("~/.config/zfs-assistant/config.json")
        
        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if not config.get("pacman_integration", True):
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = config.get("prefix", "zfs-assistant")
        
        for dataset in config.get("datasets", []):
            snapshot_name = f"{dataset}@{prefix}-pacman-{timestamp}"
            subprocess.run(['zfs', 'snapshot', snapshot_name], check=True)
            print(f"Created pre-pacman snapshot: {snapshot_name}")
    
    except Exception as e:
        print(f"Error creating pre-pacman snapshot: {e}")

if __name__ == "__main__":
    create_pre_pacman_snapshot()
"""
            try:
                # Ensure directories exist
                hook_dir = os.path.dirname(self.pacman_hook_path)
                os.makedirs(hook_dir, exist_ok=True)
                
                # Write the hook file
                with open(self.pacman_hook_path, 'w') as f:
                    f.write(hook_content)
                
                # Write the hook script
                script_path = PACMAN_SCRIPT_PATH
                with open(script_path, 'w') as f:
                    f.write(script_content)
                
                # Make the script executable
                os.chmod(script_path, 0o755)
                
                return True, "Pacman hook installed successfully"
            except Exception as e:
                return False, f"Error installing pacman hook: {e}"
        else:
            # Remove the hook
            try:
                if os.path.exists(self.pacman_hook_path):
                    os.remove(self.pacman_hook_path)
                
                script_path = PACMAN_SCRIPT_PATH
                if os.path.exists(script_path):
                    os.remove(script_path)
                
                return True, "Pacman hook removed successfully"
            except Exception as e:
                return False, f"Error removing pacman hook: {e}"

    def setup_systemd_timers(self, schedules):
        """Setup systemd timers for automated snapshots"""
        try:
            # Create the snapshot script
            script_content = """#!/usr/bin/env python3
import subprocess
import datetime
import json
import os
import sys

def create_scheduled_snapshot(interval):
    try:
        config_file = os.path.expanduser("~/.config/zfs-assistant/config.json")
        
        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = config.get("prefix", "zfs-assistant")
        
        for dataset in config.get("datasets", []):
            snapshot_name = f"{dataset}@{prefix}-{interval}-{timestamp}"
            subprocess.run(['zfs', 'snapshot', snapshot_name], check=True)
            print(f"Created {interval} snapshot: {snapshot_name}")
    
    except Exception as e:
        print(f"Error creating {interval} snapshot: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: zfs-assistant-systemd.py <interval>")
        sys.exit(1)
    
    interval = sys.argv[1]
    create_scheduled_snapshot(interval)
"""
            # Write the script
            script_path = SYSTEMD_SCRIPT_PATH
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make the script executable
            os.chmod(script_path, 0o755)
            
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
