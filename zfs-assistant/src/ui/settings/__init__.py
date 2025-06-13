#!/usr/bin/env python3
# ZFS Assistant - UI Settings Package
# Author: GitHub Copilot

"""
UI Settings Package

Contains settings-related UI components, organized into logical tabs and sections.
"""

from .settings_dialog import SettingsDialog
from .general_tab import GeneralSettingsTab
from .schedule_tab import ScheduleSettingsTab
from .maintenance_tab import MaintenanceSettingsTab
from .advanced_tab import AdvancedSettingsTab

__all__ = [
    'SettingsDialog',
    'GeneralSettingsTab',
    'ScheduleSettingsTab', 
    'MaintenanceSettingsTab',
    'AdvancedSettingsTab'
]
