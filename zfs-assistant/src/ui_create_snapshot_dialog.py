#!/usr/bin/env python3
# ZFS Assistant - Create Snapshot Dialog
# Author: GitHub Copilot

import gi
import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, GObject

class CreateSnapshotDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(
            title="Create Snapshot",
            transient_for=parent,
            modal=True,
            destroy_with_parent=True        )
        
        self.parent = parent
        self.zfs_assistant = parent.zfs_assistant
        
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Create", Gtk.ResponseType.OK)
        
        content_area = self.get_content_area()
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
        content_area.set_spacing(6)
        
        # Dataset selection
        content_area.append(Gtk.Label(label="Select Dataset:"))
        
        # Dataset combo
        self.dataset_combo = Gtk.DropDown()        model = Gtk.StringList.new([])
        
        # Add available datasets
        datasets = self.zfs_assistant.get_datasets()
        for dataset in datasets:
            model.append(dataset['name'])
        
        self.dataset_combo.set_model(model)
        if model.get_n_items() > 0:
            self.dataset_combo.set_selected(0)
        
        content_area.append(self.dataset_combo)
        
        # Custom name checkbox
        self.custom_name_check = Gtk.CheckButton(label="Use custom snapshot name")
        self.custom_name_check.connect("toggled", self.on_custom_name_toggled)
        content_area.append(self.custom_name_check)
        
        # Custom name entry        self.name_entry = Gtk.Entry()
        self.name_entry.set_sensitive(False)
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = self.zfs_assistant.config['prefix']
        self.name_entry.set_text(f"{prefix}-{timestamp}")
        content_area.append(self.name_entry)
        
        # Connect to response signal
        self.connect("response", self.on_response)
        
        self.show()

    def on_custom_name_toggled(self, button):
        """Handle custom name checkbox toggle"""
        self.name_entry.set_sensitive(button.get_active())

    def on_response(self, dialog, response):
        """Handle dialog response"""
        if response == Gtk.ResponseType.OK:
            # Get selected dataset
            selected = self.dataset_combo.get_selected()
            model = self.dataset_combo.get_model()
            
            if selected != Gtk.INVALID_LIST_POSITION and model.get_n_items() > 0:
                dataset = model.get_string(selected)
                
                # Get snapshot name
                name = None
                if self.custom_name_check.get_active():
                    name = self.name_entry.get_text().strip()
                    if not name:                    name = None
                
                # Create snapshot
                success, result = self.zfs_assistant.create_snapshot(dataset, name)
                
                # Show result dialog
                result_dialog = Gtk.MessageDialog(
                    transient_for=self.parent,
                    modal=True,
                    message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Snapshot Creation Result"
                )
                
                if success:
                    result_dialog.format_secondary_text(f"Snapshot '{result}' created successfully.")
                else:
                    result_dialog.format_secondary_text(result)
                
                # Use a separate function to handle the dialog response to ensure proper cleanup
                result_dialog.connect("response", self._on_result_dialog_response)
                result_dialog.present()
            else:
                # No dataset selected, show error
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.parent,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="No Dataset Selected"
                )
                error_dialog.format_secondary_text("Please select a dataset for the snapshot.")
                error_dialog.connect("response", lambda d, r: d.destroy())
                error_dialog.present()
                return  # Don't destroy the dialog so user can select a dataset
        else:
            # Cancel was clicked, just destroy the dialog
            self.destroy()
            
    def _on_result_dialog_response(self, dialog, response):
        """Handle result dialog response"""
        dialog.destroy()
        
        # Refresh the snapshot list in the parent window
        self.parent.refresh_snapshots()
        
        # Send notification
        self.parent.app.send_notification("Snapshot Created", "A new ZFS snapshot has been created successfully.")
        
        # Now destroy the create snapshot dialog
        self.destroy()
