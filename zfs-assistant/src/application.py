#!/usr/bin/env python3
# ZFS Assistant - Application class
# Author: GitHub Copilot

import gi
import os
import sys

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

# Add the current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Use absolute imports with proper paths
try:
    # First try relative imports (when running as a package)
    from .zfs_assistant import ZFSAssistant
    from .ui_main_window import MainWindow
    from .common import APP_ID
except ImportError:
    # Fall back to direct imports from current directory
    from zfs_assistant import ZFSAssistant
    from ui_main_window import MainWindow
    from common import APP_ID

class Application(Adw.Application):    
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)
        self.zfs_assistant = ZFSAssistant()
        
        # Setup custom CSS
        self.setup_css()
        
        # Setup theme
        self.setup_theme()
        
        # Set up notifications
        self.notification_enabled = self.zfs_assistant.config.get("notifications_enabled", True)
    
    def setup_css(self):
        """Setup CSS styling - use GTK4 defaults for clean appearance"""
        # Check if we have a CSS file and if it has meaningful content
        css_file_path = os.path.join(os.path.dirname(__file__), 'style.css')
        
        # If CSS file exists and has content (>100 bytes), load it
        if os.path.exists(css_file_path) and os.path.getsize(css_file_path) > 100:
            css_provider = Gtk.CssProvider()
            try:
                css_provider.load_from_path(css_file_path)
                # Apply CSS to default display
                display = Gdk.Display.get_default()
                Gtk.StyleContext.add_provider_for_display(
                    display, 
                    css_provider, 
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            except Exception as e:
                print(f"Failed to load external CSS: {e}")
        
        # If no CSS file or empty file, use minimal essential CSS only
        if not os.path.exists(css_file_path) or os.path.getsize(css_file_path) <= 100:
            css_provider = Gtk.CssProvider()
            minimal_css = """
            /* Essential constraints only - maintain GTK4 theme */
            window {
                min-width: 1000px; 
                min-height: 650px;
            }
            """
            css_provider.load_from_data(minimal_css.encode('utf-8'))
            
            # Apply minimal CSS
            display = Gdk.Display.get_default()
            Gtk.StyleContext.add_provider_for_display(
                display, 
                css_provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def on_activate(self, app):
        # Check if there's already a window
        win = self.get_active_window()
        if not win:
            win = MainWindow(app)
            # Apply dark mode class if dark mode is enabled
            if hasattr(self, 'dark_mode') and self.dark_mode:
                win.add_css_class("dark-mode")
        win.present()

    def run(self):
        """Run the application"""
        print("Running ZFS Assistant application...")
        return super().run(None)
        
    def setup_theme(self):
        """Setup application theme based on config"""
        style_manager = Adw.StyleManager.get_default()
        self.dark_mode = self.zfs_assistant.config.get("dark_mode", False)
        
        # Apply GTK dark mode
        if self.dark_mode:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        
    def toggle_dark_mode(self, enable_dark):
        """Toggle dark mode"""
        style_manager = Adw.StyleManager.get_default()
        self.zfs_assistant.config["dark_mode"] = enable_dark
        self.zfs_assistant.save_config()
        
        # Update dark mode flag
        self.dark_mode = enable_dark
        
        # Apply GTK dark mode
        if enable_dark:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            
        # Apply dark mode to main window if it exists
        win = self.get_active_window()
        if win:
            if enable_dark:
                win.add_css_class("dark-mode")
            else:
                win.remove_css_class("dark-mode")
            
    def send_app_notification(self, title, body=None):
        """Send a system notification"""
        if not self.notification_enabled:
            return
            
        notification = Gio.Notification.new(title)
        if body:
            notification.set_body(body)
        # Use send_notification method from Gio.Application
        super().send_notification(APP_ID, notification)
        
    def toggle_notifications(self, enabled):
        """Toggle notifications"""
        self.notification_enabled = enabled
        self.zfs_assistant.config["notifications_enabled"] = enabled
        self.zfs_assistant.save_config()
