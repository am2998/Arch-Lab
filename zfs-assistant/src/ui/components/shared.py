#!/usr/bin/env python3
# ZFS Assistant - Shared UI Components
# Author: GitHub Copilot

"""
Shared UI components and utilities for consistent styling and behavior across the application.
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

class FrameWithContent:
    """Utility class to create consistent frame layouts"""
    
    @staticmethod
    def create(title, margin=10, spacing=6):
        """Create a frame with a content box inside"""
        frame = Gtk.Frame()
        frame.set_label(title)
        frame.set_margin_bottom(margin)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
        content_box.set_margin_top(margin)
        content_box.set_margin_bottom(margin)
        content_box.set_margin_start(margin)
        content_box.set_margin_end(margin)
        frame.set_child(content_box)
        
        return frame, content_box

class ButtonBox:
    """Utility class to create consistent button layouts"""
    
    @staticmethod
    def create_horizontal(spacing=10, homogeneous=False, margin_top=0):
        """Create a horizontal button box"""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=spacing)
        button_box.set_homogeneous(homogeneous)
        if margin_top > 0:
            button_box.set_margin_top(margin_top)
        return button_box

class LabeledEntry:
    """Utility class to create labeled entry widgets"""
    
    @staticmethod
    def create(label_text, entry_text="", label_width=140, entry_width=200, placeholder=""):
        """Create a labeled entry widget"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_halign(Gtk.Align.START)
        
        label = Gtk.Label(label=label_text)
        label.set_size_request(label_width, -1)
        label.set_halign(Gtk.Align.START)
        box.append(label)
        
        entry = Gtk.Entry()
        entry.set_text(entry_text)
        entry.set_size_request(entry_width, -1)
        if placeholder:
            entry.set_placeholder_text(placeholder)
        box.append(entry)
        
        return box, label, entry

class LabeledSwitch:
    """Utility class to create labeled switch widgets"""
    
    @staticmethod
    def create(label_text, active=False):
        """Create a labeled switch widget"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        label = Gtk.Label(label=label_text)
        switch = Gtk.Switch()
        switch.set_active(active)
        
        box.append(label)
        box.append(switch)
        
        return box, label, switch

class InfoLabel:
    """Utility class to create consistent info/help labels"""
    
    @staticmethod
    def create(text, margin_start=0, margin_top=5):
        """Create an info label with dim styling"""
        label = Gtk.Label(label=text)
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(margin_start)
        label.set_margin_top(margin_top)
        label.add_css_class("dim-label")
        label.set_wrap(True)
        return label

class ResponsiveGrid:
    """Utility class to create responsive grid layouts"""
    
    @staticmethod
    def create(columns=2, row_spacing=8, column_spacing=20, homogeneous=True):
        """Create a responsive grid layout"""
        grid = Gtk.Grid()
        grid.set_column_spacing(column_spacing)
        grid.set_row_spacing(row_spacing)
        grid.set_column_homogeneous(homogeneous)
        return grid
