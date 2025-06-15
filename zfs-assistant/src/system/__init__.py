#!/usr/bin/env python3
# ZFS Assistant - System Module
# Author: GitHub Copilot

"""
ZFS System Module

Contains functionality for system integration, maintenance, updates,
and package management related to ZFS.
"""

from .system_integration import SystemIntegration
from .system_maintenance import SystemMaintenance

__all__ = ['SystemIntegration', 'SystemMaintenance']
