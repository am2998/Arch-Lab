#!/usr/bin/env python3
# ZFS Assistant - Main Window UI
# Author: GitHub Copilot

import gi
import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GObject, Gio, GLib, Gdk

try:
    # Try relative imports first
    from ...models import ZFSSnapshot
    from ..settings.settings_dialog import SettingsDialog
except ImportError:
    # Fall back for direct execution
    from models import ZFSSnapshot
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
        
        # Create properties tab label with icon
        properties_tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        properties_tab_icon = Gtk.Image.new_from_icon_name("document-properties-symbolic")
        properties_tab_label = Gtk.Label(label="Properties")
        properties_tab_box.append(properties_tab_icon)
        properties_tab_box.append(properties_tab_label)
        
        notebook.append_page(properties_page, properties_tab_box)
        
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
            
            # Dataset name with styling
            header_label = Gtk.Label()
            header_label.set_markup(f"<span size='large'><b>{dataset_name}</b></span>")
            header_label.set_xalign(0)
            header_label.set_hexpand(True)
            info_box.append(header_label)
            
            # Add quick summary of type and mountpoint below the name
            type_value = dataset_properties.get("type", "N/A")
            mountpoint_value = dataset_properties.get("mountpoint", "N/A")
            
            summary_label = Gtk.Label()
            summary_label.set_markup(f"<span size='small' alpha='80%'>{type_value} • {mountpoint_value}</span>")
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

    def on_refresh_clicked(self, button):
        """Handle refresh button click"""
        self.update_dataset_combo()
        self.refresh_snapshots()
        self.refresh_dataset_properties()
        
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

    def on_cleanup_clicked(self, button):
        """Handle cleanup button click"""
        # Create confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Clean Up Snapshots",
            secondary_text="This will delete old snapshots based on your retention policy settings.\n\n"
                         "Do you want to continue?"
        )
        
        dialog.connect("response", self._on_cleanup_dialog_response)
        dialog.present()
        
    def _on_cleanup_dialog_response(self, dialog, response):
        """Handle cleanup dialog response"""
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Show progress dialog
            progress_dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.NONE,
                text="Cleaning Up Snapshots",
                secondary_text="Please wait while snapshots are being cleaned up..."
            )
            progress_dialog.present()
            
            # Run cleanup in a separate thread to avoid blocking UI
            def cleanup_thread():
                success, message = self.zfs_assistant.cleanup_snapshots()
                
                # Update UI on main thread
                GLib.idle_add(self._cleanup_completed, progress_dialog, success, message)
            
            # Start the thread
            import threading
            thread = threading.Thread(target=cleanup_thread)
            thread.daemon = True
            thread.start()
            
    def _cleanup_completed(self, progress_dialog, success, message):
        """Called when cleanup is complete"""
        progress_dialog.destroy()
        
        # Show result dialog
        result_dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Cleanup Result",
            secondary_text=message
        )
        result_dialog.connect("response", lambda d, r: d.destroy())
        result_dialog.present()
        
        # Send notification
        self.app.send_app_notification("Snapshot Cleanup Completed", message)
        
        # Refresh snapshot list
        self.refresh_snapshots()
        
        return False  # Required for GLib.idle_add

    def on_settings_clicked(self, button):
        """Handle settings button click"""
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
                text="Rollback to Snapshot",
                secondary_text=f"Are you sure you want to roll back to snapshot '{snapshot.name}'?\n\n"
                             "This will revert your dataset to the state at the time of this snapshot.\n"
                             "Any changes made after this snapshot will be lost."
            )
            
            dialog.connect("response", self._on_rollback_dialog_response, snapshot)
            dialog.present()
            
    def _on_rollback_dialog_response(self, dialog, response, snapshot):
        """Handle rollback dialog response"""
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:            # Perform rollback
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
            # Get target name
            target_name = target_entry.get_text().strip()
            
            if not target_name:
                # Show error for empty name
                error_dialog = Gtk.MessageDialog(
                    transient_for=dialog,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Invalid Target Name",
                    secondary_text="Please enter a valid target dataset name."
                )
                error_dialog.connect("response", lambda d, r: d.destroy())
                error_dialog.present()
                return
            
            # Perform clone
            snapshot_full_name = f"{snapshot.dataset}@{snapshot.name}"
            success, message = self.zfs_assistant.clone_snapshot(snapshot_full_name, target_name)
            
            # Show result dialog
            result_dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Clone Result",
                secondary_text=message
            )
            result_dialog.connect("response", lambda d, r: d.destroy())
            result_dialog.present()
            
            if success:
                self.update_dataset_combo()
        
        dialog.destroy()

    def on_delete_clicked(self, button):
        """Handle delete button click"""
        selected = self.snapshots_list.get_selected_row()
        if selected is not None:
            # Get the snapshot object from the selected row
            snapshot = selected.get_child().snapshot
            
            # Directly delete without confirmation
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
        snapshot_name = self.quick_create_entry.get_text().strip()
        
        # Get currently selected dataset
        selected = self.dataset_combo.get_selected()
        model = self.dataset_combo.get_model()
        
        if selected == 0 or selected == Gtk.INVALID_LIST_POSITION:
            self.update_status("error", "Please select a specific dataset first")
            return
        
        if not snapshot_name:
            self.update_status("error", "Please enter a snapshot name")
            return
        
        dataset = model.get_string(selected)
        
        # Update status to show progress
        self.update_status("info", f"Creating snapshot '{snapshot_name}' for {dataset}...")
        
        # Create snapshot
        success, result = self.zfs_assistant.create_snapshot(dataset, snapshot_name)
        
        if success:
            # Clear the entry
            self.quick_create_entry.set_text("")
            # Refresh snapshots
            self.refresh_snapshots()
            # Update status
            self.update_status("success", f"Snapshot '{snapshot_name}' created successfully")
            # Send notification
            self.app.send_app_notification("Snapshot Created", f"Snapshot '{snapshot_name}' has been created successfully.")
        else:
            self.update_status("error", f"Failed to create snapshot: {result}")
    
    def on_search_changed(self, search_entry):
        """Handle search text changes"""
        search_text = search_entry.get_text().lower()
        
        # Show/hide rows based on search
        for row in self.snapshots_list:
            if row.get_child():
                box = row.get_child()
                if hasattr(box, 'snapshot'):
                    snapshot = box.snapshot
                    # Search in snapshot name and dataset
                    if (search_text in snapshot.name.lower() or 
                        search_text in snapshot.dataset.lower()):
                        row.set_visible(True)
                    else:
                        row.set_visible(False)
                else:
                    row.set_visible(True)
        
        # Update the snapshot count after filtering
        self.update_snapshot_count()
    
    def update_status(self, status_type, message):
        """Update the status bar with a message and icon"""
        icon_map = {
            "success": "emblem-ok-symbolic",
            "error": "dialog-error-symbolic", 
            "warning": "dialog-warning-symbolic",
            "info": "dialog-information-symbolic",
            "loading": "view-refresh-symbolic"
        }
        
        icon_name = icon_map.get(status_type, "dialog-information-symbolic")
        self.status_icon.set_visible(True)  # Ensure icon is visible
        self.status_icon.set_from_icon_name(icon_name)
        self.status_label.set_text(message)
        
        # Auto-clear status after 5 seconds for non-error messages
        if status_type != "error":
            GLib.timeout_add_seconds(5, self._clear_status)
    
    def _clear_status(self):
        """Clear the status bar"""
        self.status_icon.set_visible(False)
        self.status_label.set_text("Ready")
        return False  # Don't repeat the timeout
    
    def update_snapshot_count(self):
        """Update the snapshot count display"""
        count = 0
        visible_count = 0
        
        for row in self.snapshots_list:
            count += 1
            if row.get_visible():
                visible_count += 1
        
        if count == visible_count:
            self.snapshot_count_label.set_text(f"{count} snapshots")
        else:
            self.snapshot_count_label.set_text(f"{visible_count} of {count} snapshots")
        
        # Also update settings status when snapshot count is updated
        self._update_settings_status()
        
    def _update_settings_status(self):
        """Update the settings status display with information about enabled features and next snapshot"""
        config = self.zfs_assistant.config
        
        # Get actual timer status from system integration instead of config values
        try:
            actual_schedule_status = self.zfs_assistant.system_integration.get_schedule_status()
            schedule_status = "on" if any(actual_schedule_status.values()) else "off"
        except Exception as e:
            # Fallback to config-based status if timer status check fails
            schedule_status = "on" if (config.get("hourly_schedule", []) or 
                                     config.get("daily_schedule", []) or
                                     config.get("weekly_schedule", False) or 
                                     config.get("monthly_schedule", False)) else "off"
                                 
        pacman_status = "on" if config.get("pacman_integration", False) else "off"
        
        # System update status depends on both the config setting AND the schedule being enabled
        # because system updates require the schedule to function
        update_config_enabled = config.get("update_snapshots", "disabled") != "disabled"
        schedule_enabled = schedule_status == "on"
        update_status = "on" if (update_config_enabled and schedule_enabled) else "off"
        
        # Clean cache status depends on BOTH system updates being enabled AND schedule being enabled
        clean_config_enabled = config.get("clean_cache_after_updates", False)
        clean_status = "on" if (clean_config_enabled and update_config_enabled and schedule_enabled) else "off"
        
        # Calculate time until next snapshot - only show if schedule is enabled
        next_snapshot_info = self._calculate_next_snapshot_time(config) if schedule_enabled else None
        
        # Build status text
        status_text = f"schedule: {schedule_status}    pacman-int: {pacman_status}    sys-update: {update_status}    clean: {clean_status}"
        
        if next_snapshot_info and schedule_enabled:
            status_text += f"    next snapshot in: {next_snapshot_info}"
        
        self.settings_status_label.set_text(status_text)
        
        # Return True to allow the timeout to continue
        return True
        
    def _calculate_next_snapshot_time(self, config):
        """Calculate the time until the next scheduled snapshot"""
        now = datetime.datetime.now()
        next_times = []
        
        # Check hourly schedule
        hourly_schedule = config.get("hourly_schedule", [])
        hourly_minute = config.get("hourly_minute", 0)
        if hourly_schedule:
            current_hour = now.hour
            current_minute = now.minute
            next_hour = None
            
            # Find the next scheduled hour
            for hour in sorted(hourly_schedule):
                if hour > current_hour or (hour == current_hour and hourly_minute > current_minute):
                    next_hour = hour
                    break
            
            # If no next hour found today, get the first hour for tomorrow
            if next_hour is None and hourly_schedule:
                next_hour = min(hourly_schedule)
                next_time = now.replace(hour=next_hour, minute=hourly_minute, second=0, microsecond=0) + datetime.timedelta(days=1)
            else:
                next_time = now.replace(hour=next_hour, minute=hourly_minute, second=0, microsecond=0)
            
            if next_hour is not None:
                next_times.append(next_time)
        
        # Check daily schedule
        daily_schedule = config.get("daily_schedule", [])
        daily_hour = config.get("daily_hour", 0)
        daily_minute = config.get("daily_minute", 0)
        
        if daily_schedule:
            current_day = now.weekday()  # 0 is Monday, 6 is Sunday
            next_day = None
            
            # Find the next scheduled day
            for day in sorted(daily_schedule):
                if day > current_day:
                    next_day = day
                    break
            
            # If no next day found this week, get the first day for next week
            if next_day is None and daily_schedule:
                next_day = min(daily_schedule)
                days_until_next = 7 - current_day + next_day
            else:
                days_until_next = next_day - current_day
            
            # Calculate the datetime for the next daily snapshot
            next_daily_time = now.replace(hour=daily_hour, minute=daily_minute, second=0, microsecond=0)
            
            # If the scheduled time for today has passed, add the days until next
            if days_until_next == 0 and now > next_daily_time:
                days_until_next = 7
            
            next_daily_time += datetime.timedelta(days=days_until_next)
            next_times.append(next_daily_time)
        
        # Check weekly schedule
        if config.get("weekly_schedule", False):
            # Assume weekly snapshots happen on Sunday at the daily hour and minute
            current_day = now.weekday()
            days_until_sunday = 6 - current_day  # 6 is Sunday
            weekly_time = now.replace(hour=daily_hour, minute=daily_minute, second=0, microsecond=0)
            if days_until_sunday == 0 and now > weekly_time:
                days_until_sunday = 7
            
            next_weekly_time = weekly_time + datetime.timedelta(days=days_until_sunday)
            next_times.append(next_weekly_time)
        
        # Check monthly schedule
        if config.get("monthly_schedule", False):
            # Assume monthly snapshots happen on the 1st of each month at the daily hour and minute
            current_day = now.day
            monthly_time = now.replace(hour=daily_hour, minute=daily_minute, second=0, microsecond=0)
            
            if current_day == 1 and now < monthly_time:
                # It's the 1st and the scheduled time hasn't passed yet
                next_monthly_time = monthly_time
            else:
                # Move to the 1st of next month
                if now.month == 12:
                    next_month = 1
                    next_year = now.year + 1
                else:
                    next_month = now.month + 1
                    next_year = now.year
                
                next_monthly_time = datetime.datetime(year=next_year, month=next_month, day=1, hour=daily_hour, minute=daily_minute, second=0)
            
            next_times.append(next_monthly_time)
        
        # Find the earliest next snapshot time
        if not next_times:
            return None
        
        next_snapshot_time = min(next_times)
        time_diff = next_snapshot_time - now
        
        # Format the time difference
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
        
        return None
    def _setup_real_time_updates(self):
        """Setup real-time updates for status bar and UI elements"""
        # Store previous settings hash to detect changes
        self._previous_settings_hash = None
        
        # Start frequent status checks (every 2 seconds for quick response)
        GLib.timeout_add_seconds(2, self._check_for_settings_changes)
    
    def _check_for_settings_changes(self):
        """Check if settings have changed and update status immediately"""
        try:
            # Create a hash of current settings to detect changes
            config = self.zfs_assistant.config
            settings_data = {
                'auto_snapshot': config.get('auto_snapshot', False),
                'hourly_schedule': config.get('hourly_schedule', []),
                'daily_schedule': config.get('daily_schedule', []),
                'weekly_schedule': config.get('weekly_schedule', False),
                'monthly_schedule': config.get('monthly_schedule', False),
                'pacman_integration': config.get('pacman_integration', False),
                'update_snapshots': config.get('update_snapshots', 'disabled'),
                'clean_cache_after_updates': config.get('clean_cache_after_updates', False)
            }
            
            # Get actual timer states for comparison
            try:
                actual_schedule_status = self.zfs_assistant.system_integration.get_schedule_status()
                settings_data['actual_timers'] = actual_schedule_status
            except:
                settings_data['actual_timers'] = {}
            
            current_hash = hash(str(sorted(settings_data.items())))
            
            # If settings changed, update status immediately
            if self._previous_settings_hash != current_hash:
                self._previous_settings_hash = current_hash
                self._update_settings_status()
                
        except Exception as e:
            print(f"Error checking for settings changes: {e}")
        
        # Continue checking
        return True

    def trigger_status_update(self):
        """Trigger an immediate status update - can be called externally"""
        self._previous_settings_hash = None  # Force update
        self._update_settings_status()
        
        # Also trigger snapshot count update for consistency
        GLib.idle_add(self.update_snapshot_count)
