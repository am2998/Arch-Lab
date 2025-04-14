#!/bin/bash

# LVM + BTRFS + EFISTUB 
# COSMIC

cat <<'EOF'
 ______                                             ______                       __              _______   ________  __       __ 
/      |                                           /      \                     /  |            /       \ /        |/  |  _  /  |
$$$$$$/        __    __   _______   ______        /$$$$$$  |  ______    _______ $$ |____        $$$$$$$  |$$$$$$$$/ $$ | / \ $$ |
  $$ |        /  |  /  | /       | /      \       $$ |__$$ | /      \  /       |$$      \       $$ |__$$ |   $$ |   $$ |/$  \$$ |
  $$ |        $$ |  $$ |/$$$$$$$/ /$$$$$$  |      $$    $$ |/$$$$$$  |/$$$$$$$/ $$$$$$$  |      $$    $$<    $$ |   $$ /$$$  $$ |
  $$ |        $$ |  $$ |$$      \ $$    $$ |      $$$$$$$$ |$$ |  $$/ $$ |      $$ |  $$ |      $$$$$$$  |   $$ |   $$ $$/$$ $$ |
 _$$ |_       $$ \__$$ | $$$$$$  |$$$$$$$$/       $$ |  $$ |$$ |      $$ \_____ $$ |  $$ |      $$ |__$$ |   $$ |   $$$$/  $$$$ |
/ $$   |      $$    $$/ /     $$/ $$       |      $$ |  $$ |$$ |      $$       |$$ |  $$ |      $$    $$/    $$ |   $$$/    $$$ |
$$$$$$/        $$$$$$/  $$$$$$$/   $$$$$$$/       $$/   $$/ $$/        $$$$$$$/ $$/   $$/       $$$$$$$/     $$/    $$/      $$/ 
                                                                                                                                 
EOF


exec > >(tee -a result.log) 2>&1


# --------------------------------------------------------------------------------------------------------------------------
# Prompt for user and system settings                                                                                      
# --------------------------------------------------------------------------------------------------------------------------

get_password() {
    local prompt=$1
    local password_var
    local password_recheck_var

    while true; do
        echo -n "$prompt: "; read -r -s password_var; echo
        echo -n "Re-enter password: "; read -r -s password_recheck_var; echo
        if [ "$password_var" = "$password_recheck_var" ]; then
            eval "$2='$password_var'"
            break
        else
            echo "Passwords do not match. Please enter a new password."
        fi
    done
}

echo -ne "\n\nEnter the username: "; read -r USER
get_password "Enter the password for user $USER" USERPASS
get_password "Enter the password for user root" ROOTPASS
echo -n "Enter the hostname: "; read -r HOSTNAME


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Check if there are existing PV and VG"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

umount -R /mnt 2>/dev/null
VG_NAME=$(vgdisplay -c | cut -d: -f1 | xargs)

if [ -z "$VG_NAME" ]; then
    echo -e "No volume group found. Skipping VG removal."
else
    echo -e "Removing volume group ${VG_NAME} and all associated volumes..."
    yes | vgremove "$VG_NAME" 2>/dev/null
    PV_NAME=$(pvs --noheadings -o pv_name | grep -w "$VG_NAME" | xargs)
    yes | pvremove "$PV_NAME" 2>/dev/null
fi


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Cleaning old partition table and partitioning"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

if lsblk | grep nvme &>/dev/null; then
    DISK="/dev/nvme0n1"
    PARTITION_1="p1"
    PARTITION_2="p2"
    echo "NVMe disk detected: $DISK"
elif lsblk | grep sda &>/dev/null; then
    DISK="/dev/sda"
    PARTITION_1="1"
    PARTITION_2="2"
    echo "SATA disk detected: $DISK"
else 
    echo "ERROR: No NVMe or SATA drive found. Exiting."
    exit 1
fi

wipefs -a -f $DISK 

(
echo g           # Create a GPT partition table
echo n           # Create the EFI partition
echo             # Default, 1
echo             # Default
echo +1G         # 1GB for the EFI partition
echo t           # Change partition type to EFI
echo 1           # EFI type
echo n           # Create the system partition
echo             # Default, 2
echo             # Default
echo             # Default, use the rest of the space
echo w           # Write the partition table
) | fdisk $DISK



echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# LVM"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

pvcreate --dataalignment 1m ${DISK}${PARTITION_2}
vgcreate sys ${DISK}${PARTITION_2}
yes | lvcreate -l 100%FREE -n root sys


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Format and mount partitions"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

mkfs.fat -F32 ${DISK}${PARTITION_1}  
mkfs.btrfs -f /dev/sys/root
mount /dev/sys/root /mnt
btrfs subvolume create /mnt/@
btrfs subvolume create /mnt/@home
btrfs subvolume create /mnt/@var
umount /mnt

mount -o noatime,ssd,compress=zstd,space_cache=v2,subvol=@ /dev/sys/root /mnt
mkdir -p /mnt/{home,var}
mount -o noatime,ssd,compress=zstd,space_cache=v2,subvol=@home /dev/sys/root /mnt/home
mount -o noatime,ssd,compress=zstd,space_cache=v2,subvol=@var /dev/sys/root /mnt/var

mkdir -p /mnt/boot && mount ${DISK}${PARTITION_1} /mnt/boot


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Install base system"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

pacstrap /mnt linux-zen linux-zen-headers base base-devel linux-firmware lvm2 btrfs-progs zram-generator reflector sudo networkmanager intel-ucode efibootmgr


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Generate fstab file"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

genfstab -U /mnt >> /mnt/etc/fstab
echo -e "\nFstab file generated:\n"
cat /mnt/etc/fstab
echo -e "\n"


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Chroot into the system and configure"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

env DISK=$DISK arch-chroot /mnt <<EOF

echo -e "in chroot...\n\n"

# --------------------------------------------------------------------------------------------------------------------------
# Configure mirrors
# --------------------------------------------------------------------------------------------------------------------------

reflector --country "Italy" --latest 10 --sort rate --protocol https --age 7 --save /etc/pacman.d/mirrorlist
echo -e "\nMirrors configured:\n"
cat /etc/pacman.d/mirrorlist
echo -e "\n"


# --------------------------------------------------------------------------------------------------------------------------
# Enable Multilib repository
# --------------------------------------------------------------------------------------------------------------------------

sed -i '/\[multilib\]/,/Include/ s/^#//' /etc/pacman.conf
pacman -Syy


# --------------------------------------------------------------------------------------------------------------------------
# Configure ZRAM
# --------------------------------------------------------------------------------------------------------------------------

bash -c 'cat > /etc/systemd/zram-generator.conf <<EOF
[zram0]
zram-size = min(ram, 32768)
compression-algorithm = zstd
EOF'

echo "vm.swappiness = 180" >> /etc/sysctl.d/99-vm-zram-parameters.conf
echo "vm.watermark_boost_factor = 0" >> /etc/sysctl.d/99-vm-zram-parameters.conf
echo "vm.watermark_scale_factor = 125" >> /etc/sysctl.d/99-vm-zram-parameters.conf
echo "vm.page-cluster = 0" >> /etc/sysctl.d/99-vm-zram-parameters.conf

sysctl --system


# --------------------------------------------------------------------------------------------------------------------------
# EFI Stub
# --------------------------------------------------------------------------------------------------------------------------
efibootmgr --create --disk $DISK --part 1 --label "Arch Linux" --loader /vmlinuz-linux-zen --unicode "root=UUID=$(blkid -s UUID -o value /dev/sys/root) rootfstype=btrfs rootflags=subvol=@ rw initrd=\initramfs-linux-zen.img"


# --------------------------------------------------------------------------------------------------------------------------
# Configure mkinitcpio
# --------------------------------------------------------------------------------------------------------------------------

sed -i 's/^HOOKS=.*/HOOKS=(systemd autodetect microcode modconf kms keyboard keymap block filesystems lvm2)/' /etc/mkinitcpio.conf
mkinitcpio -P


# --------------------------------------------------------------------------------------------------------------------------
# Install utilities and applications
# --------------------------------------------------------------------------------------------------------------------------

pacman -S --noconfirm net-tools flatpak firefox git man nano vi lite-xl rclone cronie snapper


# --------------------------------------------------------------------------------------------------------------------------
# Install Cosmic
# --------------------------------------------------------------------------------------------------------------------------

pacman -S --noconfirm cosmic
systemctl enable cosmic-greeter


# --------------------------------------------------------------------------------------------------------------------------
# System setup
# --------------------------------------------------------------------------------------------------------------------------

echo "$HOSTNAME" > /etc/hostname

localectl set-keymap --no-convert us

ln -sf /usr/share/zoneinfo/Europe/Rome /etc/localtime

hwclock --systohc

timedatectl set-ntp true

sed -i '/^#en_US.UTF-8/s/^#//g' /etc/locale.gen && locale-gen

echo -e "127.0.0.1   localhost\n::1         localhost\n127.0.1.1   $HOSTNAME.localdomain   $HOSTNAME" > /etc/hosts


# --------------------------------------------------------------------------------------------------------------------------
# Create user and set passwords
# --------------------------------------------------------------------------------------------------------------------------

useradd -m $USER
echo "$USER:$USERPASS" | chpasswd
echo "root:$ROOTPASS" | chpasswd


# --------------------------------------------------------------------------------------------------------------------------
# Configure sudoers file
# --------------------------------------------------------------------------------------------------------------------------

echo -e "\n\n%$USER ALL=(ALL:ALL) ALL" | tee -a /etc/sudoers
echo -e "\nSudoers file configured"

# --------------------------------------------------------------------------------------------------------------------------
# Manage services
# --------------------------------------------------------------------------------------------------------------------------

systemctl enable NetworkManager
systemctl enable cronie
systemctl disable ldconfig.service
systemctl disable geoclue
systemctl mask geoclue


EOF


# --------------------------------------------------------------------------------------------------------------------------
# Umount and reboot
# --------------------------------------------------------------------------------------------------------------------------

umount -R /mnt
reboot
