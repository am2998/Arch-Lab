#!/usr/bin/env python3
# ZFS Assistant - Main entry point
# Author: am2998

"""
Main entry point for the ZFS Assistant application.
This file enables running the application with 'python -m src'.
"""

import os
import sys
import subprocess

def is_running_as_appimage():
    """Check if we're running inside an AppImage"""
    return os.environ.get('APPIMAGE') is not None or os.environ.get('APPDIR') is not None

def is_running_with_privileges():
    """Check if we're already running with elevated privileges"""
    return os.geteuid() == 0

def get_python_executable():
    """Get the current Python executable path"""
    return sys.executable

def restart_with_privileges():
    """Restart the application with elevated privileges using pkexec"""
    try:
        python_exe = get_python_executable()
        script_path = os.path.abspath(__file__)
        
        print("ZFS Assistant requires administrative privileges for ZFS operations.")
        print("Requesting elevated privileges...")
        
        # Preserve essential environment variables for GUI
        env_vars = {}
        important_vars = [
            'DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'XDG_SESSION_TYPE',
            'XAUTHORITY', 'HOME', 'USER', 'PULSE_RUNTIME_PATH', 'PULSE_SOCKET',
            'XDG_DATA_DIRS', 'XDG_CONFIG_DIRS', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME',
            'XDG_DATA_HOME', 'LANG', 'LC_ALL', 'PATH'
        ]
        
        for var in important_vars:
            if var in os.environ:
                env_vars[var] = os.environ[var]
        
        # Build the command to re-execute with pkexec
        cmd = [
            'pkexec',
            'env',  # Use env to preserve environment variables
        ]
        
        # Add environment variables
        for key, value in env_vars.items():
            cmd.extend([f'{key}={value}'])
        
        # Add the python command
        cmd.extend([
            python_exe,
            script_path,
            '--elevated'  # Flag to prevent infinite recursion
        ])
        
        # Add any original arguments (except --elevated)
        original_args = [arg for arg in sys.argv[1:] if arg != '--elevated']
        cmd.extend(original_args)
        
        print(f"Executing: pkexec env [env_vars] {python_exe} {script_path} --elevated")
        os.execvp('pkexec', cmd)
        
    except OSError as e:
        print(f"Failed to restart with elevated privileges: {e}")
        print("Please ensure pkexec is installed or run as root:")
        print(f"sudo {python_exe} {script_path}")
        return False
    
    return True

def main():
    """Main entry point with privilege handling"""
    
    # When running with elevated privileges, suppress some D-Bus warnings
    if os.geteuid() == 0:
        # Suppress D-Bus session bus warnings when running as root
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = ''
        # Reduce systemd noise
        os.environ.setdefault('SYSTEMD_LOG_LEVEL', 'warning')
    
    # Check if we need elevated privileges
    need_elevation = False
    already_elevated = '--elevated' in sys.argv
    
    if not is_running_as_appimage() and not is_running_with_privileges() and not already_elevated:
        # We're running in development mode and need privileges
        need_elevation = True
        
        # Check if pkexec is available for development
        try:
            subprocess.run(['which', 'pkexec'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("Warning: pkexec not found. ZFS operations may fail without privileges.")
            print("Install polkit or run with sudo for full functionality.")
            need_elevation = False
    
    if need_elevation:
        return restart_with_privileges()
    
    # Continue with normal startup
    # Get absolute path to the current directory and its parent
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)

    # Add both to the Python path to ensure imports work
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Print debug info only in development
    if not is_running_as_appimage() and os.environ.get('DEBUG'):
        print(f"Current directory: {current_dir}")
        print(f"Python path: {sys.path}")
        print(f"Running with privileges: {is_running_with_privileges()}")

    # Try importing the application
    try:
        # Try direct import first
        from .application import Application
    except ImportError as e:
        print(f"Relative import failed: {e}")
        try:
            # Try direct import 
            from application import Application
        try:
            # Try with src prefix
            from src.application import Application
        except ImportError as e:
            print(f"Import from src failed: {e}")
            sys.exit(1)

    print("Starting ZFS Assistant...")
    try:
        app = Application()
        return app.run()
    except Exception as e:
        print(f"Failed to start ZFS Assistant: {e}")
        
        # If this is a GUI-related error and we're running with elevated privileges,
        # provide helpful guidance
        if "Gtk" in str(e) or "display" in str(e).lower():
            print("\nThis appears to be a GUI initialization error.")
            if is_running_with_privileges():
                print("When running with elevated privileges, GUI applications may have issues.")
                print("This can happen due to display permissions or missing environment variables.")
                print("\nTry one of these solutions:")
                print("1. Run without elevation first: python -m src")
                print("2. Ensure your user is in the 'wheel' or 'sudo' group")
                print("3. Check that polkit is properly configured")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
