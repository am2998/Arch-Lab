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
        
        # Match the main window size
        self.set_default_size(900, 600)
        self.set_size_request(800, 500)
        
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
        
        # Snapshot prefix
        prefix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        prefix_box.append(Gtk.Label(label="Snapshot Prefix:"))
        self.prefix_entry = Gtk.Entry()
        self.prefix_entry.set_text(self.config.get("prefix", "zfs-assistant"))
        prefix_box.append(self.prefix_entry)
        general_box.append(prefix_box)
        
        # Datasets selection
        general_box.append(Gtk.Label(label="Managed Datasets:"))
        
        # Create scrolled window for datasets
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(150)
        general_box.append(scrolled)
        
        # Create list box for datasets
        self.datasets_list = Gtk.ListBox()
        self.datasets_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.set_child(self.datasets_list)
        
        # Add available datasets with checkboxes
        available_datasets = self.zfs_assistant.get_datasets()
        managed_datasets = self.config.get("datasets", [])
        
        for dataset in available_datasets:
            dataset_name = dataset['name']
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            check = Gtk.CheckButton(label=dataset_name)
            
            if dataset_name in managed_datasets:
                check.set_active(True)
            
            box.append(check)
            row.set_child(box)
            self.datasets_list.append(row)
        
        # Add/remove datasets
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_homogeneous(True)
        
        select_all_button = Gtk.Button(label="Select All")
        select_all_button.connect("clicked", self.on_select_all_clicked)
        button_box.append(select_all_button)
        
        select_none_button = Gtk.Button(label="Select None")
        select_none_button.connect("clicked", self.on_select_none_clicked)
        button_box.append(select_none_button)
        
        general_box.append(button_box)        # Schedule settings tab
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
                  "you can select multiple hours or days."
        )
        explanation_label.set_wrap(True)
        explanation_label.set_margin_top(5)
        explanation_label.set_margin_bottom(5)
        schedule_box.append(explanation_label)
        
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
        hourly_explanation.set_margin_start(20)
        hourly_explanation.set_halign(Gtk.Align.START)
        hourly_section.append(hourly_explanation)
          # Hours selection grid
        self.hourly_grid = Gtk.Grid()
        self.hourly_grid.set_column_homogeneous(True)
        self.hourly_grid.set_row_spacing(5)
        self.hourly_grid.set_column_spacing(10)
        self.hourly_grid.set_margin_start(20)  # Indent
        
        # Hour selection button box
        hourly_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hourly_button_box.set_margin_bottom(5)
        hourly_button_box.set_margin_start(20)  # Indent
        
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
            self.hour_checks[hour] = check
            self.hourly_grid.attach(check, col, row, 1, 1)
        
        hourly_section.append(self.hourly_grid)
        schedule_types_box.append(hourly_section)
        
        # Add a separator
        schedule_types_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))        # Daily snapshots with multiple days selection
        daily_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        daily_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.daily_check = Gtk.CheckButton(label="Daily Snapshots")
        self.daily_check.connect("toggled", self.on_daily_check_toggled)
        daily_header.append(self.daily_check)
        
        # Time selection for daily snapshots
        daily_header.append(Gtk.Label(label="at time:"))
        self.daily_hour_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.daily_hour_spin.set_value(self.config.get("daily_hour", 0))
        daily_header.append(self.daily_hour_spin)
        daily_header.append(Gtk.Label(label=":00"))
        
        daily_section.append(daily_header)
        
        # Add explanation for daily
        daily_explanation = Gtk.Label(label="Select the days of the week when snapshots should be taken")
        daily_explanation.set_margin_start(20)
        daily_explanation.set_halign(Gtk.Align.START)
        daily_section.append(daily_explanation)
          # Days selection grid
        self.daily_grid = Gtk.Grid()
        self.daily_grid.set_column_homogeneous(True)
        self.daily_grid.set_row_spacing(5)
        self.daily_grid.set_column_spacing(10)
        self.daily_grid.set_margin_start(20)  # Indent
        
        # Day selection button box
        daily_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        daily_button_box.set_margin_bottom(5)
        daily_button_box.set_margin_start(20)  # Indent
        
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
            self.day_checks[day_idx] = check
            self.daily_grid.attach(check, col, row, 1, 1)
        
        daily_section.append(self.daily_grid)
        schedule_types_box.append(daily_section)
        
        # Add a separator
        schedule_types_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
          # Weekly snapshots
        weekly_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.weekly_check = Gtk.CheckButton(label="Weekly Snapshots (every Monday at midnight)")
        weekly_section.append(self.weekly_check)
        schedule_types_box.append(weekly_section)
        
        # Add a separator
        schedule_types_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Monthly snapshots
        monthly_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.monthly_check = Gtk.CheckButton(label="Monthly Snapshots (on the 1st of each month at midnight)")
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
        
        # Pacman integration tab
        pacman_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        pacman_box.set_margin_top(10)
        pacman_box.set_margin_bottom(10)
        pacman_box.set_margin_start(10)
        pacman_box.set_margin_end(10)
        notebook.append_page(pacman_box, Gtk.Label(label="Pacman Integration"))
        
        # Enable pacman integration
        self.pacman_switch = Gtk.Switch()
        self.pacman_switch.set_active(self.config.get("pacman_integration", True))
        pacman_enable_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pacman_enable_box.append(Gtk.Label(label="Create Snapshots Before Pacman Operations:"))
        pacman_enable_box.append(self.pacman_switch)
        pacman_box.append(pacman_enable_box)
        
        # Info about pacman hook
        pacman_box.append(Gtk.Label(label="This will create snapshots before package installations,\nupdates, and removals via pacman."))
        
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
        
        self.show()

    def on_select_all_clicked(self, button):
        """Handle select all button click"""
        for row in self.datasets_list:
            box = row.get_child()
            check = box.get_first_child()
            check.set_active(True)

    def on_select_none_clicked(self, button):
        """Handle select none button click"""
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
            
            # Update appearance settings
            dark_mode_changed = self.config.get("dark_mode", False) != self.dark_mode_switch.get_active()
            self.config["dark_mode"] = self.dark_mode_switch.get_active()
            
            # Update notification settings
            self.config["notifications_enabled"] = self.notifications_switch.get_active()
            
            # Update managed datasets
            managed_datasets = []
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
            
            # Save config
            self.zfs_assistant.config = self.config
            self.zfs_assistant.save_config()
            
            # Setup pacman hook
            self.zfs_assistant.setup_pacman_hook(self.config["pacman_integration"])
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
                self.zfs_assistant.setup_systemd_timers(schedules)
            
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
            
    def on_hourly_select_all_clicked(self, button):
        """Select all hours"""
        for check in self.hour_checks.values():
            check.set_active(True)
            
    def on_hourly_select_none_clicked(self, button):
        """Deselect all hours"""
        for check in self.hour_checks.values():
            check.set_active(False)
            
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
        
    def on_daily_select_all_clicked(self, button):
        """Select all days"""
        for check in self.day_checks.values():
            check.set_active(True)
            
    def on_daily_select_none_clicked(self, button):
        """Deselect all days"""
        for check in self.day_checks.values():
            check.set_active(False)
            
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
        
        return False  # Allow the state change to proceed
