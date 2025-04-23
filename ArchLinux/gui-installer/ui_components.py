#!/usr/bin/env python3
"""
UI Components for the Arch Linux Installer GUI
Contains frame classes for different sections of the installer
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import subprocess
import re
from PIL import Image, ImageTk

# Try to import ttkbootstrap if available
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.scrolled import ScrolledFrame
    USING_BOOTSTRAP = True
except ImportError:
    import tkinter.ttk as ttk
    USING_BOOTSTRAP = False
    # Create a simple ScrolledFrame replacement if ttkbootstrap is not available
    class ScrolledFrame(ttk.Frame):
        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
            self.canvas = tk.Canvas(self)
            self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.scrollable_frame = ttk.Frame(self.canvas)
            
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            )
            
            self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            self.canvas.configure(yscrollcommand=self.scrollbar.set)
            
            self.canvas.pack(side="left", fill="both", expand=True)
            self.scrollbar.pack(side="right", fill="y")

# Base frame for all installer screens
class BaseInstallerFrame(ttk.Frame):
    """Base class for installer frames with common functionality"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.config_manager = app.config_manager
        
    def validate(self):
        """Validate inputs on this frame. Override in subclasses."""
        return True
    
    def create_section_header(self, text):
        """Create a styled section header"""
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=10, pady=(20, 10))
        
        # Header label
        if USING_BOOTSTRAP:
            label = ttk.Label(frame, text=text, font=("Helvetica", 16, "bold"), 
                              bootstyle="primary")
        else:
            label = ttk.Label(frame, text=text, font=("Helvetica", 16, "bold"))
            
        label.pack(anchor=tk.W)
        
        # Separator
        sep = ttk.Separator(frame, orient="horizontal")
        sep.pack(fill=tk.X, pady=5)
        
        return frame
    
    def create_option_group(self, parent, title, options, variable_name, default=None):
        """Create a group of radio buttons for options"""
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        
        # Get current value or use default
        current_value = self.config_manager.get(variable_name, default)
        
        # Create StringVar and bind to config_manager
        var = tk.StringVar(value=current_value)
        var.trace_add("write", lambda *args: self.config_manager.set(variable_name, var.get()))
        
        # Create radio buttons for each option
        for text, value in options:
            rb = ttk.Radiobutton(frame, text=text, value=value, variable=var)
            rb.pack(anchor=tk.W, padx=20, pady=2)
        
        return var
    
    def create_input_field(self, parent, label_text, variable_name, default="", show=None, width=30):
        """Create an input field with label"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        label = ttk.Label(frame, text=label_text, width=20, anchor="e")
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Get current value or use default
        current_value = self.config_manager.get(variable_name, default)
        
        # Create StringVar and bind to config_manager
        var = tk.StringVar(value=current_value)
        var.trace_add("write", lambda *args: self.config_manager.set(variable_name, var.get()))
        
        # Create entry field
        entry = ttk.Entry(frame, textvariable=var, width=width, show=show)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        return var, entry


# Welcome Frame
class WelcomeFrame(BaseInstallerFrame):
    """Welcome screen with installation mode selection"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)
        self.create_widgets()
        
    def create_widgets(self):
        # Welcome message
        welcome_frame = ttk.Frame(self)
        welcome_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = ttk.Label(welcome_frame, text="Welcome to the Arch Linux Installer", 
                         font=("Helvetica", 24, "bold"))
        title.pack(pady=(0, 20))
        
        subtitle = ttk.Label(welcome_frame, text="This wizard will guide you through the installation process",
                            font=("Helvetica", 12))
        subtitle.pack(pady=(0, 40))
        
        # Installation mode selection
        mode_frame = ttk.LabelFrame(welcome_frame, text="Installation Mode")
        mode_frame.pack(fill=tk.X, padx=50, pady=10, ipady=10)
        
        # Get current value
        current_mode = self.config_manager.get("install_mode", "simple")
        
        # Mode selection radio buttons
        self.mode_var = tk.StringVar(value=current_mode)
        self.mode_var.trace_add("write", lambda *args: self.config_manager.set("install_mode", self.mode_var.get()))
        
        # Simple mode
        mode_simple = ttk.Radiobutton(
            mode_frame, text="Simple Mode", value="simple", variable=self.mode_var,
            style="primary" if USING_BOOTSTRAP else "TRadiobutton"
        )
        mode_simple.pack(anchor=tk.W, padx=20, pady=5)
        
        simple_desc = ttk.Label(
            mode_frame, 
            text="Recommended for most users. Fewer choices with sensible defaults.",
            font=("Helvetica", 10), foreground="gray"
        )
        simple_desc.pack(anchor=tk.W, padx=50, pady=(0, 10))
        
        # Advanced mode
        mode_advanced = ttk.Radiobutton(
            mode_frame, text="Advanced Mode", value="advanced", variable=self.mode_var,
            style="primary" if USING_BOOTSTRAP else "TRadiobutton"
        )
        mode_advanced.pack(anchor=tk.W, padx=20, pady=5)
        
        advanced_desc = ttk.Label(
            mode_frame, 
            text="More customization options including ZFS settings, encryption, and detailed partitioning.",
            font=("Helvetica", 10), foreground="gray"
        )
        advanced_desc.pack(anchor=tk.W, padx=50, pady=(0, 10))
        
        # Warning for advanced mode
        warning_label = ttk.Label(
            welcome_frame, 
            text="⚠️ Advanced mode requires understanding of Linux systems and disk partitioning.",
            font=("Helvetica", 10), foreground="orange"
        )
        warning_label.pack(pady=20)
        
    def validate(self):
        return True


# System Configuration Frame
class SystemConfigFrame(BaseInstallerFrame):
    """System configuration screen with device, hostname, keyboard, locale settings"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)
        self.create_widgets()
        
    def create_widgets(self):
        # Create a scrollable frame for all content
        self.scrolled_frame = ScrolledFrame(self)
        self.scrolled_frame.pack(fill=tk.BOTH, expand=True)
        content = self.scrolled_frame.scrollable_frame
        
        # Installation Device Section
        self.create_section_header("Installation Device")
        
        # Device selection
        device_frame = ttk.Frame(content)
        device_frame.pack(fill=tk.X, padx=10, pady=5)
        
        device_label = ttk.Label(device_frame, text="Select Disk:", width=15, anchor="e")
        device_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Get available disks
        available_disks = self.get_available_disks()
        
        # Current device
        current_device = self.config_manager.get("device", "")
        if current_device not in available_disks and available_disks:
            current_device = list(available_disks.keys())[0]
            
        # Device combobox
        self.device_var = tk.StringVar(value=current_device)
        self.device_var.trace_add("write", lambda *args: self.config_manager.set("device", self.device_var.get()))
        
        device_cb = ttk.Combobox(device_frame, textvariable=self.device_var, state="readonly")
        device_cb['values'] = list(available_disks.keys())
        device_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Disk info
        disk_info_frame = ttk.Frame(content)
        disk_info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.disk_info_label = ttk.Label(disk_info_frame, text="", style="info.TLabel")
        self.disk_info_label.pack(side=tk.LEFT, padx=25)
        
        # Update disk info when selection changes
        def update_disk_info(*args):
            disk = self.device_var.get()
            if disk in available_disks:
                self.disk_info_label.config(text=available_disks[disk])
        
        self.device_var.trace_add("write", update_disk_info)
        update_disk_info()  # Initial update
        
        # Warning label
        warning_label = ttk.Label(
            content, 
            text="⚠️ WARNING: The selected disk will be completely erased!",
            font=("Helvetica", 10, "bold"), foreground="red"
        )
        warning_label.pack(padx=10, pady=5)
        
        # Boot type
        boot_options = [
            ("EFI (Modern systems, recommended)", "efi"),
            ("BIOS (Legacy systems)", "bios")
        ]
        self.boot_var = self.create_option_group(content, "Boot Type", boot_options, "boot_type", "efi")
        
        # System Configuration Section
        self.create_section_header("System Configuration")
        
        # Hostname
        hostname_var, _ = self.create_input_field(content, "Hostname:", "hostname", "archlinux")
        
        # Keyboard layout
        keyboard_frame = ttk.Frame(content)
        keyboard_frame.pack(fill=tk.X, padx=10, pady=5)
        
        keyboard_label = ttk.Label(keyboard_frame, text="Keyboard Layout:", width=20, anchor="e")
        keyboard_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Get available keyboard layouts
        available_layouts = self.get_keyboard_layouts()
        
        # Current layout
        current_layout = self.config_manager.get("keyboard_layout", "us")
        
        self.keyboard_var = tk.StringVar(value=current_layout)
        self.keyboard_var.trace_add("write", lambda *args: self.config_manager.set("keyboard_layout", self.keyboard_var.get()))
        
        keyboard_cb = ttk.Combobox(keyboard_frame, textvariable=self.keyboard_var)
        keyboard_cb['values'] = available_layouts
        keyboard_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Locale
        locale_frame = ttk.Frame(content)
        locale_frame.pack(fill=tk.X, padx=10, pady=5)
        
        locale_label = ttk.Label(locale_frame, text="System Locale:", width=20, anchor="e")
        locale_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Get available locales
        available_locales = self.get_locales()
        
        # Current locale
        current_locale = self.config_manager.get("locale", "en_US.UTF-8")
        
        self.locale_var = tk.StringVar(value=current_locale)
        self.locale_var.trace_add("write", lambda *args: self.config_manager.set("locale", self.locale_var.get()))
        
        locale_cb = ttk.Combobox(locale_frame, textvariable=self.locale_var)
        locale_cb['values'] = available_locales
        locale_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Mirror country
        mirror_frame = ttk.Frame(content)
        mirror_frame.pack(fill=tk.X, padx=10, pady=5)
        
        mirror_label = ttk.Label(mirror_frame, text="Mirror Country:", width=20, anchor="e")
        mirror_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Define available mirror countries
        mirror_countries = [
            "", "Worldwide", "Australia", "Austria", "Belarus", "Belgium", "Brazil", 
            "Bulgaria", "Canada", "Chile", "China", "Colombia", "Czech Republic", 
            "Denmark", "Ecuador", "Finland", "France", "Germany", "Greece", "Hong Kong", 
            "Hungary", "Iceland", "India", "Indonesia", "Iran", "Ireland", "Israel", 
            "Italy", "Japan", "Kazakhstan", "Kenya", "Latvia", "Lithuania", "Luxembourg", 
            "Netherlands", "New Zealand", "Norway", "Poland", "Portugal", "Romania", 
            "Russia", "Serbia", "Singapore", "Slovakia", "Slovenia", "South Africa", 
            "South Korea", "Spain", "Sweden", "Switzerland", "Taiwan", "Turkey", 
            "Ukraine", "United Kingdom", "United States", "Vietnam"
        ]
        
        # Current mirror country
        current_mirror = self.config_manager.get("mirror_country", "")
        if current_mirror == "":
            current_mirror = "Worldwide"
            
        self.mirror_var = tk.StringVar(value=current_mirror)
        self.mirror_var.trace_add("write", lambda *args: 
            self.config_manager.set("mirror_country", "" if self.mirror_var.get() == "Worldwide" else self.mirror_var.get())
        )
        
        mirror_cb = ttk.Combobox(mirror_frame, textvariable=self.mirror_var)
        mirror_cb['values'] = mirror_countries
        mirror_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
    def get_available_disks(self):
        """Get a list of available disks with their details"""
        disks = {}
        try:
            output = subprocess.check_output(['lsblk', '-dpno', 'NAME,SIZE,MODEL'], 
                                          universal_newlines=True)
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 2 and (parts[0].startswith('/dev/sd') or 
                                          parts[0].startswith('/dev/nvme') or
                                          parts[0].startswith('/dev/vd')):
                        name = parts[0]
                        size = parts[1]
                        model = parts[2] if len(parts) > 2 else "Unknown"
                        disks[name] = f"{size}, {model}"
        except Exception as e:
            print(f"Error getting disk list: {e}")
            # Provide some sample data
            disks = {"/dev/sda": "500G, Samsung SSD", "/dev/sdb": "1T, Western Digital"}
            
        return disks
        
    def get_keyboard_layouts(self):
        """Get available keyboard layouts"""
        try:
            # Try to get actual layouts from system
            output = subprocess.check_output(['localectl', 'list-keymaps'], 
                                          universal_newlines=True)
            layouts = output.strip().split('\n')
            return layouts
        except:
            # Fallback to common layouts
            return [
                "us", "uk", "de", "fr", "it", "es", "pt", "br", "ru", "jp",
                "cn", "kr", "pl", "se", "no", "fi", "dk", "tr", "ar"
            ]
            
    def get_locales(self):
        """Get available system locales"""
        try:
            # Try to get actual locales from system
            if os.path.exists('/etc/locale.gen'):
                with open('/etc/locale.gen', 'r') as f:
                    content = f.read()
                    # Extract locales (they usually start with a comment # that we remove)
                    locales = re.findall(r'#\s*([a-zA-Z_@.]+)', content)
                    return sorted(locales)
        except:
            pass
            
        # Fallback to common locales
        return [
            "en_US.UTF-8", "en_GB.UTF-8", "de_DE.UTF-8", "fr_FR.UTF-8", 
            "it_IT.UTF-8", "es_ES.UTF-8", "pt_BR.UTF-8", "ru_RU.UTF-8",
            "zh_CN.UTF-8", "ja_JP.UTF-8", "ko_KR.UTF-8", "ar_SA.UTF-8"
        ]
        
    def validate(self):
        """Validate inputs on this frame"""
        # Check if a device is selected
        device = self.device_var.get()
        if not device:
            messagebox.showerror("Error", "Please select an installation device.")
            return False
            
        # Check hostname
        hostname = self.config_manager.get("hostname", "")
        if not hostname or not re.match(r'^[a-zA-Z0-9-]+$', hostname):
            messagebox.showerror("Error", "Please enter a valid hostname (letters, numbers, and hyphens only).")
            return False
            
        return True


# User Configuration Frame
class UserConfigFrame(BaseInstallerFrame):
    """User account configuration screen"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)
        self.create_widgets()
        
    def create_widgets(self):
        # Create a scrollable frame for all content
        self.scrolled_frame = ScrolledFrame(self)
        self.scrolled_frame.pack(fill=tk.BOTH, expand=True)
        content = self.scrolled_frame.scrollable_frame
        
        # User Account Section
        self.create_section_header("User Account")
        
        # Username
        username_var, self.username_entry = self.create_input_field(
            content, "Username:", "username", "")
            
        # User password
        password_var, self.password_entry = self.create_input_field(
            content, "User Password:", "user_password", "", show="*")
            
        # Confirm user password
        self.confirm_password_var = tk.StringVar()
        confirm_password_frame = ttk.Frame(content)
        confirm_password_frame.pack(fill=tk.X, padx=10, pady=5)
        
        confirm_label = ttk.Label(confirm_password_frame, text="Confirm Password:", width=20, anchor="e")
        confirm_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.confirm_password_entry = ttk.Entry(confirm_password_frame, 
                                            textvariable=self.confirm_password_var,
                                            show="*", width=30)
        self.confirm_password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Root Account Section
        self.create_section_header("Root Account")
        
        # Root password
        root_password_var, self.root_password_entry = self.create_input_field(
            content, "Root Password:", "root_password", "", show="*")
            
        # Confirm root password
        self.confirm_root_var = tk.StringVar()
        confirm_root_frame = ttk.Frame(content)
        confirm_root_frame.pack(fill=tk.X, padx=10, pady=5)
        
        confirm_root_label = ttk.Label(confirm_root_frame, text="Confirm Root Password:", width=20, anchor="e")
        confirm_root_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.confirm_root_entry = ttk.Entry(confirm_root_frame, 
                                        textvariable=self.confirm_root_var,
                                        show="*", width=30)
        self.confirm_root_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Password tips
        tips_frame = ttk.LabelFrame(content, text="Password Tips")
        tips_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        
        tips_text = (
            "• Use a minimum of 8 characters\n"
            "• Include uppercase and lowercase letters\n"
            "• Include numbers and special characters\n"
            "• Avoid common words or phrases"
        )
        
        tips_label = ttk.Label(tips_frame, text=tips_text, justify=tk.LEFT)
        tips_label.pack(padx=10, pady=10, anchor=tk.W)
        
    def validate(self):
        """Validate user inputs"""
        # Check username
        username = self.config_manager.get("username", "")
        if not username or not re.match(r'^[a-z_][a-z0-9_-]*$', username):
            messagebox.showerror("Error", 
                             "Username must start with a lowercase letter or underscore, "
                             "and contain only lowercase letters, numbers, underscores, or hyphens.")
            return False
            
        # Check user password
        password = self.config_manager.get("user_password", "")
        if not password or len(password) < 6:
            messagebox.showerror("Error", "User password must be at least 6 characters.")
            return False
            
        # Check if passwords match
        if password != self.confirm_password_var.get():
            messagebox.showerror("Error", "User passwords do not match.")
            return False
            
        # Check root password
        root_password = self.config_manager.get("root_password", "")
        if not root_password or len(root_password) < 6:
            messagebox.showerror("Error", "Root password must be at least 6 characters.")
            return False
            
        # Check if root passwords match
        if root_password != self.confirm_root_var.get():
            messagebox.showerror("Error", "Root passwords do not match.")
            return False
            
        return True


# Hardware Configuration Frame
class HardwareConfigFrame(BaseInstallerFrame):
    """Hardware configuration screen"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)
        self.create_widgets()
        
    def create_widgets(self):
        # Create a scrollable frame for all content
        self.scrolled_frame = ScrolledFrame(self)
        self.scrolled_frame.pack(fill=tk.BOTH, expand=True)
        content = self.scrolled_frame.scrollable_frame
        
        # CPU Configuration
        self.create_section_header("CPU Configuration")
        
        # CPU type options
        cpu_options = [
            ("Intel", "Intel"),
            ("AMD", "AMD")
        ]
        
        self.cpu_var = self.create_option_group(content, "CPU Type", cpu_options, "cpu_type", "AMD")
        
        # Update CPU microcode when CPU type changes
        def update_cpu_microcode(*args):
            if self.cpu_var.get() == "Intel":
                self.config_manager.set("cpu_microcode", "intel-ucode")
            else:
                self.config_manager.set("cpu_microcode", "amd-ucode")
                
        self.cpu_var.trace_add("write", update_cpu_microcode)
        
        # GPU Configuration
        self.create_section_header("GPU Configuration")
        
        # GPU type options
        gpu_frame = ttk.LabelFrame(content, text="GPU Type")
        gpu_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        
        # Current GPU type
        current_gpu = self.config_manager.get("gpu_type", "AMD/Intel")
        
        # GPU type radio buttons
        self.gpu_var = tk.StringVar(value=current_gpu)
        self.gpu_var.trace_add("write", lambda *args: self.update_gpu_type())
        
        # NVIDIA option
        nvidia_rb = ttk.Radiobutton(gpu_frame, text="NVIDIA", value="NVIDIA", variable=self.gpu_var)
        nvidia_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # AMD/Intel option
        amd_intel_rb = ttk.Radiobutton(gpu_frame, text="AMD/Intel (Open Source)", value="AMD/Intel", variable=self.gpu_var)
        amd_intel_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # None/VM option
        none_rb = ttk.Radiobutton(gpu_frame, text="None/VM", value="None/VM", variable=self.gpu_var)
        none_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # NVIDIA drivers frame (only shown when NVIDIA is selected)
        self.nvidia_frame = ttk.LabelFrame(content, text="NVIDIA Driver Selection")
        
        # Current NVIDIA driver type
        current_nvidia_driver = self.config_manager.get("nvidia_driver_type", "Proprietary")
        
        # NVIDIA driver radio buttons
        self.nvidia_driver_var = tk.StringVar(value=current_nvidia_driver)
        self.nvidia_driver_var.trace_add("write", lambda *args: 
                                     self.config_manager.set("nvidia_driver_type", self.nvidia_driver_var.get())
                                    )
        
        # Proprietary drivers option
        proprietary_rb = ttk.Radiobutton(self.nvidia_frame, text="Proprietary Drivers (Better performance)", 
                                      value="Proprietary", variable=self.nvidia_driver_var)
        proprietary_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # Open drivers option
        open_rb = ttk.Radiobutton(self.nvidia_frame, text="Open Source Drivers (Better compatibility)", 
                               value="Open", variable=self.nvidia_driver_var)
        open_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # Update GPU options after initialization
        self.update_gpu_type()
        
    def update_gpu_type(self):
        """Update UI based on selected GPU type"""
        gpu_type = self.gpu_var.get()
        self.config_manager.set("gpu_type", gpu_type)
        
        if gpu_type == "NVIDIA":
            self.nvidia_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        else:
            self.nvidia_frame.pack_forget()
            self.config_manager.set("nvidia_driver_type", "none")
        
    def validate(self):
        """Validate hardware configuration"""
        return True


# Desktop Configuration Frame
class DesktopConfigFrame(BaseInstallerFrame):
    """Desktop environment configuration screen"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)
        self.create_widgets()
        
    def create_widgets(self):
        # Create a scrollable frame for all content
        self.scrolled_frame = ScrolledFrame(self)
        self.scrolled_frame.pack(fill=tk.BOTH, expand=True)
        content = self.scrolled_frame.scrollable_frame
        
        # Desktop Environment Section
        self.create_section_header("Desktop Environment")
        
        # Desktop environment options
        de_frame = ttk.LabelFrame(content, text="Desktop Environment")
        de_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        
        # Current desktop environment
        current_de = self.config_manager.get("desktop_environment", "Hyprland")
        
        # Desktop environment radio buttons
        self.de_var = tk.StringVar(value=current_de)
        self.de_var.trace_add("write", lambda *args: 
                          self.config_manager.set("desktop_environment", self.de_var.get())
                         )
        
        # Hyprland
        hyprland_rb = ttk.Radiobutton(de_frame, text="Hyprland (Modern Wayland compositor)", 
                                   value="Hyprland", variable=self.de_var)
        hyprland_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # XFCE4
        xfce_rb = ttk.Radiobutton(de_frame, text="XFCE4 (Lightweight X11 desktop)", 
                               value="XFCE4", variable=self.de_var)
        xfce_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # KDE Plasma
        kde_rb = ttk.Radiobutton(de_frame, text="KDE Plasma (Feature-rich desktop)", 
                              value="KDE Plasma", variable=self.de_var)
        kde_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # GNOME
        gnome_rb = ttk.Radiobutton(de_frame, text="GNOME (Modern desktop environment)", 
                                value="GNOME", variable=self.de_var)
        gnome_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # Audio Server Section
        self.create_section_header("Audio Configuration")
        
        # Audio server options
        audio_options = [
            ("PipeWire (Modern, low-latency, recommended)", "pipewire"),
            ("PulseAudio (Traditional, widely compatible)", "pulseaudio")
        ]
        
        self.audio_var = self.create_option_group(content, "Audio Server", audio_options, "audio_server", "pipewire")
        
    def validate(self):
        """Validate desktop configuration"""
        return True


# Advanced Configuration Frame
class AdvancedFrame(BaseInstallerFrame):
    """Advanced configuration options"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)
        # Only show this frame in advanced mode
        if self.config_manager.get("install_mode") == "advanced":
            self.create_widgets()
        else:
            self.create_simple_message()
        
    def create_simple_message(self):
        """Show a message when in simple mode"""
        message_frame = ttk.Frame(self)
        message_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)
        
        message = ttk.Label(message_frame, 
                         text="Advanced options are not available in simple mode.\n"
                              "Go back to the welcome screen to switch to advanced mode.",
                         font=("Helvetica", 14), justify=tk.CENTER)
        message.pack(expand=True)
        
    def create_widgets(self):
        # Create a scrollable frame for all content
        self.scrolled_frame = ScrolledFrame(self)
        self.scrolled_frame.pack(fill=tk.BOTH, expand=True)
        content = self.scrolled_frame.scrollable_frame
        
        # Encryption Section
        self.create_section_header("Disk Encryption")
        
        # Encryption options
        encryption_options = [
            ("Yes (More secure, requires passphrase at boot)", "yes"),
            ("No (More convenient, less secure)", "no")
        ]
        
        self.encrypt_var = self.create_option_group(content, "Enable Disk Encryption", 
                                                encryption_options, "encrypt_disk", "no")
        
        # Passphrase inputs (only shown when encryption is enabled)
        self.encrypt_frame = ttk.Frame(content)
        
        # Disk encryption passphrase
        passphrase_var, self.passphrase_entry = self.create_input_field(
            self.encrypt_frame, "Disk Passphrase:", "disk_password", "", show="*")
            
        # Confirm passphrase
        self.confirm_passphrase_var = tk.StringVar()
        confirm_frame = ttk.Frame(self.encrypt_frame)
        confirm_frame.pack(fill=tk.X, padx=10, pady=5)
        
        confirm_label = ttk.Label(confirm_frame, text="Confirm Passphrase:", width=20, anchor="e")
        confirm_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.confirm_passphrase_entry = ttk.Entry(confirm_frame, 
                                              textvariable=self.confirm_passphrase_var,
                                              show="*", width=30)
        self.confirm_passphrase_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Show/hide encryption options based on selection
        def update_encryption_ui(*args):
            if self.encrypt_var.get() == "yes":
                self.encrypt_frame.pack(fill=tk.X, padx=10, pady=5)
            else:
                self.encrypt_frame.pack_forget()
                self.config_manager.set("disk_password", "")
                
        self.encrypt_var.trace_add("write", update_encryption_ui)
        update_encryption_ui()  # Initial update
        
        # ZFS Configuration Section
        self.create_section_header("ZFS Configuration")
        
        # ZFS compression options
        compression_options = [
            ("lz4 (Fast, good ratio, default)", "lz4"),
            ("zstd (Better compression, slightly slower)", "zstd"),
            ("gzip (Best compression, slowest)", "gzip"),
            ("No compression", "off")
        ]
        
        self.compression_var = self.create_option_group(content, "ZFS Compression", 
                                                    compression_options, "zfs_compression", "lz4")
        
        # Dataset configuration
        dataset_options = [
            ("Yes (Recommended for flexible management)", "yes"),
            ("No (Simpler, use only the root dataset)", "no")
        ]
        
        self.dataset_var = self.create_option_group(content, "Create Separate ZFS Datasets", 
                                                dataset_options, "separate_datasets", "yes")
        
        # ZRAM Configuration Section
        self.create_section_header("ZRAM Configuration")
        
        # ZRAM size options
        zram_size_frame = ttk.LabelFrame(content, text="ZRAM Size")
        zram_size_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        
        # Current ZRAM size
        current_zram_size = self.config_manager.get("zram_size", "min(ram, 32768)")
        
        # ZRAM size radio buttons
        self.zram_size_var = tk.StringVar(value=current_zram_size)
        self.zram_size_var.trace_add("write", lambda *args: self.update_zram_size())
        
        # Auto option
        auto_rb = ttk.Radiobutton(zram_size_frame, text="Auto (min(RAM, 32GB) - recommended)", 
                               value="min(ram, 32768)", variable=self.zram_size_var)
        auto_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # Half RAM option
        half_rb = ttk.Radiobutton(zram_size_frame, text="Half of RAM", 
                               value="ram / 2", variable=self.zram_size_var)
        half_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # Custom option
        custom_rb = ttk.Radiobutton(zram_size_frame, text="Custom value (specify in MB)", 
                                 value="custom", variable=self.zram_size_var)
        custom_rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # Custom size input frame
        self.custom_size_frame = ttk.Frame(zram_size_frame)
        self.custom_size_frame.pack(fill=tk.X, padx=40, pady=5)
        
        self.custom_size_var = tk.StringVar(value="8192")
        
        size_label = ttk.Label(self.custom_size_frame, text="Size (MB):")
        size_label.pack(side=tk.LEFT, padx=(0, 10))
        
        size_entry = ttk.Entry(self.custom_size_frame, textvariable=self.custom_size_var, width=10)
        size_entry.pack(side=tk.LEFT)
        
        # ZRAM compression algorithm
        zram_comp_options = [
            ("zstd (Best balance of speed/compression - recommended)", "zstd"),
            ("lz4 (Faster, lower compression ratio)", "lz4"),
            ("lzo-rle (Legacy option)", "lzo-rle"),
            ("lzo (Older algorithm)", "lzo")
        ]
        
        self.zram_comp_var = self.create_option_group(content, "ZRAM Compression Algorithm", 
                                                  zram_comp_options, "zram_compression", "zstd")
                                                  
        # Custom partition sizes
        if self.config_manager.get("install_mode") == "advanced":
            self.create_section_header("Partition Sizes")
            
            # EFI partition size
            efi_size_var, _ = self.create_input_field(content, "EFI Partition Size:", "efi_part_size", "1G")
            
            # Root partition size
            root_options = [
                ("Use all available space", "MAX"),
                ("Specify custom size", "custom")
            ]
            
            self.root_size_var = self.create_option_group(content, "Root Partition Size", 
                                                      root_options, "root_part_size_type", "MAX")
            
            # Custom root size input frame
            self.root_size_frame = ttk.Frame(content)
            
            self.root_size_input_var = tk.StringVar(value="50G")
            self.root_size_input_var.trace_add("write", lambda *args: 
                                           self.config_manager.set("root_part_size", self.root_size_input_var.get()))
            
            root_size_label = ttk.Label(self.root_size_frame, text="Size (e.g. 50G):", width=20, anchor="e")
            root_size_label.pack(side=tk.LEFT, padx=(0, 10))
            
            root_size_entry = ttk.Entry(self.root_size_frame, textvariable=self.root_size_input_var, width=10)
            root_size_entry.pack(side=tk.LEFT)
            
            # Update root size UI based on selection
            def update_root_size_ui(*args):
                if self.root_size_var.get() == "custom":
                    self.root_size_frame.pack(fill=tk.X, padx=10, pady=5)
                    self.config_manager.set("root_part_size", self.root_size_input_var.get())
                else:
                    self.root_size_frame.pack_forget()
                    self.config_manager.set("root_part_size", "MAX")
                    
            self.root_size_var.trace_add("write", update_root_size_ui)
            update_root_size_ui()  # Initial update
                                                  
        # Update UI based on current values
        self.update_zram_size()
        
    def update_zram_size(self):
        """Update ZRAM size configuration"""
        size_type = self.zram_size_var.get()
        
        # Show/hide custom size input
        if size_type == "custom":
            self.custom_size_frame.pack(fill=tk.X, padx=40, pady=5)
            # Use custom size value
            self.config_manager.set("zram_size", self.custom_size_var.get())
        else:
            self.custom_size_frame.pack_forget()
            # Use predefined size
            self.config_manager.set("zram_size", size_type)
            
        # Update when custom size changes
        def update_custom_size(*args):
            if self.zram_size_var.get() == "custom":
                self.config_manager.set("zram_size", self.custom_size_var.get())
                
        self.custom_size_var.trace_add("write", update_custom_size)
        
    def validate(self):
        """Validate advanced configuration"""
        # Skip validation if not in advanced mode
        if self.config_manager.get("install_mode") != "advanced":
            return True
            
        # Validate disk encryption passphrase if enabled
        if self.config_manager.get("encrypt_disk") == "yes":
            passphrase = self.config_manager.get("disk_password", "")
            if not passphrase or len(passphrase) < 8:
                messagebox.showerror("Error", "Disk encryption passphrase must be at least 8 characters.")
                return False
                
            # Check if passphrases match
            if passphrase != self.confirm_passphrase_var.get():
                messagebox.showerror("Error", "Disk encryption passphrases do not match.")
                return False
                
        # Validate custom ZRAM size if selected
        if self.zram_size_var.get() == "custom":
            try:
                size = int(self.custom_size_var.get())
                if size <= 0:
                    messagebox.showerror("Error", "ZRAM size must be a positive number.")
                    return False
            except ValueError:
                messagebox.showerror("Error", "ZRAM size must be a valid number.")
                return False
                
        return True


# Installation Frame
class InstallationFrame(BaseInstallerFrame):
    """Installation progress screen"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)
        self.create_widgets()
        
    def create_widgets(self):
        # Installation progress section
        progress_frame = ttk.LabelFrame(self, text="Installation Progress")
        progress_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        
        # Status message
        self.status_var = tk.StringVar(value="Preparing for installation...")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var, font=("Helvetica", 12))
        status_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        if USING_BOOTSTRAP:
            self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, bootstyle="success")
        else:
            self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var)
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # Cancel button
        self.cancel_button = ttk.Button(progress_frame, text="Cancel Installation", 
                                      command=self.cancel_installation)
        self.cancel_button.pack(anchor=tk.E, padx=10, pady=5)
        
        # Log output section
        log_frame = ttk.LabelFrame(self, text="Installation Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a scrolled text widget for logs
        self.log_text = tk.Text(log_frame, height=20, width=80, wrap=tk.WORD,
                             font=("Courier", 10))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Make the log text read-only
        self.log_text.config(state=tk.DISABLED)
        
        # Add initial log message
        self.log_output("Waiting to start installation...")
        
    def update_progress(self, progress, message):
        """Update the progress bar and status message"""
        self.progress_var.set(progress)
        self.status_var.set(message)
        
        # Log the message too
        self.log_output(message)
        
        # Update UI
        self.update_idletasks()
        
        # Disable cancel button if complete
        if progress >= 100:
            self.cancel_button.config(state="disabled")
        
    def log_output(self, message):
        """Add a message to the log output"""
        # Make the text widget editable
        self.log_text.config(state=tk.NORMAL)
        
        # Add timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Add the message with timestamp
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        # Scroll to the end
        self.log_text.see(tk.END)
        
        # Make the text widget read-only again
        self.log_text.config(state=tk.DISABLED)
        
        # Update UI
        self.update_idletasks()
        
    def cancel_installation(self):
        """Cancel the installation process"""
        if messagebox.askyesno("Cancel Installation", 
                         "Are you sure you want to cancel the installation? This cannot be undone."):
            self.app.installer.cancel_installation()
        
    def validate(self):
        """Nothing to validate on this frame"""
        return True