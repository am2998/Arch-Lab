#!/usr/bin/env python3
# ZFS Assistant - ARC Properties Manager
# Author: GitHub Copilot

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class ARCPropertiesManager:
    """Manages ARC properties display and editing functionality"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def refresh_arc_properties(self):
        """Refresh the ARC properties grid with statistics and tunables"""
        try:
            # Clear the grid by removing all children
            while True:
                child = self.main_window.arc_grid.get_first_child()
                if not child:
                    break
                self.main_window.arc_grid.remove(child)
            
            # Get ARC properties and tunables
            arc_properties = self.main_window.zfs_assistant.get_arc_properties()
            arc_tunables = self.main_window.zfs_assistant.get_arc_tunables()
            
            if not arc_properties:
                info_label = Gtk.Label(label="ARC statistics not available - ZFS may not be loaded")
                info_label.set_margin_top(20)
                info_label.set_margin_bottom(20)
                self.main_window.arc_grid.attach(info_label, 0, 0, 2, 1)
                return
            
            # Add ARC header with refresh button
            header_box = self._create_arc_header(arc_properties)
            self.main_window.arc_grid.attach(header_box, 0, 0, 2, 1)
            
            row = 1
            
            # Create a box to hold all ARC sections
            arc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
            arc_box.set_margin_top(10)
            
            # Display ARC statistics
            for category_name, stats in arc_properties.items():
                section_box = self._create_arc_statistics_section(category_name, stats)
                arc_box.append(section_box)
                
                # Add separator between categories
                if category_name != list(arc_properties.keys())[-1] or arc_tunables:
                    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                    separator.set_margin_top(5)
                    separator.set_margin_bottom(5)
                    arc_box.append(separator)
            
            # Add tunable parameters section with inline editing
            if arc_tunables:
                tunables_section = self._create_arc_tunables_section(arc_tunables)
                arc_box.append(tunables_section)
            
            # Add the ARC box to the grid
            self.main_window.arc_grid.attach(arc_box, 0, row, 2, 1)
            
            # Make sure all is visible
            self.main_window.arc_grid.show()
            
        except Exception as e:
            print(f"Error refreshing ARC properties: {e}")
            # Clear any existing content first
            while True:
                child = self.main_window.arc_grid.get_first_child()
                if not child:
                    break
                self.main_window.arc_grid.remove(child)
            # Add error message
            error_label = Gtk.Label(label=f"Error loading ARC properties: {str(e)}")
            error_label.set_margin_top(20)
            error_label.set_margin_bottom(20)
            self.main_window.arc_grid.attach(error_label, 0, 0, 2, 1)
    
    def _create_arc_header(self, arc_properties):
        """Create the ARC properties header"""
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
        
        return header_box
    
    def _create_arc_statistics_section(self, category_name, stats):
        """Create a section for ARC statistics"""
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
        
        return section_box
    
    def _create_arc_tunables_section(self, arc_tunables):
        """Create the ARC tunables section with inline editing"""
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
        
        return tunables_section

    def on_arc_refresh_clicked(self, button):
        """Handle ARC properties refresh button click"""
        # Animate the button with a spinning effect
        context = button.get_style_context()
        context.add_class("refreshing")
        
        # Show a brief status message
        if hasattr(self.main_window, 'set_status'):
            self.main_window.set_status("Refreshing ARC properties...", "view-refresh-symbolic")
        
        # Add a small delay for visual feedback
        GLib.timeout_add(200, self._refresh_arc_with_status, button)

    def _refresh_arc_with_status(self, button=None):
        """Refresh ARC properties with status update"""
        self.refresh_arc_properties()
        if hasattr(self.main_window, 'set_status'):
            self.main_window.set_status("ARC properties refreshed", "emblem-ok-symbolic")
        
        # Remove animation class if button provided
        if button:
            context = button.get_style_context()
            context.remove_class("refreshing")
            
        # Reset status after 2 seconds
        GLib.timeout_add(2000, lambda: self._reset_status() and False)
        return False  # Don't repeat
    
    def _reset_status(self):
        """Reset status to ready"""
        if hasattr(self.main_window, 'set_status'):
            self.main_window.set_status("Ready")
        return False

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
            if hasattr(self.main_window, 'set_status'):
                self.main_window.set_status(f"Updating {param_name}...", "system-run-symbolic")
            
            # Validate the value (basic validation)
            try:
                int(new_value)  # Most ARC tunables are integers
            except ValueError:
                if hasattr(self.main_window, 'set_status'):
                    self.main_window.set_status(f"Invalid value for {param_name}: must be a number", "dialog-error-symbolic")
                # Reset to original value
                self.refresh_arc_properties()
                return
            
            # Update the tunable
            success, message = self.main_window.zfs_assistant.set_arc_tunable(param_name, new_value)
            
            if success:
                if hasattr(self.main_window, 'set_status'):
                    self.main_window.set_status(f"Updated {param_name} successfully", "emblem-ok-symbolic")
                # Refresh to show new value
                GLib.timeout_add(500, self.refresh_arc_properties)
            else:
                if hasattr(self.main_window, 'set_status'):
                    self.main_window.set_status(f"Failed to update {param_name}: {message}", "dialog-error-symbolic")
                # Reset to original value
                self.refresh_arc_properties()
            
            # Reset status after 3 seconds
            GLib.timeout_add(3000, lambda: self._reset_status() and False)
            
        except Exception as e:
            if hasattr(self.main_window, 'set_status'):
                self.main_window.set_status(f"Error updating {param_name}: {str(e)}", "dialog-error-symbolic")
            # Reset to original value
            self.refresh_arc_properties()
            GLib.timeout_add(3000, lambda: self._reset_status() and False)
