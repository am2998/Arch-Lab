# Flexible Arch Linux Installation Script

This script automates the Arch Linux installation process while allowing you to customize various aspects of the installation.

## Prerequisites

- A bootable Arch Linux installation media
- Internet connection
- Basic knowledge of Linux commands

## 🌐 Setting Up Network Connection 

Before running the installation script, you must set up your network connection using `iwctl` (iwd - iNet wireless daemon). This is required for downloading packages during installation.

### Using iwctl to Connect to WiFi 📡

1. Start the interactive prompt:
   ```bash
   iwctl
   ```

2. List all available wireless devices:
   ```
   [iwd]# device list
   ```
   You should see your wireless adapter (e.g., wlan0)

3. Scan for networks:
   ```
   [iwd]# station wlan0 scan
   ```

4. List available networks:
   ```
   [iwd]# station wlan0 get-networks
   ```

5. Connect to your network:
   ```
   [iwd]# station wlan0 connect "Your-Network-SSID"
   ```
   You will be prompted for the network password

6. Exit the iwctl prompt:
   ```
   [iwd]# exit
   ```

7. Verify your connection:
   ```bash
   ping -c 3 archlinux.org
   ```

### 🔐 Example for Connecting to Hidden Network 

```bash
iwctl
[iwd]# device list
[iwd]# station wlan0 scan
[iwd]# station wlan0 connect-hidden "Your-Hidden-SSID"
[iwd]# exit
```

## 🚀 Running the Installation Script 

Once you have confirmed your internet connection is working, you can run the installation script:

```bash
./install-flexible.sh
```

The script will guide you through the installation process with various options for:
- Disk partitioning
- File system selection
- Desktop environment options
- Package selection
- User creation

## Customization Options

The script provides several customization options which will be presented during execution. Follow the on-screen prompts to tailor your installation.

## Troubleshooting

If you encounter network issues, try the following:
- Ensure your wireless device is not blocked: `rfkill unblock all`
- For wired connections, use: `dhcpcd`
- For more complex network setups, refer to the [Arch Wiki Network Configuration](https://wiki.archlinux.org/title/Network_configuration)

## ZFS Management Commands (Post Installation)

Here are some useful ZFS commands for managing snapshots, rollbacks, and send/receive operations:

### 📸 Snapshot Operations
```bash
# Create a snapshot of a ZFS dataset
zfs snapshot pool/dataset@snapshotname

# List all snapshots
zfs list -t snapshot

# List snapshots for a specific dataset
zfs list -t snapshot pool/dataset
```

### 🔄 Rollback Operations
```bash
# Rollback to a specific snapshot 
zfs rollback pool/dataset@snapshotname

# Rollback and destroy more recent snapshots with -r 
zfs rollback -r pool/dataset@snapshotname
```

### 📤 Send/Receive Operations
```bash
# Send a snapshot to a file 
zfs send pool/dataset@snapshotname > /path/to/backup.zfs

# Send a snapshot to another system
zfs send pool/dataset@snapshotname | ssh user@remote "zfs receive tank/dataset"

# Send an incremental snapshot 
zfs send -i pool/dataset@snap1 pool/dataset@snap2 | ssh user@remote "zfs receive tank/dataset"

# Send a replication stream (all snapshots between two points) 
zfs send -R pool/dataset@snapshotname | ssh user@remote "zfs receive -F tank/dataset"
```

### ⚙️ Common ZFS Management
```bash
# Check ZFS pool status 🔍
zpool status

# Scrub a pool to check for data integrity 🧹
zpool scrub pool_name

# List ZFS properties
zfs get all pool/dataset
```

## Contributing

Contributions to improve this script are welcome. Please submit issues or pull requests through GitHub.
