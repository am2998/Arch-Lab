# ZFS Manager for Arch Linux

A GTK GUI application for managing ZFS snapshots on Arch Linux.

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
  - Properties grouped by category (Storage, Configuration, Security)
  - Interactive property values

- **Automated Snapshots**:
  - Schedule automatic snapshots using systemd timers
  - Configurable hourly, daily, weekly, and monthly schedules
  - Set retention policies for each schedule type

- **Pacman Integration**:
  - Create snapshots before each pacman command
  - Automatic pacman hook management

- **User Interface**:
  - Modern GTK4 and libadwaita interface
  - Dark mode support
  - System notifications for important operations
  - Tabbed interface for snapshots and dataset properties

- **Configuration**:
  - Import/export configuration
  - Customize snapshot naming prefix
  - Enable/disable features as needed

## Requirements

- Arch Linux
- ZFS packages installed (`zfs-dkms`, `zfs-utils`)
- Python 3.6+
- GTK 4.0+
- libadwaita

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/zfs-manager.git
   cd zfs-manager
   ```

2. Run the application:
   ```
   python main.py
   ```

## Usage

### Managing Snapshots

1. Select a dataset from the dropdown or choose "All Datasets"
2. View existing snapshots in the list
3. Use the "Create Snapshot" button to create a new snapshot
4. Select a snapshot and use the action buttons to:
   - Roll back to the selected snapshot
   - Clone the snapshot to a new dataset
   - Delete the snapshot

### Scheduled Snapshots

1. Open Settings → Schedule
2. Enable automatic snapshots
3. Select which schedules you want (hourly, daily, weekly, monthly)
4. Set retention policy for each schedule type

### Dataset Properties

1. Select a specific dataset from the dropdown
2. Switch to the "Dataset Properties" tab
3. Browse properties organized by category

### Pacman Integration

1. Open Settings → Pacman Integration
2. Enable or disable automatic snapshots before pacman operations

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
