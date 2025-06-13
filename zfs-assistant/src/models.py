#!/usr/bin/env python3
# ZFS Assistant - ZFSSnapshot class
# Author: GitHub Copilot

import datetime

class ZFSSnapshot:
    """
    Represents a ZFS snapshot with its properties
    """
    
    def __init__(self, name, creation_date, dataset, used=None, referenced=None):
        self._name = name
        self._creation_date = creation_date
        self._dataset = dataset
        self._used = used
        self._referenced = referenced
        
    @property
    def name(self):
        return self._name
        
    @property
    def creation_date(self):
        return self._creation_date
        
    @property
    def dataset(self):
        return self._dataset
        
    @property
    def used(self):
        return self._used
        
    @property
    def referenced(self):
        return self._referenced
        
    @property
    def full_name(self):
        """Get the full snapshot name (dataset@snapshot)"""
        return f"{self.dataset}@{self.name}"
        
    @property
    def formatted_creation_date(self):
        """Get formatted creation date"""
        if isinstance(self.creation_date, datetime.datetime):
            return self.creation_date.strftime("%Y-%m-%d %H:%M")
        return str(self.creation_date)
        
    @property
    def formatted_used(self):
        """Get formatted used size"""
        return self.used or "0 B"
        
    @property
    def formatted_referenced(self):
        """Get formatted referenced size"""
        return self.referenced or "0 B"

    @staticmethod
    def from_zfs_list(line):
        """
        Parse a line from zfs list -t snapshot output
        """
        parts = line.strip().split('\t')
        if len(parts) < 4:
            return None

        full_name = parts[0]
        # Extract dataset and snapshot name
        name_parts = full_name.split('@')
        if len(name_parts) != 2:
            return None

        dataset = name_parts[0]
        name = name_parts[1]
        creation = parts[1]
        used = parts[2]
        referenced = parts[3]

        # Convert creation time format
        try:
            # Try to parse creation date
            creation_date = datetime.datetime.strptime(creation, "%a %b %d %H:%M %Y")
        except ValueError:
            creation_date = creation  # Use the original string if parsing fails

        return ZFSSnapshot(name, creation_date, dataset, used, referenced)
        
    def __str__(self):
        """String representation of the snapshot"""
        return f"{self.full_name} ({self.formatted_creation_date})"
        
    def __repr__(self):
        """Detailed representation of the snapshot"""
        return (f"ZFSSnapshot(name='{self.name}', "
                f"dataset='{self.dataset}', "
                f"creation_date='{self.creation_date}', "
                f"used='{self.used}', "
                f"referenced='{self.referenced}')")
