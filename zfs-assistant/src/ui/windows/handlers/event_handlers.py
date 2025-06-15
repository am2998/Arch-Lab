#!/usr/bin/env python3
# ZFS Assistant - Event Handlers
# Author: GitHub Copilot

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Gio

class EventHandlers:
    """Handles various UI events and user interactions"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        # Create action group
        action_group = Gio.SimpleActionGroup()
        self.main_window.insert_action_group("window", action_group)
        
        # Quick create shortcut (Ctrl+N)
        quick_create_action = Gio.SimpleAction.new("quick-create", None)
        quick_create_action.connect("activate", lambda action, param: self.main_window.quick_create_entry.grab_focus())
        action_group.add_action(quick_create_action)
        
        # Delete shortcut (Delete key)
        delete_action = Gio.SimpleAction.new("delete-snapshot", None)
        delete_action.connect("activate", lambda action, param: self.main_window.on_unified_delete_clicked(None) if self.main_window.delete_button.get_sensitive() else None)
        action_group.add_action(delete_action)
        
        # Search shortcut (Ctrl+F)
        search_action = Gio.SimpleAction.new("search", None)
        search_action.connect("activate", lambda action, param: self.main_window.search_entry.grab_focus())
        action_group.add_action(search_action)
        
        # Create keyboard controller
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.main_window.add_controller(key_controller)
        
        # Set up application accelerators
        app = self.main_window.get_application()
        if app:
            app.set_accels_for_action("window.quick-create", ["<Control>n"])
            app.set_accels_for_action("window.delete-snapshot", ["Delete"])
            app.set_accels_for_action("window.search", ["<Control>f"])
    
    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard shortcuts"""
        # ESC to clear search or deselect all snapshots
        if keyval == Gdk.KEY_Escape:
            if self.main_window.search_entry.get_text():
                self.main_window.search_entry.set_text("")
                return True
            else:
                # Deselect all snapshots
                self.main_window.snapshots_list.unselect_all()
                self.main_window.on_snapshot_selected(self.main_window.snapshots_list, None)
                return True
        return False
    
    def on_snapshot_selected(self, list_box, row):
        """Handle snapshot selection"""
        # Get all selected rows
        selected_rows = []
        def collect_selected(child):
            if child.is_selected():
                selected_rows.append(child)
        
        # Iterate through all children to find selected ones
        child = list_box.get_first_child()
        while child is not None:
            if child.is_selected():
                selected_rows.append(child)
            child = child.get_next_sibling()
        
        num_selected = len(selected_rows)
        
        # Enable/disable single selection buttons (rollback, clone)
        single_selected = num_selected == 1
        self.main_window.rollback_button.set_sensitive(single_selected)
        self.main_window.clone_button.set_sensitive(single_selected)
        
        # Enable/disable unified delete button and update its appearance
        any_selected = num_selected > 0
        self.main_window.delete_button.set_sensitive(any_selected)
        
        # Show/hide clear selection button
        self.main_window.clear_selection_button.set_visible(any_selected)
        self.main_window.clear_selection_button.set_sensitive(any_selected)
        
        if any_selected:
            if num_selected == 1:
                # Single selection mode
                self.main_window.delete_icon.set_from_icon_name("user-trash-symbolic")
                self.main_window.delete_label.set_text("Delete")
                self.main_window.delete_button.set_tooltip_text("Delete Selected Snapshot")
            else:
                # Multiple selection mode
                self.main_window.delete_icon.set_from_icon_name("user-trash-full-symbolic")
                if num_selected <= 99:
                    self.main_window.delete_label.set_text(f"Delete ({num_selected})")
                else:
                    self.main_window.delete_label.set_text(f"Delete (99+)")
                self.main_window.delete_button.set_tooltip_text(f"Delete {num_selected} Selected Snapshots")
        else:
            # No selection
            self.main_window.delete_icon.set_from_icon_name("user-trash-symbolic")
            self.main_window.delete_label.set_text("Delete")
            self.main_window.delete_button.set_tooltip_text("Delete Selected Snapshot(s)")

    def on_dataset_changed(self, combo, pspec):
        """Handle dataset selection change"""
        self.main_window.refresh_snapshots()
        self.main_window.refresh_dataset_properties()
        
    def on_search_changed(self, search_entry):
        """Handle search entry text changes"""
        search_text = search_entry.get_text().lower()
        
        # Filter snapshots based on search text
        child = self.main_window.snapshots_list.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            
            if search_text:
                # Get snapshot from the row
                try:
                    snapshot = child.get_child().snapshot
                    # Check if search text matches snapshot name or dataset
                    visible = (search_text in snapshot.name.lower() or 
                             search_text in snapshot.dataset.lower())
                    child.set_visible(visible)
                except:
                    # If we can't get snapshot data, keep it visible
                    child.set_visible(True)
            else:
                # Show all when search is empty
                child.set_visible(True)
            
            child = next_child

    def on_quick_create_activate(self, entry):
        """Handle Enter key press in quick create entry"""
        self.main_window.create_quick_snapshot()

    def on_quick_create_clicked(self, button):
        """Handle quick create button click"""
        self.main_window.create_quick_snapshot()

    def on_refresh_clicked(self, button):
        """Handle refresh button click"""
        self.main_window.update_dataset_combo()
        self.main_window.refresh_snapshots()
        self.main_window.refresh_dataset_properties()
        self.main_window.refresh_arc_properties()
        self.main_window.refresh_log_content()
        
    def on_settings_clicked(self, button):
        """Handle settings button click"""
        from ...settings.settings_dialog import SettingsDialog
        settings_dialog = SettingsDialog(self.main_window)
        settings_dialog.present()
