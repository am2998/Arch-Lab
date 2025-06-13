#!/usr/bin/env python3
# ZFS Assistant - Common utilities and constants
# Author: GitHub Copilot

import os
import subprocess
import datetime

# Application constants
APP_NAME = "ZFS Snapshot Assistant"
APP_ID = "org.archlinux.zfsassistant"
VERSION = "1.0.0"

# Default window sizes
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 500

# Configuration defaults
DEFAULT_CONFIG = {
    "auto_snapshot": True,
    "snapshot_retention": {
        "hourly": 24,
        "daily": 7,
        "weekly": 4,
        "monthly": 12
    },    "hourly_schedule": [8, 12, 16, 20],  # Default to business hours
    "daily_schedule": [0, 1, 2, 3, 4],    # Default to weekdays
    "daily_hour": 0,                      # Default hour for daily snapshots
    "weekly_schedule": True,              # Enable weekly by default
    "monthly_schedule": True,             # Enable monthly by default
    "datasets": [],
    "pacman_integration": True,
    "update_snapshots": "disabled",       # Options: "disabled", "enabled", "pacman_only"
    "clean_cache_after_updates": False,   # Default to not cleaning cache
    "snapshot_name_format": "prefix-type-timestamp", # Default snapshot naming format
    "prefix": "zfs-assistant",
    "external_backup_enabled": False,     # Default to disabled external backup
    "external_pool_name": "",             # No default external pool
    "backup_frequency": "Manual",         # Default backup frequency
    "dark_mode": False,
    "notifications_enabled": True
}

# File paths
def get_config_dir():
    """Get the configuration directory, handling elevated privileges properly"""
    # Check if we're running with elevated privileges
    if os.geteuid() == 0:
        # We're running as root - try to get the original user's config dir
        
        # First, check if SUDO_USER is set (when using sudo)
        if 'SUDO_USER' in os.environ:
            original_user = os.environ['SUDO_USER']
            # Get the original user's home directory
            import pwd
            try:
                user_info = pwd.getpwnam(original_user)
                user_home = user_info.pw_dir
                return os.path.join(user_home, ".config", "zfs-assistant")
            except KeyError:
                pass
        
        # Check for PKEXEC_UID (when using pkexec)
        if 'PKEXEC_UID' in os.environ:
            try:
                import pwd
                original_uid = int(os.environ['PKEXEC_UID'])
                user_info = pwd.getpwuid(original_uid)
                user_home = user_info.pw_dir
                return os.path.join(user_home, ".config", "zfs-assistant")
            except (KeyError, ValueError):
                pass
        
        # Fallback: try to detect the user who owns the current session
        # Look for common user directories that might indicate the original user
        for potential_user in os.listdir('/home'):
            user_config_dir = f"/home/{potential_user}/.config/zfs-assistant"
            if os.path.exists(user_config_dir):
                return user_config_dir
    
    # Default: use the current user's home directory
    return os.path.expanduser("~/.config/zfs-assistant")

CONFIG_DIR = get_config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
LOG_FILE = os.path.join(CONFIG_DIR, "zfs-assistant.log")
PACMAN_HOOK_PATH = "/etc/pacman.d/hooks/00-zfs-snapshot.hook"
SYSTEMD_SCRIPT_PATH = os.path.expanduser("~/.local/bin/zfs-assistant-systemd.py")
PACMAN_SCRIPT_PATH = os.path.expanduser("~/.local/bin/zfs-assistant-pacman-hook.py")

# Utility functions
def run_command(cmd, capture_output=True, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=capture_output, 
            text=True, 
            check=check
        )
        return True, result
    except subprocess.CalledProcessError as e:
        return False, e
    except Exception as e:
        return False, e

def get_timestamp():
    """Get current timestamp formatted for filenames"""
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
