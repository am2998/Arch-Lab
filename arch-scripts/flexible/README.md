# 🚀 Flexible Arch Linux Installation Script

This script automates the Arch Linux installation process while allowing you to customize various aspects of the installation.

## 📋 Prerequisites

- 💿 A bootable Arch Linux installation media
- 🌐 Working internet connection
- 💻 Basic knowledge of Linux commands

## 🔌 Remote Installation via SSH

You can perform the installation remotely by connecting to the target machine via SSH. This approach is useful for headless setups or remote management.

### 1. Setting Up Network Connection 🌐

> **Note:** This step is only for WiFi connections. Skip to step 2 if using a wired connection.

#### Using iwctl to Connect to WiFi 📡

1. **Start the interactive prompt:**
   ```bash
   iwctl
   ```

2. **List all available wireless devices:**
   ```bash
   [iwd]# device list
   ```
   You should see your wireless adapter (e.g., wlan0)

3. **Scan for networks:**
   ```bash
   [iwd]# station wlan0 scan
   ```

4. **List available networks:**
   ```bash
   [iwd]# station wlan0 get-networks
   ```

5. **Connect to your network:**
   ```bash
   [iwd]# station wlan0 connect "Your-Network-SSID"
   ```
   You will be prompted for the network password

6. **Exit the iwctl prompt:**
   ```bash
   [iwd]# exit
   ```

7. **Verify your connection:**
   ```bash
   ping -c 3 archlinux.org
   ```

### 2. Enable SSH on the Target Machine 🔐

Boot the target machine using the Arch Linux installation media and set a root password:

```bash
passwd
```

Start the SSH service:

```bash
systemctl start sshd
```

Find the IP address of the target machine:

```bash
ip addr show
```

### 3. Connect from Your Local Machine 🖥️

Connect to the target machine from your local computer:

```bash
ssh root@TARGET_IP_ADDRESS
```

### 4. Transfer the Installation Script 📤

There are several ways to transfer the script to the target machine:

#### Using SCP (from your local machine):

```bash
scp /path/to/install-flexible.sh root@TARGET_IP_ADDRESS:/root/
```

### 5. Make the Script Executable and Run It 🚀

On the target machine, make the script executable and run it:

```bash
chmod +x install-flexible.sh
./install-flexible.sh
```

---

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
