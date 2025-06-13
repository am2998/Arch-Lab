# ZFS Assistant

A modern GTK4 GUI application for managing ZFS snapshots on Linux systems.

## Project Structure

```
zfs-assistant/
├── build-release.sh        # Single comprehensive build script for releases
├── install.sh              # Installation script
├── Makefile                # Build automation
├── setup.py                # Python setup script
├── zfs-assistant.desktop   # Desktop entry file
└── src/                    # Source code directory      
    ├── __init__.py            # Package initialization
    ├── __main__.py            # Entry point for module execution
    ├── application.py         # Main application class
    ├── zfs_assistant.py       # Core ZFS operations
    ├── core/                  # Core ZFS operations
    ├── backup/                # Backup and restore functionality
    ├── system/                # System integration and maintenance
    ├── ui/                    # User interface components
    │   ├── windows/           # Main application windows
    │   ├── dialogs/           # Modal dialog windows
    │   ├── settings/          # Settings-related UI components
    │   └── components/        # Reusable UI components
    └── utils/                 # Common utilities, models, logging
```

## Features

- **Snapshot Management**:
  - List ZFS snapshots graphically
  - Create new snapshots with custom names
  - Delete existing snapshots
  - Roll back to snapshots
  - Clone snapshots to new datasets
  - Automatically clean up old snapshots based on retention policies

- **Dataset Properties**:
  - View ZFS dataset flags and properties
  - Monitor ZFS pool status

- **Modern UI**:
  - Built with GTK4 and libadwaita
  - Adaptive design
  - Dark mode support

## Installation

### AppImage (Recommended)

The easiest way to install ZFS Assistant is using the provided AppImage:

```bash
# Clone the repository
git clone https://github.com/am2998/Arch-Lab.git
cd Arch-Lab/zfs-assistant

# Build the release AppImage (requires Linux)
make release

# Install to user directory (~/.local/bin)
make install

# Or install system-wide (/usr/local/bin) with polkit integration
sudo make install-system
```

When installing system-wide, the installer will automatically:
- Install the polkit policy for seamless authentication
- Set up the application to request admin privileges when needed
- Configure proper desktop integration

The release build creates:
- `release/ZFS-Assistant-0.1.0-x86_64.AppImage` - The main AppImage
- `release/ZFS-Assistant-0.1.0-x86_64.AppImage.sha256` - SHA256 checksum
- `release/ZFS-Assistant-0.1.0-x86_64.AppImage.md5` - MD5 checksum  
- `release/RELEASE_INFO.txt` - Release information and instructions

### Authentication

ZFS Assistant automatically handles authentication for ZFS operations:

- **AppImage**: Prompts for authentication once when starting elevated operations
- **System Install**: Uses polkit for seamless authentication (like Timeshift)
- **Manual Install**: May require running with sudo for ZFS operations

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/am2998/Arch-Lab.git
   cd Arch-Lab/zfs-assistant
   ```

2. Install system dependencies:
   ```bash
   # Arch Linux
   sudo pacman -S gtk4 libadwaita python-gobject python-cairo

   # Ubuntu/Debian
   sudo apt install libgtk-4-dev libadwaita-1-dev python3-gi python3-gi-cairo

   # Fedora
   sudo dnf install gtk4-devel libadwaita-devel python3-gobject python3-cairo
   ```

3. Install Python dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```

4. Install the package:
   ```bash
   pip install -e .
   ```

## Running the Application

### From AppImage

If you installed via AppImage:
```bash
# If installed system-wide
zfs-assistant

# Or run the AppImage directly
./ZFS-Assistant-0.1.0-x86_64.AppImage
```

### From Development Environment

For local development and testing:

```bash
# Clone and enter the repository
git clone https://github.com/am2998/Arch-Lab.git
cd Arch-Lab/zfs-assistant

# Set up virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r src/requirements.txt

# Run with automatic privilege escalation
python -m src

# Or run with explicit sudo (alternative)
sudo python -m src

# For debugging without privilege prompts
DEBUG=1 python -m src --no-elevated
```

The application will automatically:
- Detect if it needs elevated privileges
- Prompt for authentication using pkexec (if available)
- Fall back to sudo instructions if pkexec is not available
- Handle both development and production environments seamlessly

### From Desktop Entry

After installation, you can launch "ZFS Assistant" from your application menu.

### From Command Line

If installed as a Python package:
```bash
zfs-assistant
```

Running as Python module:
```bash
python -m zfs_assistant
```

Running directly from source:
```bash
cd /path/to/zfs-assistant/src
python __main__.py
```

## Development Setup

For developers who want to contribute or test locally:

```bash
# Clone the repository
git clone https://github.com/am2998/Arch-Lab.git
cd Arch-Lab/zfs-assistant

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r src/requirements.txt

# Test the privilege system (optional)
python test_privileges.py

# Run the application in development mode
python -m src
```

### Development Notes

- The application automatically detects development vs. production environments
- In development, it will use `pkexec` for privilege escalation when needed
- If `pkexec` is not available, it will provide instructions to run with `sudo`
- Use `DEBUG=1` environment variable for verbose logging
- Use `--no-elevated` flag to skip privilege escalation for UI testing

## Building AppImage

To build your own release-ready AppImage:

```bash
# Make sure you're on a Linux system
chmod +x build-release.sh
./build-release.sh

# Or use the Makefile
make release

# The AppImage and checksums will be created in release/
```

The build script performs:
- Pre-flight checks for dependencies
- Creates proper directory structure
- Installs Python dependencies 
- Creates desktop integration files
- Generates high-quality icons
- Builds and tests the AppImage
- Creates checksums and release info

## Prerequisites

- **Linux system** (for AppImage building and ZFS)
- **Python 3.8+**
- **GTK4** (>= 4.0.0)
- **libadwaita** (>= 1.0.0)
- **ZFS utilities** (zfs-utils or equivalent)
- **PyGObject** (>= 3.42.0)
- **pycairo** (>= 1.20.0)

## Troubleshooting

### AppImage Issues

1. **AppImage won't run**: Make sure it's executable:
   ```bash
   chmod +x ZFS-Assistant-*.AppImage
   ```

2. **Missing dependencies**: The AppImage should be self-contained, but system GTK4/libadwaita libraries are required.

### General Issues

1. **Permission errors**: Make sure your user is in the appropriate groups for ZFS access:
   ```bash
   sudo usermod -a -G disk $USER
   # Logout and login again
   ```

2. **ZFS not found**: Ensure ZFS is installed and loaded:
   ```bash
   sudo modprobe zfs
   zfs version
   ```

3. **Python dependencies**: If running from source, install dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```
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
