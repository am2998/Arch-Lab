#!/usr/bin/env python3
"""
Arch Linux Flexible Installation GUI
A graphical user interface for the Arch Linux installation process.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import json

# Try to import ttkbootstrap, fallback to ttk if not available
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    USING_BOOTSTRAP = True
except ImportError:
    import tkinter.ttk as ttk
    USING_BOOTSTRAP = False

# Import our custom modules
from installer_app import InstallerApp

if __name__ == "__main__":
    # Create root window with ttkbootstrap if available
    if USING_BOOTSTRAP:
        root = ttk.Window(
            title="Arch Linux Flexible Installer",
            themename="darkly",
            size=(1024, 768),
            minsize=(800, 600),
            resizable=(True, True),
            iconphoto="",
        )
    else:
        root = tk.Tk()
        root.title("Arch Linux Flexible Installer")
        root.geometry("1024x768")
        root.minsize(800, 600)
    
    # Create and run the installer application
    app = InstallerApp(root)
    root.mainloop()