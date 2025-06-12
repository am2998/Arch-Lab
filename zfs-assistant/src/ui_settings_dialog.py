#!/usr/bin/env python3
# ZFS Assistant - Settings Dialog
# Author: GitHub Copilot

import gi
import os
import subprocess

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, GObject

# Try to import advanced settings
try:
    # First try relative imports (when running as a package)
    from .ui_advanced_settings import AdvancedSettingsTab
except ImportError:
    # Fall back to absolute imports (when running directly)
    try:
        from ui_advanced_settings import AdvancedSettingsTab
    except ImportError:
        AdvancedSettingsTab = None

class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(
            title="Settings",
            transient_for=parent,
            modal=True,
            destroy_with_parent=True
        )
        
        self.parent = parent
        self.zfs_assistant = parent.zfs_assistant
        self.config = self.zfs_assistant.config.copy()
        
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        
        # Set dialog size to match main window proportions better
        self.set_default_size(1200, 800)  # Match main window size
        self.set_size_request(1000, 650)   # Match main window minimum size
        
        # Create notebook for tabs
        notebook = Gtk.Notebook()
        content_area = self.get_content_area()
        content_area.append(notebook)
        
        # General settings tab
        general_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        general_box.set_margin_top(10)
        general_box.set_margin_bottom(10)
        general_box.set_margin_start(10)
        general_box.set_margin_end(10)
        notebook.append_page(general_box, Gtk.Label(label="General"))
        
        # Datasets section
        datasets_frame = Gtk.Frame()
        datasets_frame.set_label("Managed Datasets")
        datasets_frame.set_margin_bottom(10)
        general_box.append(datasets_frame)
        
        datasets_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        datasets_box.set_margin_top(10)
        datasets_box.set_margin_bottom(10)
        datasets_box.set_margin_start(10)
        datasets_box.set_margin_end(10)
        datasets_frame.set_child(datasets_box)
        
        # Dataset list with checkboxes
        datasets_scroll = Gtk.ScrolledWindow()
        datasets_scroll.set_size_request(-1, 150)  # Set reasonable height
        datasets_scroll.set_vexpand(True)
        datasets_box.append(datasets_scroll)
        
        # Create a list box for datasets
        self.datasets_list = Gtk.ListBox()
        self.datasets_list.set_selection_mode(Gtk.SelectionMode.NONE)
        datasets_scroll.set_child(self.datasets_list)
        
        # Get available datasets
        datasets = self.zfs_assistant.get_datasets()
        managed_datasets = self.config.get("datasets", [])
        
        # Add datasets to the list
        if datasets:
            for dataset in datasets:
                dataset_name = dataset['name']
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                box.set_margin_start(5)
                box.set_margin_end(5)
                
                check = Gtk.CheckButton(label=dataset_name)
                check.set_active(dataset_name in managed_datasets)
                box.append(check)
                
                row.set_child(box)
                self.datasets_list.append(row)
        
        # Add buttons for selecting all/none
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_margin_top(10)
        
        select_all_button = Gtk.Button(label="Select All")
        select_all_button.connect("clicked", self.on_select_all_clicked)
        button_box.append(select_all_button)
        
        select_none_button = Gtk.Button(label="Select None")
        select_none_button.connect("clicked", self.on_select_none_clicked)
        button_box.append(select_none_button)
        
        datasets_box.append(button_box)
        
        # Appearance section
        appearance_frame = Gtk.Frame()
        appearance_frame.set_label("Appearance")
        appearance_frame.set_margin_bottom(10)
        general_box.append(appearance_frame)
        
        appearance_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        appearance_box.set_margin_top(10)
        appearance_box.set_margin_bottom(10)
        appearance_box.set_margin_start(10)
        appearance_box.set_margin_end(10)
        appearance_frame.set_child(appearance_box)
        
        # Dark mode switch
        dark_mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dark_mode_box.append(Gtk.Label(label="Dark Mode:"))
        self.dark_mode_switch = Gtk.Switch()
        self.dark_mode_switch.set_active(self.config.get("dark_mode", False))
        dark_mode_box.append(self.dark_mode_switch)
        appearance_box.append(dark_mode_box)
        
        # Notifications switch
        notif_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        notif_box.append(Gtk.Label(label="Enable Notifications:"))
        self.notifications_switch = Gtk.Switch()
        self.notifications_switch.set_active(self.config.get("notifications_enabled", True))
        notif_box.append(self.notifications_switch)
        appearance_box.append(notif_box)
        
        # Schedule settings tab
        schedule_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        schedule_box.set_margin_top(10)
        schedule_box.set_margin_bottom(10)
        schedule_box.set_margin_start(10)
        schedule_box.set_margin_end(10)
        notebook.append_page(schedule_box, Gtk.Label(label="Schedule"))
        
        # Enable scheduled snapshots
        self.schedule_switch = Gtk.Switch()
        self.schedule_switch.set_active(self.config.get("auto_snapshot", True))
        self.schedule_switch.connect("state-set", self.on_schedule_switch_toggled)
        schedule_enable_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        schedule_enable_box.append(Gtk.Label(label="Enable Scheduled Snapshots:"))
        schedule_enable_box.append(self.schedule_switch)
        schedule_box.append(schedule_enable_box)
        
        # Add explanation text
        explanation_label = Gtk.Label(
            label="You can set up multiple schedules below. For hourly and daily snapshots, "
                  "you can select multiple hours or days. System updates (pacman -Syu) will be "
                  "executed automatically during scheduled snapshots."
        )
        
        explanation_label.set_wrap(True)
        explanation_label.set_margin_top(5)
        explanation_label.set_margin_bottom(5)
        explanation_label.set_halign(Gtk.Align.START)
        explanation_label.set_margin_start(0)  # Align with frame content
        explanation_label.add_css_class("dim-label")
        schedule_box.append(explanation_label)
        
        # Snapshot naming configuration frame
        naming_frame = Gtk.Frame()
        naming_frame.set_label("Snapshot Naming")
        naming_frame.set_margin_top(10)
        naming_frame.set_margin_bottom(10)
        schedule_box.append(naming_frame)
        
        naming_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        naming_box.set_margin_top(10)
        naming_box.set_margin_bottom(10)
        naming_box.set_margin_start(10)
        naming_box.set_margin_end(10)
        naming_frame.set_child(naming_box)
        
        # Prefix setting
        prefix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        prefix_box.set_halign(Gtk.Align.START)
        prefix_label = Gtk.Label(label="Snapshot Prefix:")
        prefix_label.set_size_request(140, -1)
        prefix_label.set_halign(Gtk.Align.START)
        prefix_box.append(prefix_label)
        
        self.prefix_entry = Gtk.Entry()
        self.prefix_entry.set_text(self.config.get("prefix", "zfs-assistant"))
        self.prefix_entry.set_size_request(200, -1)
        prefix_box.append(self.prefix_entry)
        naming_box.append(prefix_box)
        
        # Name format dropdown
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        format_box.set_halign(Gtk.Align.START)
        format_label = Gtk.Label(label="Naming Format:")
        format_label.set_size_request(140, -1)
        format_label.set_halign(Gtk.Align.START)
        format_box.append(format_label)
        
        self.format_combo = Gtk.DropDown()
        format_model = Gtk.StringList.new([
            "prefix-type-timestamp",
            "prefix-timestamp-type", 
            "type-prefix-timestamp",
            "timestamp-prefix-type",
            "prefix-type-timestamp-short",
            "prefix-timestamp-short-type",
            "type-prefix-timestamp-short", 
            "timestamp-short-prefix-type"
        ])
        self.format_combo.set_model(format_model)
        
        # Set current format
        current_format = self.config.get("snapshot_name_format", "prefix-type-timestamp")
        format_options = [
            "prefix-type-timestamp", "prefix-timestamp-type", "type-prefix-timestamp", "timestamp-prefix-type",
            "prefix-type-timestamp-short", "prefix-timestamp-short-type", "type-prefix-timestamp-short", "timestamp-short-prefix-type"
        ]
        try:
            current_index = format_options.index(current_format)
            self.format_combo.set_selected(current_index)
        except ValueError:
            self.format_combo.set_selected(0)
        
        self.format_combo.set_size_request(200, -1)
        format_box.append(self.format_combo)
        naming_box.append(format_box)
        
        # Preview of snapshot names
        preview_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        preview_box.set_halign(Gtk.Align.START)
        preview_label = Gtk.Label(label="Preview:")
        preview_label.set_size_request(140, -1)
        preview_label.set_halign(Gtk.Align.START)
        preview_box.append(preview_label)
        
        # Container for multiple preview labels
        self.preview_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.preview_container.set_size_request(400, -1)  # Match the input field width area
        self.preview_container.set_halign(Gtk.Align.START)
        preview_box.append(self.preview_container)
        
        naming_box.append(preview_box)
        
        # Connect signals to update preview
        self.prefix_entry.connect("changed", self.update_snapshot_preview)
        self.prefix_entry.connect("changed", self.update_pacman_preview)
        self.format_combo.connect("notify::selected", self.update_snapshot_preview)
        self.format_combo.connect("notify::selected", self.update_pacman_preview)
        
        # Update initial snapshot preview
        self.update_snapshot_preview()
        
        # Snapshot schedules frame
        schedule_frame = Gtk.Frame()
        schedule_frame.set_label("Snapshot Schedules")
        schedule_frame.set_margin_top(10)
        schedule_frame.set_margin_bottom(10)
        schedule_box.append(schedule_frame)
        
        schedule_types_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        schedule_types_box.set_margin_top(10)
        schedule_types_box.set_margin_bottom(10)
        schedule_types_box.set_margin_start(10)
        schedule_types_box.set_margin_end(10)
        schedule_frame.set_child(schedule_types_box)
          # Hourly snapshots with multiple hours selection
        hourly_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        hourly_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.hourly_check = Gtk.CheckButton(label="Hourly Snapshots")
        self.hourly_check.connect("toggled", self.on_hourly_check_toggled)
        hourly_header.append(self.hourly_check)
        hourly_section.append(hourly_header)
        
        # Add explanation for hourly
        hourly_explanation = Gtk.Label(label="Select the specific hours when snapshots should be taken")
        hourly_explanation.set_margin_start(0)  # Align with frame content
        hourly_explanation.set_halign(Gtk.Align.START)
        hourly_explanation.add_css_class("dim-label")
        hourly_section.append(hourly_explanation)
        
        # Hours selection grid
        self.hourly_grid = Gtk.Grid()
        self.hourly_grid.set_column_homogeneous(True)
        self.hourly_grid.set_row_spacing(5)
        self.hourly_grid.set_column_spacing(10)
        self.hourly_grid.set_margin_start(0)  # Align with frame content
        
        # Hour selection button box
        hourly_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hourly_button_box.set_margin_bottom(5)
        hourly_button_box.set_margin_start(0)  # Align with frame content
        
        self.hourly_select_all_button = Gtk.Button(label="Select All Hours")
        self.hourly_select_all_button.connect("clicked", self.on_hourly_select_all_clicked)
        hourly_button_box.append(self.hourly_select_all_button)
        
        self.hourly_select_none_button = Gtk.Button(label="Clear Hours")
        self.hourly_select_none_button.connect("clicked", self.on_hourly_select_none_clicked)
        hourly_button_box.append(self.hourly_select_none_button)
        
        hourly_section.append(hourly_button_box)
        
        # Create hour checkboxes
        self.hour_checks = {}
        hourly_schedule = self.config.get("hourly_schedule", list(range(24)))
        
        for hour in range(24):
            row = hour // 6
            col = hour % 6
            hour_label = f"{hour:02d}:00"
            check = Gtk.CheckButton(label=hour_label)
            check.set_active(hour in hourly_schedule)
            check.connect("toggled", self.update_snapshot_preview)  # Connect to preview update
            self.hour_checks[hour] = check
            self.hourly_grid.attach(check, col, row, 1, 1)
        
        hourly_section.append(self.hourly_grid)
        schedule_types_box.append(hourly_section)
        
        # Add a separator
        schedule_types_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Daily snapshots with multiple days selection
        daily_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        daily_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.daily_check = Gtk.CheckButton(label="Daily Snapshots")
        self.daily_check.connect("toggled", self.on_daily_check_toggled)
        daily_header.append(self.daily_check)
        
        # Time selection for daily snapshots
        daily_header.append(Gtk.Label(label="at time:"))
        self.daily_hour_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.daily_hour_spin.set_value(self.config.get("daily_hour", 0))
        self.daily_hour_spin.connect("value-changed", self.update_snapshot_preview)  # Connect to preview update
        daily_header.append(self.daily_hour_spin)
        daily_header.append(Gtk.Label(label=":00"))
        
        daily_section.append(daily_header)
        
        # Add explanation for daily
        daily_explanation = Gtk.Label(label="Select the days of the week when snapshots should be taken")
        daily_explanation.set_margin_start(0)  # Align with frame content
        daily_explanation.set_halign(Gtk.Align.START)
        daily_explanation.add_css_class("dim-label")
        daily_section.append(daily_explanation)
        
        # Days selection grid
        self.daily_grid = Gtk.Grid()
        self.daily_grid.set_column_homogeneous(True)
        self.daily_grid.set_row_spacing(5)
        self.daily_grid.set_column_spacing(10)
        self.daily_grid.set_margin_start(0)  # Align with frame content
        
        # Day selection button box
        daily_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        daily_button_box.set_margin_bottom(5)
        daily_button_box.set_margin_start(0)  # Align with frame content
        
        self.daily_select_all_button = Gtk.Button(label="Select All Days")
        self.daily_select_all_button.connect("clicked", self.on_daily_select_all_clicked)
        daily_button_box.append(self.daily_select_all_button)
        
        self.daily_select_none_button = Gtk.Button(label="Clear Days")
        self.daily_select_none_button.connect("clicked", self.on_daily_select_none_clicked)
        daily_button_box.append(self.daily_select_none_button)
        
        daily_section.append(daily_button_box)
        
        # Create day checkboxes
        self.day_checks = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_schedule = self.config.get("daily_schedule", list(range(7)))
        
        for day_idx, day_name in enumerate(days):
            row = day_idx // 4
            col = day_idx % 4
            check = Gtk.CheckButton(label=day_name)
            check.set_active(day_idx in daily_schedule)
            check.connect("toggled", self.update_snapshot_preview)  # Connect to preview update
            self.day_checks[day_idx] = check
            self.daily_grid.attach(check, col, row, 1, 1)
        
        daily_section.append(self.daily_grid)
        schedule_types_box.append(daily_section)
        
        # Add a separator
        schedule_types_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Weekly snapshots
        weekly_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        weekly_label = Gtk.Label(label="Weekly Snapshots (every Monday at midnight)")
        weekly_label.set_halign(Gtk.Align.START)
        weekly_label.set_margin_start(0)  # Align with frame content
        
        self.weekly_check = Gtk.CheckButton()
        self.weekly_check.set_child(weekly_label)
        self.weekly_check.connect("toggled", self.on_weekly_check_toggled)
        weekly_section.append(self.weekly_check)
        schedule_types_box.append(weekly_section)
        
        # Add a separator
        schedule_types_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Monthly snapshots
        monthly_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        monthly_label = Gtk.Label(label="Monthly Snapshots (on the 1st of each month at midnight)")
        monthly_label.set_halign(Gtk.Align.START)
        monthly_label.set_margin_start(0)  # Align with frame content
        
        self.monthly_check = Gtk.CheckButton()
        self.monthly_check.set_child(monthly_label)
        self.monthly_check.connect("toggled", self.on_monthly_check_toggled)
        monthly_section.append(self.monthly_check)
        schedule_types_box.append(monthly_section)
        
        # Retention settings
        retention_frame = Gtk.Frame()
        retention_frame.set_label("Retention Policy")
        retention_frame.set_margin_top(10)
        retention_frame.set_margin_bottom(10)
        schedule_box.append(retention_frame)
        
        retention_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        retention_box.set_margin_top(10)
        retention_box.set_margin_bottom(10)
        retention_box.set_margin_start(10)
        retention_box.set_margin_end(10)
        retention_frame.set_child(retention_box)
        
        retention_explanation = Gtk.Label(
            label="Specify how many snapshots of each type to keep. Older snapshots will be automatically deleted."
        )
        retention_explanation.set_wrap(True)
        retention_explanation.set_margin_bottom(10)
        retention_explanation.set_halign(Gtk.Align.START)
        retention_explanation.set_margin_start(0)  # Align with frame content
        retention_explanation.add_css_class("dim-label")
        retention_box.append(retention_explanation)
        
        # Hourly retention
        hourly_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hourly_box.append(Gtk.Label(label="Hourly:"))
        self.hourly_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.hourly_spin.set_value(self.config.get("snapshot_retention", {}).get("hourly", 24))
        hourly_box.append(self.hourly_spin)
        retention_box.append(hourly_box)
        
        # Daily retention
        daily_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        daily_box.append(Gtk.Label(label="Daily:"))
        self.daily_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.daily_spin.set_value(self.config.get("snapshot_retention", {}).get("daily", 7))
        daily_box.append(self.daily_spin)
        retention_box.append(daily_box)
        
        # Weekly retention
        weekly_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        weekly_box.append(Gtk.Label(label="Weekly:"))
        self.weekly_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.weekly_spin.set_value(self.config.get("snapshot_retention", {}).get("weekly", 4))
        weekly_box.append(self.weekly_spin)
        retention_box.append(weekly_box)
        
        # Monthly retention
        monthly_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        monthly_box.append(Gtk.Label(label="Monthly:"))
        self.monthly_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.monthly_spin.set_value(self.config.get("snapshot_retention", {}).get("monthly", 12))
        monthly_box.append(self.monthly_spin)
        retention_box.append(monthly_box)
        
        # System Maintenance tab (formerly Pacman Integration)
        maintenance_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        maintenance_box.set_margin_top(10)
        maintenance_box.set_margin_bottom(10)
        maintenance_box.set_margin_start(10)
        maintenance_box.set_margin_end(10)
        notebook.append_page(maintenance_box, Gtk.Label(label="System Maintenance"))
        
        # Pacman integration section
        pacman_frame = Gtk.Frame()
        pacman_frame.set_label("Pacman Integration")
        pacman_frame.set_margin_bottom(10)
        maintenance_box.append(pacman_frame)
        
        pacman_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        pacman_box.set_margin_top(10)
        pacman_box.set_margin_bottom(10)
        pacman_box.set_margin_start(10)
        pacman_box.set_margin_end(10)
        pacman_frame.set_child(pacman_box)
        
        # Enable pacman integration
        self.pacman_switch = Gtk.Switch()
        self.pacman_switch.set_active(self.config.get("pacman_integration", True))
        self.pacman_switch.connect("state-set", self.on_pacman_switch_toggled)
        pacman_enable_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pacman_enable_box.append(Gtk.Label(label="Create Snapshots Before Pacman Operations:"))
        pacman_enable_box.append(self.pacman_switch)
        pacman_box.append(pacman_enable_box)
        
        # Info about pacman hook
        pacman_info = Gtk.Label(label="This will create snapshots before package installations\nand removals via pacman (excludes system updates).")
        pacman_info.set_halign(Gtk.Align.START)
        pacman_info.set_margin_start(0)  # Align with frame content
        pacman_info.set_margin_top(5)
        pacman_info.add_css_class("dim-label")
        pacman_box.append(pacman_info)
        
        # Pacman snapshot name preview
        pacman_preview_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pacman_preview_box.set_halign(Gtk.Align.START)
        pacman_preview_box.set_margin_top(10)
        pacman_preview_label = Gtk.Label(label="Preview:")
        pacman_preview_label.set_size_request(70, -1)
        pacman_preview_label.set_halign(Gtk.Align.START)
        pacman_preview_box.append(pacman_preview_label)
        
        self.pacman_preview_label = Gtk.Label()
        self.pacman_preview_label.set_halign(Gtk.Align.START)
        self.pacman_preview_label.add_css_class("dim-label")
        pacman_preview_box.append(self.pacman_preview_label)
        pacman_box.append(pacman_preview_box)
        
        # Update pacman preview
        self.update_pacman_preview()
        
        # System updates section
        updates_frame = Gtk.Frame()
        updates_frame.set_label("Scheduled System Updates")
        updates_frame.set_margin_top(10)
        updates_frame.set_margin_bottom(10)
        maintenance_box.append(updates_frame)
        
        updates_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        updates_box.set_margin_top(10)
        updates_box.set_margin_bottom(10)
        updates_box.set_margin_start(10)
        updates_box.set_margin_end(10)
        updates_frame.set_child(updates_box)
        
        # Update options
        updates_info = Gtk.Label(label="System updates (pacman -Syu) can be executed automatically during scheduled snapshots.\nChoose when to create snapshots relative to the update:")
        updates_info.set_halign(Gtk.Align.START)
        updates_info.set_margin_bottom(15)  # Better spacing before radio buttons
        updates_info.set_margin_start(0)   # Align with frame content
        updates_info.add_css_class("dim-label")
        updates_box.append(updates_info)
        
        # Radio button for disabled updates
        self.update_disabled_radio = Gtk.CheckButton(label="Do not execute system updates during snapshots")
        self.update_disabled_radio.connect("toggled", self.on_update_option_toggled)
        updates_box.append(self.update_disabled_radio)
        
        # Radio button for system update after snapshot (renamed from "before")
        self.update_before_radio = Gtk.CheckButton(label="Make system update after snapshot (Scheduling needs to be enabled)")
        self.update_before_radio.connect("toggled", self.on_update_option_toggled)
        updates_box.append(self.update_before_radio)
        
        # Clean cache option
        clean_cache_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        clean_cache_box.set_margin_start(0)  # Align with frame content
        clean_cache_box.set_margin_top(10)    # Better spacing from radio buttons
        self.clean_cache_check = Gtk.CheckButton(label="Clean package cache after updates")
        self.clean_cache_check.set_active(self.config.get("clean_cache_after_updates", False))
        clean_cache_box.append(self.clean_cache_check)
        updates_box.append(clean_cache_box)
        
        # Set initial state based on config
        update_option = self.config.get("update_snapshots", "disabled")
        if update_option == "disabled":
            self.update_disabled_radio.set_active(True)
            self.clean_cache_check.set_sensitive(False)
        elif update_option == "before":
            self.update_before_radio.set_active(True)
            self.clean_cache_check.set_sensitive(True)
        else:
            # Default to disabled if invalid value
            self.update_disabled_radio.set_active(True)
            self.clean_cache_check.set_sensitive(False)
        
        # External backup pool section
        backup_frame = Gtk.Frame()
        backup_frame.set_label("External Backup Pool")
        backup_frame.set_margin_top(10)
        backup_frame.set_margin_bottom(10)
        maintenance_box.append(backup_frame)
        
        backup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        backup_box.set_margin_top(10)
        backup_box.set_margin_bottom(10)
        backup_box.set_margin_start(10)
        backup_box.set_margin_end(10)
        backup_frame.set_child(backup_box)
        
        # Enable external backup
        self.backup_switch = Gtk.Switch()
        self.backup_switch.set_active(self.config.get("external_backup_enabled", False))
        self.backup_switch.connect("state-set", self.on_backup_switch_toggled)
        backup_enable_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        backup_enable_box.append(Gtk.Label(label="Enable External Backup:"))
        backup_enable_box.append(self.backup_switch)
        backup_box.append(backup_enable_box)
        
        # Info about external backup
        backup_info = Gtk.Label(label="Send snapshots to an external ZFS pool for backup purposes.\nSnapshots will be replicated using 'zfs send' and 'zfs receive'.")
        backup_info.set_halign(Gtk.Align.START)
        backup_info.set_margin_start(0)
        backup_info.set_margin_top(5)
        backup_info.add_css_class("dim-label")
        backup_box.append(backup_info)
        
        # External pool name entry
        pool_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pool_entry_box.set_margin_top(10)
        pool_label = Gtk.Label(label="External Pool Name:")
        pool_label.set_size_request(140, -1)
        pool_label.set_halign(Gtk.Align.START)
        pool_entry_box.append(pool_label)
        
        self.external_pool_entry = Gtk.Entry()
        self.external_pool_entry.set_text(self.config.get("external_pool_name", ""))
        self.external_pool_entry.set_size_request(200, -1)
        self.external_pool_entry.set_placeholder_text("e.g., backup_pool")
        pool_entry_box.append(self.external_pool_entry)
        
        # Test connection button
        self.test_pool_button = Gtk.Button(label="Test Pool Connection")
        self.test_pool_button.connect("clicked", self.on_test_pool_clicked)
        pool_entry_box.append(self.test_pool_button)
        
        backup_box.append(pool_entry_box)
        
        # Backup schedule options
        backup_schedule_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        backup_schedule_box.set_margin_top(10)
        backup_schedule_label = Gtk.Label(label="Backup Frequency:")
        backup_schedule_label.set_size_request(140, -1)
        backup_schedule_label.set_halign(Gtk.Align.START)
        backup_schedule_box.append(backup_schedule_label)
        
        self.backup_frequency_combo = Gtk.DropDown()
        backup_frequency_model = Gtk.StringList.new([
            "Follow snapshot schedule",
            "Manual"
        ])
        self.backup_frequency_combo.set_model(backup_frequency_model)
        
        # Set current backup frequency
        current_frequency = self.config.get("backup_frequency", "Manual")
        frequency_options = ["Follow snapshot schedule", "Manual"]
        try:
            current_index = frequency_options.index(current_frequency)
            self.backup_frequency_combo.set_selected(current_index)
        except ValueError:
            self.backup_frequency_combo.set_selected(1)  # Default to "Manual"
        
        self.backup_frequency_combo.set_size_request(150, -1)
        backup_schedule_box.append(self.backup_frequency_combo)
        backup_box.append(backup_schedule_box)
        
        # Initialize backup section sensitivity
        self.on_backup_switch_toggled(self.backup_switch, self.backup_switch.get_active())
        
        # Enforce mutual exclusivity between pacman integration and system updates
        pacman_enabled = self.config.get("pacman_integration", True)
        update_option = self.config.get("update_snapshots", "disabled")
        
        if pacman_enabled and update_option != "disabled":
            # If both are enabled in config, prioritize pacman and disable updates
            self.update_disabled_radio.set_active(True)
            self.update_before_radio.set_active(False)
            self.clean_cache_check.set_sensitive(False)
            update_option = "disabled"
        
        # Set initial sensitivity based on mutual exclusivity
        if pacman_enabled:
            self.update_disabled_radio.set_sensitive(False)
            self.update_before_radio.set_sensitive(False)
        elif update_option != "disabled":
            self.pacman_switch.set_sensitive(False)
        
        # Advanced tab (if module is available)
        if AdvancedSettingsTab:
            self.advanced_tab = AdvancedSettingsTab(self)
            notebook.append_page(self.advanced_tab.get_box(), Gtk.Label(label="Advanced"))
        
        # Connect to response signal
        self.connect("response", self.on_response)
        
        # Set initial state of hourly and daily sections
        hourly_has_hours = bool(self.config.get("hourly_schedule", []))
        daily_has_days = bool(self.config.get("daily_schedule", []))
        
        self.hourly_check.set_active(hourly_has_hours)
        self.daily_check.set_active(daily_has_days)
        self.weekly_check.set_active(self.config.get("weekly_schedule", False))
        self.monthly_check.set_active(self.config.get("monthly_schedule", False))
        
        # Set initial state of time selectors
        self.daily_hour_spin.set_sensitive(daily_has_days)
        
        # Initialize sensitivity based on checkbox state
        self.on_hourly_check_toggled(self.hourly_check)
        self.on_daily_check_toggled(self.daily_check)
        
        # Initialize sensitivity based on auto-snapshot setting
        auto_snapshot_enabled = self.config.get("auto_snapshot", True)
        if not auto_snapshot_enabled:
            self.hourly_check.set_sensitive(False)
            self.daily_check.set_sensitive(False)
            self.weekly_check.set_sensitive(False)
            self.monthly_check.set_sensitive(False)
            
            # Disable selection buttons when auto-snapshot is disabled
            self.hourly_select_all_button.set_sensitive(False)
            self.hourly_select_none_button.set_sensitive(False)
            self.daily_select_all_button.set_sensitive(False)
            self.daily_select_none_button.set_sensitive(False)
            
            # Disable all hour checkboxes
            for check in self.hour_checks.values():
                check.set_sensitive(False)
                
            # Disable all day checkboxes and time selector
            for check in self.day_checks.values():
                check.set_sensitive(False)
            self.daily_hour_spin.set_sensitive(False)
            
            # Disable snapshot naming fields
            self.prefix_entry.set_sensitive(False)
            self.format_combo.set_sensitive(False)
            
            # Disable system update options when scheduling is disabled
            self.update_disabled_radio.set_sensitive(False)
            self.update_before_radio.set_sensitive(False)
            self.clean_cache_check.set_sensitive(False)
        
        self.show()

    def on_select_all_clicked(self, button):
        """Handle select all button click"""
        if not hasattr(self, 'datasets_list'):
            return
            
        for row in self.datasets_list:
            box = row.get_child()
            check = box.get_first_child()
            check.set_active(True)

    def on_select_none_clicked(self, button):
        """Handle select none button click"""
        if not hasattr(self, 'datasets_list'):
            return
            
        for row in self.datasets_list:
            box = row.get_child()
            check = box.get_first_child()
            check.set_active(False)
            
    def on_response(self, dialog, response):
        """Handle dialog response"""
        if response == Gtk.ResponseType.OK:
            # Validate schedules - ensure at least one hour/day is selected if the schedule is enabled
            hourly_enabled = self.hourly_check.get_active()
            daily_enabled = self.daily_check.get_active()
            
            # Check if any hours are selected for hourly schedule
            selected_hours = [hour for hour, check in self.hour_checks.items() if check.get_active()]
            if hourly_enabled and not selected_hours:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Invalid Schedule",
                    secondary_text="Please select at least one hour for hourly snapshots, or disable hourly snapshots."
                )
                error_dialog.connect("response", lambda d, r: d.destroy())
                error_dialog.present()
                return
            
            # Check if any days are selected for daily schedule
            selected_days = [day for day, check in self.day_checks.items() if check.get_active()]
            if daily_enabled and not selected_days:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Invalid Schedule",
                    secondary_text="Please select at least one day for daily snapshots, or disable daily snapshots."
                )
                error_dialog.connect("response", lambda d, r: d.destroy())
                error_dialog.present()
                return
                
            # Update config
            
            # Update prefix
            self.config["prefix"] = self.prefix_entry.get_text().strip()
            
            # Update snapshot name format
            selected = self.format_combo.get_selected()
            format_options = [
                "prefix-type-timestamp", "prefix-timestamp-type", "type-prefix-timestamp", "timestamp-prefix-type",
                "prefix-type-timestamp-short", "prefix-timestamp-short-type", "type-prefix-timestamp-short", "timestamp-short-prefix-type"
            ]
            if selected < len(format_options):
                self.config["snapshot_name_format"] = format_options[selected]
            else:
                self.config["snapshot_name_format"] = "prefix-type-timestamp"
            
            # Update appearance settings
            dark_mode_changed = self.config.get("dark_mode", False) != self.dark_mode_switch.get_active()
            self.config["dark_mode"] = self.dark_mode_switch.get_active()
            
            # Update notification settings
            self.config["notifications_enabled"] = self.notifications_switch.get_active()
            
            # Update managed datasets
            managed_datasets = []
            if hasattr(self, 'datasets_list'):
                for row in self.datasets_list:
                    box = row.get_child()
                    check = box.get_first_child()
                    if check.get_active():
                        managed_datasets.append(check.get_label())
            
            self.config["datasets"] = managed_datasets
              # Update auto snapshot settings
            self.config["auto_snapshot"] = self.schedule_switch.get_active()
            
            # Update hourly schedule with selected hours
            hourly_schedule = []
            if self.hourly_check.get_active():
                for hour, check in self.hour_checks.items():
                    if check.get_active():
                        hourly_schedule.append(hour)
            self.config["hourly_schedule"] = hourly_schedule
              # Update daily schedule with selected days and time
            daily_schedule = []
            if self.daily_check.get_active():
                for day, check in self.day_checks.items():
                    if check.get_active():
                        daily_schedule.append(day)
            self.config["daily_schedule"] = daily_schedule
            self.config["daily_hour"] = int(self.daily_hour_spin.get_value())
            
            # Update retention policy
            self.config["snapshot_retention"] = {
                "hourly": int(self.hourly_spin.get_value()),
                "daily": int(self.daily_spin.get_value()),
                "weekly": int(self.weekly_spin.get_value()),
                "monthly": int(self.monthly_spin.get_value())
            }
            
            # Update pacman integration
            self.config["pacman_integration"] = self.pacman_switch.get_active()
            
            # Update system update snapshots option
            if self.update_disabled_radio.get_active():
                self.config["update_snapshots"] = "disabled"
            elif self.update_before_radio.get_active():
                self.config["update_snapshots"] = "before"
            else:
                # Default to "disabled" if none is selected
                self.config["update_snapshots"] = "disabled"
            
            # Update clean cache option
            self.config["clean_cache_after_updates"] = self.clean_cache_check.get_active()
            
            # Update external backup settings
            self.config["external_backup_enabled"] = self.backup_switch.get_active()
            self.config["external_pool_name"] = self.external_pool_entry.get_text().strip()
            
            # Update backup frequency
            backup_selected = self.backup_frequency_combo.get_selected()
            frequency_options = ["Follow snapshot schedule", "Manual"]
            if backup_selected < len(frequency_options):
                self.config["backup_frequency"] = frequency_options[backup_selected]
            else:
                self.config["backup_frequency"] = "Manual"
            
            # Save config
            self.zfs_assistant.config = self.config
            self.zfs_assistant.save_config()
              # Setup pacman hook
            pacman_success, pacman_message = self.zfs_assistant.setup_pacman_hook(self.config["pacman_integration"])
            if not pacman_success:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Pacman Hook Setup Failed",
                    secondary_text=f"Failed to setup pacman hook: {pacman_message}"
                )
                error_dialog.connect("response", lambda d, r: d.destroy())
                error_dialog.present()
                
            # Setup systemd timers
            schedules = {
                "hourly": self.hourly_check.get_active(),
                "daily": self.daily_check.get_active(),
                "weekly": self.weekly_check.get_active(),
                "monthly": self.monthly_check.get_active()
            }
            
            # Save the weekly and monthly state in config
            self.config["weekly_schedule"] = self.weekly_check.get_active()
            self.config["monthly_schedule"] = self.monthly_check.get_active()
            
            if self.config["auto_snapshot"]:
                timer_success, timer_message = self.zfs_assistant.setup_systemd_timers(schedules)
                if not timer_success:
                    error_dialog = Gtk.MessageDialog(
                        transient_for=self,
                        modal=True,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Systemd Timer Setup Failed",
                        secondary_text=f"Failed to setup systemd timers: {timer_message}"
                    )
                    error_dialog.connect("response", lambda d, r: d.destroy())
                    error_dialog.present()
            
            # Update theme if dark mode changed
            if dark_mode_changed:
                self.parent.app.toggle_dark_mode(self.dark_mode_switch.get_active())
                
            # Update notifications setting
            self.parent.app.toggle_notifications(self.notifications_switch.get_active())
            
            # Close the dialog without showing a message
            self.destroy()
            return
        
        self.destroy()
        
    # Success handler removed since we no longer show the success dialog

    def on_hourly_check_toggled(self, button):
        """Handle hourly checkbox toggle to enable/disable hour selection"""
        active = button.get_active()
        for hour, check in self.hour_checks.items():
            check.set_sensitive(active)
            
        # Also enable/disable the selection buttons
        auto_snapshot_enabled = self.config.get("auto_snapshot", True)
        if auto_snapshot_enabled:  # Only toggle if auto_snapshot is enabled
            self.hourly_select_all_button.set_sensitive(active)
            self.hourly_select_none_button.set_sensitive(active)
        
        # Update snapshot preview when schedule type changes
        self.update_snapshot_preview()
            
    def on_hourly_select_all_clicked(self, button):
        """Select all hours"""
        for check in self.hour_checks.values():
            check.set_active(True)
        self.update_snapshot_preview()
            
    def on_hourly_select_none_clicked(self, button):
        """Deselect all hours"""
        for check in self.hour_checks.values():
            check.set_active(False)
        self.update_snapshot_preview()
            
    def on_daily_check_toggled(self, button):
        """Handle daily checkbox toggle to enable/disable day selection and time selection"""
        active = button.get_active()
        for day, check in self.day_checks.items():
            check.set_sensitive(active)
        self.daily_hour_spin.set_sensitive(active)
        
        # Also enable/disable the selection buttons
        auto_snapshot_enabled = self.config.get("auto_snapshot", True)
        if auto_snapshot_enabled:  # Only toggle if auto_snapshot is enabled
            self.daily_select_all_button.set_sensitive(active)
            self.daily_select_none_button.set_sensitive(active)
        
        # Update snapshot preview when schedule type changes
        self.update_snapshot_preview()
        
    def on_daily_select_all_clicked(self, button):
        """Select all days"""
        for check in self.day_checks.values():
            check.set_active(True)
        self.update_snapshot_preview()
            
    def on_daily_select_none_clicked(self, button):
        """Deselect all days"""
        for check in self.day_checks.values():
            check.set_active(False)
        self.update_snapshot_preview()
            
    def on_weekly_check_toggled(self, button):
        """Handle weekly checkbox toggle"""
        # Update snapshot preview when schedule type changes
        self.update_snapshot_preview()
            
    def on_monthly_check_toggled(self, button):
        """Handle monthly checkbox toggle"""
        # Update snapshot preview when schedule type changes
        self.update_snapshot_preview()
    
    def on_pacman_switch_toggled(self, widget, state):
        """Handle pacman integration toggle - make mutually exclusive with system updates"""
        # Check if all required attributes exist (handles initialization order)
        if not all(hasattr(self, attr) for attr in ['update_disabled_radio', 
                                                   'update_before_radio', 
                                                   'clean_cache_check']):
            return False
            
        if state:
            # If pacman integration is enabled, disable system updates
            self.update_disabled_radio.set_active(True)
            self.update_before_radio.set_active(False)
            self.clean_cache_check.set_sensitive(False)
            
            # Disable system update radio buttons
            self.update_disabled_radio.set_sensitive(False)
            self.update_before_radio.set_sensitive(False)
        else:
            # Re-enable system update radio buttons
            self.update_disabled_radio.set_sensitive(True)
            self.update_before_radio.set_sensitive(True)
        
        # Update pacman preview
        self.update_pacman_preview()
        return False
    
    def on_backup_switch_toggled(self, widget, state):
        """Handle external backup toggle"""
        # Enable/disable backup-related controls
        self.external_pool_entry.set_sensitive(state)
        self.test_pool_button.set_sensitive(state)
        self.backup_frequency_combo.set_sensitive(state)
        return False
    
    def on_test_pool_clicked(self, button):
        """Test connection to external pool"""
        pool_name = self.external_pool_entry.get_text().strip()
        if not pool_name:
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Pool Name Required",
                secondary_text="Please enter an external pool name to test."
            )
            error_dialog.connect("response", lambda d, r: d.destroy())
            error_dialog.present()
            return
        
        # Test pool existence and accessibility
        try:
            import subprocess
            result = subprocess.run(['zpool', 'list', pool_name], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Pool exists and is accessible
                success_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    modal=True,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Pool Connection Successful",
                    secondary_text=f"External pool '{pool_name}' is accessible and ready for backup operations."
                )
            else:
                # Pool not found or not accessible
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Pool Connection Failed",
                    secondary_text=f"Cannot access external pool '{pool_name}'. Please check if the pool exists and is imported."
                )
                success_dialog = error_dialog
        except subprocess.TimeoutExpired:
            error_dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Connection Timeout",
                secondary_text="The pool test operation timed out. Please check your system."
            )
            success_dialog = error_dialog
        except Exception as e:
            error_dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Test Failed",
                secondary_text=f"Error testing pool connection: {str(e)}"
            )
            success_dialog = error_dialog
        
        success_dialog.connect("response", lambda d, r: d.destroy())
        success_dialog.present()
    
    def update_pacman_preview(self, widget=None):
        """Update the pacman snapshot name preview"""
        import datetime
        
        # Check if the required attributes exist (handles initialization order)
        if not hasattr(self, 'pacman_switch') or not hasattr(self, 'pacman_preview_label'):
            return
            
        if not self.pacman_switch.get_active():
            self.pacman_preview_label.set_text("(Pacman integration disabled)")
            return
        
        prefix = self.prefix_entry.get_text().strip() or "zfs-assistant"
        selected = self.format_combo.get_selected()
        format_options = [
            "prefix-type-timestamp", "prefix-timestamp-type", "type-prefix-timestamp", "timestamp-prefix-type",
            "prefix-type-timestamp-short", "prefix-timestamp-short-type", "type-prefix-timestamp-short", "timestamp-short-prefix-type"
        ]
        format_type = format_options[selected] if selected < len(format_options) else "prefix-type-timestamp"
        
        sample_time = datetime.datetime.now()
        timestamp = sample_time.strftime("%Y%m%d-%H%M%S")
        timestamp_short = sample_time.strftime("%Y%m%d-%H%M")
        
        preview = self._generate_preview_name(prefix, "pacman", timestamp, timestamp_short, format_type)
        self.pacman_preview_label.set_text(preview)
            
    def on_schedule_switch_toggled(self, widget, state):
        """Enable or disable all schedule widgets based on auto-snapshot toggle"""
        # Update sensitivity of all schedule-related widgets
        self.hourly_check.set_sensitive(state)
        self.daily_check.set_sensitive(state)
        self.weekly_check.set_sensitive(state)
        self.monthly_check.set_sensitive(state)
        
        # Update sensitivity of hourly buttons
        self.hourly_select_all_button.set_sensitive(state)
        self.hourly_select_none_button.set_sensitive(state)
        
        # Update sensitivity of daily buttons
        self.daily_select_all_button.set_sensitive(state)
        self.daily_select_none_button.set_sensitive(state)
        
        # Update sensitivity of hourly grid
        for check in self.hour_checks.values():
            check.set_sensitive(state and self.hourly_check.get_active())
            
        # Update sensitivity of daily grid and time selector
        for check in self.day_checks.values():
            check.set_sensitive(state and self.daily_check.get_active())
        self.daily_hour_spin.set_sensitive(state and self.daily_check.get_active())
        
        # Update sensitivity of snapshot naming fields
        self.prefix_entry.set_sensitive(state)
        self.format_combo.set_sensitive(state)
        
        # Update sensitivity of system update options (only available when scheduling is enabled)
        self.update_disabled_radio.set_sensitive(state)
        self.update_before_radio.set_sensitive(state)
        # Clean cache option should only be enabled if scheduling is on AND update option is enabled
        current_update_enabled = self.update_before_radio.get_active()
        self.clean_cache_check.set_sensitive(state and current_update_enabled)
        
        return False  # Allow the state change to proceed
    
    def update_snapshot_preview(self, widget=None, *args):
        """Update the snapshot name preview"""
        import datetime
        
        # Clear existing previews
        child = self.preview_container.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.preview_container.remove(child)
            child = next_child
        
        prefix = self.prefix_entry.get_text().strip() or "zfs-assistant"
        selected = self.format_combo.get_selected()
        format_options = [
            "prefix-type-timestamp", "prefix-timestamp-type", "type-prefix-timestamp", "timestamp-prefix-type",
            "prefix-type-timestamp-short", "prefix-timestamp-short-type", "type-prefix-timestamp-short", "timestamp-short-prefix-type"
        ]
        format_type = format_options[selected] if selected < len(format_options) else "prefix-type-timestamp"
        
        # Check which schedule types are active
        active_schedules = []
        
        if hasattr(self, 'hourly_check') and self.hourly_check.get_active():
            # Get selected hours for hourly preview
            selected_hours = []
            if hasattr(self, 'hour_checks'):
                for hour, check in self.hour_checks.items():
                    if check.get_active():
                        selected_hours.append(hour)
            
            if selected_hours:
                # Show first few selected hours as examples
                example_hours = selected_hours[:3]  # Show up to 3 examples
                for hour in example_hours:
                    sample_time = datetime.datetime.now().replace(hour=hour, minute=0, second=0)
                    timestamp = sample_time.strftime("%Y%m%d-%H%M%S")
                    timestamp_short = sample_time.strftime("%Y%m%d-%H%M")
                    
                    preview = self._generate_preview_name(prefix, "hourly", timestamp, timestamp_short, format_type)
                    active_schedules.append(f"Hourly ({hour:02d}:00): {preview}")
                
                # If more than 3 hours selected, show count
                if len(selected_hours) > 3:
                    active_schedules.append(f"... and {len(selected_hours) - 3} more hourly times")
            else:
                # No hours selected but hourly is enabled
                sample_time = datetime.datetime.now()
                timestamp = sample_time.strftime("%Y%m%d-%H%M%S")
                timestamp_short = sample_time.strftime("%Y%m%d-%H%M")
                preview = self._generate_preview_name(prefix, "hourly", timestamp, timestamp_short, format_type)
                active_schedules.append(f"Hourly (no hours selected): {preview}")
        
        if hasattr(self, 'daily_check') and self.daily_check.get_active():
            # Get selected days and time for daily preview
            selected_days = []
            if hasattr(self, 'day_checks'):
                for day_idx, check in self.day_checks.items():
                    if check.get_active():
                        selected_days.append(day_idx)
            
            daily_hour = 0
            if hasattr(self, 'daily_hour_spin'):
                daily_hour = int(self.daily_hour_spin.get_value())
            
            if selected_days:
                # Show first few selected days as examples
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                example_days = selected_days[:3]  # Show up to 3 examples
                for day_idx in example_days:
                    # Calculate next occurrence of this day at the specified hour
                    today = datetime.date.today()
                    days_ahead = day_idx - today.weekday()
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    target_date = today + datetime.timedelta(days=days_ahead)
                    sample_time = datetime.datetime.combine(target_date, datetime.time(daily_hour, 0))
                    
                    timestamp = sample_time.strftime("%Y%m%d-%H%M%S")
                    timestamp_short = sample_time.strftime("%Y%m%d-%H%M")
                    
                    preview = self._generate_preview_name(prefix, "daily", timestamp, timestamp_short, format_type)
                    active_schedules.append(f"Daily ({days[day_idx]} {daily_hour:02d}:00): {preview}")
                
                # If more than 3 days selected, show count
                if len(selected_days) > 3:
                    active_schedules.append(f"... and {len(selected_days) - 3} more daily schedules")
            else:
                # No days selected but daily is enabled
                sample_time = datetime.datetime.now().replace(hour=daily_hour, minute=0, second=0)
                timestamp = sample_time.strftime("%Y%m%d-%H%M%S")
                timestamp_short = sample_time.strftime("%Y%m%d-%H%M")
                preview = self._generate_preview_name(prefix, "daily", timestamp, timestamp_short, format_type)
                active_schedules.append(f"Daily (no days selected): {preview}")
        
        if hasattr(self, 'weekly_check') and self.weekly_check.get_active():
            # Calculate next Monday
            today = datetime.date.today()
            days_ahead = 0 - today.weekday()  # Monday is 0
            if days_ahead <= 0:  # Monday already happened this week
                days_ahead += 7
            next_monday = today + datetime.timedelta(days=days_ahead)
            sample_time = datetime.datetime.combine(next_monday, datetime.time(0, 0))
            
            timestamp = sample_time.strftime("%Y%m%d-%H%M%S")
            timestamp_short = sample_time.strftime("%Y%m%d-%H%M")
            
            preview = self._generate_preview_name(prefix, "weekly", timestamp, timestamp_short, format_type)
            active_schedules.append(f"Weekly (Monday 00:00): {preview}")
        
        if hasattr(self, 'monthly_check') and self.monthly_check.get_active():
            # Calculate next 1st of month
            today = datetime.date.today()
            if today.day == 1:
                # If today is the 1st, show next month
                if today.month == 12:
                    next_first = datetime.date(today.year + 1, 1, 1)
                else:
                    next_first = datetime.date(today.year, today.month + 1, 1)
            else:
                # Show 1st of next month
                if today.month == 12:
                    next_first = datetime.date(today.year + 1, 1, 1)
                else:
                    next_first = datetime.date(today.year, today.month + 1, 1)
            
            sample_time = datetime.datetime.combine(next_first, datetime.time(0, 0))
            timestamp = sample_time.strftime("%Y%m%d-%H%M%S")
            timestamp_short = sample_time.strftime("%Y%m%d-%H%M")
            
            preview = self._generate_preview_name(prefix, "monthly", timestamp, timestamp_short, format_type)
            active_schedules.append(f"Monthly (1st 00:00): {preview}")
        
        # If no schedules are active, show manual snapshot example
        if not active_schedules:
            sample_time = datetime.datetime.now()
            timestamp = sample_time.strftime("%Y%m%d-%H%M%S")
            timestamp_short = sample_time.strftime("%Y%m%d-%H%M")
            preview = self._generate_preview_name(prefix, "manual", timestamp, timestamp_short, format_type)
            active_schedules.append(f"Manual snapshot: {preview}")
        
        # Create labels for each preview
        for schedule_preview in active_schedules:
            label = Gtk.Label(label=schedule_preview)
            label.set_halign(Gtk.Align.START)
            label.add_css_class("dim-label")
            self.preview_container.append(label)
    
    def _generate_preview_name(self, prefix, sample_type, timestamp, timestamp_short, format_type):
        """Generate a preview name based on format type"""
        if format_type == "prefix-type-timestamp":
            return f"{prefix}-{sample_type}-{timestamp}"
        elif format_type == "prefix-timestamp-type":
            return f"{prefix}-{timestamp}-{sample_type}"
        elif format_type == "type-prefix-timestamp":
            return f"{sample_type}-{prefix}-{timestamp}"
        elif format_type == "timestamp-prefix-type":
            return f"{timestamp}-{prefix}-{sample_type}"
        elif format_type == "prefix-type-timestamp-short":
            return f"{prefix}-{sample_type}-{timestamp_short}"
        elif format_type == "prefix-timestamp-short-type":
            return f"{prefix}-{timestamp_short}-{sample_type}"
        elif format_type == "type-prefix-timestamp-short":
            return f"{sample_type}-{prefix}-{timestamp_short}"
        elif format_type == "timestamp-short-prefix-type":
            return f"{timestamp_short}-{prefix}-{sample_type}"
        else:
            return f"{prefix}-{sample_type}-{timestamp}"

    def on_update_option_toggled(self, toggled_button):
        """Make the update option checkboxes act as radio buttons and mutually exclusive with pacman"""
        # Check if all required attributes exist (handles initialization order)
        if not all(hasattr(self, attr) for attr in ['pacman_switch', 'update_disabled_radio', 
                                                   'update_before_radio', 
                                                   'clean_cache_check']):
            return
            
        if toggled_button.get_active():
            # If any system update option is enabled, disable pacman integration
            if toggled_button != self.update_disabled_radio:
                self.pacman_switch.set_active(False)
                self.pacman_switch.set_sensitive(False)
            else:
                # If disabled is selected, re-enable pacman integration
                self.pacman_switch.set_sensitive(True)
            
            # Determine which button was toggled and deactivate the others
            if toggled_button == self.update_disabled_radio:
                self.update_before_radio.set_active(False)
                self.clean_cache_check.set_sensitive(False)
            elif toggled_button == self.update_before_radio:
                self.update_disabled_radio.set_active(False)
                self.clean_cache_check.set_sensitive(True)
        
        # Update pacman preview since it might have changed
        self.update_pacman_preview()
