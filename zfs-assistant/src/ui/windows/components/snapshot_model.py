#!/usr/bin/env python3
# ZFS Assistant - Snapshot List Model
# Author: GitHub Copilot

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GObject

class SnapshotListModel(GObject.GObject):
    """Model for managing snapshot data in the UI"""
    __gtype_name__ = 'SnapshotListModel'
    
    def __init__(self):
        super().__init__()
        self.snapshots = []

    def add_snapshot(self, snapshot):
        """Add a snapshot to the model"""
        self.snapshots.append(snapshot)
    
    def clear(self):
        """Clear all snapshots from the model"""
        self.snapshots = []
    
    def get_snapshot(self, index):
        """Get a snapshot by index"""
        if 0 <= index < len(self.snapshots):
            return self.snapshots[index]
        return None
    
    def get_snapshot_count(self):
        """Get the total number of snapshots"""
        return len(self.snapshots)
