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
        
        # Datasets section
        self._create_datasets_section()
        
        # Appearance section
        self._create_appearance_section()
    
    def _create_datasets_section(self):
        """Create the managed datasets selection section"""
        datasets_frame = Gtk.Frame()
        datasets_frame.set_label("Managed Datasets")
        datasets_frame.set_margin_bottom(10)
        self.box.append(datasets_frame)
        
        datasets_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        datasets_box.set_margin_top(10)
        datasets_box.set_margin_bottom(10)
        datasets_box.set_margin_start(10)
        datasets_box.set_margin_end(10)
        datasets_frame.set_child(datasets_box)
        
        # Dataset list with checkboxes
        datasets_scroll = Gtk.ScrolledWindow()
        datasets_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        datasets_scroll.set_size_request(-1, 150)  # Set reasonable height
        datasets_scroll.set_vexpand(True)
        datasets_box.append(datasets_scroll)
        
        # Create a list box for datasets
        self.datasets_list = Gtk.ListBox()
        self.datasets_list.set_selection_mode(Gtk.SelectionMode.NONE)
        datasets_scroll.set_child(self.datasets_list)
        
        # Get available datasets (exclude root pool datasets)
        datasets = self.zfs_assistant.get_filtered_datasets()
        managed_datasets = self.config.get("datasets", [])
        
        # Add datasets to the list
        if datasets:
            for dataset in datasets:
                dataset_name = dataset
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                box.set_margin_start(5)
                box.set_margin_end(5)
                
                check = Gtk.CheckButton(label=dataset_name)
                check.set_active(dataset_name in managed_datasets)
                box.append(check)
                
                row.set_child(box)
                self.datasets_list.append(row)
        
        # Add buttons for selecting all/none
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_margin_top(10)
        
        select_all_button = Gtk.Button(label="Select All")
        select_all_button.connect("clicked", self.on_select_all_clicked)
        button_box.append(select_all_button)
        
        select_none_button = Gtk.Button(label="Select None")
        select_none_button.connect("clicked", self.on_select_none_clicked)
        button_box.append(select_none_button)
        
        datasets_box.append(button_box)
    
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
    
    def on_select_all_clicked(self, button):
        """Handle select all button click"""
        for row in self.datasets_list:
            box = row.get_child()
            check = box.get_first_child()
            check.set_active(True)
    
    def on_select_none_clicked(self, button):
        """Handle select none button click"""
        for row in self.datasets_list:
            box = row.get_child()
            check = box.get_first_child()
            check.set_active(False)
    
    def apply_settings(self, config):
        """Apply settings from this tab to the config"""
        # Update appearance settings
        config["dark_mode"] = self.dark_mode_switch.get_active()
        config["notifications_enabled"] = self.notifications_switch.get_active()
        
        # Update managed datasets
        managed_datasets = []
        if hasattr(self, 'datasets_list'):
            for row in self.datasets_list:
                box = row.get_child()
                check = box.get_first_child()
                if check.get_active():
                    managed_datasets.append(check.get_label())
        
        config["datasets"] = managed_datasets
        
        return config
