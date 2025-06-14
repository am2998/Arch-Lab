#!/usr/bin/env python3
# ZFS Assistant - General Settings Tab
# Author: GitHub Copilot

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

class GeneralSettingsTab:
    """General settings tab for dataset selection and appearance"""
    
    def __init__(self, parent_dialog):
        self.dialog = parent_dialog
        self.zfs_assistant = parent_dialog.zfs_assistant
        self.config = parent_dialog.config
        
        # Build the general settings UI
        self._build_ui()
    
    def _build_ui(self):
        """Build the general settings tab UI"""
        # Create main container
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.box.set_margin_top(10)
        self.box.set_margin_bottom(10)
        self.box.set_margin_start(10)
        self.box.set_margin_end(10)
        
        # Appearance section
        self._create_appearance_section()
    
    def _create_appearance_section(self):
        """Create the appearance settings section"""
        appearance_frame = Gtk.Frame()
        appearance_frame.set_label("Appearance")
        appearance_frame.set_margin_bottom(10)
        self.box.append(appearance_frame)
        
        appearance_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        appearance_box.set_margin_top(10)
        appearance_box.set_margin_bottom(10)
        appearance_box.set_margin_start(10)
        appearance_box.set_margin_end(10)
        appearance_frame.set_child(appearance_box)
        
        # Dark mode switch
        dark_mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dark_mode_box.append(Gtk.Label(label="Dark Mode:"))
        self.dark_mode_switch = Gtk.Switch()
        self.dark_mode_switch.set_active(self.config.get("dark_mode", False))
        dark_mode_box.append(self.dark_mode_switch)
        appearance_box.append(dark_mode_box)
        
        # Notifications switch
        notif_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        notif_box.append(Gtk.Label(label="Enable Notifications:"))
        self.notifications_switch = Gtk.Switch()
        self.notifications_switch.set_active(self.config.get("notifications_enabled", True))
        notif_box.append(self.notifications_switch)
        appearance_box.append(notif_box)
    
    def get_box(self):
        """Get the main container widget"""
        return self.box
    
    def apply_settings(self, config):
        """Apply settings from this tab to the config"""
        # Update appearance settings
        config["dark_mode"] = self.dark_mode_switch.get_active()
        config["notifications_enabled"] = self.notifications_switch.get_active()
        
        return config
