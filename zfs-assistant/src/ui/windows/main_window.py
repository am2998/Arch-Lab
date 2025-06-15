#!/usr/bin/env python3
# ZFS Assistant - Main Window UI
# Author: GitHub Copilot

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

import sys
import os
import importlib.util

# First, try to import directly using relative imports
try:
    from ...utils.models import ZFSSnapshot
    from ..settings.settings_dialog import SettingsDialog
    
    # Try importing components 
    from .components.snapshot_model import SnapshotListModel
    from .components.layout_manager import WindowLayoutManager
    from .components.notebook_manager import NotebookManager
    from .components.data_refresh_manager import DataRefreshManager
    from .components.status_manager import StatusManager
    from .components.arc_properties_manager import ARCPropertiesManager
    
    # Try importing handlers
    from .handlers.event_handlers import EventHandlers
    from .handlers.snapshot_operations import SnapshotOperations
    
except ImportError as e:
    print(f"Relative import failed: {e}")
    
    # Fall back to absolute imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    try:
        from utils.models import ZFSSnapshot
        from ui.settings.settings_dialog import SettingsDialog
        
        # Try absolute imports for components
        from ui.windows.components.snapshot_model import SnapshotListModel
        from ui.windows.components.layout_manager import WindowLayoutManager
        from ui.windows.components.notebook_manager import NotebookManager
        from ui.windows.components.data_refresh_manager import DataRefreshManager
        from ui.windows.components.status_manager import StatusManager
        from ui.windows.components.arc_properties_manager import ARCPropertiesManager
        
        # Try absolute imports for handlers
        from ui.windows.handlers.event_handlers import EventHandlers
        from ui.windows.handlers.snapshot_operations import SnapshotOperations
    
    except ImportError as e:
        print(f"Absolute import failed: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Current file directory: {current_dir}")
        print(f"Python path: {sys.path}")
        
        # As a last resort, list available modules
        print("Available files in current directory:")
        for f in os.listdir(os.getcwd()):
            if os.path.isfile(f) and f.endswith('.py'):
                print(f"  {f}")
        
        # Re-raise the exception to indicate import failure
        raise

class MainWindow(Gtk.ApplicationWindow):
    """Main application window with modular architecture"""
    
    def __init__(self, app):
        super().__init__(application=app, title="ZFS Snapshot Assistant")
        self.app = app
        self.zfs_assistant = app.zfs_assistant
        self.snapshot_model = SnapshotListModel()
        
        # Initialize component managers
        self.layout_manager = WindowLayoutManager(self)
        self.notebook_manager = NotebookManager(self)
        self.data_refresh_manager = DataRefreshManager(self)
        self.status_manager = StatusManager(self)
        self.arc_properties_manager = ARCPropertiesManager(self)
        self.event_handlers = EventHandlers(self)
        self.snapshot_operations = SnapshotOperations(self)
        
        # Setup the window
        self._setup_window()
    
    def _setup_window(self):
        """Setup the complete window layout and functionality"""
        # Basic window properties
        self.layout_manager.setup_window_properties()
        
        # Create header bar
        self.layout_manager.create_header_bar()
        
        # Create main layout
        main_box = self.layout_manager.create_main_layout()
        
        # Create toolbar
        toolbar = self.layout_manager.create_toolbar(main_box)
        self.layout_manager.create_dataset_selection(toolbar)
        self.layout_manager.create_quick_create_area(toolbar)
        
        # Create notebook with tabs
        self.notebook_manager.create_notebook(main_box)
        
        # Create status bar
        self.layout_manager.create_status_bar(main_box)
        
        # Setup keyboard shortcuts
        self.event_handlers.setup_keyboard_shortcuts()
        
        # Connect dataset combo change event
        self.dataset_combo.connect("notify::selected", self.event_handlers.on_dataset_changed)
        
        # Setup initial status
        self._setup_initial_status()
        
        # Setup periodic updates
        self.status_manager.setup_periodic_updates()
        
        # Use GLib.timeout_add to ensure the window is fully rendered before initializing
        GLib.timeout_add(100, self._deferred_init)

    def _setup_initial_status(self):
        """Setup initial status messages"""
        if hasattr(self, 'schedule_label'):
            self.schedule_label.set_text("Schedule: Initializing...")
        if hasattr(self, 'next_snapshot_label'):
            self.next_snapshot_label.set_text("")
        if hasattr(self, 'system_update_label'):
            self.system_update_label.set_text("")
        
        # Set initial visibility
        self.status_manager._update_status_bar_visibility()

    def _deferred_init(self):
        """Initialize data after the window is fully constructed"""
        try:
            # Update dataset combo
            self.data_refresh_manager.update_dataset_combo()
            # Update snapshot list
            self.data_refresh_manager.refresh_snapshots()
            # Update dataset properties
            self.data_refresh_manager.refresh_dataset_properties()
            # Update ARC properties
            self.arc_properties_manager.refresh_arc_properties()
            # Load log content
            self.data_refresh_manager.refresh_log_content()
        except Exception as e:
            print(f"Error during deferred initialization: {e}")
        return False  # Don't repeat the timeout

    # Delegate methods to appropriate managers
    def update_dataset_combo(self):
        """Update the dataset combo box with available datasets"""
        return self.data_refresh_manager.update_dataset_combo()

    def refresh_snapshots(self):
        """Refresh the snapshot list"""
        return self.data_refresh_manager.refresh_snapshots()

    def add_snapshot_to_list(self, snapshot):
        """Add a snapshot to the snapshots list"""
        return self.data_refresh_manager.add_snapshot_to_list(snapshot)

    def refresh_dataset_properties(self):
        """Refresh the dataset properties grid"""
        return self.data_refresh_manager.refresh_dataset_properties()

    def refresh_arc_properties(self):
        """Refresh the ARC properties grid"""
        return self.arc_properties_manager.refresh_arc_properties()

    def refresh_log_content(self):
        """Refresh the log content"""
        return self.data_refresh_manager.refresh_log_content()

    def update_status(self, status_type, message):
        """Update status"""
        return self.status_manager.update_status(status_type, message)

    def update_snapshot_count(self):
        """Update the snapshot count"""
        return self.status_manager.update_snapshot_count()

    def set_status(self, message, icon=None):
        """Set a temporary status message"""
        return self.status_manager.set_status(message, icon)

    def force_status_update(self):
        """Force an immediate status update (useful after settings changes)"""
        return self.status_manager.force_status_update()
    
    def force_status_update_with_retry(self):
        """Force status update with retry mechanism for when systemd changes need time to propagate"""
        return self.status_manager.force_status_update_with_retry()

    # Event handler delegation
    def on_snapshot_selected(self, list_box, row):
        """Handle snapshot selection"""
        return self.event_handlers.on_snapshot_selected(list_box, row)

    def on_dataset_changed(self, combo, pspec):
        """Handle dataset selection change"""
        return self.event_handlers.on_dataset_changed(combo, pspec)

    def on_search_changed(self, search_entry):
        """Handle search entry text changes"""
        return self.event_handlers.on_search_changed(search_entry)

    def on_quick_create_activate(self, entry):
        """Handle Enter key press in quick create entry"""
        return self.event_handlers.on_quick_create_activate(entry)

    def on_quick_create_clicked(self, button):
        """Handle quick create button click"""
        return self.event_handlers.on_quick_create_clicked(button)

    def on_refresh_clicked(self, button):
        """Handle refresh button click"""
        return self.event_handlers.on_refresh_clicked(button)

    def on_settings_clicked(self, button):
        """Handle settings button click"""
        return self.event_handlers.on_settings_clicked(button)

    # Snapshot operations delegation
    def on_rollback_clicked(self, button):
        """Handle rollback button click"""
        return self.snapshot_operations.on_rollback_clicked(button)

    def on_clone_clicked(self, button):
        """Handle clone button click"""
        return self.snapshot_operations.on_clone_clicked(button)

    def on_delete_clicked(self, button):
        """Handle delete button click"""
        return self.snapshot_operations.on_delete_clicked(button)

    def on_delete_selected_clicked(self, button):
        """Handle delete selected snapshots button click"""
        return self.snapshot_operations.on_delete_selected_clicked(button)

    def on_unified_delete_clicked(self, button):
        """Handle unified delete button click - delegates to single or multiple deletion based on selection"""
        return self.snapshot_operations.on_unified_delete_clicked(button)

    def create_quick_snapshot(self):
        """Create a quick snapshot"""
        return self.snapshot_operations.create_quick_snapshot()

    # Properties refresh delegation
    def on_properties_refresh_clicked(self, button):
        """Handle properties refresh button click"""
        return self.status_manager.on_properties_refresh_clicked(button)

    def on_arc_refresh_clicked(self, button):
        """Handle ARC properties refresh button click"""
        return self.arc_properties_manager.on_arc_refresh_clicked(button)

    def on_arc_tunable_changed(self, entry, param_name):
        """Handle ARC tunable parameter change"""
        return self.arc_properties_manager.on_arc_tunable_changed(entry, param_name)

    def on_arc_tunable_focus_out(self, controller, param_name):
        """Handle ARC tunable parameter focus out"""
        return self.arc_properties_manager.on_arc_tunable_focus_out(controller, param_name)


