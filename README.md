# 🧪 Arch-Lab

This is a personal repository created to make Arch Linux code experiments.

## 📂 Repository Structure

### 🐧 arch-scripts

Contains various Arch Linux installation scripts:

- **basic/** - Core installation scripts with different priorities:
  - `install-fast.sh` - Performance-oriented installation using EFISTUB and ext4 filesystem
  - `install-reliable.sh` - Reliability-focused installation using ZFS filesystem (with ZFSBootMenu)
  - `install-secure+stable.sh` - Hardened installation with LVM, BTRFS and LUKS encryption for security and stability

- **flexible/** - Customizable installation options:
  - `install-flexible.sh` - Adaptable installation script with more configuration options
  - `README.md` - Documentation for the flexible installation process

### ⚙️ configs

Contains configuration files for various applications:

- **arkenfox/** - Firefox privacy and security configurations
  - `user.js` - Hardened Firefox settings

- **fastfetch/** - System information display tool configurations
  - `config.jsonc` - Custom Fastfetch appearance settings

- **kitty/** - Terminal emulator configurations
  - `kitty.conf` - Kitty terminal settings and customizations

- **system-maintenance/** - System maintenance automation
  - `maintenance.md` - Documentation for setting up automated system maintenance
  - `maintenance.sh` - Script for ZFS snapshots, system updates, and cleanup tasks

### 🔧 zfs-assistant

A GTK GUI application for managing ZFS snapshots on Arch Linux:

- Modern GTK4 and libadwaita interface for ZFS management
- Create, delete, and roll back to snapshots
- Schedule automatic snapshots using systemd timers
- View ZFS dataset properties
- Pacman integration for pre-install/remove snapshots
- System updates integration for scheduled snapshots

---

*Feel free to explore and use these configurations and scripts for your own Arch Linux installations.*
