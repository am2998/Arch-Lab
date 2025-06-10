#!/usr/bin/env python3
# ZFS Assistant - Main entry point
# Author: am2998

"""
Main entry point for the ZFS Assistant application.
This file enables running the application with 'python -m zfs_assistant'.
"""

import os
import sys

# Try importing directly from the package first
try:
    from .application import Application
except ImportError:
    # If running as a script, add parent directory to path for absolute imports
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    try:
        # Try with src as a direct submodule
        from src.application import Application
    except ImportError:
        # Last resort, use direct file path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        from application import Application

def main():
    app = Application()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
