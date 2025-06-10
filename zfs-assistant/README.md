# ZFS Assistant for Arch Linux

A GTK GUI application for managing ZFS snapshots on Arch Linux.

## Project Structure

```
zfs-assistant/
├── PKGBUILD          # Arch Linux package build script
├── .SRCINFO          # AUR package metadata
├── setup.py          # Python setup script for installation
├── zfs-assistant.py  # Launcher script for direct execution
└── src/              # Source code directory      
    ├── __init__.py      # Package initialization
    ├── __main__.py      # Entry point for module execution
    ├── application.py   # Main application class
    ├── zfs_assistant.py # Core ZFS operations
    ├── models.py        # Data models
    ├── ui_*.py          # UI components
    └── requirements.txt # Python dependencies
```

## Features

- **Snapshot Management**:
  - List ZFS snapshots graphically
  - Create new snapshots
  - Delete existing snapshots
  - Roll back to snapshots
  - Clone snapshots to new datasets
  - Automatically clean up old snapshots based on retention policies

- **Dataset Properties**:
  - View ZFS dataset flags and properties

## Installation

### From AUR (Recommended)

```bash
yay -S zfs-assistant
# or
paru -S zfs-assistant
```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/am2998/Arch-Lab.git
   cd Arch-Lab/zfs-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

## Running the Application

After installation, you can run the application in several ways:

### Using the Desktop Entry

If installed from AUR, simply search for "ZFS Assistant" in your application menu.

### From the Command Line

If installed as a package:
```bash
zfs-assistant
```

Using Python module syntax:
```bash
python -m zfs_assistant
```

Running directly from the repository:
```bash
cd /path/to/zfs-assistant
python zfs-assistant.py
```

## Troubleshooting

If you encounter any issues with running the application, try the following:

1. Make sure all dependencies are installed:
   ```bash
   pip install -r src/requirements.txt
   ```

2. If running as a module fails, try the direct launcher:
   ```bash
   python zfs-assistant.py
   ```

3. Check your Python version (requires Python 3.6+):
   ```bash
   python --version
   ```

4. For permission issues when managing ZFS pools, make sure you're running with appropriate privileges:
   ```bash
   sudo zfs-assistant
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
