<p align="center">
  <img src="archlinux-logo.png" alt="Arch Logo"/>
</p>

<br>

# Arch installation script

> **Warning** ⚠️
> This script **automatically delete existing partitions on disk**. Anyone who wants to use it should adjust according to their use case. This script was initially created for personal use, and i do not take responsibility for any damage or other issues that may arise from its use. For testing purposes, try first install-vm script for virtual machines.


This script automates the installation of Arch Linux with a custom configuration. It includes setting up LUKS encryption, LVM, Btrfs, and various system configurations.

## Features

- LUKS encryption
- LVM
- Btrfs file system
- CachyOS kernel
- ZRAM 
- Plasma with SDDM
- Systemd-boot
- Open NVIDIA drivers
- Pipewire for audio


## Usage

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/i-use-arch-BTW.git
    cd i-use-arch-BTW
    ```

2. **Make the script executable:**

    ```bash
    chmod +x install.sh
    ```

3. **Run the script:** 🚀

    ```bash
     ./install.sh
    ```
4. **Reboot and enjoy!** 
<br><br>

> **Note**
> The script generates an install log file named `result.log` in the current directory.

> **Note** ⚠️
> Timeshift need to be configured after install in order to snapshot and backup your sistem. 

> **Note** ⚠️
> Script allows sudo privileges with no password. Change it after install.

## Script Details

### Prompt for User and System Settings

The script will prompt you to enter the following details:

- Username
- Password for the user
- Password for the root user
- LUKS volume passphrase
- Hostname

### Partitioning and Formatting

The script will:

- Unmount any mounted partitions
- Check for existing volume groups and physical volumes and remove them if found
- Clean the old partition table and create new partitions
- Set up LUKS encryption and LVM
- Format partitions with Btrfs file system and mount them

### Base System Installation

The script will install the base system and essential packages using `pacstrap`.

### System Configuration

The script will:

- Generate the `fstab` file
- Chroot into the new system and configure basic settings
- Configure mirrors using `reflector`
- Enable Multilib repo
- Configure ZRAM
- Create a user and set passwords
- Configure the `sudoers` file
- Install and configure systemd-boot


### Additional Packages and Services

The script will install additional packages and enable necessary services:

- Install basic utilities and applications
- Install Pipewire audio components
- Install Plasma and SDDM
- Install NVIDIA drivers
- Modify SDDM settings for the theme

### Enabling Services

The script will enable the following services:

- NetworkManager
- SDDM

### Exit Chroot

The script will exit the chroot environment and complete the installation.

## Notes

- Ensure you have a stable internet connection during the installation.
- The script is designed for a specific disk layout and may need adjustments for different setups.

## License

This project is licensed under the MIT License. See the [LICENSE](http://_vscodecontentref_/2) file for details.



