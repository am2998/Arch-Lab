#!/usr/bin/env python3
# ZFS Assistant - Application class
# Author: GitHub Copilot

import gi
import os
import sys

# Check for essential environment variables before GTK initialization
def check_gui_environment():
    """Check if we have the necessary environment for GUI applications"""
    # Check for display
    if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        print("Warning: No display environment found (DISPLAY or WAYLAND_DISPLAY)")
        return False
    
    # Check for XDG runtime directory
    if not os.environ.get('XDG_RUNTIME_DIR'):
        print("Warning: XDG_RUNTIME_DIR not set")
        # Try to set a reasonable default if running as root
        if os.geteuid() == 0:
            user_id = os.environ.get('SUDO_UID', '1000')  # Default to 1000 if not available
            xdg_runtime = f"/run/user/{user_id}"
            if os.path.exists(xdg_runtime):
                os.environ['XDG_RUNTIME_DIR'] = xdg_runtime
                print(f"Set XDG_RUNTIME_DIR to {xdg_runtime}")
    
    return True

# Initialize GUI environment check
if not check_gui_environment():
    print("GUI environment may not be properly configured for elevated privileges")

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

try:
    from gi.repository import Gtk, Adw, Gio, Gdk
except Exception as e:
    print(f"Failed to import GTK: {e}")
    print("This may be due to running with elevated privileges.")
    print("Try running the application normally or ensure GUI libraries are accessible.")
    sys.exit(1)

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
        # Initialize GTK first if needed
        if not Gtk.is_initialized():
            try:
                Gtk.init()
                print("GTK initialized successfully")
            except Exception as e:
                print(f"Failed to initialize GTK: {e}")
                raise
        
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)
        self.zfs_assistant = ZFSAssistant()
        
        # Initialize privilege session early (like Timeshift)
        self.privilege_authenticated = False
        
        # Setup custom CSS (deferred if display not available)
        self.setup_css()
        
        # Setup theme
        self.setup_theme()
        
        # Set up notifications
        self.notification_enabled = self.zfs_assistant.config.get("notifications_enabled", True)
    
    def ensure_privileges(self):
        """
        Ensure we have administrative privileges for ZFS operations.
        This authenticates once at app startup, similar to how Timeshift works.
        """
        if not self.privilege_authenticated:
            try:
                # Check if we're already running with elevated privileges
                if os.geteuid() == 0:
                    self.privilege_authenticated = True
                    print("✓ Already running with administrative privileges")
                    return True
                
                # Try to authenticate early - this will prompt for password if needed
                success = self.zfs_assistant.privilege_manager._refresh_auth_cache()
                if success:
                    self.privilege_authenticated = True
                    print("✓ Administrative privileges obtained")
                    return True
                else:
                    print("✗ Failed to obtain administrative privileges")
                    return False
            except Exception as e:
                print(f"✗ Error during authentication: {e}")
                return False
        return True

    def setup_css(self):
        """Setup CSS styling - use GTK4 defaults for clean appearance"""
        # Check if display is available - defer CSS loading if not
        display = Gdk.Display.get_default()
        if display is None:
            # Display not ready yet, CSS will be applied later in on_activate
            return
            
        # Check if we have a CSS file and if it has meaningful content
        css_file_path = os.path.join(os.path.dirname(__file__), 'style.css')
        
        # If CSS file exists and has content (>100 bytes), load it
        if os.path.exists(css_file_path) and os.path.getsize(css_file_path) > 100:
            css_provider = Gtk.CssProvider()
            try:
                css_provider.load_from_path(css_file_path)
                # Apply CSS to default display
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
            Gtk.StyleContext.add_provider_for_display(
                display, 
                css_provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def on_activate(self, app):
        # Ensure CSS is applied now that display is available
        self.setup_css()
        
        # Authenticate privileges early if this is the first window
        win = self.get_active_window()
        if not win:
            # Try to authenticate before creating the main window
            if not self.ensure_privileges():
                # If authentication fails, show error and exit
                dialog = Adw.MessageDialog.new(
                    None,
                    "Authentication Required",
                    "ZFS Assistant requires administrative privileges to manage ZFS datasets and snapshots.\n\nPlease run the application with proper privileges or ensure your user account has access to ZFS commands."
                )
                dialog.add_response("close", "Close")
                dialog.set_response_appearance("close", Adw.ResponseAppearance.DESTRUCTIVE)
                dialog.connect("response", lambda d, r: self.quit())
                dialog.present()
                return
            
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
        
        # Skip notifications when running with elevated privileges as D-Bus may not be available
        if os.geteuid() == 0:
            print(f"Notification: {title}" + (f" - {body}" if body else ""))
            return
            
        try:
            notification = Gio.Notification.new(title)
            if body:
                notification.set_body(body)
            # Use send_notification method from Gio.Application
            super().send_notification(APP_ID, notification)
        except Exception as e:
            # Fallback to console output if D-Bus fails
            print(f"Notification: {title}" + (f" - {body}" if body else ""))
            print(f"Note: Desktop notifications unavailable: {e}")
        
    def toggle_notifications(self, enabled):
        """Toggle notifications"""
        self.notification_enabled = enabled
        self.zfs_assistant.config["notifications_enabled"] = enabled
        self.zfs_assistant.save_config()
