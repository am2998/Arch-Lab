# 🚀 Basic Arch Linux Installation Script

This script automates the Arch Linux installation process with sensible defaults for a quick and straightforward setup.

## 📋 Prerequisites

- 💿 A bootable Arch Linux installation media
- 🌐 Working internet connection
- 💻 Basic knowledge of Linux commands

## 🔧 How to Use This Script

Follow these steps to use this basic installation script:

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
cd Arch-Lab/arch-scripts/basic
```

### 4. Run the Basic Installation Script ⚙️

Execute the basic installation script:
```bash
chmod +x install-<MODE>.sh
./install-<MODE>.sh
```

The script will perform a standard Arch Linux installation.
## 🤝 Contributing

Contributions to improve this script are welcome. Please submit issues or pull requests through GitHub.
