#!/usr/bin/env python3
# ZFS Assistant - Main Window UI
# Author: GitHub Copilot

import gi
import datetime
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GObject, Gio, GLib, Gdk

try:
    # Try relative imports first
    from ...utils.models import ZFSSnapshot
    from ..settings.settings_dialog import SettingsDialog
except ImportError:
    # Fall back for direct execution
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from utils.models import ZFSSnapshot
    from ui.settings.settings_dialog import SettingsDialog

class SnapshotListModel(GObject.GObject):
    __gtype_name__ = 'SnapshotListModel'
    
    def __init__(self):
        super().__init__()
        self.snapshots = []

    def add_snapshot(self, snapshot):
        self.snapshots.append(snapshot)
    
    def clear(self):
        self.snapshots = []
    
    def get_snapshot(self, index):
        if 0 <= index < len(self.snapshots):
            return self.snapshots[index]
        return None
    
    def get_snapshot_count(self):
        return len(self.snapshots)

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="ZFS Snapshot Assistant")
        self.app = app
        self.zfs_assistant = app.zfs_assistant
        self.snapshot_model = SnapshotListModel()
        
        # Set up the window with larger default size for better UI fit
        self.set_default_size(1200, 800)  # Increased from 900x600
        self.set_size_request(1000, 650)  # Increased minimum size from 800x500
        
        # Enable window resizing and maximize button
        self.set_resizable(True)
        
        # Create header bar
        header = Gtk.HeaderBar()
        self.set_titlebar(header)
        
        # Add refresh button to header
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh Snapshots")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        header.pack_start(refresh_button)
        
        # Add settings button to header with better icon
        settings_button = Gtk.Button()
        settings_button.set_icon_name("applications-system-symbolic")  # Better settings icon
        settings_button.set_tooltip_text("Settings")
        settings_button.connect("clicked", self.on_settings_clicked)
        header.pack_end(settings_button)
        
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(main_box)
        
        # Create modern toolbar area with more compact spacing
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)  # Reduced from 16 to 12
        toolbar.set_margin_top(10)       # Reduced from 12 to 10
        toolbar.set_margin_bottom(10)    # Reduced from 12 to 10
        toolbar.set_margin_start(12)     # Reduced from 16 to 12
        toolbar.set_margin_end(12)       # Reduced from 16 to 12
        toolbar.add_css_class("toolbar")
        toolbar.set_homogeneous(False)  # Allow flexible sizing
        main_box.append(toolbar)
        
        # Dataset selection area with more compact styling
        dataset_group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)  # Reduced from 6 to 4
        dataset_group.set_hexpand(False)  # Don't expand unnecessarily
        dataset_label = Gtk.Label(label="Dataset")
        dataset_label.add_css_class("heading")
        dataset_label.set_halign(Gtk.Align.START)
        dataset_group.append(dataset_label)
        
        # Dataset dropdown with more compact sizing
        self.dataset_combo = Gtk.DropDown()
        self.dataset_combo.set_size_request(220, 32)  # Reduced height from 36 to 32
        self.dataset_combo.add_css_class("dataset-combo")
        model = Gtk.StringList.new(["All Datasets"])
        self.dataset_combo.set_model(model)
        self.dataset_combo.set_selected(0)
        dataset_group.append(self.dataset_combo)
        
        toolbar.append(dataset_group)
        
        # Spacer to push quick create to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
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
        self.quick_create_entry = Gtk.Entry()
        self.quick_create_entry.set_placeholder_text("Enter snapshot name and press Enter...")
        self.quick_create_entry.set_size_request(220, 36)  # Reduced height from 40 to 36
        self.quick_create_entry.set_hexpand(True)  # Allow expansion
        self.quick_create_entry.add_css_class("large-entry")
        self.quick_create_entry.connect("activate", self.on_quick_create_activate)
        quick_input_box.append(self.quick_create_entry)
        
        # Quick create button with consistent styling to match other action buttons
        quick_create_button = Gtk.Button()
        quick_create_button.set_icon_name("document-new-symbolic")
        quick_create_button.set_tooltip_text("Create Snapshot (Enter)")
        quick_create_button.add_css_class("action-button")
        quick_create_button.add_css_class("suggested-action")
        quick_create_button.set_size_request(100, 36)  # Match other action buttons
        quick_create_button.connect("clicked", self.on_quick_create_clicked)
        quick_input_box.append(quick_create_button)
        
        quick_create_group.append(quick_input_box)
        
        toolbar.append(quick_create_group)
        
        # Create notebook for tabs with more compact styling and responsive behavior
        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        notebook.set_hexpand(True)
        notebook.set_margin_start(16)    # Reduced from 20 to 16
        notebook.set_margin_end(16)      # Reduced from 20 to 16
        notebook.set_margin_bottom(16)   # Reduced from 20 to 16
        notebook.add_css_class("main-notebook")
        notebook.add_css_class("main-content")  # Add responsive class
        main_box.append(notebook)
        
        # Snapshots tab with modern layout
        snapshots_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Content area with reduced padding for more compact UI
        snapshots_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)  # Reduced from 16 to 12
        snapshots_content.set_margin_top(16)    # Reduced from 20 to 16
        snapshots_content.set_margin_bottom(16)  # Reduced from 20 to 16
        snapshots_content.set_margin_start(16)   # Reduced from 20 to 16
        snapshots_content.set_margin_end(16)     # Reduced from 20 to 16
        snapshots_content.set_vexpand(True)  # Allow vertical expansion
        snapshots_page.append(snapshots_content)
        
        # Search area with more compact styling (SearchEntry has built-in icon)
        search_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)  # Reduced from 12 to 10
        search_container.add_css_class("search-container")
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search snapshots by name or dataset...")
        self.search_entry.set_hexpand(True)
        self.search_entry.set_size_request(-1, 36)  # Reduced height from 40 to 36
        self.search_entry.add_css_class("large-search")
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_container.append(self.search_entry)
        
        snapshots_content.append(search_container)
        
        # Main content area with card styling
        content_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_card.add_css_class("content-card")
        content_card.set_vexpand(True)
        
        # Create scrolled window for snapshots
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_card.append(scrolled_window)
        
        # Create snapshots list with modern styling
        self.snapshots_list = Gtk.ListBox()
        self.snapshots_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.snapshots_list.connect("row-selected", self.on_snapshot_selected)
        self.snapshots_list.add_css_class("snapshots-list")
        scrolled_window.set_child(self.snapshots_list)
        
        snapshots_content.append(content_card)

        # Action bar at bottom with more compact spacing
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)  # Reduced from 12 to 10
        action_bar.set_margin_top(12)    # Reduced from 16 to 12
        action_bar.set_halign(Gtk.Align.END)
        action_bar.add_css_class("action-bar")
        
        # Action buttons with text and icons for better UX
        self.rollback_button = Gtk.Button()
        rollback_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rollback_icon = Gtk.Image.new_from_icon_name("edit-undo-symbolic")
        rollback_label = Gtk.Label(label="Rollback")
        rollback_box.append(rollback_icon)
        rollback_box.append(rollback_label)
        self.rollback_button.set_child(rollback_box)
        self.rollback_button.set_tooltip_text("Rollback to Selected Snapshot")
        self.rollback_button.connect("clicked", self.on_rollback_clicked)
        self.rollback_button.set_sensitive(False)
        self.rollback_button.add_css_class("action-button")
        self.rollback_button.set_size_request(100, 36)  # Reduced height from 40 to 36
        action_bar.append(self.rollback_button)
        
        self.clone_button = Gtk.Button()
        clone_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        clone_icon = Gtk.Image.new_from_icon_name("edit-copy-symbolic")
        clone_label = Gtk.Label(label="Clone")
        clone_box.append(clone_icon)
        clone_box.append(clone_label)
        self.clone_button.set_child(clone_box)
        self.clone_button.set_tooltip_text("Clone Selected Snapshot")
        self.clone_button.connect("clicked", self.on_clone_clicked)
        self.clone_button.set_sensitive(False)
        self.clone_button.add_css_class("action-button")
        self.clone_button.set_size_request(100, 36)  # Reduced height from 40 to 36
        action_bar.append(self.clone_button)
        
        self.delete_button = Gtk.Button()
        delete_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        delete_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
        delete_label = Gtk.Label(label="Delete")
        delete_box.append(delete_icon)
        delete_box.append(delete_label)
        self.delete_button.set_child(delete_box)
        self.delete_button.set_tooltip_text("Delete Selected Snapshot")
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.delete_button.set_sensitive(False)
        self.delete_button.add_css_class("action-button")
        self.delete_button.add_css_class("destructive-action")
        self.delete_button.set_size_request(100, 36)  # Reduced height from 40 to 36
        action_bar.append(self.delete_button)
        
        snapshots_content.append(action_bar)
        
        # Create tab label with icon
        snapshots_tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        snapshots_tab_icon = Gtk.Image.new_from_icon_name("camera-photo-symbolic")
        snapshots_tab_label = Gtk.Label(label="Snapshots")
        snapshots_tab_box.append(snapshots_tab_icon)
        snapshots_tab_box.append(snapshots_tab_label)
        
        notebook.append_page(snapshots_page, snapshots_tab_box)
        
        # Dataset Properties tab with more compact styling
        properties_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        properties_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)  # Reduced from 16 to 12
        properties_content.set_margin_top(16)    # Reduced from 20 to 16
        properties_content.set_margin_bottom(16)  # Reduced from 20 to 16
        properties_content.set_margin_start(16)   # Reduced from 20 to 16
        properties_content.set_margin_end(16)     # Reduced from 20 to 16
        properties_page.append(properties_content)
        
        # Create scrolled window for properties with modern styling
        props_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        props_card.add_css_class("content-card")
        props_card.set_vexpand(True)
        
        props_scrolled_window = Gtk.ScrolledWindow()
        props_scrolled_window.set_vexpand(True)
        props_scrolled_window.set_hexpand(True)
        props_scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        props_card.append(props_scrolled_window)
        
        # Create grid for dataset properties with more compact spacing
        self.properties_grid = Gtk.Grid()
        self.properties_grid.set_column_spacing(20)  # Reduced from 24 to 20
        self.properties_grid.set_row_spacing(10)     # Reduced from 12 to 10
        self.properties_grid.set_margin_top(16)      # Reduced from 20 to 16
        self.properties_grid.set_margin_bottom(16)   # Reduced from 20 to 16
        self.properties_grid.set_margin_start(16)    # Reduced from 20 to 16
        self.properties_grid.set_margin_end(16)      # Reduced from 20 to 16
        self.properties_grid.add_css_class("properties-grid")
        props_scrolled_window.set_child(self.properties_grid)
        
        properties_content.append(props_card)
        
        # Create dataset properties tab label with icon
        properties_tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        properties_tab_icon = Gtk.Image.new_from_icon_name("document-properties-symbolic")
        properties_tab_label = Gtk.Label(label="Dataset Properties")
        properties_tab_box.append(properties_tab_icon)
        properties_tab_box.append(properties_tab_label)
        
        notebook.append_page(properties_page, properties_tab_box)
        
        # ARC Properties tab with inline editing capabilities
        arc_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        arc_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        arc_content.set_margin_top(16)
        arc_content.set_margin_bottom(16)
        arc_content.set_margin_start(16)
        arc_content.set_margin_end(16)
        arc_page.append(arc_content)
        
        # Create ARC properties card
        arc_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        arc_card.add_css_class("content-card")
        arc_card.set_vexpand(True)
        
        # Scrolled window for ARC properties
        arc_scrolled_window = Gtk.ScrolledWindow()
        arc_scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        arc_scrolled_window.set_vexpand(True)
        arc_scrolled_window.set_min_content_height(200)
        arc_card.append(arc_scrolled_window)
        
        # Grid for ARC properties with inline editing
        self.arc_grid = Gtk.Grid()
        self.arc_grid.set_column_spacing(12)
        self.arc_grid.set_row_spacing(8)
        self.arc_grid.set_margin_top(16)
        self.arc_grid.set_margin_bottom(16)
        self.arc_grid.set_margin_start(16)
        self.arc_grid.set_margin_end(16)
        self.arc_grid.add_css_class("arc-properties-grid")
        arc_scrolled_window.set_child(self.arc_grid)
        
        arc_content.append(arc_card)
        
        # Create ARC properties tab label with icon
        arc_tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        arc_tab_icon = Gtk.Image.new_from_icon_name("applications-system-symbolic")
        arc_tab_label = Gtk.Label(label="ARC Properties")
        arc_tab_box.append(arc_tab_icon)
        arc_tab_box.append(arc_tab_label)
        
        notebook.append_page(arc_page, arc_tab_box)
        
        # Log tab for displaying log file contents
        log_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        log_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        log_content.set_margin_top(16)
        log_content.set_margin_bottom(16)
        log_content.set_margin_start(16)
        log_content.set_margin_end(16)
        log_page.append(log_content)
        
        # Create log content card
        log_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        log_card.add_css_class("content-card")
        log_card.set_vexpand(True)
        
        # Scrolled window for log content
        log_scrolled_window = Gtk.ScrolledWindow()
        log_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        log_scrolled_window.set_vexpand(True)
        log_scrolled_window.set_min_content_height(200)
        log_card.append(log_scrolled_window)
        
        # Create grid for log content like other tabs
        self.log_grid = Gtk.Grid()
        self.log_grid.set_column_spacing(20)
        self.log_grid.set_row_spacing(10)
        self.log_grid.set_margin_top(16)
        self.log_grid.set_margin_bottom(16)
        self.log_grid.set_margin_start(16)
        self.log_grid.set_margin_end(16)
        self.log_grid.add_css_class("log-grid")
        log_scrolled_window.set_child(self.log_grid)
        
        log_content.append(log_card)
        
        # Create log tab label with icon
        log_tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        log_tab_icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic")
        log_tab_label = Gtk.Label(label="Log")
        log_tab_box.append(log_tab_icon)
        log_tab_box.append(log_tab_label)
        
        notebook.append_page(log_page, log_tab_box)
        
        # Add more compact status bar at the bottom
        self.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)  # Reduced from 12 to 10
        self.status_bar.set_margin_top(10)    # Reduced from 12 to 10
        self.status_bar.set_margin_bottom(12) # Reduced from 16 to 12
        self.status_bar.set_margin_start(16)  # Reduced from 20 to 16
        self.status_bar.set_margin_end(16)    # Reduced from 20 to 16
        self.status_bar.add_css_class("status-bar")
        
        self.status_icon = Gtk.Image()
        self.status_icon.set_size_request(16, 16)
        self.status_bar.append(self.status_icon)
        
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.add_css_class("status-text")
        self.status_bar.append(self.status_label)
        
        # Spacer
        status_spacer = Gtk.Box()
        status_spacer.set_hexpand(True)
        self.status_bar.append(status_spacer)
        
        # Settings status label
        self.settings_status_label = Gtk.Label()
        self.settings_status_label.add_css_class("settings-status")
        self.status_bar.append(self.settings_status_label)
        
        # Separator
        status_separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        status_separator.set_margin_start(8)
        status_separator.set_margin_end(8)
        self.status_bar.append(status_separator)
        
        # Snapshot count label with modern styling
        self.snapshot_count_label = Gtk.Label()
        self.snapshot_count_label.add_css_class("count-badge")
        self.status_bar.append(self.snapshot_count_label)
        
        main_box.append(self.status_bar)
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Connect to dataset combo changed
        self.dataset_combo.connect("notify::selected", self.on_dataset_changed)
        
        # Use GLib.timeout_add to ensure the window is fully rendered before initializing
        GLib.timeout_add(100, self._deferred_init)
        
        # Update settings status periodically (every 15 seconds for more responsive updates)
        GLib.timeout_add_seconds(15, self._update_settings_status)
        
        # Add real-time status update triggers
        self._setup_real_time_updates()
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        # Create action group
        action_group = Gio.SimpleActionGroup()
        self.insert_action_group("window", action_group)
        
        # Quick create shortcut (Ctrl+N)
        quick_create_action = Gio.SimpleAction.new("quick-create", None)
        quick_create_action.connect("activate", lambda action, param: self.quick_create_entry.grab_focus())
        action_group.add_action(quick_create_action)
        
        # Delete shortcut (Delete key)
        delete_action = Gio.SimpleAction.new("delete-snapshot", None)
        delete_action.connect("activate", lambda action, param: self.on_delete_clicked(None) if self.delete_button.get_sensitive() else None)
        action_group.add_action(delete_action)
        
        # Search shortcut (Ctrl+F)
        search_action = Gio.SimpleAction.new("search", None)
        search_action.connect("activate", lambda action, param: self.search_entry.grab_focus())
        action_group.add_action(search_action)
        
        # Create keyboard controller
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)
        
        # Set up application accelerators
        app = self.get_application()
        if app:
            app.set_accels_for_action("window.quick-create", ["<Control>n"])
            app.set_accels_for_action("window.delete-snapshot", ["Delete"])
            app.set_accels_for_action("window.search", ["<Control>f"])
    
    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard shortcuts"""
        # ESC to clear search
        if keyval == Gdk.KEY_Escape:
            if self.search_entry.get_text():
                self.search_entry.set_text("")
                return True
        return False

    def _deferred_init(self):
        """Initialize data after the window is fully constructed"""
        try:
            # Update dataset combo
            self.update_dataset_combo()
            # Update snapshot list
            self.refresh_snapshots()
            # Update dataset properties
            self.refresh_dataset_properties()
            # Update ARC properties
            self.refresh_arc_properties()
            # Load log content
            self.refresh_log_content()
        except Exception as e:
            print(f"Error during deferred initialization: {e}")
        return False  # Don't repeat the timeout

    def update_dataset_combo(self):
        """Update the dataset combo box with available datasets"""
        model = Gtk.StringList.new([])
        
        # Add "All Datasets" option
        model.append("All Datasets")
        
        # Add available datasets (exclude root pool datasets)
        datasets = self.zfs_assistant.get_filtered_datasets()
        for dataset in datasets:
            model.append(dataset)
        
        self.dataset_combo.set_model(model)
        
        # Find a top-level dataset to use as default
        # Get all dataset names and find the first top-level one (the most parent dataset)
        if datasets:
            # Sort datasets by name length to find parent datasets first
            sorted_datasets = sorted(datasets, key=lambda d: len(d.split('/')))
            if sorted_datasets:
                # Find the index of the first dataset in the model
                first_dataset_name = sorted_datasets[0]
                for i in range(model.get_n_items()):
                    if model.get_string(i) == first_dataset_name:
                        self.dataset_combo.set_selected(i)
                        break
                else:
                    # If we couldn't find it, default to "All Datasets"
                    self.dataset_combo.set_selected(0)
            else:
                self.dataset_combo.set_selected(0)
        else:
            self.dataset_combo.set_selected(0)

    def refresh_snapshots(self):
        """Refresh the snapshot list"""
        try:
            self.update_status("loading", "Loading snapshots...")
            
            selected = self.dataset_combo.get_selected()
            model = self.dataset_combo.get_model()
            
            # Clear current list
            self.snapshots_list.remove_all()
            if selected == 0:
                # "All Datasets" is selected
                snapshots = self.zfs_assistant.get_snapshots()
            else:
                dataset = model.get_string(selected)
                snapshots = self.zfs_assistant.get_snapshots(dataset)
            
            # Add snapshots to model
            for snapshot in snapshots:
                self.add_snapshot_to_list(snapshot)
            
            # Update snapshot count
            self.update_snapshot_count()
            
            # Update status
            if snapshots:
                self.update_status("success", f"Loaded {len(snapshots)} snapshots")
            else:
                self.update_status("info", "No snapshots found")
                
        except Exception as e:
            print(f"Error refreshing snapshots: {e}")
            self.update_status("error", f"Failed to load snapshots: {e}")

    def add_snapshot_to_list(self, snapshot):
        """Add a snapshot to the snapshots list with modern card-like styling"""
        # Create a row for the snapshot
        row = Gtk.ListBoxRow()
        row.add_css_class("snapshot-row")
        
        # Create a modern card-like container with improved spacing and alignment
        card_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        card_box.set_margin_top(10)
        card_box.set_margin_bottom(10) 
        card_box.set_margin_start(16)
        card_box.set_margin_end(16)
        
        # Left side - Icon and main info with consistent spacing
        left_section = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        left_section.set_hexpand(True)
        left_section.set_halign(Gtk.Align.FILL)
        
        # Snapshot icon with consistent styling
        snapshot_icon = Gtk.Image.new_from_icon_name("camera-photo-symbolic")
        snapshot_icon.set_size_request(22, 22)
        snapshot_icon.add_css_class("snapshot-icon")
        left_section.append(snapshot_icon)
        
        # Info container with consistent spacing
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_hexpand(True)
        info_box.set_halign(Gtk.Align.FILL)
        
        # Snapshot name (primary, larger)
        name_label = Gtk.Label()
        name_label.set_markup(f"<span size='large' weight='600'>{snapshot.name}</span>")
        name_label.set_xalign(0)
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("snapshot-title")
        info_box.append(name_label)
        
        # Dataset name (secondary, smaller)
        dataset_label = Gtk.Label()
        dataset_label.set_markup(f"<span alpha='70%' size='small'>{snapshot.dataset}</span>")
        dataset_label.set_xalign(0)
        dataset_label.set_halign(Gtk.Align.START)
        dataset_label.add_css_class("snapshot-subtitle")
        info_box.append(dataset_label)
        
        left_section.append(info_box)
        card_box.append(left_section)
        
        # Right side - Metadata with consistent alignment and spacing
        right_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        right_section.set_halign(Gtk.Align.END)
        right_section.set_valign(Gtk.Align.CENTER)
        right_section.set_size_request(160, -1)  # Set minimum width for consistent alignment
        
        # Remote backup indicator (if applicable)
        if hasattr(snapshot, 'has_remote_backup') and snapshot.has_remote_backup:
            remote_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            remote_box.set_halign(Gtk.Align.END)
            remote_box.set_size_request(160, -1)  # Match parent width
            remote_icon = Gtk.Image.new_from_icon_name("network-server-symbolic")
            remote_icon.set_size_request(14, 14)
            remote_icon.add_css_class("metadata-icon")
            remote_icon.add_css_class("remote-backup")
            remote_box.append(remote_icon)
            
            remote_label = Gtk.Label()
            remote_label.set_text("Remote")
            remote_label.set_xalign(1.0)  # Right-align text
            remote_label.add_css_class("metadata-text")
            remote_label.add_css_class("remote-backup")
            remote_box.append(remote_label)
            right_section.append(remote_box)
        
        # Creation date with icon - consistent layout
        date_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        date_box.set_halign(Gtk.Align.END)
        date_box.set_size_request(160, -1)  # Match parent width
        date_icon = Gtk.Image.new_from_icon_name("x-office-calendar-symbolic")
        date_icon.set_size_request(14, 14)  # Consistent icon size
        date_icon.add_css_class("metadata-icon")
        date_box.append(date_icon)
        
        date_label = Gtk.Label()
        date_label.set_text(snapshot.formatted_creation_date)
        date_label.set_xalign(1.0)  # Right-align text
        date_label.add_css_class("metadata-text")
        date_box.append(date_label)
        right_section.append(date_box)
        
        # Size info with icon - consistent layout
        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        size_box.set_halign(Gtk.Align.END)
        size_box.set_size_request(160, -1)  # Match parent width
        size_icon = Gtk.Image.new_from_icon_name("drive-harddisk-symbolic")
        size_icon.set_size_request(14, 14)  # Consistent icon size
        size_icon.add_css_class("metadata-icon")
        size_box.append(size_icon)
        
        size_label = Gtk.Label()
        size_label.set_text(snapshot.formatted_used)
        size_label.set_xalign(1.0)  # Right-align text
        size_label.add_css_class("metadata-text")
        size_box.append(size_label)
        right_section.append(size_box)
        
        card_box.append(right_section)
        
        row.set_child(card_box)
        
        # Store references for easier access
        row.name_label = name_label
        row.dataset_label = dataset_label
        row.date_label = date_label
        row.size_label = size_label
        
        # Bind data to the row
        self._bind_snapshot_to_row(snapshot, row)
        
        # Add the row to the snapshots list
        self.snapshots_list.append(row)

    def _bind_snapshot_to_row(self, snapshot, row):
        """Bind snapshot data to a row in the snapshots list"""
        # Make sure we handle Python objects correctly
        if isinstance(snapshot, GObject.Object):
            # Extract the ZFSSnapshot object from the GObject wrapper
            snapshot = snapshot.get_property("value")
        
        # Store the snapshot object on the row's child box for later access
        box = row.get_child()
        box.snapshot = snapshot
        
        # The labels are already set in add_snapshot_to_list with the new layout
        # This method now just stores the snapshot reference

    def on_snapshot_selected(self, list_box, row):
        """Handle snapshot selection"""
        selected = row is not None
        self.rollback_button.set_sensitive(selected)
        self.clone_button.set_sensitive(selected)
        self.delete_button.set_sensitive(selected)

    def on_dataset_changed(self, combo, pspec):
        """Handle dataset selection change"""
        self.refresh_snapshots()
        self.refresh_dataset_properties()
        
    def refresh_dataset_properties(self):
        """Refresh the dataset properties grid"""
        try:
            # Clear the grid by removing all children
            while True:
                child = self.properties_grid.get_first_child()
                if not child:
                    break
                self.properties_grid.remove(child)
                
            selected = self.dataset_combo.get_selected()
            model = self.dataset_combo.get_model()
            
            if selected == 0 or selected == Gtk.INVALID_LIST_POSITION:
                # "All Datasets" is selected or no selection
                info_label = Gtk.Label(label="Select a specific dataset to view its properties")
                info_label.set_margin_top(20)
                info_label.set_margin_bottom(20)
                self.properties_grid.attach(info_label, 0, 0, 2, 1)
                return
            
            dataset_name = model.get_string(selected)
            # Get dataset properties directly
            dataset_properties = self.zfs_assistant.get_dataset_properties(dataset_name)
            
            if not dataset_properties:
                info_label = Gtk.Label(label=f"No properties found for dataset: {dataset_name}")
                info_label.set_margin_top(20)
                info_label.set_margin_bottom(20)
                self.properties_grid.attach(info_label, 0, 0, 2, 1)
                return
                
            # Add dataset header with modern styling
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            header_box.add_css_class("content-card")
            header_box.set_margin_bottom(15)
            header_box.set_margin_top(5)
            header_box.set_margin_start(21)
            header_box.set_margin_end(21)
            
            # Add dataset icon with improved styling
            icon_box = Gtk.Box()
            icon_box.set_size_request(40, 40)
            icon_box.add_css_class("snapshot-icon")
            icon_box.set_valign(Gtk.Align.CENTER)
            
            icon = Gtk.Image.new_from_icon_name("folder-symbolic")
            icon.set_pixel_size(18)
            # Fix for Gtk.Box not having set_child
            icon_box.append(icon)
            
            header_box.append(icon_box)
            
            # Dataset details in vertical layout
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            info_box.set_hexpand(True)
            
            # Dataset header with larger text like ARC Properties
            header_label = Gtk.Label()
            header_label.set_markup(f"<span size='large'><b>ZFS Dataset Properties</b></span>")
            header_label.set_xalign(0)
            header_label.set_hexpand(True)
            info_box.append(header_label)
            
            # Add summary with dataset name, type and mountpoint below the header
            type_value = dataset_properties.get("type", "N/A")
            mountpoint_value = dataset_properties.get("mountpoint", "N/A")
            
            summary_label = Gtk.Label()
            summary_label.set_markup(f"<span size='small' alpha='80%'>{dataset_name} • {type_value} • {mountpoint_value}</span>")
            summary_label.set_xalign(0)
            summary_label.set_hexpand(True)
            info_box.append(summary_label)
            
            header_box.append(info_box)
            
            # Add refresh button
            refresh_button = Gtk.Button()
            refresh_button.set_icon_name("view-refresh-symbolic")
            refresh_button.set_tooltip_text("Refresh Properties")
            refresh_button.set_valign(Gtk.Align.CENTER)
            refresh_button.add_css_class("flat")
            refresh_button.add_css_class("refresh-properties-button")
            refresh_button.connect("clicked", self.on_properties_refresh_clicked)
            header_box.append(refresh_button)
            
            self.properties_grid.attach(header_box, 0, 0, 2, 1)
            
            # Access properties and organize them into categories
            row = 1
            
            # Define property categories with readable labels
            property_categories = {
                "Storage": [
                    ("Type", "type"),
                    ("Used", "used"),
                    ("Available", "available"),
                    ("Referenced", "referenced"),
                    ("Mountpoint", "mountpoint"),
                    ("Quota", "quota"),
                    ("Reservation", "reservation"),
                ],
                "Performance": [
                    ("Compression", "compression"),
                    ("Compression Ratio", "compressratio"),
                    ("Record Size", "recordsize"),
                ],
                "Security": [
                    ("Read Only", "readonly"),
                    ("Encryption", "encryption"),
                ]
            }
            
            # Create a box to hold all property sections
            props_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
            props_box.set_margin_top(10)
            
            # Create sections for each category
            for category_name, props_list in property_categories.items():
                # Create category section
                section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                section_box.add_css_class("dataset-category")
                
                # Add category header with subtle styling
                category_label = Gtk.Label()
                category_label.set_markup(f"<b>{category_name}</b>")
                category_label.set_xalign(0)
                section_box.append(category_label)
                
                # Add properties in this category
                for label, prop_key in props_list:
                    value = dataset_properties.get(prop_key, "N/A")
                    if value == "-" or not value or value == "none":
                        value = "N/A"
                    
                    # Format specific properties nicely
                    if prop_key == "compressratio" and value != "N/A":
                        # Format compression ratio as readable value (e.g., "1.5x")
                        try:
                            ratio = float(value.strip("x"))
                            value = f"{ratio:.2f}x"
                        except:
                            pass
                    elif prop_key in ["used", "available", "referenced"] and value != "N/A":
                        # Make sure human-readable sizes have proper spacing
                        value = value.replace("K", " K").replace("M", " M").replace("G", " G").replace("T", " T")
                        
                    # Format the property row
                    prop_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                    prop_box.add_css_class("dataset-property-row")
                    
                    # Property name
                    name_label = Gtk.Label(label=f"{label}:")
                    name_label.set_xalign(0)
                    name_label.set_size_request(120, -1)  # Fixed width for alignment
                    name_label.add_css_class("dataset-property-name")
                    
                    # Property value
                    value_label = Gtk.Label(label=value)
                    value_label.set_xalign(0)
                    value_label.set_selectable(True)
                    value_label.set_hexpand(True)
                    value_label.add_css_class("dataset-property-value")
                    
                    prop_box.append(name_label)
                    prop_box.append(value_label)
                    section_box.append(prop_box)
                
                props_box.append(section_box)
                
                # Add separator between categories (except for the last one)
                if category_name != list(property_categories.keys())[-1]:
                    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                    separator.set_margin_top(5)
                    separator.set_margin_bottom(5)
                    props_box.append(separator)
            
            # Add the properties box to the grid
            self.properties_grid.attach(props_box, 0, row, 2, 1)
            
            # Make sure all is visible
            self.properties_grid.show()
        except Exception as e:
            print(f"Error refreshing dataset properties: {e}")
            # Clear any existing content first
            while True:
                child = self.properties_grid.get_first_child()
                if not child:
                    break
                self.properties_grid.remove(child)
            # Add a simple error message to the grid
            error_label = Gtk.Label(label=f"Error loading dataset properties: {str(e)}")
            error_label.set_margin_top(20)
            error_label.set_margin_bottom(20)
            self.properties_grid.attach(error_label, 0, 0, 2, 1)

    def refresh_arc_properties(self):
        """Refresh the ARC properties grid with statistics and tunables"""
        try:
            # Clear the grid by removing all children
            while True:
                child = self.arc_grid.get_first_child()
                if not child:
                    break
                self.arc_grid.remove(child)
            
            # Get ARC properties and tunables
            arc_properties = self.zfs_assistant.get_arc_properties()
            arc_tunables = self.zfs_assistant.get_arc_tunables()
            
            if not arc_properties:
                info_label = Gtk.Label(label="ARC statistics not available - ZFS may not be loaded")
                info_label.set_margin_top(20)
                info_label.set_margin_bottom(20)
                self.arc_grid.attach(info_label, 0, 0, 2, 1)
                return
            
            # Add ARC header with refresh button
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            header_box.add_css_class("content-card")
            header_box.set_margin_bottom(15)
            header_box.set_margin_top(5)
            header_box.set_margin_start(21)
            header_box.set_margin_end(21)
            
            # Add ARC icon
            icon_box = Gtk.Box()
            icon_box.set_size_request(40, 40)
            icon_box.add_css_class("snapshot-icon")
            icon_box.set_valign(Gtk.Align.CENTER)
            
            icon = Gtk.Image.new_from_icon_name("applications-system-symbolic")
            icon.set_pixel_size(18)
            icon_box.append(icon)
            header_box.append(icon_box)
            
            # ARC details
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            info_box.set_hexpand(True)
            
            header_label = Gtk.Label()
            header_label.set_markup(f"<span size='large'><b>ZFS ARC Properties</b></span>")
            header_label.set_xalign(0)
            header_label.set_hexpand(True)
            info_box.append(header_label)
            
            # Get cache size for summary
            cache_stats = arc_properties.get("Memory Usage", {})
            arc_size = cache_stats.get("ARC Size", "N/A")
            hit_rate = arc_properties.get("Cache Statistics", {}).get("Hit Rate", "N/A")
            
            summary_label = Gtk.Label()
            summary_label.set_markup(f"<span size='small' alpha='80%'>Cache Size: {arc_size} • Hit Rate: {hit_rate}</span>")
            summary_label.set_xalign(0)
            summary_label.set_hexpand(True)
            info_box.append(summary_label)
            
            header_box.append(info_box)
            
            # Add refresh button
            refresh_button = Gtk.Button()
            refresh_button.set_icon_name("view-refresh-symbolic")
            refresh_button.set_tooltip_text("Refresh ARC Properties")
            refresh_button.set_valign(Gtk.Align.CENTER)
            refresh_button.add_css_class("flat")
            refresh_button.add_css_class("refresh-properties-button")
            refresh_button.connect("clicked", self.on_arc_refresh_clicked)
            header_box.append(refresh_button)
            
            self.arc_grid.attach(header_box, 0, 0, 2, 1)
            
            row = 1
            
            # Create a box to hold all ARC sections
            arc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
            arc_box.set_margin_top(10)
            
            # Display ARC statistics
            for category_name, stats in arc_properties.items():
                section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                section_box.add_css_class("dataset-category")
                
                # Add category header
                category_label = Gtk.Label()
                category_label.set_markup(f"<b>{category_name}</b>")
                category_label.set_xalign(0)
                section_box.append(category_label)
                
                # Add statistics in this category
                for label, value in stats.items():
                    stat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                    stat_box.add_css_class("dataset-property-row")
                    
                    # Statistic name
                    name_label = Gtk.Label(label=f"{label}:")
                    name_label.set_xalign(0)
                    name_label.set_size_request(150, -1)
                    name_label.add_css_class("dataset-property-name")
                    
                    # Statistic value
                    value_label = Gtk.Label(label=str(value))
                    value_label.set_xalign(0)
                    value_label.set_selectable(True)
                    value_label.set_hexpand(True)
                    value_label.add_css_class("dataset-property-value")
                    
                    stat_box.append(name_label)
                    stat_box.append(value_label)
                    section_box.append(stat_box)
                
                arc_box.append(section_box)
                
                # Add separator between categories
                if category_name != list(arc_properties.keys())[-1] or arc_tunables:
                    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                    separator.set_margin_top(5)
                    separator.set_margin_bottom(5)
                    arc_box.append(separator)
            
            # Add tunable parameters section with inline editing
            if arc_tunables:
                tunables_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                tunables_section.add_css_class("dataset-category")
                
                # Add tunables header
                tunables_label = Gtk.Label()
                tunables_label.set_markup("<b>Tunable Parameters (Editable)</b>")
                tunables_label.set_xalign(0)
                tunables_section.append(tunables_label)
                
                # Add description
                desc_label = Gtk.Label()
                desc_label.set_markup("<span size='small' alpha='70%'>Click on values to edit. Changes require root privileges.</span>")
                desc_label.set_xalign(0)
                desc_label.set_margin_bottom(5)
                tunables_section.append(desc_label)
                
                # Add editable tunables
                for param_name, param_info in arc_tunables.items():
                    tunable_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                    tunable_box.add_css_class("dataset-property-row")
                    
                    # Parameter name with tooltip
                    name_label = Gtk.Label(label=f"{param_name.replace('zfs_', '')}:")
                    name_label.set_xalign(0)
                    name_label.set_size_request(150, -1)
                    name_label.add_css_class("dataset-property-name")
                    name_label.set_tooltip_text(param_info.get("description", ""))
                    
                    if param_info.get("editable", False):
                        # Create editable entry for tunable values
                        value_entry = Gtk.Entry()
                        value_entry.set_text(str(param_info.get("value", "")))
                        value_entry.set_hexpand(True)
                        value_entry.add_css_class("arc-tunable-entry")
                        value_entry.connect("activate", self.on_arc_tunable_changed, param_name)
                        
                        # Use focus controller for GTK4 instead of focus-out-event
                        focus_controller = Gtk.EventControllerFocus()
                        focus_controller.connect("leave", self.on_arc_tunable_focus_out, param_name)
                        value_entry.add_controller(focus_controller)
                        
                        tunable_box.append(name_label)
                        tunable_box.append(value_entry)
                    else:
                        # Read-only value
                        value_label = Gtk.Label(label=str(param_info.get("value", "N/A")))
                        value_label.set_xalign(0)
                        value_label.set_selectable(True)
                        value_label.set_hexpand(True)
                        value_label.add_css_class("dataset-property-value")
                        
                        tunable_box.append(name_label)
                        tunable_box.append(value_label)
                    
                    tunables_section.append(tunable_box)
                
                arc_box.append(tunables_section)
            
            # Add the ARC box to the grid
            self.arc_grid.attach(arc_box, 0, row, 2, 1)
            
            # Make sure all is visible
            self.arc_grid.show()
            
        except Exception as e:
            print(f"Error refreshing ARC properties: {e}")
            # Clear any existing content first
            while True:
                child = self.arc_grid.get_first_child()
                if not child:
                    break
                self.arc_grid.remove(child)
            # Add error message
            error_label = Gtk.Label(label=f"Error loading ARC properties: {str(e)}")
            error_label.set_margin_top(20)
            error_label.set_margin_bottom(20)
            self.arc_grid.attach(error_label, 0, 0, 2, 1)

    def on_refresh_clicked(self, button):
        """Handle refresh button click"""
        self.update_dataset_combo()
        self.refresh_snapshots()
        self.refresh_dataset_properties()
        self.refresh_arc_properties()
        self.refresh_log_content()
        
    def on_properties_refresh_clicked(self, button):
        """Handle properties refresh button click"""
        # Animate the button with a spinning effect
        context = button.get_style_context()
        context.add_class("refreshing")
        
        # Show a brief status message
        self.set_status("Refreshing dataset properties...", "view-refresh-symbolic")
        
        # Add a small delay for visual feedback
        GLib.timeout_add(200, self._refresh_properties_with_status, button)
        
    def _refresh_properties_with_status(self, button=None):
        """Refresh properties with status update"""
        self.refresh_dataset_properties()
        self.set_status("Dataset properties refreshed", "emblem-ok-symbolic")
        
        # Remove animation class if button provided
        if button:
            context = button.get_style_context()
            context.remove_class("refreshing")
            
        # Reset status after 2 seconds
        GLib.timeout_add(2000, lambda: self.set_status("Ready") and False)
        return False  # Don't repeat

    def on_arc_refresh_clicked(self, button):
        """Handle ARC properties refresh button click"""
        # Animate the button with a spinning effect
        context = button.get_style_context()
        context.add_class("refreshing")
        
        # Show a brief status message
        self.set_status("Refreshing ARC properties...", "view-refresh-symbolic")
        
        # Add a small delay for visual feedback
        GLib.timeout_add(200, self._refresh_arc_with_status, button)

    def _refresh_arc_with_status(self, button=None):
        """Refresh ARC properties with status update"""
        self.refresh_arc_properties()
        self.set_status("ARC properties refreshed", "emblem-ok-symbolic")
        
        # Remove animation class if button provided
        if button:
            context = button.get_style_context()
            context.remove_class("refreshing")
            
        # Reset status after 2 seconds
        GLib.timeout_add(2000, lambda: self.set_status("Ready") and False)
        return False  # Don't repeat

    def on_arc_tunable_changed(self, entry, param_name):
        """Handle ARC tunable parameter change on Enter key"""
        new_value = entry.get_text().strip()
        self._update_arc_tunable(param_name, new_value, entry)

    def on_arc_tunable_focus_out(self, controller, param_name):
        """Handle ARC tunable parameter change on focus out"""
        # Get the entry widget from the controller
        entry = controller.get_widget()
        new_value = entry.get_text().strip()
        self._update_arc_tunable(param_name, new_value, entry)

    def _update_arc_tunable(self, param_name, new_value, entry):
        """Update an ARC tunable parameter"""
        if not new_value:
            return
            
        try:
            # Show updating status
            self.set_status(f"Updating {param_name}...", "system-run-symbolic")
            
            # Validate the value (basic validation)
            try:
                int(new_value)  # Most ARC tunables are integers
            except ValueError:
                self.set_status(f"Invalid value for {param_name}: must be a number", "dialog-error-symbolic")
                # Reset to original value
                self.refresh_arc_properties()
                return
            
            # Update the tunable
            success, message = self.zfs_assistant.set_arc_tunable(param_name, new_value)
            
            if success:
                self.set_status(f"Updated {param_name} successfully", "emblem-ok-symbolic")
                # Refresh to show new value
                GLib.timeout_add(500, self.refresh_arc_properties)
            else:
                self.set_status(f"Failed to update {param_name}: {message}", "dialog-error-symbolic")
                # Reset to original value
                self.refresh_arc_properties()
            
            # Reset status after 3 seconds
            GLib.timeout_add(3000, lambda: self.set_status("Ready") and False)
            
        except Exception as e:
            self.set_status(f"Error updating {param_name}: {str(e)}", "dialog-error-symbolic")
            # Reset to original value
            self.refresh_arc_properties()
            GLib.timeout_add(3000, lambda: self.set_status("Ready") and False)

    def on_settings_clicked(self, button):
        """Handle settings button click"""
        from ..settings.settings_dialog import SettingsDialog
        settings_dialog = SettingsDialog(self)
        settings_dialog.present()

    def on_rollback_clicked(self, button):
        """Handle rollback button click"""
        selected = self.snapshots_list.get_selected_row()
        if selected is not None:
            # Get the snapshot object from the selected row
            snapshot = selected.get_child().snapshot
            
            # Create confirmation dialog
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Confirm Rollback",
                secondary_text=f"Are you sure you want to rollback dataset '{snapshot.dataset}' to snapshot '{snapshot.name}'?\n\n"
                             f"This will revert all changes made after the snapshot was created.\n"
                             f"This action cannot be undone."
            )
            
            dialog.connect("response", self._on_rollback_dialog_response, snapshot)
            dialog.present()

    def _on_rollback_dialog_response(self, dialog, response, snapshot):
        """Handle rollback dialog response"""
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Perform rollback
            snapshot_full_name = f"{snapshot.dataset}@{snapshot.name}"
            success, message = self.zfs_assistant.rollback_snapshot(snapshot_full_name)
            
            # Show result dialog
            result_dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Rollback Result",
                secondary_text=message
            )
            result_dialog.connect("response", lambda d, r: d.destroy())
            result_dialog.present()
            
            if success:
                self.refresh_snapshots()
                # Send notification
                self.app.send_app_notification("Snapshot Rollback", 
                                          f"Dataset {snapshot.dataset} has been rolled back to snapshot {snapshot.name}.")

    def on_clone_clicked(self, button):
        """Handle clone button click"""
        selected = self.snapshots_list.get_selected_row()
        if selected is not None:
            # Get the snapshot object from the selected row
            snapshot = selected.get_child().snapshot
            
            # Create clone dialog
            dialog = Gtk.Dialog(
                title="Clone Snapshot",
                transient_for=self,
                modal=True,
                destroy_with_parent=True
            )
            
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Clone", Gtk.ResponseType.OK)
            
            content_area = dialog.get_content_area()
            content_area.set_margin_top(10)
            content_area.set_margin_bottom(10)
            content_area.set_margin_start(10)
            content_area.set_margin_end(10)
            content_area.set_spacing(6)
            
            # Add target name entry
            content_area.append(Gtk.Label(label=f"Cloning snapshot: {snapshot.dataset}@{snapshot.name}"))
            content_area.append(Gtk.Label(label="Enter target dataset name:"))
            
            target_entry = Gtk.Entry()
            target_entry.set_text(f"{snapshot.dataset}-clone")
            content_area.append(target_entry)
            
            dialog.connect("response", self._on_clone_dialog_response, snapshot, target_entry)
            dialog.present()

    def _on_clone_dialog_response(self, dialog, response, snapshot, target_entry):
        """Handle clone dialog response"""
        if response == Gtk.ResponseType.OK:
            target_name = target_entry.get_text().strip()
            if target_name:
                snapshot_full_name = f"{snapshot.dataset}@{snapshot.name}"
                success, message = self.zfs_assistant.clone_snapshot(snapshot_full_name, target_name)
                
                # Show result
                if not success:
                    error_dialog = Gtk.MessageDialog(
                        transient_for=self,
                        modal=True,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Clone Error",
                        secondary_text=message
                    )
                    error_dialog.connect("response", lambda d, r: d.destroy())
                    error_dialog.present()
                else:
                    # Send notification for successful clone
                    self.app.send_app_notification("Snapshot Cloned", 
                                              f"Snapshot {snapshot.name} has been cloned to {target_name}.")
        
        dialog.destroy()

    def on_delete_clicked(self, button):
        """Handle delete button click"""
        selected = self.snapshots_list.get_selected_row()
        if selected is not None:
            # Get the snapshot object from the selected row
            snapshot = selected.get_child().snapshot
            
            # Perform delete immediately without confirmation
            snapshot_full_name = f"{snapshot.dataset}@{snapshot.name}"
            success, message = self.zfs_assistant.delete_snapshot(snapshot_full_name)
            
            # Only show dialog on error
            if not success:
                # Show error dialog
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Delete Error",
                    secondary_text=message
                )
                error_dialog.connect("response", lambda d, r: d.destroy())
                error_dialog.present()
            else:
                # Just refresh the list and send notification
                self.refresh_snapshots()
                # Send notification
                self.app.send_app_notification("Snapshot Deleted", f"Snapshot {snapshot.name} has been deleted.")

    def on_quick_create_activate(self, entry):
        """Handle Enter key press in quick create entry"""
        self.create_quick_snapshot()

    def on_quick_create_clicked(self, button):
        """Handle quick create button click"""
        self.create_quick_snapshot()

    def create_quick_snapshot(self):
        """Create a snapshot with the name from quick create entry"""
        name = self.quick_create_entry.get_text().strip()
        if not name:
            return
            
        # Get selected dataset
        selected = self.dataset_combo.get_selected()
        model = self.dataset_combo.get_model()
        
        if selected == 0:
            # "All Datasets" is selected - need to choose a dataset
            self.set_status("Please select a specific dataset to create a snapshot", "dialog-warning-symbolic")
            return
            
        dataset = model.get_string(selected)
        
        # Create snapshot
        success, message = self.zfs_assistant.create_snapshot(dataset, name)
        
        if success:
            self.quick_create_entry.set_text("")  # Clear entry
            self.refresh_snapshots()
            self.set_status(f"Created snapshot: {name}", "emblem-ok-symbolic")
            # Send notification
            self.app.send_app_notification("Snapshot Created", f"Snapshot '{name}' created for dataset '{dataset}'.")
        else:
            self.set_status(f"Failed to create snapshot: {message}", "dialog-error-symbolic")
        
        # Clear status after 3 seconds
        GLib.timeout_add(3000, lambda: self.set_status("Ready") and False)

    def on_search_changed(self, search_entry):
        """Handle search text changes"""
        search_text = search_entry.get_text().lower()
        
        # Show/hide rows based on search
        row = self.snapshots_list.get_first_child()
        while row:
            if hasattr(row, 'get_child') and row.get_child():
                snapshot = getattr(row.get_child(), 'snapshot', None)
                if snapshot:
                    # Search in snapshot name and dataset
                    visible = (search_text in snapshot.name.lower() or 
                             search_text in snapshot.dataset.lower())
                    row.set_visible(visible)
            row = row.get_next_sibling()

    def set_status(self, message, icon_name="emblem-ok-symbolic"):
        """Set status bar message with icon"""
        self.status_label.set_text(message)
        self.status_icon.set_from_icon_name(icon_name)

    def update_status(self, status_type, message):
        """Update the status bar with a message and icon"""
        icon_map = {
            "loading": "content-loading-symbolic",
            "success": "emblem-ok-symbolic", 
            "error": "dialog-error-symbolic",
            "warning": "dialog-warning-symbolic",
            "info": "dialog-information-symbolic"
        }
        
        icon = icon_map.get(status_type, "emblem-ok-symbolic")
        self.set_status(message, icon)

    def update_snapshot_count(self):
        """Update the snapshot count in status bar"""
        try:
            selected = self.dataset_combo.get_selected()
            model = self.dataset_combo.get_model()
            
            if selected == 0:
                # "All Datasets" - count all snapshots
                snapshots = self.zfs_assistant.get_snapshots()
            else:
                dataset = model.get_string(selected)
                snapshots = self.zfs_assistant.get_snapshots(dataset)
            
            count = len(snapshots) if snapshots else 0
            self.snapshot_count_label.set_text(f"{count} snapshots")
            
        except Exception as e:
            print(f"Error updating snapshot count: {e}")
            self.snapshot_count_label.set_text("0 snapshots")

    def _setup_real_time_updates(self):
        """Setup real-time status updates"""
        self._previous_settings_hash = None
        self._update_settings_status()

    def _update_settings_status(self):
        """Update the settings status display with information about enabled features"""
        try:
            config = self.zfs_assistant.config
            
            # Create a simple hash of relevant config items to detect changes
            config_items = [
                config.get("hourly_schedule", []),
                config.get("daily_schedule", []),
                config.get("weekly_schedule", False),
                config.get("monthly_schedule", False),
                config.get("pacman_integration", False),
                config.get("update_snapshots", "disabled"),
                config.get("clean_cache_after_updates", False)
            ]
            current_hash = hash(str(config_items))
            
            # Only update if something changed
            if self._previous_settings_hash == current_hash:
                return True
            
            self._previous_settings_hash = current_hash
            
            # Get settings status
            schedule_status = "on" if (config.get("hourly_schedule", []) or 
                                     config.get("daily_schedule", []) or
                                     config.get("weekly_schedule", False) or 
                                     config.get("monthly_schedule", False)) else "off"
                                     
            pacman_status = "on" if config.get("pacman_integration", False) else "off"
            update_status = "on" if config.get("update_snapshots", "disabled") != "disabled" else "off"
            clean_status = "on" if config.get("clean_cache_after_updates", False) else "off"
            
            # Build status text
            status_text = f"schedule: {schedule_status} • pacman: {pacman_status} • updates: {update_status} • clean: {clean_status}"
            
            self.settings_status_label.set_text(status_text)
            
            # Return True to allow the timeout to continue
            return True
            
        except Exception as e:
            print(f"Error updating settings status: {e}")
            return True

    def on_log_refresh_clicked(self, button):
        """Handle log refresh button click"""
        # Animate the button with a spinning effect
        context = button.get_style_context()
        context.add_class("refreshing")
        
        # Show a brief status message
        self.set_status("Refreshing log...", "view-refresh-symbolic")
        
        # Add a small delay for visual feedback
        GLib.timeout_add(200, self._refresh_log_with_status, button)

    def _refresh_log_with_status(self, button=None):
        """Refresh log content with status update"""
        self.refresh_log_content()
        self.set_status("Log refreshed", "emblem-ok-symbolic")
        
        # Remove animation class if button provided
        if button:
            context = button.get_style_context()
            context.remove_class("refreshing")
            
        # Reset status after 2 seconds
        GLib.timeout_add(2000, lambda: self.set_status("Ready") and False)
        return False  # Don't repeat

    def refresh_log_content(self):
        """Refresh the log content by reading from the log file"""
        try:
            # Clear the grid by removing all children
            while True:
                child = self.log_grid.get_first_child()
                if not child:
                    break
                self.log_grid.remove(child)
            
            log_file_path = "/var/log/zfs-assistant.log"
            
            # Add log header with refresh button
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            header_box.add_css_class("content-card")
            header_box.set_margin_bottom(15)
            header_box.set_margin_top(5)
            header_box.set_margin_start(21)
            header_box.set_margin_end(21)
            
            # Add log icon
            icon_box = Gtk.Box()
            icon_box.set_size_request(40, 40)
            icon_box.add_css_class("snapshot-icon")
            icon_box.set_valign(Gtk.Align.CENTER)
            
            icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic")
            icon.set_pixel_size(18)
            icon_box.append(icon)
            header_box.append(icon_box)
            
            # Log details
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            info_box.set_hexpand(True)
            
            header_label = Gtk.Label()
            header_label.set_markup(f"<span size='large'><b>ZFS Assistant Log</b></span>")
            header_label.set_xalign(0)
            header_label.set_hexpand(True)
            info_box.append(header_label)
            
            summary_label = Gtk.Label()
            summary_label.set_markup(f"<span size='small' alpha='80%'>Log file: /var/log/zfs-assistant.log</span>")
            summary_label.set_xalign(0)
            summary_label.set_hexpand(True)
            info_box.append(summary_label)
            
            header_box.append(info_box)
            
            # Add refresh button
            refresh_button = Gtk.Button()
            refresh_button.set_icon_name("view-refresh-symbolic")
            refresh_button.set_tooltip_text("Refresh Log")
            refresh_button.set_valign(Gtk.Align.CENTER)
            refresh_button.add_css_class("flat")
            refresh_button.add_css_class("refresh-properties-button")
            refresh_button.connect("clicked", self.on_log_refresh_clicked)
            header_box.append(refresh_button)
            
            self.log_grid.attach(header_box, 0, 0, 2, 1)
            
            row = 1
            
            # Create a box to hold the log content
            log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            log_box.set_margin_top(10)
            
            # Create scrolled window for log text
            text_scrolled_window = Gtk.ScrolledWindow()
            text_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            text_scrolled_window.set_vexpand(True)
            text_scrolled_window.set_min_content_height(300)
            
            # Text view for log content
            self.log_text_view = Gtk.TextView()
            self.log_text_view.set_editable(False)
            self.log_text_view.set_cursor_visible(False)
            self.log_text_view.set_monospace(True)
            self.log_text_view.set_margin_top(16)
            self.log_text_view.set_margin_bottom(16)
            self.log_text_view.set_margin_start(16)
            self.log_text_view.set_margin_end(16)
            self.log_text_view.add_css_class("log-text-view")
            text_scrolled_window.set_child(self.log_text_view)
            
            log_box.append(text_scrolled_window)
            
            # Get the text buffer
            buffer = self.log_text_view.get_buffer()
            
            if not os.path.exists(log_file_path):
                # Log file doesn't exist
                buffer.set_text("Log file not found. No logs available yet.\n\nThe log file will be created when ZFS Assistant performs operations.")
            else:
                try:
                    # Read the log file
                    with open(log_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if not content.strip():
                        # Log file is empty
                        buffer.set_text("Log file is empty. No logs available yet.")
                    else:
                        # Show log content
                        buffer.set_text(content)
                        
                        # Auto-scroll to the bottom to show latest entries
                        mark = buffer.get_insert()
                        iter_end = buffer.get_end_iter()
                        buffer.place_cursor(iter_end)
                        self.log_text_view.scroll_mark_onscreen(mark)
                        
                except PermissionError:
                    # No permission to read log file
                    buffer.set_text("Permission denied: Cannot read log file.\n\nThe log file requires elevated permissions to read. Try running the application with appropriate privileges.")
                except Exception as e:
                    # Other file reading errors
                    buffer.set_text(f"Error reading log file: {str(e)}\n\nThere was an issue accessing the log file. Please check that the file exists and is readable.")
            
            # Add the log box to the grid
            self.log_grid.attach(log_box, 0, row, 2, 1)
            
            # Make sure all is visible
            self.log_grid.show()
                
        except Exception as e:
            print(f"Error refreshing log content: {e}")
            # Clear any existing content first
            while True:
                child = self.log_grid.get_first_child()
                if not child:
                    break
                self.log_grid.remove(child)
            # Add error message
            error_label = Gtk.Label(label=f"Error loading log content: {str(e)}")
            error_label.set_margin_top(20)
            error_label.set_margin_bottom(20)
            self.log_grid.attach(error_label, 0, 0, 2, 1)
