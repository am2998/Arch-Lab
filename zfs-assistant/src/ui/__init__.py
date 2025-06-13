#!/usr/bin/env python3
# ZFS Assistant - UI Package
# Author: GitHub Copilot

"""
UI Package for ZFS Assistant

This package contains all user interface components organized into logical submodules:
- windows: Main application windows
- dialogs: Modal dialog windows  
- settings: Settings-related UI components
- components: Reusable UI components and widgets
"""

# Import main UI components for easier access
from .windows.main_window import MainWindow
from .dialogs.create_snapshot_dialog import CreateSnapshotDialog
from .settings.settings_dialog import SettingsDialog

__all__ = [
    'MainWindow',
    'CreateSnapshotDialog', 
    'SettingsDialog'
]
