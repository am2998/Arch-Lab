#!/usr/bin/env python3
# ZFS Assistant - Root Package
# Author: GitHub Copilot

"""
ZFS Assistant - A GTK-based tool for managing ZFS snapshots

This application provides a simple interface for managing ZFS snapshots,
clones, and system maintenance operations.
"""

# Main application components
from .zfs_assistant import ZFSAssistant
from .application import Application

# Import subpackages
from . import core
from . import backup
from . import system
from . import ui
from . import utils

__version__ = "1.0.0"
__author__ = "GitHub Copilot"
__all__ = [
    'ZFSAssistant',
    'Application',
    'core',
    'backup',
    'system',
    'ui',
    'utils'
]
