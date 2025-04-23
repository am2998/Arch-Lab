#!/bin/bash
# Arch Linux GUI Installer Launcher
# This script launches the GUI installer application

# Detect the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check for dependencies
check_dependencies() {
  echo "Checking dependencies..."
  
  # Check if python is installed
  if ! command -v python &> /dev/null; then
    echo "Python not found! Please install Python 3.6 or later."
    exit 1
  fi
  
  # Check if pip is installed
  if ! command -v pip &> /dev/null; then
    echo "pip not found! Please install pip."
    exit 1
  fi
  
  # Install required Python packages
  echo "Installing required Python packages..."
  pip install --user -r "$SCRIPT_DIR/requirements.txt"
}

# Run the installer
run_installer() {
  echo "Starting Arch Linux GUI Installer..."
  cd "$SCRIPT_DIR"
  python "$SCRIPT_DIR/main.py"
}

# Main
echo "Arch Linux GUI Installer"
echo "========================"

# Check if running with root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root to perform installation."
  echo "Launching in demo mode (installation features will be limited)."
  check_dependencies
  run_installer
else
  check_dependencies
  run_installer
fi