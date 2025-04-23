#!/usr/bin/env python3
"""
Configuration Manager for the Arch Linux Installer GUI
Handles saving, loading, and managing configuration settings
"""
import os
import json
import tempfile

class ConfigManager:
    """
    Manages configuration settings for the installation process
    """
    def __init__(self):
        """Initialize the configuration manager"""
        self.config = {
            # Install mode (simple or advanced)
            "install_mode": "simple",
            
            # System configuration
            "hostname": "archlinux",
            "keyboard_layout": "us",
            "locale": "en_US.UTF-8",
            "mirror_country": "",  # Empty for worldwide
            
            # User configuration
            "username": "",
            "user_password": "",
            "root_password": "",
            
            # Hardware configuration
            "cpu_type": "AMD",  # AMD or Intel
            "cpu_microcode": "amd-ucode",  # amd-ucode or intel-ucode
            "gpu_type": "AMD/Intel",  # NVIDIA, AMD/Intel, or None/VM
            "nvidia_driver_type": "none",  # Proprietary, Open, or none
            
            # Desktop configuration
            "desktop_environment": "Hyprland",  # Hyprland, XFCE4, KDE Plasma, GNOME
            "audio_server": "pipewire",  # pipewire or pulseaudio
            
            # Advanced options
            "encrypt_disk": "no",  # yes or no
            "disk_password": "",
            "zfs_compression": "lz4",  # lz4, zstd, gzip, off
            "separate_datasets": "yes",  # yes or no
            "zram_size": "min(ram, 32768)",
            "zram_compression": "zstd",  # zstd, lz4, lzo-rle, lzo
            
            # Installation device and partition info
            "device": "",  # e.g., /dev/sda
            "boot_type": "efi",  # efi or bios
            "efi_part_size": "1G",
            "root_part_size": "MAX"
        }
        
        # Path to temporary config file
        self.temp_dir = tempfile.gettempdir()
        self.config_path = os.path.join(self.temp_dir, "archlinux_installer_config.json")
        
        # Load existing configuration if available
        self.load_config()
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Set a configuration value"""
        self.config[key] = value
        self.save_config()
        
    def update(self, values):
        """Update multiple configuration values at once"""
        self.config.update(values)
        self.save_config()
    
    def save_config(self):
        """Save the configuration to a temporary file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def load_config(self):
        """Load configuration from the temporary file if it exists"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    def get_bash_export_commands(self):
        """
        Generate bash export commands for all configuration settings
        This is used to pass configuration to the installation script
        """
        commands = []
        
        # Map our config keys to the bash script variables
        mapping = {
            "hostname": "HOSTNAME",
            "keyboard_layout": "KEYBOARD_LAYOUT",
            "locale": "SYSTEM_LOCALE", 
            "mirror_country": "MIRROR_COUNTRY",
            "username": "USER",
            "user_password": "USERPASS",
            "root_password": "ROOTPASS",
            "cpu_type": "CPU_TYPE",
            "cpu_microcode": "CPU_MICROCODE",
            "gpu_type": "GPU_TYPE",
            "nvidia_driver_type": "NVIDIA_DRIVER_TYPE",
            "desktop_environment": "DE_TYPE",
            "audio_server": "AUDIO_SERVER",
            "install_mode": "INSTALL_MODE",
            "encrypt_disk": "ENCRYPT_DISK",
            "disk_password": "DISK_PASSWORD",
            "zfs_compression": "ZFS_COMPRESSION",
            "separate_datasets": "SEPARATE_DATASETS",
            "zram_size": "ZRAM_SIZE",
            "zram_compression": "ZRAM_COMPRESSION",
            "device": "DEVICE",
            "boot_type": "BOOT_TYPE",
            "efi_part_size": "EFI_PART_SIZE",
            "root_part_size": "ROOT_PART_SIZE"
        }
        
        # Special case for DE_CHOICE (desktop environment choice number)
        de_choices = {"Hyprland": 1, "XFCE4": 2, "KDE Plasma": 3, "GNOME": 4}
        commands.append(f"export DE_CHOICE={de_choices.get(self.get('desktop_environment'), 1)}")
        
        # Add export commands for all mapped variables
        for key, bash_var in mapping.items():
            value = self.get(key, "")
            # Properly quote the value to handle spaces and special characters
            if isinstance(value, str):
                commands.append(f"export {bash_var}='{value}'")
            else:
                commands.append(f"export {bash_var}={value}")
        
        return commands
    
    def save_all(self):
        """Save all configuration and generate the final export commands"""
        self.save_config()
        return self.get_bash_export_commands()