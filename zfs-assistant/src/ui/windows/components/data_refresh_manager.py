#!/usr/bin/env python3
# ZFS Assistant - Data Refresh Manager
# Author: GitHub Copilot

import gi
import datetime
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GLib

try:
    # Try relative imports first
    from ....utils.common import LOG_FILE
except ImportError:
    # Fall back for direct execution
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from utils.common import LOG_FILE

class DataRefreshManager:
    """Manages data refresh operations for various UI components"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def update_dataset_combo(self):
        """Update the dataset combo box with available datasets"""
        model = Gtk.StringList.new([])
        
        # Add "All Datasets" option
        model.append("All Datasets")
        
        # Add available datasets (exclude root pool datasets)
        datasets = self.main_window.zfs_assistant.get_filtered_datasets()
        for dataset in datasets:
            model.append(dataset)
        
        self.main_window.dataset_combo.set_model(model)
        
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
                        self.main_window.dataset_combo.set_selected(i)
                        break
                else:
                    # If we couldn't find it, default to "All Datasets"
                    self.main_window.dataset_combo.set_selected(0)
            else:
                self.main_window.dataset_combo.set_selected(0)
        else:
            self.main_window.dataset_combo.set_selected(0)

    def refresh_snapshots(self):
        """Refresh the snapshot list"""
        try:
            self.main_window.update_status("loading", "Loading snapshots...")
            
            selected = self.main_window.dataset_combo.get_selected()
            model = self.main_window.dataset_combo.get_model()
            
            # Clear current list
            self.main_window.snapshots_list.remove_all()
            if selected == 0:
                # "All Datasets" is selected
                snapshots = self.main_window.zfs_assistant.get_snapshots()
            else:
                dataset = model.get_string(selected)
                snapshots = self.main_window.zfs_assistant.get_snapshots(dataset)
            
            # Add snapshots to model
            for snapshot in snapshots:
                self.add_snapshot_to_list(snapshot)
            
            # Update snapshot count
            self.main_window.update_snapshot_count()
            
            # Update status
            if snapshots:
                self.main_window.update_status("success", f"Loaded {len(snapshots)} snapshots")
            else:
                self.main_window.update_status("info", "No snapshots found")
                
        except Exception as e:
            print(f"Error refreshing snapshots: {e}")
            self.main_window.update_status("error", f"Failed to load snapshots: {e}")

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
        self.main_window.snapshots_list.append(row)

    def _bind_snapshot_to_row(self, snapshot, row):
        """Bind snapshot data to a row in the snapshots list"""
        # Make sure we handle Python objects correctly
        if hasattr(snapshot, 'get_property'):
            # Extract the ZFSSnapshot object from the GObject wrapper
            snapshot = snapshot.get_property("value")
        
        # Store the snapshot object on the row's child box for later access
        box = row.get_child()
        box.snapshot = snapshot
        
        # The labels are already set in add_snapshot_to_list with the new layout
        # This method now just stores the snapshot reference

    def refresh_dataset_properties(self):
        """Refresh the dataset properties grid"""
        try:
            # Clear the grid by removing all children
            while True:
                child = self.main_window.properties_grid.get_first_child()
                if not child:
                    break
                self.main_window.properties_grid.remove(child)
                
            selected = self.main_window.dataset_combo.get_selected()
            model = self.main_window.dataset_combo.get_model()
            
            if selected == 0 or selected == Gtk.INVALID_LIST_POSITION:
                # "All Datasets" is selected or no selection
                info_label = Gtk.Label(label="Select a specific dataset to view its properties")
                info_label.set_margin_top(20)
                info_label.set_margin_bottom(20)
                self.main_window.properties_grid.attach(info_label, 0, 0, 2, 1)
                return
            
            dataset_name = model.get_string(selected)
            # Get dataset properties directly
            dataset_properties = self.main_window.zfs_assistant.get_dataset_properties(dataset_name)
            
            if not dataset_properties:
                info_label = Gtk.Label(label=f"No properties found for dataset: {dataset_name}")
                info_label.set_margin_top(20)
                info_label.set_margin_bottom(20)
                self.main_window.properties_grid.attach(info_label, 0, 0, 2, 1)
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
            refresh_button.connect("clicked", self.main_window.on_properties_refresh_clicked)
            header_box.append(refresh_button)
            
            self.main_window.properties_grid.attach(header_box, 0, 0, 2, 1)
            
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
            self.main_window.properties_grid.attach(props_box, 0, row, 2, 1)
            
            # Make sure all is visible
            self.main_window.properties_grid.show()
        except Exception as e:
            print(f"Error refreshing dataset properties: {e}")
            # Clear any existing content first
            while True:
                child = self.main_window.properties_grid.get_first_child()
                if not child:
                    break
                self.main_window.properties_grid.remove(child)
            # Add a simple error message to the grid
            error_label = Gtk.Label(label=f"Error loading dataset properties: {str(e)}")
            error_label.set_margin_top(20)
            error_label.set_margin_bottom(20)
            self.main_window.properties_grid.attach(error_label, 0, 0, 2, 1)

    def refresh_log_content(self):
        """Refresh the log content in the logs tab"""
        try:
            if hasattr(self.main_window, 'log_text_view'):
                # Get the text buffer
                buffer = self.main_window.log_text_view.get_buffer()
                
                # Clear existing content
                buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())
                
                # Read log file content
                if os.path.exists(LOG_FILE):
                    try:
                        with open(LOG_FILE, 'r') as f:
                            log_content = f.read()
                            # Only show last 1000 lines to avoid performance issues
                            lines = log_content.split('\n')
                            if len(lines) > 1000:
                                lines = lines[-1000:]
                                log_content = '\n'.join(lines)
                            buffer.set_text(log_content)
                    except Exception as e:
                        buffer.set_text(f"Error reading log file: {e}")
                else:
                    buffer.set_text("Log file not found.")
                
                # Scroll to bottom
                mark = buffer.get_insert()
                self.main_window.log_text_view.scroll_mark_onscreen(mark)
        except Exception as e:
            print(f"Error refreshing log content: {e}")
