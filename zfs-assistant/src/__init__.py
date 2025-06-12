#!/usr/bin/env python3
# ZFS Assistant package initialization
# This file marks the src directory as a Python package

# Import key components to make them available at the package level
try:
    from .zfs_assistant import ZFSAssistant
    from .application import Application
except ImportError:
    pass
