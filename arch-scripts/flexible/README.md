# 🚀 Flexible Arch Linux Installation Script

This script automates the Arch Linux installation process while allowing you to customize various aspects of the installation.

## 📋 Prerequisites

- 💿 A bootable Arch Linux installation media (it's suggested to use a custom ZFS-enabled image like the one from https://github.com/r-maerz/archlinux-lts-zfs)
- 🌐 Working internet connection
- 💻 Basic knowledge of Linux commands

## 🔧 How to Use This Script

Follow these steps to use this flexible installation script:

### 1. Boot Into Arch Linux Live Environment 💻

Boot your computer using the Arch Linux installation media. 

### 2. Connect to the Internet 🌐

#### For Wired Connection
If you're using a wired connection, it should work automatically. Verify with:
```bash
ping -c 3 archlinux.org
```

#### For Wireless Connection
If you need to connect to WiFi, use the `iwctl` command:
```bash
iwctl station wlan0 connect "Your-Network-SSID"
```
Enter your password when prompted. Replace `wlan0` with your actual wireless device name.

### 3. Clone the Repository 📥

Clone this repository to get the installation scripts:
```bash
pacman -Sy git --noconfirm
git clone https://github.com/yourusername/Arch-Lab.git
cd Arch-Lab/arch-scripts/flexible
```

### 4. Run the Flexible Installation Script ⚙️

Execute the flexible installation script:
```bash
chmod +x install.sh
./install.sh
```

The script will guide you through the installation process, allowing you to customize various aspects of your Arch Linux installation.

### 5. Follow the Interactive Prompts 🖥️

The flexible script will present you with multiple options for:
- Disk partitioning and filesystem setup
- Desktop environment selection
- Additional packages installation
- System configuration options

Choose the options that best suit your needs.

## 📊 ZFS Management Commands (Post Installation)

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

## 🤝 Contributing

Contributions to improve this script are welcome. Please submit issues or pull requests through GitHub.
