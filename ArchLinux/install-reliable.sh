#!/bin/bash

# ZFS + ZFS BOOTMENU

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


exec >(tee -a result.log) 2>&1


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
echo -e "# Format and mount partitions"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

zpool create \
    -o ashift=12 \
    -O acltype=posixacl -O canmount=off -O compression=lz4 \
    -O dnodesize=auto -O normalization=formD -o autotrim=on \
    -O atime=off -O xattr=sa -O mountpoint=none \
    -R /mnt zroot ${DISK}${PARTITION_2} -f
echo "ZFS pool created successfully."

zfs create -o canmount=noauto -o mountpoint=/ zroot/rootfs
echo "ZFS dataset created successfully."

zpool set bootfs=zroot/rootfs zroot
echo "bootfs property set successfully."

zfs mount zroot/rootfs

mkdir -p  /mnt/etc/zfs
zpool set cachefile=/etc/zfs/zpool.cache zroot
cp /etc/zfs/zpool.cache /mnt/etc/zfs/zpool.cache

mkfs.fat -F32 ${DISK}${PARTITION_1}   
mkdir -p /mnt/efi && mount ${DISK}${PARTITION_1} /mnt/efi


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Install base system"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

pacstrap /mnt linux-lts linux-lts-headers base base-devel linux-firmware efibootmgr zram-generator reflector sudo networkmanager amd-ucode wget


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Generate fstab file"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

genfstab -U /mnt >> /mnt/etc/fstab


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Chroot into the system and configure"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

env DISK=$DISK arch-chroot /mnt <<EOF


# --------------------------------------------------------------------------------------------------------------------------
# Configure mirrors and Enable Network Manager service
# --------------------------------------------------------------------------------------------------------------------------

reflector --country "Italy" --latest 10 --sort rate --protocol https --age 7 --save /etc/pacman.d/mirrorlist
systemctl enable NetworkManager


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Setup ZFS"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

echo -e '
[archzfs]
Server = https://github.com/archzfs/archzfs/releases/download/experimental' >> /etc/pacman.conf

# ArchZFS GPG keys (see https://wiki.archlinux.org/index.php/Unofficial_user_repositories#archzfs)
pacman-key -r DDF7DB817396A49B2A2723F7403BD972F75D9D76
pacman-key --lsign-key DDF7DB817396A49B2A2723F7403BD972F75D9D76

pacman -Sy --noconfirm zfs-dkms
systemctl enable zfs.target zfs-import-cache zfs-mount zfs-import.target


# --------------------------------------------------------------------------------------------------------------------------
# Install ZFSBootMenu
# --------------------------------------------------------------------------------------------------------------------------

mkdir -p /efi/EFI/zbm
wget https://get.zfsbootmenu.org/latest.EFI -O /efi/EFI/zbm/zfsbootmenu.EFI
efibootmgr --disk $DISK --part 1 --create --label "ZFSBootMenu" --loader '\EFI\zbm\zfsbootmenu.EFI' --unicode "spl_hostid=$(hostid) zbm.timeout=3 zbm.prefer=zroot zbm.import_policy=hostid" --verbose
zfs set org.zfsbootmenu:commandline="noresume init_on_alloc=0 rw spl.spl_hostid=$(hostid)" zroot/rootfs


# --------------------------------------------------------------------------------------------------------------------------
# Configure mkinitcpio
# --------------------------------------------------------------------------------------------------------------------------

sed -i 's/\(filesystems\) \(fsck\)/\1 zfs \2/' /etc/mkinitcpio.conf

mkinitcpio -p linux-lts


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
# Enable Multilib repository
# --------------------------------------------------------------------------------------------------------------------------

sed -i '/\[multilib\]/,/Include/ s/^#//' /etc/pacman.conf
pacman -Syy


# --------------------------------------------------------------------------------------------------------------------------
# System config
# --------------------------------------------------------------------------------------------------------------------------

echo "$HOSTNAME" > /etc/hostname

localectl set-keymap --no-convert us

ln -sf /usr/share/zoneinfo/Europe/Rome /etc/localtime

hwclock --systohc

timedatectl set-ntp true

sed -i '/^#en_US.UTF-8/s/^#//g' /etc/locale.gen && locale-gen

echo -e "127.0.0.1   localhost\n::1         localhost\n127.0.1.1   $HOSTNAME.localdomain   $HOSTNAME" > /etc/hosts


# --------------------------------------------------------------------------------------------------------------------------
# Install utilities and Enable services
# --------------------------------------------------------------------------------------------------------------------------

pacman -S --noconfirm net-tools flatpak git man vi nano lite-xl distrobox veracrypt rclone cronie podman
systemctl enable cronie


# --------------------------------------------------------------------------------------------------------------------------
# Install audio components
# --------------------------------------------------------------------------------------------------------------------------

pacman -S --noconfirm pipewire wireplumber pipewire-pulse alsa-plugins alsa-firmware sof-firmware alsa-card-profiles pavucontrol-qt


# --------------------------------------------------------------------------------------------------------------------------
# Install NVIDIA drivers
# --------------------------------------------------------------------------------------------------------------------------

pacman -S --noconfirm nvidia-open-lts nvidia-settings nvidia-utils opencl-nvidia libxnvctrl


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


EOF


# --------------------------------------------------------------------------------------------------------------------------
# Umount and reboot
# --------------------------------------------------------------------------------------------------------------------------

umount -R /mnt
zfs umount -a
zpool export -a
reboot