#!/usr/bin/env python3
# ZFS Assistant - Schedule Settings Tab
# Author: GitHub Copilot

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

class ScheduleSettingsTab:
    """Schedule settings tab for snapshot scheduling and retention"""
    
    def __init__(self, parent_dialog):
        self.dialog = parent_dialog
        self.zfs_assistant = parent_dialog.zfs_assistant
        self.config = parent_dialog.config
        
        # Initialize collections for controls
        self.day_checks = {}
        
        # Build the schedule settings UI
        self._build_ui()
        
        # Set initial states
        self._set_initial_schedule_state()
    
    def _build_ui(self):
        """Build the schedule settings tab UI"""
        # Create main container
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.box.set_margin_top(10)
        self.box.set_margin_bottom(10)
        self.box.set_margin_start(10)
        self.box.set_margin_end(10)
        
        # Enable scheduled snapshots
        self._create_schedule_enable_section()
        
        # Schedule types configuration (create before naming to avoid AttributeError)
        self._create_schedule_types_section()
        
        # Snapshot naming configuration
        self._create_naming_section()
        
        # Retention policy configuration
        self._create_retention_section()
        
        # Update initial snapshot preview after all UI components are created
        self.update_snapshot_preview()
    
    def _create_schedule_enable_section(self):
        """Create the schedule enable/disable section"""
        self.schedule_switch = Gtk.Switch()
        self.schedule_switch.set_active(self.config.get("auto_snapshot", True))
        self.schedule_switch.connect("state-set", self.on_schedule_switch_toggled)
        schedule_enable_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        schedule_enable_box.append(Gtk.Label(label="Enable Scheduled Snapshots:"))
        schedule_enable_box.append(self.schedule_switch)
        self.box.append(schedule_enable_box)
        
        # Add explanation text
        explanation_label = Gtk.Label(
            label="Choose one schedule type below. Only one schedule type can be active at a time. "
                  "For daily snapshots, you can select multiple days within that type. "
                  "System updates (pacman -Syu) will be executed automatically during scheduled snapshots."
        )
        
        explanation_label.set_wrap(True)
        explanation_label.set_margin_top(5)
        explanation_label.set_margin_bottom(5)
        explanation_label.set_halign(Gtk.Align.START)
        explanation_label.set_margin_start(0)  # Align with frame content
        explanation_label.add_css_class("dim-label")
        self.box.append(explanation_label)
    
    def _create_naming_section(self):
        """Create the snapshot naming configuration section"""
        naming_frame = Gtk.Frame()
        naming_frame.set_label("Snapshot Naming")
        naming_frame.set_margin_top(10)
        naming_frame.set_margin_bottom(10)
        self.box.append(naming_frame)
        
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
            "timestamp-prefix-type"
        ])
        self.format_combo.set_model(format_model)
        
        # Set current format
        current_format = self.config.get("snapshot_name_format", "prefix-type-timestamp")
        format_options = [
            "prefix-type-timestamp", "prefix-timestamp-type", "type-prefix-timestamp", "timestamp-prefix-type"
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
        self.format_combo.connect("notify::selected", self.update_snapshot_preview)
        
        # Note: Initial preview will be updated after all UI components are created
    
    def _create_schedule_types_section(self):
        """Create the schedule types configuration section"""
        schedule_frame = Gtk.Frame()
        schedule_frame.set_label("Snapshot Schedules")
        schedule_frame.set_margin_top(10)
        schedule_frame.set_margin_bottom(10)
        self.box.append(schedule_frame)
        
        schedule_types_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        schedule_types_box.set_margin_top(10)
        schedule_types_box.set_margin_bottom(10)
        schedule_types_box.set_margin_start(10)
        schedule_types_box.set_margin_end(10)
        schedule_frame.set_child(schedule_types_box)
        
        # Daily snapshots
        self._create_daily_section(schedule_types_box)
        
        # Weekly snapshots
        self._create_weekly_section(schedule_types_box)
        
        # Monthly snapshots
        self._create_monthly_section(schedule_types_box)
    
    def _create_daily_section(self, parent):
        """Create daily snapshots configuration"""
        daily_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        daily_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.daily_check = Gtk.CheckButton(label="Daily Snapshots")
        self.daily_check.connect("toggled", self.on_schedule_type_toggled)
        daily_header.append(self.daily_check)
        
        # Time selection for daily snapshots
        daily_header.append(Gtk.Label(label="at time:"))
        self.daily_hour_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.daily_hour_spin.set_value(self.config.get("daily_hour", 0))
        self.daily_hour_spin.connect("value-changed", self.update_snapshot_preview)  # Connect to preview update
        daily_header.append(self.daily_hour_spin)
        daily_header.append(Gtk.Label(label=":"))
        self.daily_minute_spin = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.daily_minute_spin.set_value(self.config.get("daily_minute", 0))
        self.daily_minute_spin.connect("value-changed", self.update_snapshot_preview)
        daily_header.append(self.daily_minute_spin)
        
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
        self.daily_grid.set_row_spacing(3)  # Reduced row spacing for more compact layout
        self.daily_grid.set_column_spacing(8)  # Slightly reduced column spacing
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
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_schedule = self.config.get("daily_schedule", list(range(7)))
        
        for day_idx, day_name in enumerate(days):
            row = 0  # All days in one row (more horizontal)
            col = day_idx
            check = Gtk.CheckButton(label=day_name)
            check.set_active(day_idx in daily_schedule)
            check.connect("toggled", self.update_snapshot_preview)  # Connect to preview update
            self.day_checks[day_idx] = check
            self.daily_grid.attach(check, col, row, 1, 1)
        
        daily_section.append(self.daily_grid)
        parent.append(daily_section)
        
        # Add a separator
        parent.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
    
    def _create_weekly_section(self, parent):
        """Create weekly snapshots configuration"""
        weekly_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        weekly_label = Gtk.Label(label="Weekly Snapshots (every Monday at midnight)")
        weekly_label.set_halign(Gtk.Align.START)
        weekly_label.set_margin_start(0)  # Align with frame content
        
        self.weekly_check = Gtk.CheckButton()
        self.weekly_check.set_child(weekly_label)
        self.weekly_check.connect("toggled", self.on_schedule_type_toggled)
        weekly_section.append(self.weekly_check)
        parent.append(weekly_section)
        
        # Add a separator
        parent.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
    
    def _create_monthly_section(self, parent):
        """Create monthly snapshots configuration"""
        monthly_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        monthly_label = Gtk.Label(label="Monthly Snapshots (on the 1st of each month at midnight)")
        monthly_label.set_halign(Gtk.Align.START)
        monthly_label.set_margin_start(0)  # Align with frame content
        
        self.monthly_check = Gtk.CheckButton()
        self.monthly_check.set_child(monthly_label)
        self.monthly_check.connect("toggled", self.on_schedule_type_toggled)
        monthly_section.append(self.monthly_check)
        parent.append(monthly_section)
    
    def _create_retention_section(self):
        """Create retention policy configuration"""
        retention_frame = Gtk.Frame()
        retention_frame.set_label("Retention Policy")
        retention_frame.set_margin_top(10)
        retention_frame.set_margin_bottom(10)
        self.box.append(retention_frame)
        
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
        
        # Create a horizontal grid layout for retention settings (more compact)
        retention_grid = Gtk.Grid()
        retention_grid.set_column_spacing(20)  # Space between columns
        retention_grid.set_row_spacing(8)      # Space between rows
        retention_grid.set_column_homogeneous(True)  # Make columns equal width
        retention_box.append(retention_grid)
        
        # Daily retention (row 0, col 0)
        daily_label = Gtk.Label(label="Daily:")
        daily_label.set_halign(Gtk.Align.START)
        retention_grid.attach(daily_label, 0, 0, 1, 1)
        self.daily_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.daily_spin.set_value(self.config.get("snapshot_retention", {}).get("daily", 7))
        retention_grid.attach(self.daily_spin, 1, 0, 1, 1)
        
        # Weekly retention (row 0, col 2)
        weekly_label = Gtk.Label(label="Weekly:")
        weekly_label.set_halign(Gtk.Align.START)
        retention_grid.attach(weekly_label, 2, 0, 1, 1)
        self.weekly_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.weekly_spin.set_value(self.config.get("snapshot_retention", {}).get("weekly", 4))
        retention_grid.attach(self.weekly_spin, 3, 0, 1, 1)
        
        # Monthly retention (row 1, col 0)
        monthly_label = Gtk.Label(label="Monthly:")
        monthly_label.set_halign(Gtk.Align.START)
        retention_grid.attach(monthly_label, 0, 1, 1, 1)
        self.monthly_spin = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.monthly_spin.set_value(self.config.get("snapshot_retention", {}).get("monthly", 12))
        retention_grid.attach(self.monthly_spin, 1, 1, 1, 1)
    
    def _set_initial_schedule_state(self):
        """Set initial state of schedule sections"""
        # Set initial state of schedule sections - only one can be active
        daily_has_days = bool(self.config.get("daily_schedule", []))
        weekly_enabled = self.config.get("weekly_schedule", False)
        monthly_enabled = self.config.get("monthly_schedule", False)
        
        # Determine which schedule type should be active (priority: daily > weekly > monthly)
        if daily_has_days:
            self.daily_check.set_active(True)
            self.weekly_check.set_active(False)
            self.monthly_check.set_active(False)
        elif weekly_enabled:
            self.daily_check.set_active(False)
            self.weekly_check.set_active(True)
            self.monthly_check.set_active(False)
        elif monthly_enabled:
            self.daily_check.set_active(False)
            self.weekly_check.set_active(False)
            self.monthly_check.set_active(True)
        else:
            # No schedule active
            self.daily_check.set_active(False)
            self.weekly_check.set_active(False)
            self.monthly_check.set_active(False)
        
        # Initialize sensitivity based on active schedule type
        if self.daily_check.get_active():
            self.on_schedule_type_toggled(self.daily_check)
        elif self.weekly_check.get_active():
            self.on_schedule_type_toggled(self.weekly_check)
        elif self.monthly_check.get_active():
            self.on_schedule_type_toggled(self.monthly_check)
        else:
            # No schedule active, disable all controls
            for day, check in self.day_checks.items():
                check.set_sensitive(False)
            self.daily_hour_spin.set_sensitive(False)
            self.daily_minute_spin.set_sensitive(False)
            self.daily_select_all_button.set_sensitive(False)
            self.daily_select_none_button.set_sensitive(False)
        
        # Initialize sensitivity based on auto-snapshot setting
        auto_snapshot_enabled = self.config.get("auto_snapshot", True)
        if not auto_snapshot_enabled:
            self.daily_check.set_sensitive(False)
            self.weekly_check.set_sensitive(False)
            self.monthly_check.set_sensitive(False)
            
            # Disable selection buttons when auto-snapshot is disabled
            self.daily_select_all_button.set_sensitive(False)
            self.daily_select_none_button.set_sensitive(False)
                
            # Disable all day checkboxes and time selector
            for check in self.day_checks.values():
                check.set_sensitive(False)
            self.daily_hour_spin.set_sensitive(False)
            self.daily_minute_spin.set_sensitive(False)
            
            # Disable snapshot naming fields
            self.prefix_entry.set_sensitive(False)
            self.format_combo.set_sensitive(False)
    
    def get_box(self):
        """Get the main container widget"""
        return self.box
    
    def update_snapshot_preview(self, widget=None):
        """Update the snapshot preview based on current settings"""
        import datetime
        
        # Safety check: ensure all required widgets exist
        if not hasattr(self, 'preview_container') or not hasattr(self, 'daily_check'):
            return
        
        # Clear existing previews
        child = self.preview_container.get_first_child()
        while child:
            self.preview_container.remove(child)
            child = self.preview_container.get_first_child()
        
        prefix = self.prefix_entry.get_text().strip() or "zfs-assistant"
        selected = self.format_combo.get_selected()
        format_options = [
            "prefix-type-timestamp", "prefix-timestamp-type", "type-prefix-timestamp", "timestamp-prefix-type"
        ]
        format_type = format_options[selected] if selected < len(format_options) else "prefix-type-timestamp"
        
        # Example timestamp
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d-%H%M%S")
        
        # Generate examples for different snapshot types
        examples = []
        
        if self.daily_check.get_active():
            examples.append(("Daily", "daily"))
        if self.weekly_check.get_active():
            examples.append(("Weekly", "weekly"))
        if self.monthly_check.get_active():
            examples.append(("Monthly", "monthly"))
        
        if not examples:
            examples = [("Example", "manual")]
        
        for type_name, type_key in examples:
            if format_type == "prefix-type-timestamp":
                snapshot_name = f"{prefix}-{type_key}-{timestamp}"
            elif format_type == "prefix-timestamp-type":
                snapshot_name = f"{prefix}-{timestamp}-{type_key}"
            elif format_type == "type-prefix-timestamp":
                snapshot_name = f"{type_key}-{prefix}-{timestamp}"
            elif format_type == "timestamp-prefix-type":
                snapshot_name = f"{timestamp}-{prefix}-{type_key}"
            else:
                snapshot_name = f"{prefix}-{type_key}-{timestamp}"
            
            preview_label = Gtk.Label(label=f"{type_name}: {snapshot_name}")
            preview_label.set_halign(Gtk.Align.START)
            preview_label.add_css_class("dim-label")
            self.preview_container.append(preview_label)
    
    def on_schedule_switch_toggled(self, widget, state):
        """Enable or disable all schedule widgets based on auto-snapshot toggle"""
        # Update sensitivity of all schedule-related widgets
        self.daily_check.set_sensitive(state)
        self.weekly_check.set_sensitive(state)
        self.monthly_check.set_sensitive(state)
        
        # Update sensitivity of daily buttons
        self.daily_select_all_button.set_sensitive(state)
        self.daily_select_none_button.set_sensitive(state)
            
        # Update sensitivity of daily grid and time selector
        for check in self.day_checks.values():
            check.set_sensitive(state and self.daily_check.get_active())
        self.daily_hour_spin.set_sensitive(state and self.daily_check.get_active())
        self.daily_minute_spin.set_sensitive(state and self.daily_check.get_active())
        
        # Update sensitivity of snapshot naming fields
        self.prefix_entry.set_sensitive(state)
        self.format_combo.set_sensitive(state)
        
        return False  # Allow the state change to proceed
    
    def on_schedule_type_toggled(self, button):
        """Handle schedule type checkbox toggle - make them mutually exclusive (radio button behavior)"""
        if not button.get_active():
            return  # Don't process deactivation
        
        # Deactivate all other schedule types
        if button == self.daily_check:
            self.weekly_check.set_active(False)
            self.monthly_check.set_active(False)
        elif button == self.weekly_check:
            self.daily_check.set_active(False)
            self.monthly_check.set_active(False)
        elif button == self.monthly_check:
            self.daily_check.set_active(False)
            self.weekly_check.set_active(False)
        
        # Update sensitivity based on which type is now active
        schedule_enabled = self.schedule_switch.get_active()
        
        # Daily controls
        for check in self.day_checks.values():
            check.set_sensitive(schedule_enabled and self.daily_check.get_active())
        self.daily_hour_spin.set_sensitive(schedule_enabled and self.daily_check.get_active())
        self.daily_minute_spin.set_sensitive(schedule_enabled and self.daily_check.get_active())
        self.daily_select_all_button.set_sensitive(schedule_enabled and self.daily_check.get_active())
        self.daily_select_none_button.set_sensitive(schedule_enabled and self.daily_check.get_active())
        
        # Update preview
        self.update_snapshot_preview()
    
    def on_daily_select_all_clicked(self, button):
        """Select all days"""
        for check in self.day_checks.values():
            check.set_active(True)
    
    def on_daily_select_none_clicked(self, button):
        """Deselect all days"""
        for check in self.day_checks.values():
            check.set_active(False)
    
    def apply_settings(self, config):
        """Apply settings from this tab to the config"""
        # Update prefix
        config["prefix"] = self.prefix_entry.get_text().strip()
        
        # Update snapshot name format
        selected = self.format_combo.get_selected()
        format_options = [
            "prefix-type-timestamp", "prefix-timestamp-type", "type-prefix-timestamp", "timestamp-prefix-type"
        ]
        if selected < len(format_options):
            config["snapshot_name_format"] = format_options[selected]
        else:
            config["snapshot_name_format"] = "prefix-type-timestamp"
        
        # Update auto snapshot settings
        config["auto_snapshot"] = self.schedule_switch.get_active()
        
        # Update schedule settings (only one type can be active)
        # Clear all schedule types first
        config["daily_schedule"] = []
        config["weekly_schedule"] = False
        config["monthly_schedule"] = False
        
        # Set the active schedule type
        if self.daily_check.get_active():
            daily_schedule = []
            for day, check in self.day_checks.items():
                if check.get_active():
                    daily_schedule.append(day)
            config["daily_schedule"] = daily_schedule
            config["daily_hour"] = int(self.daily_hour_spin.get_value())
            config["daily_minute"] = int(self.daily_minute_spin.get_value())
        elif self.weekly_check.get_active():
            config["weekly_schedule"] = True
        elif self.monthly_check.get_active():
            config["monthly_schedule"] = True
        
        # Update retention policy
        config["snapshot_retention"] = {
            "daily": int(self.daily_spin.get_value()),
            "weekly": int(self.weekly_spin.get_value()),
            "monthly": int(self.monthly_spin.get_value())
        }
        
        return config
