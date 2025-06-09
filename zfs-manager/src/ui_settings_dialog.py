#!/usr/bin/env python3
# ZFS Manager - Settings Dialog
# Author: GitHub Copilot

import gi
import os
import subprocess

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, GObject

# Try to import advanced settings
try:
    from .ui_advanced_settings import AdvancedSettingsTab
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
        self.zfs_manager = parent.zfs_manager
        self.config = self.zfs_manager.config.copy()
        
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        
        self.set_default_size(500, 400)
        
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
        self.prefix_entry.set_text(self.config.get("prefix", "zfs-manager"))
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
        available_datasets = self.zfs_manager.get_datasets()
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
        
        general_box.append(button_box)
        
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
        schedule_enable_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        schedule_enable_box.append(Gtk.Label(label="Enable Scheduled Snapshots:"))
        schedule_enable_box.append(self.schedule_switch)
        schedule_box.append(schedule_enable_box)
        
        # Snapshot schedules
        schedule_box.append(Gtk.Label(label="Snapshot Schedules:"))
        
        # Hourly snapshots
        self.hourly_check = Gtk.CheckButton(label="Hourly Snapshots")
        schedule_box.append(self.hourly_check)
        
        # Daily snapshots
        self.daily_check = Gtk.CheckButton(label="Daily Snapshots")
        schedule_box.append(self.daily_check)
        
        # Weekly snapshots
        self.weekly_check = Gtk.CheckButton(label="Weekly Snapshots")
        schedule_box.append(self.weekly_check)
        
        # Monthly snapshots
        self.monthly_check = Gtk.CheckButton(label="Monthly Snapshots")
        schedule_box.append(self.monthly_check)
        
        # Retention settings
        schedule_box.append(Gtk.Label(label="Retention Policy (Number to Keep):"))
        
        # Hourly retention
        hourly_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hourly_box.append(Gtk.Label(label="Hourly:"))
        self.hourly_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.hourly_spin.set_value(self.config.get("snapshot_retention", {}).get("hourly", 24))
        hourly_box.append(self.hourly_spin)
        schedule_box.append(hourly_box)
        
        # Daily retention
        daily_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        daily_box.append(Gtk.Label(label="Daily:"))
        self.daily_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.daily_spin.set_value(self.config.get("snapshot_retention", {}).get("daily", 7))
        daily_box.append(self.daily_spin)
        schedule_box.append(daily_box)
        
        # Weekly retention
        weekly_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        weekly_box.append(Gtk.Label(label="Weekly:"))
        self.weekly_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.weekly_spin.set_value(self.config.get("snapshot_retention", {}).get("weekly", 4))
        weekly_box.append(self.weekly_spin)
        schedule_box.append(weekly_box)
        
        # Monthly retention
        monthly_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        monthly_box.append(Gtk.Label(label="Monthly:"))
        self.monthly_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.monthly_spin.set_value(self.config.get("snapshot_retention", {}).get("monthly", 12))
        monthly_box.append(self.monthly_spin)
        schedule_box.append(monthly_box)
        
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
            self.zfs_manager.config = self.config
            self.zfs_manager.save_config()
            
            # Setup pacman hook
            self.zfs_manager.setup_pacman_hook(self.config["pacman_integration"])
            
            # Setup systemd timers
            schedules = {
                "hourly": self.hourly_check.get_active(),
                "daily": self.daily_check.get_active(),
                "weekly": self.weekly_check.get_active(),
                "monthly": self.monthly_check.get_active()
            }
            
            if self.config["auto_snapshot"]:
                self.zfs_manager.setup_systemd_timers(schedules)
            
            # Update theme if dark mode changed
            if dark_mode_changed:
                self.parent.app.toggle_dark_mode(self.dark_mode_switch.get_active())
                
            # Update notifications setting
            self.parent.app.toggle_notifications(self.notifications_switch.get_active())
            
            # Show success message
            result_dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Settings Saved"
            )
            result_dialog.format_secondary_text("Settings have been saved successfully.")
            result_dialog.connect("response", lambda d, r: d.destroy())
            result_dialog.present()
        
        self.destroy()
