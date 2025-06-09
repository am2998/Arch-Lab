#!/usr/bin/env python3
# ZFS Manager - Common utilities and constants
# Author: GitHub Copilot

import os
import json
import subprocess
import datetime

# Application constants
APP_NAME = "ZFS Snapshot Manager"
APP_ID = "org.archlinux.zfsmanager"
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
    },
    "datasets": [],
    "pacman_integration": True,
    "prefix": "zfs-manager",
    "dark_mode": False,
    "notifications_enabled": True
}

# File paths
CONFIG_DIR = os.path.expanduser("~/.config/zfs-manager")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
PACMAN_HOOK_PATH = "/etc/pacman.d/hooks/00-zfs-snapshot.hook"
SYSTEMD_SCRIPT_PATH = "/usr/local/bin/zfs-manager-systemd.py"
PACMAN_SCRIPT_PATH = "/usr/local/bin/zfs-manager-pacman-hook.py"

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

def format_size(size_str):
    """Format size string for display"""
    if not size_str or size_str == "-" or size_str.lower() == "none":
        return "0 B"
    
    # Return as is if already formatted
    if any(unit in size_str for unit in ["B", "K", "M", "G", "T", "P"]):
        return size_str
    
    try:
        size = float(size_str)
        units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"
    except (ValueError, TypeError):
        return size_str

def format_datetime(dt):
    """Format datetime for display"""
    if isinstance(dt, datetime.datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt)

def get_timestamp():
    """Get current timestamp formatted for filenames"""
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
