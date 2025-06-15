#!/usr/bin/env python3
# ZFS Assistant - Status Manager
# Author: GitHub Copilot

import gi
import datetime

gi.require_version('Gtk', '4.0')
from gi.repository import GLib

class StatusManager:
    """Manages status updates, timers, and real-time data updates"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self._next_snapshot_timestamp = None
    
    def force_status_update(self):
        """Force an immediate status update (useful after settings changes)"""
        try:
            print("Forcing immediate status update...")
            # Update visibility first to show/hide elements immediately
            self._update_status_bar_visibility()
            # Update settings status 
            self._update_settings_status()
            # Then update system update status 
            self._update_system_update_status()
            print("Forced status update completed")
        except Exception as e:
            print(f"Error in forced status update: {e}")
            import traceback
            traceback.print_exc()
    
    def force_status_update_with_retry(self, max_retries=3, delay_ms=1000):
        """Force status update with retry mechanism for when systemd changes need time to propagate"""
        def attempt_update(retry_count=0):
            try:
                print(f"Status update attempt {retry_count + 1}/{max_retries}")
                old_schedule_text = ""
                if hasattr(self.main_window, 'schedule_label'):
                    old_schedule_text = self.main_window.schedule_label.get_text()
                
                self.force_status_update()
                
                # Check if the status actually changed or if it's stable
                if hasattr(self.main_window, 'schedule_label'):
                    new_schedule_text = self.main_window.schedule_label.get_text()
                    print(f"Schedule status: '{old_schedule_text}' -> '{new_schedule_text}'")
                    
                    # Check if we have a valid schedule status (not error states)
                    if new_schedule_text in ["Auto: Not Ready", "Auto: Error"] and retry_count < max_retries - 1:
                        print(f"Status not ready, retrying in {delay_ms}ms...")
                        GLib.timeout_add(delay_ms, lambda: attempt_update(retry_count + 1) and False)
                        return False
                
                print("Status update completed successfully")
            except Exception as e:
                print(f"Error in status update attempt {retry_count + 1}: {e}")
                if retry_count < max_retries - 1:
                    print(f"Retrying in {delay_ms}ms...")
                    GLib.timeout_add(delay_ms, lambda: attempt_update(retry_count + 1) and False)
            return False
        
        attempt_update()
    
    def setup_periodic_updates(self):
        """Setup periodic updates for various UI elements"""
        # Update settings status after a longer delay to ensure ZFS Assistant is initialized
        GLib.timeout_add_seconds(1, self._initial_settings_status_update)
        
        # Update settings status periodically (every 5 seconds for system timer checks)
        GLib.timeout_add_seconds(5, self._update_settings_status)
        
        # Update system update status initially and periodically
        GLib.timeout_add_seconds(1, self._update_system_update_status)
        GLib.timeout_add_seconds(5, self._update_system_update_status)
        
        # Update time remaining display very frequently (every second) for real-time countdown
        GLib.timeout_add_seconds(1, self._update_time_remaining)
        
        # Add real-time status update triggers
        self._setup_real_time_updates()
    
    def update_status(self, status_type, message):
        """Log status messages (status bar display has been removed)"""
        # Just log the message since we no longer display it
        log_level = "INFO"
        if status_type == "error":
            log_level = "ERROR"
        elif status_type == "warning":
            log_level = "WARNING"
        elif status_type == "success":
            log_level = "SUCCESS"
        
        print(f"{log_level}: {message}")

    def update_snapshot_count(self):
        """Update the snapshot count in the status bar"""
        try:
            # Count visible snapshots in the list
            count = 0
            child = self.main_window.snapshots_list.get_first_child()
            while child is not None:
                if child.get_visible():
                    count += 1
                child = child.get_next_sibling()
            
            if count == 0:
                self.main_window.snapshot_count_label.set_text("No snapshots")
            elif count == 1:
                self.main_window.snapshot_count_label.set_text("1 snapshot")
            else:
                self.main_window.snapshot_count_label.set_text(f"{count} snapshots")
        except Exception as e:
            print(f"Error updating snapshot count: {e}")
            self.main_window.snapshot_count_label.set_text("? snapshots")

    def _update_settings_status(self):
        """Update settings status in the status bar"""
        try:
            if hasattr(self.main_window, 'zfs_assistant') and self.main_window.zfs_assistant:
                # Get schedule config from ZFS Assistant
                config = self.main_window.zfs_assistant.config
                auto_snapshot = config.get("auto_snapshot", True)
                
                if not auto_snapshot:
                    # If auto_snapshot is disabled, show schedule as off
                    status_text = "Schedule: Off"
                else:
                    # Check if any schedule type is actually active
                    daily_schedule = config.get("daily_schedule", [])
                    weekly_schedule = config.get("weekly_schedule", False)
                    monthly_schedule = config.get("monthly_schedule", False)
                    
                    enabled_schedules = []
                    if daily_schedule:
                        enabled_schedules.append("Daily")
                    if weekly_schedule:
                        enabled_schedules.append("Weekly")
                    if monthly_schedule:
                        enabled_schedules.append("Monthly")
                    
                    if enabled_schedules:
                        status_text = f"Schedule: {', '.join(enabled_schedules)}"
                    else:
                        status_text = "Schedule: Off"
                
                # Update the schedule status label
                if hasattr(self.main_window, 'schedule_label'):
                    self.main_window.schedule_label.set_text(status_text)
                
                # Update visibility after setting the text
                self._update_status_bar_visibility()
                
                # Show next snapshot time only if schedules are enabled
                schedules_enabled = auto_snapshot and (bool(daily_schedule) or weekly_schedule or monthly_schedule)
                
                if schedules_enabled and hasattr(self.main_window, 'next_snapshot_label'):
                    # Set a temporary "calculating" message immediately for responsive UI
                    self.main_window.next_snapshot_label.set_text("Next snapshot in: calculating...")
                    
                    # Calculate next snapshot time using config directly (faster than systemd query)
                    next_time = self._calculate_next_snapshot_from_config(config)
                    
                    if next_time:
                        # Store the parsed datetime object for future updates
                        self._next_snapshot_timestamp = next_time
                        
                        # Format and display
                        time_remaining = self._format_time_remaining(next_time)
                        self.main_window.next_snapshot_label.set_text(f"Next snapshot in: {time_remaining}")
                    else:
                        self._next_snapshot_timestamp = None
                        self.main_window.next_snapshot_label.set_text("")
                else:
                    # If no schedules are active, clear the next snapshot label
                    if hasattr(self.main_window, 'next_snapshot_label'):
                        self.main_window.next_snapshot_label.set_text("")
            else:
                # ZFS Assistant not ready yet, show a neutral status
                if hasattr(self.main_window, 'schedule_label'):
                    self.main_window.schedule_label.set_text("Auto: Not Ready")
                if hasattr(self.main_window, 'next_snapshot_label'):
                    self.main_window.next_snapshot_label.set_text("")
        except Exception as e:
            print(f"Error updating settings status: {e}")
            import traceback
            traceback.print_exc()
            # More informative error message for debugging
            if hasattr(self.main_window, 'schedule_label'):
                self.main_window.schedule_label.set_text("Auto: Error")
            if hasattr(self.main_window, 'next_snapshot_label'):
                self.main_window.next_snapshot_label.set_text("")
        
        # Return True to keep the timeout active
        return True

    def _initial_settings_status_update(self):
        """Initial settings status update (one-time with longer delay)"""
        try:
            # Check if ZFS Assistant is properly initialized
            if not hasattr(self.main_window, 'zfs_assistant') or self.main_window.zfs_assistant is None:
                print("ZFS Assistant not initialized yet")
                if hasattr(self.main_window, 'schedule_label'):
                    self.main_window.schedule_label.set_text("Auto: Initializing...")
                if hasattr(self.main_window, 'next_snapshot_label'):
                    self.main_window.next_snapshot_label.set_text("")
                if hasattr(self.main_window, 'system_update_label'):
                    self.main_window.system_update_label.set_text("")
                return True  # Try again later
                
            # Call the regular update functions
            self._update_settings_status()
            self._update_system_update_status()
            self._update_status_bar_visibility()
        except Exception as e:
            print(f"Error in initial settings status update: {e}")
            if hasattr(self.main_window, 'schedule_label'):
                self.main_window.schedule_label.set_text("Auto: Error")
            if hasattr(self.main_window, 'next_snapshot_label'):
                self.main_window.next_snapshot_label.set_text("")
            if hasattr(self.main_window, 'system_update_label'):
                self.main_window.system_update_label.set_text("")
        return False  # Don't repeat
    
    def _format_time_remaining(self, next_time):
        """Format time remaining until next snapshot"""
        from datetime import datetime
        
        # Calculate time difference
        current_time = datetime.now()
        time_diff = next_time - current_time
        
        # Format based on time remaining
        total_seconds = int(time_diff.total_seconds())
        days = time_diff.days
        hours = total_seconds // 3600 %  24
        minutes = total_seconds // 60 % 60
        seconds = total_seconds % 60
        
        if days > 0:
            if days == 1:
                if hours == 1:
                    return f"{days} day {hours} hour"
                else:
                    return f"{days} day {hours} hours"
            else:
                if hours == 1:
                    return f"{days} days {hours} hour"
                else:
                    return f"{days} days {hours} hours"
        try:
            if hours > 0:
                if hours == 1:
                    if minutes == 1:
                        return f"{hours} hour {minutes} minute"
                    else:
                        return f"{hours} hour {minutes} minutes"
                else:
                    if minutes == 1:
                        return f"{hours} hours {minutes} minute"
                    else:
                        return f"{hours} hours {minutes} minutes"
            elif minutes > 0:
                if minutes == 1:
                    return f"{minutes} minute {seconds} seconds"
                else:
                    return f"{minutes} minutes {seconds} seconds"
            else:
                if seconds == 1:
                    return f"{seconds} second"
                else:
                    return f"{seconds} seconds"
        except Exception as e:
            print(f"Error formatting time remaining: {e}")
            return str(next_time)  # Return original on error

    def _update_time_remaining(self):
        """Update just the time remaining display without querying systemd again.
        This keeps the countdown accurate without excessive system calls."""
        try:
            if hasattr(self, '_next_snapshot_timestamp') and self._next_snapshot_timestamp:
                # Calculate new time remaining
                formatted_time = self._format_time_remaining(self._next_snapshot_timestamp)
                if formatted_time:
                    self.main_window.next_snapshot_label.set_text(f"Next snapshot in: {formatted_time}")
                else:
                    # Time has passed, trigger a full refresh
                    self._update_settings_status()
        except Exception as e:
            print(f"Error updating time remaining: {e}")
        
        # Return True to keep the timeout active
        return True
    
    def _update_system_update_status(self):
        """Update system update status in the status bar"""
        try:
            if hasattr(self.main_window, 'zfs_assistant') and self.main_window.zfs_assistant:
                config = self.main_window.zfs_assistant.config
                update_status = config.get("update_snapshots", "disabled")
                clean_cache = config.get("clean_cache_after_updates", False)
                
                # Always update the text, visibility is controlled separately
                if update_status == "disabled":
                    self.main_window.system_update_label.set_text("System update: Off")
                else:
                    status_text = "System update: "
                    
                    if update_status == "enabled":
                        status_text += "On"
                    elif update_status == "pacman_only":
                        status_text += "Pacman"
                    
                    if clean_cache:
                        status_text += " (Clean)"
                    
                    self.main_window.system_update_label.set_text(status_text)
                
                # Update visibility based on schedule state - no longer call here to avoid conflicts
                # The visibility is now controlled only by _update_status_bar_visibility
        except Exception as e:
            print(f"Error updating system update status: {e}")
            
        # Return True to keep the timeout active
        return True

    def _update_status_bar_visibility(self):
        """Update the visibility of status bar elements based on schedule state"""
        try:
            if not hasattr(self.main_window, 'schedule_label'):
                return
            
            # Check actual schedule status from config instead of label text
            schedules_enabled = False
            if hasattr(self.main_window, 'zfs_assistant') and self.main_window.zfs_assistant:
                config = self.main_window.zfs_assistant.config
                auto_snapshot = config.get("auto_snapshot", True)
                
                if auto_snapshot:
                    # Check if any schedule type is actually active
                    daily_schedule = config.get("daily_schedule", [])
                    weekly_schedule = config.get("weekly_schedule", False)
                    monthly_schedule = config.get("monthly_schedule", False)
                    
                    schedules_enabled = bool(daily_schedule) or weekly_schedule or monthly_schedule
            
            # Update all elements visibility simultaneously for better UX
            elements_to_update = [
                ('schedule_label', True),  # Always visible
                ('system_update_label', schedules_enabled),
                ('next_snapshot_label', schedules_enabled)
            ]
            
            for element_name, should_be_visible in elements_to_update:
                if hasattr(self.main_window, element_name):
                    element = getattr(self.main_window, element_name)
                    element.set_visible(should_be_visible)
                
        except Exception as e:
            print(f"Error updating status bar visibility: {e}")

    def _setup_real_time_updates(self):
        """Setup real-time updates for various UI elements"""
        try:
            # Update snapshot count initially
            GLib.timeout_add_seconds(1, self._initial_snapshot_count_update)
            
            # Setup periodic log refresh (every 30 seconds)
            GLib.timeout_add_seconds(30, self._periodic_log_refresh)
        except Exception as e:
            print(f"Error setting up real-time updates: {e}")

    def _initial_snapshot_count_update(self):
        """Initial snapshot count update (one-time)"""
        try:
            self.update_snapshot_count()
        except Exception as e:
            print(f"Error in initial snapshot count update: {e}")
        return False  # Don't repeat

    def _periodic_log_refresh(self):
        """Periodic log refresh"""
        try:
            # Only refresh if logs tab is visible/active
            if hasattr(self.main_window, 'log_text_view') and self.main_window.log_text_view.get_visible():
                self.main_window.refresh_log_content()
        except Exception as e:
            print(f"Error in periodic log refresh: {e}")
        return True  # Keep repeating
    
    def set_status(self, message, icon=None):
        """Set a temporary status message"""
        # Since we removed the main status bar, just log the message
        print(f"Status: {message}")
    
    def on_properties_refresh_clicked(self, button):
        """Handle properties refresh button click"""
        # Animate the button with a spinning effect
        context = button.get_style_context()
        context.add_class("refreshing")
        
        # Show a brief status message
        self.set_status("Refreshing dataset properties...", "view-refresh-symbolic")
        
        # Add a small delay for visual feedback
        GLib.timeout_add(200, self._refresh_properties_with_status, button)
        
    def _refresh_properties_with_status(self, button=None):
        """Refresh properties with status update"""
        self.main_window.refresh_dataset_properties()
        self.set_status("Dataset properties refreshed", "emblem-ok-symbolic")
        
        # Remove animation class if button provided
        if button:
            context = button.get_style_context()
            context.remove_class("refreshing")
            
        # Reset status after 2 seconds
        GLib.timeout_add(2000, lambda: self.set_status("Ready") and False)
        return False  # Don't repeat

    def _calculate_next_snapshot_from_config(self, config):
        """Calculate next snapshot time directly from configuration (faster than systemd query)"""
        import datetime
        
        now = datetime.datetime.now()
        next_times = []
        
        try:
            daily_schedule = config.get("daily_schedule", [])
            if daily_schedule:
                daily_hour = config.get("daily_hour", 0)
                daily_minute = config.get("daily_minute", 0)
                
                current_weekday = now.weekday()
                
                for day_idx in daily_schedule:
                    days_ahead = day_idx - current_weekday
                    if days_ahead < 0:
                        days_ahead += 7
                    elif days_ahead == 0:
                        target_time = now.replace(hour=daily_hour, minute=daily_minute, second=0, microsecond=0)
                        if now >= target_time:
                            days_ahead = 7
                    
                    target_date = now + datetime.timedelta(days=days_ahead)
                    target_time = target_date.replace(hour=daily_hour, minute=daily_minute, second=0, microsecond=0)
                    next_times.append(target_time)
            
            if config.get("weekly_schedule", False):
                days_until_monday = (7 - now.weekday()) % 7
                if days_until_monday == 0 and now.hour >= 0:
                    days_until_monday = 7
                weekly_time = now + datetime.timedelta(days=days_until_monday)
                weekly_time = weekly_time.replace(hour=0, minute=0, second=0, microsecond=0)
                next_times.append(weekly_time)
            
            if config.get("monthly_schedule", False):
                if now.day == 1 and now.hour < 0:
                    monthly_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    if now.month == 12:
                        next_month = 1
                        next_year = now.year + 1
                    else:
                        next_month = now.month + 1
                        next_year = now.year
                    monthly_time = datetime.datetime(year=next_year, month=next_month, day=1, hour=0, minute=0, second=0)
                next_times.append(monthly_time)
            
            if next_times:
                return min(next_times)
            
        except Exception as e:
            print(f"Error calculating next snapshot time from config: {e}")
        
        return None
