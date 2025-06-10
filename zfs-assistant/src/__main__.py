#!/usr/bin/env python3
# ZFS Assistant - Main entry point
# Author: am2998

"""
Main entry point for the ZFS Assistant application.
This file enables running the application with 'python -m src'.
"""

import os
import sys

# Get absolute path to the current directory and its parent
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add both to the Python path to ensure imports work
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Print paths for debugging
print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path}")

# Try importing the application
try:
    # Try direct import first
    from application import Application
except ImportError as e:
    print(f"Direct import failed: {e}")
    try:
        # Try with src prefix
        from src.application import Application
    except ImportError as e:
        print(f"Import from src failed: {e}")
        sys.exit(1)

def main():
    print("Starting ZFS Assistant...")
    app = Application()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
