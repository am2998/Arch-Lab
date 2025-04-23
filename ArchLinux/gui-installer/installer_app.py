#!/usr/bin/env python3
"""
Installer Application Module
Main application class for the Arch Linux Installer GUI
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import json
from PIL import Image, ImageTk
import time

# Try to import ttkbootstrap if available
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.scrolled import ScrolledFrame
    USING_BOOTSTRAP = True
except ImportError:
    import tkinter.ttk as ttk
    USING_BOOTSTRAP = False
    
# Import our modules
from ui_components import WelcomeFrame, SystemConfigFrame, UserConfigFrame, HardwareConfigFrame
from ui_components import DesktopConfigFrame, AdvancedFrame, InstallationFrame
from config_manager import ConfigManager
from installer import Installer

class InstallerApp:
    """Main installer application"""
    
    def __init__(self, root):
        """Initialize the installer application"""
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Load configuration
        self.config_manager = ConfigManager()
        
        # Set up styles
        self.setup_styles()
        
        # Create UI components
        self.create_widgets()
        
        # Initialize the installer backend
        self.installer = Installer(self)
        
        # Start at the welcome page
        self.show_frame("welcome")

    def setup_styles(self):
        """Set up styles for the application"""
        if USING_BOOTSTRAP:
            # ttkbootstrap already has nice styles
            pass
        else:
            # Configure ttk styles
            style = ttk.Style()
            style.configure("TLabel", font=("Helvetica", 11))
            style.configure("TButton", font=("Helvetica", 11))
            style.configure("TCheckbutton", font=("Helvetica", 11))
            style.configure("TRadiobutton", font=("Helvetica", 11))
            style.configure("TNotebook", font=("Helvetica", 11))
            style.configure("TNotebook.Tab", font=("Helvetica", 11))
    
    def create_widgets(self):
        """Create all widgets for the application"""
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the header with Arch Linux logo
        self.create_header()
        
        # Create a container for the changing content
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create all the frames but only show the welcome one initially
        self.frames = {}
        
        # Create all frames
        self.frames["welcome"] = WelcomeFrame(self.content_frame, self)
        self.frames["system"] = SystemConfigFrame(self.content_frame, self)
        self.frames["user"] = UserConfigFrame(self.content_frame, self)
        self.frames["hardware"] = HardwareConfigFrame(self.content_frame, self)
        self.frames["desktop"] = DesktopConfigFrame(self.content_frame, self)
        self.frames["advanced"] = AdvancedFrame(self.content_frame, self)
        self.frames["installation"] = InstallationFrame(self.content_frame, self)
        
        # Create navigation buttons at the bottom
        self.create_navigation_buttons()
        
    def create_header(self):
        """Create the header with Arch Linux logo"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=10)
        
        # Try to load the Arch Linux logo
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "archlinux-logo.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)
                
                logo_label = ttk.Label(header_frame, image=logo_photo)
                logo_label.image = logo_photo  # Keep a reference to prevent garbage collection
                logo_label.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        # Title and subtitle
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, padx=10)
        
        title_label = ttk.Label(title_frame, text="Arch Linux Installer", 
                               font=("Helvetica", 20, "bold"))
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(title_frame, text="Flexible Installation GUI", 
                                  font=("Helvetica", 12))
        subtitle_label.pack(anchor=tk.W)
        
    def create_navigation_buttons(self):
        """Create navigation buttons at the bottom"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Back button
        self.back_button = ttk.Button(button_frame, text="Back", command=self.go_back)
        self.back_button.pack(side=tk.LEFT, padx=10)
        
        # Next button
        self.next_button = ttk.Button(button_frame, text="Next", command=self.go_next)
        self.next_button.pack(side=tk.RIGHT, padx=10)
        
        # Cancel button
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_close)
        self.cancel_button.pack(side=tk.RIGHT, padx=10)
        
    def show_frame(self, frame_name):
        """Show a specific frame and hide the others"""
        # Hide all frames
        for frame in self.frames.values():
            frame.pack_forget()
        
        # Show the selected frame
        self.frames[frame_name].pack(fill=tk.BOTH, expand=True)
        self.current_frame = frame_name
        
        # Update navigation buttons
        self.update_navigation_buttons()
        
    def update_navigation_buttons(self):
        """Update navigation buttons based on current frame"""
        # Disable Back button on welcome page
        if self.current_frame == "welcome":
            self.back_button.config(state="disabled")
        else:
            self.back_button.config(state="normal")
            
        # Change Next button to Install on the last page
        if self.current_frame == "advanced":
            self.next_button.config(text="Install")
        elif self.current_frame == "installation":
            self.next_button.config(state="disabled")
            self.back_button.config(state="disabled")
        else:
            self.next_button.config(text="Next", state="normal")
    
    def go_back(self):
        """Go to the previous screen"""
        current_index = self.get_frame_order().index(self.current_frame)
        if current_index > 0:
            prev_frame = self.get_frame_order()[current_index - 1]
            self.show_frame(prev_frame)
    
    def go_next(self):
        """Go to the next screen or start installation"""
        # Validate current frame inputs if needed
        if not self.validate_current_frame():
            return
            
        # Get current position in frame order
        frame_order = self.get_frame_order()
        current_index = frame_order.index(self.current_frame)
        
        # If we're on the advanced page, go to installation
        if self.current_frame == "advanced":
            self.start_installation()
            return
            
        # Otherwise, go to next page if there is one
        if current_index < len(frame_order) - 1:
            next_frame = frame_order[current_index + 1]
            self.show_frame(next_frame)
            
    def get_frame_order(self):
        """Get the order of frames for navigation"""
        # Define the order of frames for navigation
        # The simple installation mode might skip the advanced frame
        if self.config_manager.get("install_mode") == "simple":
            return ["welcome", "system", "user", "hardware", "desktop", "installation"]
        else:
            return ["welcome", "system", "user", "hardware", "desktop", "advanced", "installation"]
    
    def validate_current_frame(self):
        """Validate inputs on the current frame before proceeding"""
        # Delegate validation to the current frame
        return self.frames[self.current_frame].validate()
    
    def start_installation(self):
        """Start the installation process"""
        # Save all configuration before starting
        self.config_manager.save_all()
        
        # Move to installation page
        self.show_frame("installation")
        
        # Start installation in a separate thread
        threading.Thread(target=self.installer.run_installation, daemon=True).start()
    
    def on_close(self):
        """Handle closing the application"""
        if messagebox.askyesno("Quit", "Are you sure you want to quit? Any unsaved configuration will be lost."):
            self.root.destroy()
    
    def update_installation_progress(self, progress, message):
        """Update the installation progress in the UI"""
        self.frames["installation"].update_progress(progress, message)