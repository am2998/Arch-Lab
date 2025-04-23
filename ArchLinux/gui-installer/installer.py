#!/usr/bin/env python3
"""
Installer Module for Arch Linux Installation
Handles running the installation script with the user's configuration
"""
import os
import sys
import subprocess
import threading
import time

class Installer:
    """Handles the installation process"""
    
    def __init__(self, app):
        """Initialize the installer"""
        self.app = app
        self.config_manager = app.config_manager
        self.installation_running = False
        self.installation_complete = False
        self.process = None
    
    def run_installation(self):
        """Run the installation script with the user's configuration"""
        if self.installation_running:
            return
            
        self.installation_running = True
        try:
            # Update progress in UI
            self.update_progress(0, "Preparing for installation...")
            
            # Get the path to the installation script
            script_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "flexible-install", "install.sh"
            )
            
            # Check if script exists
            if not os.path.exists(script_path):
                self.update_progress(0, "Error: Installation script not found!")
                return
            
            # Generate temporary script with export commands
            temp_script = self._generate_temp_script(script_path)
            
            # Make the script executable
            os.chmod(temp_script, 0o755)
            
            # Update progress
            self.update_progress(5, "Starting installation...")
            
            # Run the script and capture output
            self._run_script(temp_script)
            
        except Exception as e:
            self.update_progress(0, f"Error during installation: {str(e)}")
            self.installation_running = False
    
    def _generate_temp_script(self, script_path):
        """Generate a temporary script that sets environment variables and runs the installation script"""
        # Get export commands for configuration
        export_commands = self.config_manager.get_bash_export_commands()
        
        # Create temp script path
        temp_script = os.path.join(os.path.dirname(script_path), "gui_install_wrapper.sh")
        
        # Write the wrapper script
        with open(temp_script, 'w') as f:
            f.write("#!/bin/bash\n\n")
            f.write("# This is an automatically generated wrapper script\n")
            f.write("# that sets environment variables and runs the installation script\n\n")
            
            # Add export commands
            f.write("# Set configuration variables\n")
            for cmd in export_commands:
                f.write(f"{cmd}\n")
            
            f.write("\n# Run the installation script\n")
            f.write(f"bash '{script_path}'\n")
            
            f.write("\n# Signal GUI that installation is complete\n")
            f.write("echo '===INSTALLATION_COMPLETE==='\n")
        
        return temp_script
    
    def _run_script(self, script_path):
        """Run the installation script and monitor progress"""
        # Start the process
        self.process = subprocess.Popen(
            ['pkexec', 'bash', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Track progress
        progress = 5
        
        # Read output line by line
        for line in self.process.stdout:
            # Check if installation is complete
            if "===INSTALLATION_COMPLETE===" in line:
                self.installation_complete = True
                self.update_progress(100, "Installation complete!")
                break
                
            # Update progress based on recognized markers in the output
            if "NETWORK VERIFICATION" in line:
                progress = 10
                self.update_progress(progress, "Verifying network connection...")
            elif "SETUP: INITIAL VARIABLES" in line:
                progress = 15
                self.update_progress(progress, "Setting up initial variables...")
            elif "CHOOSE BOOT TYPE" in line:
                progress = 20
                self.update_progress(progress, "Configuring boot settings...")
            elif "DESKTOP ENVIRONMENT SELECTION" in line:
                progress = 25
                self.update_progress(progress, "Configuring desktop environment...")
            elif "SYSTEM INFORMATION" in line:
                progress = 30
                self.update_progress(progress, "Configuring system information...")
            elif "MIRROR COUNTRY SELECTION" in line:
                progress = 35
                self.update_progress(progress, "Configuring mirrors...")
            elif "KEYBOARD LAYOUT SELECTION" in line:
                progress = 40
                self.update_progress(progress, "Setting keyboard layout...")
            elif "LOCALE SELECTION" in line:
                progress = 45
                self.update_progress(progress, "Setting system locale...")
            elif "USER CONFIGURATION" in line:
                progress = 50
                self.update_progress(progress, "Configuring user accounts...")
            elif "PASSWORD CONFIGURATION" in line:
                progress = 55
                self.update_progress(progress, "Setting passwords...")
            elif "CPU SELECTION" in line:
                progress = 60
                self.update_progress(progress, "Configuring CPU settings...")
            elif "GPU SELECTION" in line:
                progress = 65
                self.update_progress(progress, "Configuring GPU settings...")
            elif "AUDIO SERVER SELECTION" in line:
                progress = 70
                self.update_progress(progress, "Configuring audio settings...")
            elif "CLEAN SYSTEM DISK" in line:
                progress = 75
                self.update_progress(progress, "Preparing system disk...")
            elif "FORMAT/MOUNT PARTITIONS" in line:
                progress = 80
                self.update_progress(progress, "Formatting and mounting partitions...")
            elif "INSTALL BASE" in line:
                progress = 85
                self.update_progress(progress, "Installing base system...")
            elif "GENERATING FSTAB" in line:
                progress = 90
                self.update_progress(progress, "Generating fstab...")
            elif "ARCH-CHROOT" in line:
                progress = 95
                self.update_progress(progress, "Configuring system in chroot...")
            
            # Log output to the UI
            self.log_output(line.strip())
        
        # Wait for process to complete
        self.process.wait()
        
        # Update status based on exit code
        if not self.installation_complete:
            if self.process.returncode == 0:
                self.update_progress(100, "Installation completed successfully!")
            else:
                self.update_progress(0, f"Installation failed with exit code {self.process.returncode}")
        
        # Clean up
        self.installation_running = False
    
    def cancel_installation(self):
        """Cancel the installation process if it's running"""
        if self.installation_running and self.process:
            try:
                self.process.terminate()
                time.sleep(1)
                if self.process.poll() is None:
                    self.process.kill()
                self.update_progress(0, "Installation was cancelled.")
            except Exception as e:
                print(f"Error cancelling installation: {e}")
            finally:
                self.installation_running = False
    
    def update_progress(self, progress, message):
        """Update the installation progress in the UI"""
        # Call the app's method to update progress in the UI
        self.app.update_installation_progress(progress, message)
    
    def log_output(self, message):
        """Log output to the UI"""
        # This will be implemented by the InstallationFrame
        try:
            self.app.frames["installation"].log_output(message)
        except:
            pass