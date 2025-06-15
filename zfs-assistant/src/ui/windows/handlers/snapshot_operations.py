#!/usr/bin/env python3
# ZFS Assistant - Snapshot Operations Handler
# Author: GitHub Copilot

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

class SnapshotOperations:
    """Handles snapshot-specific operations like rollback, clone, delete"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def on_rollback_clicked(self, button):
        """Handle rollback button click"""
        # Get selected rows in multiple selection mode
        selected_rows = []
        child = self.main_window.snapshots_list.get_first_child()
        while child is not None:
            if child.is_selected():
                selected_rows.append(child)
            child = child.get_next_sibling()
        
        if len(selected_rows) != 1:
            return  # Should only work with exactly one selection
        
        selected = selected_rows[0]
        if selected is not None:
            # Get the snapshot object from the selected row
            snapshot = selected.get_child().snapshot
            
            # Create confirmation dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
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
            success, message = self.main_window.zfs_assistant.rollback_snapshot(snapshot_full_name)
            
            # Show result dialog
            result_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Rollback Result",
                secondary_text=message
            )
            result_dialog.connect("response", lambda d, r: d.destroy())
            result_dialog.present()
            
            if success:
                self.main_window.refresh_snapshots()
                # Send notification
                self.main_window.app.send_app_notification("Snapshot Rollback", 
                                          f"Dataset {snapshot.dataset} has been rolled back to snapshot {snapshot.name}.")

    def on_clone_clicked(self, button):
        """Handle clone button click"""
        # Get selected rows in multiple selection mode
        selected_rows = []
        child = self.main_window.snapshots_list.get_first_child()
        while child is not None:
            if child.is_selected():
                selected_rows.append(child)
            child = child.get_next_sibling()
        
        if len(selected_rows) != 1:
            return  # Should only work with exactly one selection
        
        selected = selected_rows[0]
        if selected is not None:
            # Get the snapshot object from the selected row
            snapshot = selected.get_child().snapshot
            
            # Create clone dialog
            dialog = Gtk.Dialog(
                title="Clone Snapshot",
                transient_for=self.main_window,
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
                success, message = self.main_window.zfs_assistant.clone_snapshot(snapshot_full_name, target_name)
                
                # Show result
                if not success:
                    error_dialog = Gtk.MessageDialog(
                        transient_for=self.main_window,
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
                    self.main_window.app.send_app_notification("Snapshot Cloned", 
                                              f"Snapshot {snapshot.name} has been cloned to {target_name}.")
        
        dialog.destroy()

    def on_delete_clicked(self, button):
        """Handle delete button click for single snapshot"""
        # In multiple selection mode, we need to find the last selected row
        selected_rows = []
        child = self.main_window.snapshots_list.get_first_child()
        while child is not None:
            if child.is_selected():
                selected_rows.append(child)
            child = child.get_next_sibling()
        
        if len(selected_rows) != 1:
            return  # Should only work with exactly one selection
        
        selected = selected_rows[0]
        if selected is not None:
            # Get the snapshot object from the selected row
            snapshot = selected.get_child().snapshot
            
            # Perform delete immediately without confirmation
            snapshot_full_name = f"{snapshot.dataset}@{snapshot.name}"
            success, message = self.main_window.zfs_assistant.delete_snapshot(snapshot_full_name)
            
            # Only show dialog on error
            if not success:
                # Show error dialog
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.main_window,
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
                self.main_window.refresh_snapshots()
                # Send notification
                self.main_window.app.send_app_notification("Snapshot Deleted", f"Snapshot {snapshot.name} has been deleted.")

    def on_delete_selected_clicked(self, button):
        """Handle delete selected snapshots button click"""
        # Get all selected rows
        selected_rows = []
        child = self.main_window.snapshots_list.get_first_child()
        while child is not None:
            if child.is_selected():
                selected_rows.append(child)
            child = child.get_next_sibling()
        
        if not selected_rows:
            return
        
        # Show confirmation dialog for multiple deletions
        num_snapshots = len(selected_rows)
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete {num_snapshots} Snapshots?",
            secondary_text=f"Are you sure you want to delete {num_snapshots} selected snapshots? This action cannot be undone."
        )
        
        dialog.connect("response", self._on_delete_selected_response, selected_rows)
        dialog.present()
    
    def _on_delete_selected_response(self, dialog, response, selected_rows):
        """Handle the response from the delete selected confirmation dialog"""
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        # Collect snapshot information before deletion
        snapshots_to_delete = []
        for row in selected_rows:
            snapshot = row.get_child().snapshot
            snapshot_full_name = f"{snapshot.dataset}@{snapshot.name}"
            snapshots_to_delete.append((snapshot_full_name, snapshot.name))
        
        # Perform deletions
        success_count = 0
        failed_deletions = []
        
        for snapshot_full_name, snapshot_name in snapshots_to_delete:
            success, message = self.main_window.zfs_assistant.delete_snapshot(snapshot_full_name)
            if success:
                success_count += 1
            else:
                failed_deletions.append(f"{snapshot_name}: {message}")
        
        # Refresh the list
        self.main_window.refresh_snapshots()
        
        # Show results
        if failed_deletions:
            # Show error dialog for failed deletions
            error_text = f"Successfully deleted {success_count} snapshots, but {len(failed_deletions)} failed:"
            error_details = "\n".join(failed_deletions)
            
            error_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Partial Success",
                secondary_text=f"{error_text}\n\n{error_details}"
            )
            error_dialog.connect("response", lambda d, r: d.destroy())
            error_dialog.present()
        else:
            # All deletions successful
            self.main_window.app.send_app_notification("Snapshots Deleted", 
                                         f"Successfully deleted {success_count} snapshots.")

    def create_quick_snapshot(self):
        """Create a quick snapshot with the given name"""
        selected = self.main_window.dataset_combo.get_selected()
        model = self.main_window.dataset_combo.get_model()
        
        if selected == Gtk.INVALID_LIST_POSITION:
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="No Dataset Selected",
                secondary_text="Please select a dataset before creating a snapshot."
            )
            error_dialog.connect("response", lambda d, r: d.destroy())
            error_dialog.present()
            return
        
        if selected == 0:
            # "All Datasets" is selected, which isn't valid for snapshot creation
            error_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Invalid Dataset Selection",
                secondary_text="You cannot create a snapshot for 'All Datasets'. Please select a specific dataset."
            )
            error_dialog.connect("response", lambda d, r: d.destroy())
            error_dialog.present()
            return

        dataset = model.get_string(selected)
        
        snapshot_name = self.main_window.quick_create_entry.get_text().strip()
        if not snapshot_name:
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="No Snapshot Name",
                secondary_text="Please enter a snapshot name."
            )
            error_dialog.connect("response", lambda d, r: d.destroy())
            error_dialog.present()
            return
        
        # Create the snapshot
        success, message = self.main_window.zfs_assistant.create_snapshot(dataset, snapshot_name)
        
        if success:
            # Clear the entry and refresh the list
            self.main_window.quick_create_entry.set_text("")
            self.main_window.refresh_snapshots()
            # Send notification
            self.main_window.app.send_app_notification("Snapshot Created", f"Snapshot {snapshot_name} has been created for dataset {dataset}.")
        else:
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Snapshot Creation Failed",
                secondary_text=message
            )
            error_dialog.connect("response", lambda d, r: d.destroy())
            error_dialog.present()

    def on_unified_delete_clicked(self, button):
        """Handle unified delete button click - automatically detects single vs multiple selection"""
        # Get all selected rows
        selected_rows = []
        child = self.main_window.snapshots_list.get_first_child()
        while child is not None:
            if child.is_selected():
                selected_rows.append(child)
            child = child.get_next_sibling()
        
        if not selected_rows:
            return
        
        num_selected = len(selected_rows)
        
        if num_selected == 1:
            # Single selection - delete immediately without confirmation
            selected = selected_rows[0]
            snapshot = selected.get_child().snapshot
            snapshot_full_name = f"{snapshot.dataset}@{snapshot.name}"
            success, message = self.main_window.zfs_assistant.delete_snapshot(snapshot_full_name)
            
            if not success:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.main_window,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Delete Error",
                    secondary_text=message
                )
                error_dialog.connect("response", lambda d, r: d.destroy())
                error_dialog.present()
            else:
                self.main_window.refresh_snapshots()
                self.main_window.app.send_app_notification("Snapshot Deleted", 
                                               f"Snapshot {snapshot.name} has been deleted.")
        else:
            # Multiple selection - show confirmation dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Delete {num_selected} Snapshots?",
                secondary_text=f"Are you sure you want to delete {num_selected} selected snapshots? This action cannot be undone."
            )
            
            dialog.connect("response", self._on_unified_delete_multiple_response, selected_rows)
            dialog.present()
    
    def _on_unified_delete_multiple_response(self, dialog, response, selected_rows):
        """Handle the response from the unified delete confirmation dialog for multiple snapshots"""
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        # Collect snapshot information before deletion
        snapshots_to_delete = []
        for row in selected_rows:
            snapshot = row.get_child().snapshot
            snapshot_full_name = f"{snapshot.dataset}@{snapshot.name}"
            snapshots_to_delete.append((snapshot_full_name, snapshot.name))
        
        # Perform deletions
        success_count = 0
        failed_deletions = []
        
        for snapshot_full_name, snapshot_name in snapshots_to_delete:
            success, message = self.main_window.zfs_assistant.delete_snapshot(snapshot_full_name)
            if success:
                success_count += 1
            else:
                failed_deletions.append(f"{snapshot_name}: {message}")
        
        # Refresh the list
        self.main_window.refresh_snapshots()
        
        # Show results
        if failed_deletions:
            error_text = f"Successfully deleted {success_count} snapshots, but {len(failed_deletions)} failed:"
            error_details = "\n".join(failed_deletions)
            
            error_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Partial Success",
                secondary_text=f"{error_text}\n\n{error_details}"
            )
            error_dialog.connect("response", lambda d, r: d.destroy())
            error_dialog.present()
        else:
            self.main_window.app.send_app_notification("Snapshots Deleted", 
                                         f"Successfully deleted {success_count} snapshots.")
