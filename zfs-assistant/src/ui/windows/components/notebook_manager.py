#!/usr/bin/env python3
# ZFS Assistant - Notebook Manager
# Author: GitHub Copilot

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Pango, GLib, GLib

class NotebookManager:
    """Manages the notebook (tabs) in the main window"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def create_notebook(self, main_box):
        """Create the main notebook with all tabs"""
        # Create notebook for tabs with more compact styling and responsive behavior
        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        notebook.set_hexpand(True)
        notebook.set_margin_start(16)    # Reduced from 20 to 16
        notebook.set_margin_end(16)      # Reduced from 20 to 16
        notebook.set_margin_bottom(16)   # Reduced from 20 to 16
        notebook.add_css_class("main-notebook")
        notebook.add_css_class("main-content")  # Add responsive class
        main_box.append(notebook)
        
        # Create all tabs
        self._create_snapshots_tab(notebook)
        self._create_properties_tab(notebook)
        self._create_arc_tab(notebook)
        self._create_log_tab(notebook)
        
        return notebook
    
    def _create_snapshots_tab(self, notebook):
        """Create the snapshots tab"""
        # Snapshots tab with modern layout
        snapshots_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Content area with reduced padding for more compact UI
        snapshots_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)  # Reduced from 16 to 12
        snapshots_content.set_margin_top(16)    # Reduced from 20 to 16
        snapshots_content.set_margin_bottom(16)  # Reduced from 20 to 16
        snapshots_content.set_margin_start(16)   # Reduced from 20 to 16
        snapshots_content.set_margin_end(16)     # Reduced from 20 to 16
        snapshots_content.set_vexpand(True)  # Allow vertical expansion
        snapshots_page.append(snapshots_content)
        
        # Search area with more compact styling (SearchEntry has built-in icon)
        search_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)  # Reduced from 12 to 10
        search_container.add_css_class("search-container")
        
        self.main_window.search_entry = Gtk.SearchEntry()
        self.main_window.search_entry.set_placeholder_text("Search snapshots by name or dataset...")
        self.main_window.search_entry.set_hexpand(True)
        self.main_window.search_entry.set_size_request(-1, 36)  # Reduced height from 40 to 36
        self.main_window.search_entry.add_css_class("large-search")
        self.main_window.search_entry.connect("search-changed", self.main_window.on_search_changed)
        search_container.append(self.main_window.search_entry)
        
        snapshots_content.append(search_container)
        
        # Main content area with card styling
        content_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_card.add_css_class("content-card")
        content_card.set_vexpand(True)
        
        # Create scrolled window for snapshots
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_card.append(scrolled_window)
        
        # Create snapshots list with modern styling
        self.main_window.snapshots_list = Gtk.ListBox()
        self.main_window.snapshots_list.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.main_window.snapshots_list.connect("row-selected", self.main_window.on_snapshot_selected)
        self.main_window.snapshots_list.add_css_class("snapshots-list")
        
        scrolled_window.set_child(self.main_window.snapshots_list)
        
        snapshots_content.append(content_card)

        # Action bar at bottom with more compact spacing
        action_bar = self._create_action_bar()
        snapshots_content.append(action_bar)
        
        # Create tab label with icon
        snapshots_tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        snapshots_tab_icon = Gtk.Image.new_from_icon_name("camera-photo-symbolic")
        snapshots_tab_label = Gtk.Label(label="Snapshots")
        snapshots_tab_box.append(snapshots_tab_icon)
        snapshots_tab_box.append(snapshots_tab_label)
        
        notebook.append_page(snapshots_page, snapshots_tab_box)
    
    def _create_action_bar(self):
        """Create the action bar for snapshot operations"""
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)  # Reduced from 12 to 10
        action_bar.set_margin_top(12)    # Reduced from 16 to 12
        action_bar.set_halign(Gtk.Align.END)
        action_bar.add_css_class("action-bar")
        
        # Action buttons with text and icons for better UX
        self.main_window.rollback_button = Gtk.Button()
        rollback_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rollback_icon = Gtk.Image.new_from_icon_name("edit-undo-symbolic")
        rollback_label = Gtk.Label(label="Rollback")
        rollback_box.append(rollback_icon)
        rollback_box.append(rollback_label)
        self.main_window.rollback_button.set_child(rollback_box)
        self.main_window.rollback_button.set_tooltip_text("Rollback to Selected Snapshot")
        self.main_window.rollback_button.connect("clicked", self.main_window.on_rollback_clicked)
        self.main_window.rollback_button.set_sensitive(False)
        self.main_window.rollback_button.add_css_class("action-button")
        self.main_window.rollback_button.set_size_request(100, 36)  # Reduced height from 40 to 36
        action_bar.append(self.main_window.rollback_button)
        
        self.main_window.clone_button = Gtk.Button()
        clone_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        clone_icon = Gtk.Image.new_from_icon_name("edit-copy-symbolic")
        clone_label = Gtk.Label(label="Clone")
        clone_box.append(clone_icon)
        clone_box.append(clone_label)
        self.main_window.clone_button.set_child(clone_box)
        self.main_window.clone_button.set_tooltip_text("Clone Selected Snapshot")
        self.main_window.clone_button.connect("clicked", self.main_window.on_clone_clicked)
        self.main_window.clone_button.set_sensitive(False)
        self.main_window.clone_button.add_css_class("action-button")
        self.main_window.clone_button.set_size_request(100, 36)  # Reduced height from 40 to 36
        action_bar.append(self.main_window.clone_button)
        
        self.main_window.delete_button = Gtk.Button()
        self.main_window.delete_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.main_window.delete_box.set_halign(Gtk.Align.CENTER)
        self.main_window.delete_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
        self.main_window.delete_label = Gtk.Label(label="Delete")
        self.main_window.delete_label.set_ellipsize(Pango.EllipsizeMode.NONE)
        self.main_window.delete_box.append(self.main_window.delete_icon)
        self.main_window.delete_box.append(self.main_window.delete_label)
        self.main_window.delete_button.set_child(self.main_window.delete_box)
        self.main_window.delete_button.set_tooltip_text("Delete Selected Snapshot(s)")
        self.main_window.delete_button.connect("clicked", self.main_window.on_unified_delete_clicked)
        self.main_window.delete_button.set_sensitive(False)
        self.main_window.delete_button.add_css_class("action-button")
        self.main_window.delete_button.add_css_class("destructive-action")
        self.main_window.delete_button.set_size_request(120, 36)
        action_bar.append(self.main_window.delete_button)
        
        # Add clear selection button
        self.main_window.clear_selection_button = Gtk.Button()
        clear_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        clear_box.set_halign(Gtk.Align.CENTER)
        clear_icon = Gtk.Image.new_from_icon_name("edit-clear-symbolic")
        clear_label = Gtk.Label(label="Clear")
        clear_box.append(clear_icon)
        clear_box.append(clear_label)
        self.main_window.clear_selection_button.set_child(clear_box)
        self.main_window.clear_selection_button.set_tooltip_text("Clear Selection")
        self.main_window.clear_selection_button.connect("clicked", self._on_clear_selection_clicked)
        self.main_window.clear_selection_button.set_sensitive(False)
        self.main_window.clear_selection_button.add_css_class("action-button")
        self.main_window.clear_selection_button.set_size_request(80, 36)
        self.main_window.clear_selection_button.set_visible(False)
        action_bar.append(self.main_window.clear_selection_button)

        return action_bar
    
    def _create_properties_tab(self, notebook):
        """Create the dataset properties tab"""
        # Dataset Properties tab with more compact styling
        properties_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        properties_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)  # Reduced from 16 to 12
        properties_content.set_margin_top(16)    # Reduced from 20 to 16
        properties_content.set_margin_bottom(16)  # Reduced from 20 to 16
        properties_content.set_margin_start(16)   # Reduced from 20 to 16
        properties_content.set_margin_end(16)     # Reduced from 20 to 16
        properties_page.append(properties_content)
        
        # Create scrolled window for properties with modern styling
        props_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        props_card.add_css_class("content-card")
        props_card.set_vexpand(True)
        
        props_scrolled_window = Gtk.ScrolledWindow()
        props_scrolled_window.set_vexpand(True)
        props_scrolled_window.set_hexpand(True)
        props_scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        props_card.append(props_scrolled_window)
        
        # Create grid for dataset properties with more compact spacing
        self.main_window.properties_grid = Gtk.Grid()
        self.main_window.properties_grid.set_column_spacing(20)  # Reduced from 24 to 20
        self.main_window.properties_grid.set_row_spacing(10)     # Reduced from 12 to 10
        self.main_window.properties_grid.set_margin_top(16)      # Reduced from 20 to 16
        self.main_window.properties_grid.set_margin_bottom(16)   # Reduced from 20 to 16
        self.main_window.properties_grid.set_margin_start(16)    # Reduced from 20 to 16
        self.main_window.properties_grid.set_margin_end(16)      # Reduced from 20 to 16
        self.main_window.properties_grid.add_css_class("properties-grid")
        props_scrolled_window.set_child(self.main_window.properties_grid)
        
        properties_content.append(props_card)
        
        # Create dataset properties tab label with icon
        properties_tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        properties_tab_icon = Gtk.Image.new_from_icon_name("document-properties-symbolic")
        properties_tab_label = Gtk.Label(label="Dataset Properties")
        properties_tab_box.append(properties_tab_icon)
        properties_tab_box.append(properties_tab_label)
        
        notebook.append_page(properties_page, properties_tab_box)
    
    def _create_arc_tab(self, notebook):
        """Create the ARC properties tab"""
        # ARC Properties tab with inline editing capabilities
        arc_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        arc_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        arc_content.set_margin_top(16)
        arc_content.set_margin_bottom(16)
        arc_content.set_margin_start(16)
        arc_content.set_margin_end(16)
        arc_page.append(arc_content)
        
        # Create ARC properties card
        arc_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        arc_card.add_css_class("content-card")
        arc_card.set_vexpand(True)
        
        # Scrolled window for ARC properties
        arc_scrolled_window = Gtk.ScrolledWindow()
        arc_scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        arc_scrolled_window.set_vexpand(True)
        arc_scrolled_window.set_min_content_height(200)
        arc_card.append(arc_scrolled_window)
        
        # Grid for ARC properties with inline editing
        self.main_window.arc_grid = Gtk.Grid()
        self.main_window.arc_grid.set_column_spacing(12)
        self.main_window.arc_grid.set_row_spacing(8)
        self.main_window.arc_grid.set_margin_top(16)
        self.main_window.arc_grid.set_margin_bottom(16)
        self.main_window.arc_grid.set_margin_start(16)
        self.main_window.arc_grid.set_margin_end(16)
        self.main_window.arc_grid.add_css_class("arc-properties-grid")
        arc_scrolled_window.set_child(self.main_window.arc_grid)
        
        arc_content.append(arc_card)
        
        # Create ARC properties tab label with icon
        arc_tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        arc_tab_icon = Gtk.Image.new_from_icon_name("applications-system-symbolic")
        arc_tab_label = Gtk.Label(label="ARC Properties")
        arc_tab_box.append(arc_tab_icon)
        arc_tab_box.append(arc_tab_label)
        
        notebook.append_page(arc_page, arc_tab_box)
    
    def _create_log_tab(self, notebook):
        """Create the log tab"""
        # Log tab for displaying log file contents
        log_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        log_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        log_content.set_margin_top(16)
        log_content.set_margin_bottom(16)
        log_content.set_margin_start(16)
        log_content.set_margin_end(16)
        log_page.append(log_content)

        # Header with clear logs button
        log_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        log_header.set_margin_bottom(10)
        
        # Title label
        log_title = Gtk.Label()
        log_title.set_markup("<b>Application Logs</b>")
        log_title.set_halign(Gtk.Align.START)
        log_title.set_hexpand(True)
        log_header.append(log_title)
        
        # Clear logs button
        clear_logs_button = Gtk.Button()
        clear_logs_button.set_icon_name("edit-clear-all-symbolic")
        clear_logs_button.set_tooltip_text("Clear all logs")
        clear_logs_button.add_css_class("flat")
        clear_logs_button.add_css_class("destructive-action")
        clear_logs_button.connect("clicked", self._on_clear_logs_clicked)
        log_header.append(clear_logs_button)
        
        log_content.append(log_header)
        
        # Create log content card
        log_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        log_card.add_css_class("content-card")
        log_card.set_vexpand(True)
        
        # Scrolled window for log content
        log_scrolled_window = Gtk.ScrolledWindow()
        log_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        log_scrolled_window.set_vexpand(True)
        log_scrolled_window.set_min_content_height(200)
        log_card.append(log_scrolled_window)
        
        # Create grid for log content like other tabs
        self.main_window.log_grid = Gtk.Grid()
        self.main_window.log_grid.set_column_spacing(20)
        self.main_window.log_grid.set_row_spacing(10)
        self.main_window.log_grid.set_margin_top(16)
        self.main_window.log_grid.set_margin_bottom(16)
        self.main_window.log_grid.set_margin_start(16)
        self.main_window.log_grid.set_margin_end(16)
        self.main_window.log_grid.add_css_class("log-grid")
        
        # Create TextView for log content
        self.main_window.log_text_view = Gtk.TextView()
        self.main_window.log_text_view.set_editable(False)
        self.main_window.log_text_view.set_cursor_visible(False)
        self.main_window.log_text_view.set_monospace(True)
        self.main_window.log_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.main_window.log_text_view.add_css_class("log-content")
        
        # Add TextView to scrolled window instead of grid
        log_scrolled_window.set_child(self.main_window.log_text_view)
        
        log_content.append(log_card)
        
        # Create log tab label with icon
        log_tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        log_tab_icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic")
        log_tab_label = Gtk.Label(label="Log")
        log_tab_box.append(log_tab_icon)
        log_tab_box.append(log_tab_label)
        
        notebook.append_page(log_page, log_tab_box)

    def _on_clear_logs_clicked(self, button):
        """Handle clear logs button click"""
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Clear all logs?",
            secondary_text="This will permanently delete all log entries from both the display and the log file. This action cannot be undone."
        )
        
        dialog.connect("response", self._on_clear_logs_response)
        dialog.present()
    
    def _on_clear_logs_response(self, dialog, response):
        """Handle clear logs confirmation dialog response"""
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self._clear_all_logs()
    
    def _clear_all_logs(self):
        """Clear both the log display and the log files"""
        try:
            # Clear the text view
            if hasattr(self.main_window, 'log_text_view'):
                buffer = self.main_window.log_text_view.get_buffer()
                buffer.set_text("")
            
            # Clear the log files
            self._clear_log_files()
            
            # Show success message
            self.main_window.set_status("Logs cleared successfully", "dialog-information-symbolic")
            
        except Exception as e:
            # Show error message
            self.main_window.set_status(f"Failed to clear logs: {str(e)}", "dialog-error-symbolic")
    
    def _clear_log_files(self):
        """Clear the actual log files"""
        try:
            # Import the logger utilities
            from utils.logger import get_logger
            from utils.common import LOG_FILE
            from pathlib import Path
            
            # Clear the main log file used by the streamlined logger
            log_file = Path(LOG_FILE)
            if log_file.exists():
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("")
            
            # Also try to clear the comprehensive logger files
            try:
                logger = get_logger()
                if hasattr(logger, 'log_file') and logger.log_file.exists():
                    with open(logger.log_file, 'w', encoding='utf-8') as f:
                        f.write("")
            except Exception:
                pass
            
            # Try to clear other potential log files in the log directory
            try:
                import os
                log_dir = Path("~/.config/zfs-assistant/logs").expanduser()
                if log_dir.exists():
                    for log_file_path in log_dir.glob("*.log"):
                        if log_file_path.is_file():
                            with open(log_file_path, 'w', encoding='utf-8') as f:
                                f.write("")
            except Exception:
                pass
                
        except Exception as e:
            raise Exception(f"Failed to clear log files: {str(e)}")

    def _on_clear_selection_clicked(self, button):
        """Handle clear selection button click"""
        self.main_window.snapshots_list.unselect_all()
        self.main_window.on_snapshot_selected(self.main_window.snapshots_list, None)
