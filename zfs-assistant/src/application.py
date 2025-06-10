#!/usr/bin/env python3
# ZFS Assistant - Application class
# Author: GitHub Copilot

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

from .zfs_assistant import ZFSAssistant
from .ui_main_window import MainWindow
from .common import APP_ID

class Application(Adw.Application):    
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)
        self.zfs_assistant = ZFSAssistant()
        
        # Setup theme
        self.setup_theme()
        
        # Set up notifications
        self.notification_enabled = self.zfs_assistant.config.get("notifications_enabled", True)

    def on_activate(self, app):
        # Check if there's already a window
        win = self.get_active_window()
        if not win:
            win = MainWindow(app)
        win.present()
          def run(self):
        """Run the application"""
        print("Running ZFS Assistant application...")
        return super().run(None)
        
    def setup_theme(self):
        """Setup application theme based on config"""
        style_manager = Adw.StyleManager.get_default()
        if self.zfs_assistant.config.get("dark_mode", False):
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        
    def toggle_dark_mode(self, enable_dark):
        """Toggle dark mode"""
        style_manager = Adw.StyleManager.get_default()
        self.zfs_assistant.config["dark_mode"] = enable_dark
        self.zfs_assistant.save_config()
        
        if enable_dark:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            
    def send_notification(self, title, body=None):
        """Send a system notification"""
        if not self.notification_enabled:
            return
            
        notification = Gio.Notification.new(title)
        if body:
            notification.set_body(body)
        self.send(notification)
        
    def toggle_notifications(self, enabled):
        """Toggle notifications"""
        self.notification_enabled = enabled
        self.zfs_assistant.config["notifications_enabled"] = enabled
        self.zfs_assistant.save_config()
