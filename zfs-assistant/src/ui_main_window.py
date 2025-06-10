#!/usr/bin/env python3
# ZFS Assistant - Main Window UI
# Author: GitHub Copilot

import gi
import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, GObject

from .models import ZFSSnapshot
from .ui_settings_dialog import SettingsDialog
from .ui_create_snapshot_dialog import CreateSnapshotDialog

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
        
        # Set up the window
        self.set_default_size(900, 600)
        self.set_size_request(800, 500)
        
        # Create header bar
        header = Gtk.HeaderBar()
        self.set_titlebar(header)
        
        # Add refresh button to header
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh Snapshots")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        header.pack_start(refresh_button)
        
        # Add settings button to header
        settings_button = Gtk.Button()
        settings_button.set_icon_name("emblem-system-symbolic")
        settings_button.set_tooltip_text("Settings")
        settings_button.connect("clicked", self.on_settings_clicked)
        header.pack_end(settings_button)
        
        # Create snapshot button
        create_button = Gtk.Button(label="Create Snapshot")
        create_button.connect("clicked", self.on_create_snapshot_clicked)
        header.pack_end(create_button)
        
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_child(main_box)
        
        # Create top area for dataset selection
        top_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        top_area.set_margin_top(10)
        top_area.set_margin_bottom(10)
        top_area.set_margin_start(10)
        top_area.set_margin_end(10)
        main_box.append(top_area)
        
        # Dataset label
        dataset_label = Gtk.Label(label="Dataset:")
        top_area.append(dataset_label)
        
        # Dataset dropdown - initialize with empty model
        self.dataset_combo = Gtk.DropDown()
        model = Gtk.StringList.new(["All Datasets"])
        self.dataset_combo.set_model(model)
        self.dataset_combo.set_selected(0)
        top_area.append(self.dataset_combo)
        
        # Create notebook for tabs
        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        notebook.set_hexpand(True)
        main_box.append(notebook)
        
        # Snapshots tab
        snapshots_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        notebook.append_page(snapshots_box, Gtk.Label(label="Snapshots"))
        
        # Create scrolled window for snapshots
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        snapshots_box.append(scrolled_window)
        
        # Create snapshots list with a ListBox
        self.snapshots_list = Gtk.ListBox()
        self.snapshots_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.snapshots_list.connect("row-selected", self.on_snapshot_selected)
        scrolled_window.set_child(self.snapshots_list)

        # Create action buttons area for snapshots
        action_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_area.set_homogeneous(True)
        action_area.set_margin_top(10)
        action_area.set_margin_bottom(10)
        action_area.set_margin_start(10)
        action_area.set_margin_end(10)
        snapshots_box.append(action_area)
        
        # Add action buttons
        self.rollback_button = Gtk.Button(label="Rollback")
        self.rollback_button.connect("clicked", self.on_rollback_clicked)
        self.rollback_button.set_sensitive(False)
        action_area.append(self.rollback_button)
        
        self.clone_button = Gtk.Button(label="Clone")
        self.clone_button.connect("clicked", self.on_clone_clicked)
        self.clone_button.set_sensitive(False)
        action_area.append(self.clone_button)
        
        self.delete_button = Gtk.Button(label="Delete")
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.delete_button.set_sensitive(False)
        action_area.append(self.delete_button)
        
        # Dataset Properties tab
        properties_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        notebook.append_page(properties_box, Gtk.Label(label="Dataset Properties"))
        
        # Create scrolled window for properties
        props_scrolled_window = Gtk.ScrolledWindow()
        props_scrolled_window.set_vexpand(True)
        props_scrolled_window.set_hexpand(True)
        properties_box.append(props_scrolled_window)
        
        # Create grid for dataset properties
        self.properties_grid = Gtk.Grid()
        self.properties_grid.set_column_spacing(20)
        self.properties_grid.set_row_spacing(10)
        self.properties_grid.set_margin_top(10)
        self.properties_grid.set_margin_bottom(10)
        self.properties_grid.set_margin_start(10)
        self.properties_grid.set_margin_end(10)
        props_scrolled_window.set_child(self.properties_grid)
        
        # Connect to dataset combo changed
        self.dataset_combo.connect("notify::selected", self.on_dataset_changed)
        
        # Use GLib.timeout_add to ensure the window is fully rendered before initializing
        GLib.timeout_add(100, self._deferred_init)
    
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
        
        # Add available datasets
        datasets = self.zfs_assistant.get_datasets()
        for dataset in datasets:
            model.append(dataset['name'])
        
        self.dataset_combo.set_model(model)
        
        # Find a top-level dataset to use as default
        # Get all dataset names and find the first top-level one (the most parent dataset)
        if datasets:
            # Sort datasets by name length to find parent datasets first
            sorted_datasets = sorted(datasets, key=lambda d: len(d['name'].split('/')))
            if sorted_datasets:
                # Find the index of the first dataset in the model
                first_dataset_name = sorted_datasets[0]['name']
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
        except Exception as e:
            print(f"Error refreshing snapshots: {e}")

    def add_snapshot_to_list(self, snapshot):
        """Add a snapshot to the snapshots list"""
        # Create a row for the snapshot
        row = Gtk.ListBoxRow()
        
        # Create a box to contain the snapshot info
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Name label
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name_label = Gtk.Label(xalign=0)
        name_label.set_markup("<b>Name</b>")
        name_box.append(name_label)
        
        dataset_label = Gtk.Label(xalign=0)
        name_box.append(dataset_label)
        
        box.append(name_box)
        name_box.set_hexpand(True)
        
        # Date label
        date_label = Gtk.Label(xalign=0)
        box.append(date_label)
        
        # Size label
        size_label = Gtk.Label(xalign=0)
        box.append(size_label)
        
        row.set_child(box)
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
        
        # Set snapshot name
        row.name_label.set_markup(f"<b>{snapshot.name}</b>")
        
        # Set dataset name
        row.dataset_label.set_text(f"{snapshot.dataset}")
        
        # Format and set creation date
        row.date_label.set_text(snapshot.formatted_creation_date)
        
        # Set size info
        row.size_label.set_text(f"Used: {snapshot.formatted_used}")

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
            # Use a completely different approach to clear the grid that doesn't rely on get_first_child
            # First create a new grid with the same properties
            new_grid = Gtk.Grid()
            new_grid.set_column_spacing(20)
            new_grid.set_row_spacing(10)
            new_grid.set_margin_top(10)
            new_grid.set_margin_bottom(10)
            new_grid.set_margin_start(10)
            new_grid.set_margin_end(10)
            
            # Get the parent widget that contains our grid
            parent = self.properties_grid.get_parent()
            if parent:
                # Remove the old grid and add the new one
                parent.set_child(new_grid)
                # Update our reference
                self.properties_grid = new_grid
                
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
            # Get dataset properties
            datasets = self.zfs_assistant.get_datasets()
            dataset_info = None
            for dataset in datasets:
                if dataset['name'] == dataset_name:
                    dataset_info = dataset
                    break
                    
            if not dataset_info:
                info_label = Gtk.Label(label=f"No properties found for dataset: {dataset_name}")
                info_label.set_margin_top(20)
                info_label.set_margin_bottom(20)
                self.properties_grid.attach(info_label, 0, 0, 2, 1)
                return
                
            # Add header
            header_label = Gtk.Label()
            header_label.set_markup(f"<b>Properties for dataset: {dataset_name}</b>")
            header_label.set_margin_bottom(10)
            self.properties_grid.attach(header_label, 0, 0, 2, 1)
            
            # Add property headers
            prop_header = Gtk.Label()
            prop_header.set_markup("<b>Property</b>")
            prop_header.set_xalign(0)
            prop_header.set_margin_bottom(5)
            
            value_header = Gtk.Label()
            value_header.set_markup("<b>Value</b>")
            value_header.set_xalign(0)
            value_header.set_margin_bottom(5)
            
            self.properties_grid.attach(prop_header, 0, 1, 1, 1)
            self.properties_grid.attach(value_header, 1, 1, 1, 1)
            
            # Add properties
            row = 2
            properties = dataset_info['properties']
            
            # Define property groups and their order
            property_groups = [
                {
                    "name": "Storage",
                    "props": ["used", "available", "referenced", "compressratio", "quota", "reservation"]
                },
                {
                    "name": "Configuration",
                    "props": ["type", "mountpoint", "compression", "recordsize", "readonly"]
                },
                {
                    "name": "Security",
                    "props": ["encryption"]
                }
            ]
            
            for group in property_groups:
                # Add group header
                group_label = Gtk.Label()
                group_label.set_markup(f"<b>{group['name']}</b>")
                group_label.set_xalign(0)
                group_label.set_margin_top(15)
                group_label.set_margin_bottom(5)
                self.properties_grid.attach(group_label, 0, row, 2, 1)
                row += 1
                
                # Add properties in this group
                for prop in group["props"]:
                    if prop in properties:
                        prop_label = Gtk.Label(label=prop)
                        prop_label.set_xalign(0)
                        
                        value_label = Gtk.Label(label=properties[prop])
                        value_label.set_xalign(0)
                        value_label.set_selectable(True)
                        
                        self.properties_grid.attach(prop_label, 0, row, 1, 1)
                        self.properties_grid.attach(value_label, 1, row, 1, 1)
                        row += 1
            
            # Make sure all is visible
            self.properties_grid.show()
        except Exception as e:
            print(f"Error refreshing dataset properties: {e}")
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

    def on_create_snapshot_clicked(self, button):
        """Handle create snapshot button click"""
        create_dialog = CreateSnapshotDialog(self)
        create_dialog.present()

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
            
            # Create confirmation dialog
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Delete Snapshot",
                secondary_text=f"Are you sure you want to delete snapshot '{snapshot.name}'?\n\n"
                             "This operation cannot be undone."
            )
            
            dialog.connect("response", self._on_delete_dialog_response, snapshot)
            dialog.present()
            
    def _on_delete_dialog_response(self, dialog, response, snapshot):
        """Handle delete dialog response"""
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Perform delete
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
