#!/usr/bin/env python3
# ZFS Assistant - Advanced Settings Tab
# Author: GitHub Copilot

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

class AdvancedSettingsTab:
    def __init__(self, parent_dialog):
        self.dialog = parent_dialog
        self.zfs_assistant = parent_dialog.zfs_assistant
        
        # Create main box
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.box.set_margin_top(10)
        self.box.set_margin_bottom(10)
        self.box.set_margin_start(10)
        self.box.set_margin_end(10)
        
        # Import/Export config
        import_export_frame = Gtk.Frame()
        import_export_frame.set_label("Configuration Import/Export")
        self.box.append(import_export_frame)
        
        import_export_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        import_export_box.set_homogeneous(True)
        import_export_box.set_margin_top(10)
        import_export_box.set_margin_bottom(10)
        import_export_box.set_margin_start(10)
        import_export_box.set_margin_end(10)
        import_export_frame.set_child(import_export_box)
        
        export_button = Gtk.Button(label="Export Configuration")
        export_button.connect("clicked", self.on_export_config_clicked)
        import_export_box.append(export_button)
        
        import_button = Gtk.Button(label="Import Configuration")
        import_button.connect("clicked", self.on_import_config_clicked)
        import_export_box.append(import_button)
    
    def get_box(self):
        return self.box
    
    def on_export_config_clicked(self, button):
        """Handle export config button click"""
        dialog = Gtk.FileChooserDialog(
            title="Export Configuration",
            transient_for=self.dialog,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.ACCEPT)
        
        # Add filters
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON Files")
        filter_json.add_pattern("*.json")
        dialog.add_filter(filter_json)
        
        filter_any = Gtk.FileFilter()
        filter_any.set_name("All Files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)
        
        # Set default filename
        dialog.set_current_name("zfs-assistant-config.json")
        
        dialog.connect("response", self._on_export_dialog_response)
        dialog.present()
        
    def _on_export_dialog_response(self, dialog, response):
        """Handle export dialog response"""
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            success, message = self.zfs_assistant.export_config(file_path)
            
            # Show result dialog
            result_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                modal=True,
                message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Export Configuration",
                secondary_text=message
            )
            result_dialog.connect("response", lambda d, r: d.destroy())
            result_dialog.present()
        
        dialog.destroy()
    
    def on_import_config_clicked(self, button):
        """Handle import config button click"""
        dialog = Gtk.FileChooserDialog(
            title="Import Configuration",
            transient_for=self.dialog,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Open", Gtk.ResponseType.ACCEPT)
        
        # Add filters
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON Files")
        filter_json.add_pattern("*.json")
        dialog.add_filter(filter_json)
        
        filter_any = Gtk.FileFilter()
        filter_any.set_name("All Files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)
        
        dialog.connect("response", self._on_import_dialog_response)
        dialog.present()
        
    def _on_import_dialog_response(self, dialog, response):
        """Handle import dialog response"""
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            success, message = self.zfs_assistant.import_config(file_path)
            
            # Show result dialog
            result_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                modal=True,
                message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Import Configuration",
                secondary_text=message
            )
            
            if success:
                # Need to reload the settings dialog if import successful
                result_dialog.connect("response", self._on_import_success_response)
            else:
                result_dialog.connect("response", lambda d, r: d.destroy())
                
            result_dialog.present()
        
        dialog.destroy()
    
    def _on_import_success_response(self, dialog, response):
        """Handle import success dialog response"""
        dialog.destroy()
        
        # Close the settings dialog and reopen to reflect new settings
        new_dialog = type(self.dialog)(self.dialog.parent)
        self.dialog.destroy()
        new_dialog.present()
