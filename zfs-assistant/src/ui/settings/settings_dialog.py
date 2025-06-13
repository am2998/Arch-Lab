#!/usr/bin/env python3
# ZFS Assistant - Settings Dialog
# Author: GitHub Copilot

import gi
import threading
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

# Import the tab components
from .general_tab import GeneralSettingsTab
from .schedule_tab import ScheduleSettingsTab
from .maintenance_tab import MaintenanceSettingsTab
from .advanced_tab import AdvancedSettingsTab

class SettingsDialog(Gtk.Dialog):
    """Main settings dialog with organized tabs"""
    
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
        self._dialog_alive = True
        
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        
        # Set dialog size to be more horizontal (wider, less tall)
        self.set_default_size(1400, 600)  # Wider and shorter than before
        self.set_size_request(1200, 500)   # Minimum size also wider and shorter
        
        # Create notebook for tabs
        notebook = Gtk.Notebook()
        content_area = self.get_content_area()
        content_area.append(notebook)
        
        # Initialize tab components
        self.general_tab = GeneralSettingsTab(self)
        self.schedule_tab = ScheduleSettingsTab(self)
        self.maintenance_tab = MaintenanceSettingsTab(self)
        self.advanced_tab = AdvancedSettingsTab(self)
        
        # Add tabs to notebook
        notebook.append_page(self.general_tab.get_box(), Gtk.Label(label="General"))
        notebook.append_page(self.schedule_tab.get_box(), Gtk.Label(label="Schedule"))
        notebook.append_page(self.maintenance_tab.get_box(), Gtk.Label(label="System Maintenance"))
        notebook.append_page(self.advanced_tab.get_box(), Gtk.Label(label="Advanced"))
        
        # Connect to response signal
        self.connect("response", self.on_response)
        
        self.show()
    
    def is_destroyed(self):
        """Check if the dialog has been destroyed"""
        return not self._dialog_alive
    
    def on_response(self, dialog, response):
        """Handle dialog response"""
        if response == Gtk.ResponseType.OK:
            # Validate and apply settings from all tabs
            if not self._validate_settings():
                return  # Don't close if validation fails
            
            # Apply settings from all tabs
            self.config = self.general_tab.apply_settings(self.config)
            self.config = self.schedule_tab.apply_settings(self.config)
            self.config = self.maintenance_tab.apply_settings(self.config)
            # Advanced tab handles its own settings
            
            # Check if dark mode changed
            dark_mode_changed = self.zfs_assistant.config.get("dark_mode", False) != self.config.get("dark_mode", False)
            
            # Save config
            self.zfs_assistant.config = self.config
            self.zfs_assistant.save_config()
            
            # Setup system integration in a background thread to avoid UI freezing
            def setup_system_integration():
                """Run system integration setup in background thread"""
                # Import GLib at the beginning of the function
                from gi.repository import GLib
                
                try:
                    # Setup pacman hook
                    pacman_success, pacman_message = self.zfs_assistant.setup_pacman_hook(self.config["pacman_integration"])
                    if not pacman_success:
                        # Use GLib.idle_add to safely update UI from background thread
                        def show_pacman_error():
                            if not self.is_destroyed():
                                error_dialog = Gtk.MessageDialog(
                                    transient_for=self.parent,
                                    modal=True,
                                    message_type=Gtk.MessageType.ERROR,
                                    buttons=Gtk.ButtonsType.OK,
                                    text="Pacman Hook Error",
                                    secondary_text=pacman_message
                                )
                                error_dialog.connect("response", lambda d, r: d.destroy())
                                error_dialog.present()
                        GLib.idle_add(show_pacman_error)
                        
                    # Setup systemd timers
                    schedules = {
                        "daily": self.config.get("daily_schedule", []),
                        "weekly": self.config.get("weekly_schedule", False),
                        "monthly": self.config.get("monthly_schedule", False)
                    }
                    
                    # Additional validation for schedule configuration before timer setup
                    schedule_validation_errors = []
                    
                    if schedules["daily"]:
                        if not schedules["daily"]:
                            schedule_validation_errors.append("Daily snapshots enabled but no days selected.")
                    
                    if schedule_validation_errors:
                        def show_schedule_validation_error():
                            if not self.is_destroyed():
                                error_dialog = Gtk.MessageDialog(
                                    transient_for=self.parent,
                                    modal=True,
                                    message_type=Gtk.MessageType.ERROR,
                                    buttons=Gtk.ButtonsType.OK,
                                    text="Schedule Configuration Error",
                                    secondary_text="\n".join(schedule_validation_errors)
                                )
                                error_dialog.connect("response", lambda d, r: d.destroy())
                                error_dialog.present()
                        GLib.idle_add(show_schedule_validation_error)
                        return  # Stop processing, don't save config or setup timers
                    
                    # Save the weekly and monthly state in config
                    self.config["weekly_schedule"] = schedules["weekly"]
                    self.config["monthly_schedule"] = schedules["monthly"]
                    
                    timer_success, timer_message = self.zfs_assistant.setup_systemd_timers(schedules)
                    if not timer_success:
                        def show_timer_error():
                            if not self.is_destroyed():
                                error_dialog = Gtk.MessageDialog(
                                    transient_for=self.parent,
                                    modal=True,
                                    message_type=Gtk.MessageType.WARNING,
                                    buttons=Gtk.ButtonsType.OK,
                                    text="Timer Setup Warning",
                                    secondary_text=f"Timer setup completed with warnings:\n{timer_message}"
                                )
                                error_dialog.connect("response", lambda d, r: d.destroy())
                                error_dialog.present()
                        GLib.idle_add(show_timer_error)
                    
                    # Clean up old timer files if needed
                    try:
                        cleanup_success, cleanup_message = self.zfs_assistant.system_integration.cleanup_timer_files()
                        if not cleanup_success:
                            # Log warning but don't show error dialog for cleanup failures
                            def show_cleanup_warning():
                                print(f"Warning: Timer cleanup issues: {cleanup_message}")
                            GLib.idle_add(show_cleanup_warning)
                    except Exception as e:
                        # Handle cleanup errors gracefully
                        error_message = str(e)  # Capture error message in a variable
                        def show_cleanup_error():
                            print(f"Warning: Timer cleanup failed: {error_message}")
                        GLib.idle_add(show_cleanup_error)
                        
                except Exception as e:
                    # Handle any unexpected errors in background thread
                    error_message = str(e)  # Capture error message in a variable
                    def show_general_error():
                        if not self.is_destroyed():
                            error_dialog = Gtk.MessageDialog(
                                transient_for=self.parent,
                                modal=True,
                                message_type=Gtk.MessageType.ERROR,
                                buttons=Gtk.ButtonsType.OK,
                                text="Configuration Error",
                                secondary_text=f"An error occurred while applying settings:\n{error_message}"
                            )
                            error_dialog.connect("response", lambda d, r: d.destroy())
                            error_dialog.present()
                    GLib.idle_add(show_general_error)
            
            # Run system integration in background thread
            thread = threading.Thread(target=setup_system_integration, daemon=True)
            thread.start()
            
            # Update theme if dark mode changed
            if dark_mode_changed:
                self.parent.app.toggle_dark_mode(self.config.get("dark_mode", False))
                
            # Update notifications setting
            self.parent.app.toggle_notifications(self.config.get("notifications_enabled", True))
            
            # Close the dialog without showing a message
            self.destroy()
            return
        
        self.destroy()
    
    def _validate_settings(self):
        """Validate settings before applying them"""
        # Only validate schedules if auto-snapshot is enabled
        if self.schedule_tab.schedule_switch.get_active():
            # First check if any schedule type is selected at all
            daily_enabled = self.schedule_tab.daily_check.get_active()
            weekly_enabled = self.schedule_tab.weekly_check.get_active()
            monthly_enabled = self.schedule_tab.monthly_check.get_active()
            
            if not (daily_enabled or weekly_enabled or monthly_enabled):
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="No Schedule Type Selected",
                    secondary_text="Scheduled snapshots are enabled, but no schedule type is selected. Please choose at least one schedule type (daily, weekly, or monthly) or disable scheduled snapshots."
                )
                error_dialog.connect("response", lambda d, r: d.destroy())
                error_dialog.present()
                return False
                
            # Validate schedules - ensure at least one day is selected if the schedule is enabled
            
            # Check if any days are selected for daily schedule
            if daily_enabled:
                selected_days = [day for day, check in self.schedule_tab.day_checks.items() if check.get_active()]
                if not selected_days:
                    error_dialog = Gtk.MessageDialog(
                        transient_for=self,
                        modal=True,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Invalid Schedule",
                        secondary_text="Please select at least one day for daily snapshots, or choose a different schedule type."
                    )
                    error_dialog.connect("response", lambda d, r: d.destroy())
                    error_dialog.present()
                    return False
        
        return True
    
    def destroy(self):
        """Override destroy to mark dialog as destroyed"""
        self._dialog_alive = False
        super().destroy()
