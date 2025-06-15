#!/usr/bin/env python3
# ZFS Assistant - Window Layout Manager
# Author: GitHub Copilot

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class WindowLayoutManager:
    """Manages the main window layout and UI setup"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def setup_window_properties(self):
        """Set up basic window properties"""
        # Set up the window with larger default size for better UI fit
        self.main_window.set_default_size(1200, 800)  # Increased from 900x600
        self.main_window.set_size_request(1000, 650)  # Increased minimum size from 800x500
        
        # Enable window resizing and maximize button
        self.main_window.set_resizable(True)
    
    def create_header_bar(self):
        """Create and setup the header bar"""
        header = Gtk.HeaderBar()
        self.main_window.set_titlebar(header)
        
        # Add refresh button to header
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh Snapshots")
        refresh_button.connect("clicked", self.main_window.on_refresh_clicked)
        header.pack_start(refresh_button)
        
        # Add settings button to header with better icon
        settings_button = Gtk.Button()
        settings_button.set_icon_name("applications-system-symbolic")  # Better settings icon
        settings_button.set_tooltip_text("Settings")
        settings_button.connect("clicked", self.main_window.on_settings_clicked)
        header.pack_end(settings_button)
        
        return header
    
    def create_main_layout(self):
        """Create the main window layout structure"""
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_window.set_child(main_box)
        
        return main_box
    
    def create_toolbar(self, main_box):
        """Create the toolbar area"""
        # Create modern toolbar area with more compact spacing
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)  # Reduced from 16 to 12
        toolbar.set_margin_top(10)       # Reduced from 12 to 10
        toolbar.set_margin_bottom(10)    # Reduced from 12 to 10
        toolbar.set_margin_start(12)     # Reduced from 16 to 12
        toolbar.set_margin_end(12)       # Reduced from 16 to 12
        toolbar.add_css_class("toolbar")
        toolbar.set_homogeneous(False)  # Allow flexible sizing
        main_box.append(toolbar)
        
        return toolbar
    
    def create_dataset_selection(self, toolbar):
        """Create the dataset selection area"""
        dataset_group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)  # Reduced from 6 to 4
        dataset_group.set_hexpand(False)  # Don't expand unnecessarily
        
        dataset_label = Gtk.Label(label="Dataset")
        dataset_label.add_css_class("heading")
        dataset_label.set_halign(Gtk.Align.START)
        dataset_group.append(dataset_label)
        
        # Dataset dropdown with more compact sizing
        self.main_window.dataset_combo = Gtk.DropDown()
        self.main_window.dataset_combo.set_size_request(220, 32)  # Reduced height from 36 to 32
        self.main_window.dataset_combo.add_css_class("dataset-combo")
        model = Gtk.StringList.new(["All Datasets"])
        self.main_window.dataset_combo.set_model(model)
        self.main_window.dataset_combo.set_selected(0)
        dataset_group.append(self.main_window.dataset_combo)
        
        toolbar.append(dataset_group)
        
        # Spacer to push quick create to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        return dataset_group
    
    def create_quick_create_area(self, toolbar):
        """Create the quick snapshot creation area"""
        # Quick snapshot creation area with more compact card-like styling
        quick_create_group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)  # Reduced from 8 to 6
        quick_create_group.add_css_class("quick-create-card")
        
        quick_create_label = Gtk.Label(label="Quick Create")
        quick_create_label.add_css_class("heading")
        quick_create_label.set_halign(Gtk.Align.START)
        quick_create_group.append(quick_create_label)
        
        # Input area with reduced spacing
        quick_input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)  # Reduced from 8 to 6
        
        # Quick create entry with more compact sizing
        self.main_window.quick_create_entry = Gtk.Entry()
        self.main_window.quick_create_entry.set_placeholder_text("Enter snapshot name and press Enter...")
        self.main_window.quick_create_entry.set_size_request(220, 36)  # Reduced height from 40 to 36
        self.main_window.quick_create_entry.set_hexpand(True)  # Allow expansion
        self.main_window.quick_create_entry.add_css_class("large-entry")
        self.main_window.quick_create_entry.connect("activate", self.main_window.on_quick_create_activate)
        quick_input_box.append(self.main_window.quick_create_entry)
        
        # Quick create button with consistent styling to match other action buttons
        quick_create_button = Gtk.Button()
        quick_create_button.set_icon_name("document-new-symbolic")
        quick_create_button.set_tooltip_text("Create Snapshot (Enter)")
        quick_create_button.add_css_class("action-button")
        quick_create_button.add_css_class("suggested-action")
        quick_create_button.set_size_request(100, 36)  # Match other action buttons
        quick_create_button.connect("clicked", self.main_window.on_quick_create_clicked)
        quick_input_box.append(quick_create_button)
        
        quick_create_group.append(quick_input_box)
        toolbar.append(quick_create_group)
        
        return quick_create_group
    
    def create_status_bar(self, main_box):
        """Create the status bar at the bottom"""
        # Add more compact status bar at the bottom
        self.main_window.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)  # Reduced from 12 to 10
        self.main_window.status_bar.set_margin_top(10)    # Reduced from 12 to 10
        self.main_window.status_bar.set_margin_bottom(12) # Reduced from 16 to 12
        self.main_window.status_bar.set_margin_start(16)  # Reduced from 20 to 16
        self.main_window.status_bar.set_margin_end(16)    # Reduced from 20 to 16
        self.main_window.status_bar.add_css_class("status-bar")
        self.main_window.status_bar.set_visible(True)  # Ensure it's visible
        
        # Schedule status label
        self.main_window.schedule_label = Gtk.Label(label="Schedule: Loading...")
        self.main_window.schedule_label.add_css_class("settings-status")
        self.main_window.schedule_label.set_margin_start(12)
        self.main_window.status_bar.append(self.main_window.schedule_label)
        
        # System update status label
        self.main_window.system_update_label = Gtk.Label(label="")
        self.main_window.system_update_label.add_css_class("system-update-status")
        self.main_window.system_update_label.set_margin_start(12)
        self.main_window.status_bar.append(self.main_window.system_update_label)
        
        # Next snapshot time label
        self.main_window.next_snapshot_label = Gtk.Label(label="")
        self.main_window.next_snapshot_label.add_css_class("next-snapshot")
        self.main_window.next_snapshot_label.set_margin_start(12)
        self.main_window.status_bar.append(self.main_window.next_snapshot_label)
        
        # Spacer to push snapshot count to the right
        status_spacer = Gtk.Box()
        status_spacer.set_hexpand(True)
        self.main_window.status_bar.append(status_spacer)
        
        # Separator before snapshot count
        status_separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        status_separator.set_margin_start(8)
        status_separator.set_margin_end(8)
        self.main_window.status_bar.append(status_separator)
        
        # Snapshot count label with modern styling
        self.main_window.snapshot_count_label = Gtk.Label(label="No snapshots")
        self.main_window.snapshot_count_label.add_css_class("count-badge")
        self.main_window.status_bar.append(self.main_window.snapshot_count_label)
        
        main_box.append(self.main_window.status_bar)
        
        return self.main_window.status_bar
