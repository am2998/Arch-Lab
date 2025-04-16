#!/bin/bash

# EXT4 + EFISTUB 
# Hyprland

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
# Prompt for all user and system settings at the beginning                                                                                     
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

echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Initial configuration                                                               "
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

# --------------------------------------------------------------------------------------------------------------------------
# CPU Selection
# --------------------------------------------------------------------------------------------------------------------------
echo -e "\n=== CPU Selection ==="
echo "  1) Intel"
echo "  2) AMD"
echo
read -p "Enter your choice (1-2): " cpu_choice

case $cpu_choice in
    1)
        CPU_MICROCODE="intel-ucode"
        CPU_TYPE="Intel"
        echo "✓ Selected Intel CPU. Will install intel-ucode."
        ;;
    2)
        CPU_MICROCODE="amd-ucode"
        CPU_TYPE="AMD"
        echo "✓ Selected AMD CPU. Will install amd-ucode."
        ;;
    *)
        echo "⚠ Invalid choice. Defaulting to AMD."
        CPU_MICROCODE="amd-ucode"
        CPU_TYPE="AMD"
        ;;
esac

# --------------------------------------------------------------------------------------------------------------------------
# Boot Method Selection
# --------------------------------------------------------------------------------------------------------------------------
echo -e "\n=== Boot Method Selection ==="
echo "  1) EFISTUB"
echo "  2) ZFSBootMenu"
echo
read -p "Enter your choice (1-2): " boot_choice

case $boot_choice in
    1)
        BOOT_METHOD="EFISTUB"
        echo "✓ Selected EFISTUB for boot method."
        ;;
    2)
        BOOT_METHOD="ZFSBootMenu"
        echo "✓ Selected ZFSBootMenu for boot method."
        ;;
    *)
        echo "⚠ Invalid choice. Defaulting to EFISTUB."
        boot_choice=1
        BOOT_METHOD="EFISTUB"
        ;;
esac

# --------------------------------------------------------------------------------------------------------------------------
# Desktop Environment Selection
# --------------------------------------------------------------------------------------------------------------------------
echo -e "\n=== Desktop Environment Selection ==="
echo "  1) Hyprland"
echo "  2) XFCE4"
echo "  3) KDE Plasma"
echo "  4) GNOME"
echo
read -p "Enter your choice (1-4): " de_choice

case $de_choice in
    1)
        DE_TYPE="Hyprland"
        echo "✓ Selected Hyprland for desktop environment."
        ;;
    2)
        DE_TYPE="XFCE4"
        echo "✓ Selected XFCE4 for desktop environment."
        ;;
    3)
        DE_TYPE="KDE Plasma"
        echo "✓ Selected KDE Plasma for desktop environment."
        ;;
    4)
        DE_TYPE="GNOME"
        echo "✓ Selected GNOME for desktop environment."
        ;;
    *)
        echo "⚠ Invalid choice. Defaulting to Hyprland."
        de_choice=1
        DE_TYPE="Hyprland"
        ;;
esac

# --------------------------------------------------------------------------------------------------------------------------
# System Information
# --------------------------------------------------------------------------------------------------------------------------
echo -e "\n=== System Information ==="
echo -n "Enter hostname: "; read -r HOSTNAME
echo -n "Enter keyboard layout (e.g. us, it, de): "; read -r KEYBOARD_LAYOUT
echo -n "Enter the username: "; read -r USER

# --------------------------------------------------------------------------------------------------------------------------
# Password Configuration
# --------------------------------------------------------------------------------------------------------------------------
echo -e "\n=== Password Configuration ==="
get_password "Enter the password for user $USER" USERPASS
get_password "Enter the password for user root" ROOTPASS

# --------------------------------------------------------------------------------------------------------------------------
# GPU Selection
# --------------------------------------------------------------------------------------------------------------------------
echo -e "\n=== GPU Selection ==="
echo "  1) NVIDIA"
echo "  2) AMD/Intel (Open Source)"
echo "  3) None/VM"
echo
read -p "Enter your choice (1-3): " gpu_choice

case $gpu_choice in
    1)
        GPU_TYPE="NVIDIA"
        echo -e "\n=== NVIDIA Driver Selection ==="
        echo "  Do you want to use NVIDIA open drivers?"
        echo "  (No will install proprietary drivers)"
        echo
        read -p "Use NVIDIA open drivers? [y/N]: " nvidia_open_choice
        
        case $nvidia_open_choice in
            [Yy]*)
            NVIDIA_DRIVER_TYPE="Open"
            echo "✓ Selected NVIDIA open source drivers."
            ;;
            *)
            NVIDIA_DRIVER_TYPE="Proprietary"
            echo "✓ Selected NVIDIA proprietary drivers."
            ;;
        esac
        ;;
        2)
        GPU_TYPE="AMD/Intel"
        NVIDIA_DRIVER_TYPE="none"
        echo "✓ Selected AMD/Intel GPU. Will use open source drivers."
        ;;
        3)
        GPU_TYPE="None/VM"
        NVIDIA_DRIVER_TYPE="none"
        echo "✓ Selected None/VM. Will use basic drivers."
        ;;
        *)
        echo "⚠ Invalid choice. Defaulting to AMD/Intel."
        gpu_choice=2
        GPU_TYPE="AMD/Intel"
        NVIDIA_DRIVER_TYPE="none"
        ;;
    esac

# --------------------------------------------------------------------------------------------------------------------------
# Configuration Summary
# --------------------------------------------------------------------------------------------------------------------------
display_summary() {
    echo -e "\n"
    echo "╔═══════════════════════════════════════════════╗"
    echo "║             Configuration Summary             ║"
    echo "╠═══════════════════════════════════════════════╣"
    echo "║ 1) CPU Type:            $(printf "%-21s" "$CPU_TYPE") ║"
    echo "║ 2) Boot Method:         $(printf "%-21s" "$BOOT_METHOD") ║"
    echo "║ 3) Desktop Environment: $(printf "%-21s" "$DE_TYPE") ║"
    echo "║ 4) Hostname:            $(printf "%-21s" "$HOSTNAME") ║"
    echo "║ 5) Keyboard Layout:     $(printf "%-21s" "$KEYBOARD_LAYOUT") ║"
    echo "║ 6) Username:            $(printf "%-21s" "$USER") ║"
    echo "║ 7) Passwords:           $(printf "%-21s" "[Hidden]") ║"
    echo "║ 8) GPU Type:            $(printf "%-21s" "$GPU_TYPE") ║"
    if [ "$GPU_TYPE" = "NVIDIA" ]; then
    echo "║ 9) NVIDIA Driver:       $(printf "%-21s" "$NVIDIA_DRIVER_TYPE") ║"
    fi
    echo "╚═══════════════════════════════════════════════╝"
}

# Display initial summary
display_summary

# Allow user to modify choices
while true; do
    echo -en "\nWould you like to modify any settings? (Enter the number to change, or 'c' to continue): "
    read choice
    
    case $choice in
        1)  # CPU Type
            echo -e "\n=== CPU Selection ==="
            echo "  1) Intel"
            echo "  2) AMD"
            read -p "Enter your choice (1-2): " cpu_choice
            case $cpu_choice in
                1) CPU_MICROCODE="intel-ucode"; CPU_TYPE="Intel" ;;
                2) CPU_MICROCODE="amd-ucode"; CPU_TYPE="AMD" ;;
                *) echo "⚠ Invalid choice. No changes made." ;;
            esac
            ;;
        2)  # Boot Method
            echo -e "\n=== Boot Method Selection ==="
            echo "  1) EFISTUB"
            echo "  2) ZFSBootMenu"
            read -p "Enter your choice (1-2): " boot_choice
            case $boot_choice in
                1) BOOT_METHOD="EFISTUB" ;;
                2) BOOT_METHOD="ZFSBootMenu" ;;
                *) echo "⚠ Invalid choice. No changes made." ;;
            esac
            ;;
        3)  # Desktop Environment
            echo -e "\n=== Desktop Environment Selection ==="
            echo "  1) Hyprland"
            echo "  2) XFCE4"
            echo "  3) KDE Plasma"
            echo "  4) GNOME"
            read -p "Enter your choice (1-4): " de_choice
            case $de_choice in
                1) DE_TYPE="Hyprland" ;;
                2) DE_TYPE="XFCE4" ;;
                3) DE_TYPE="KDE Plasma" ;;
                4) DE_TYPE="GNOME" ;;
                *) echo "⚠ Invalid choice. No changes made." ;;
            esac
            ;;
        4)  # Hostname
            echo -n "Enter hostname: "; read -r HOSTNAME
            ;;
        5)  # Keyboard Layout
            echo -n "Enter keyboard layout (e.g. us, it, de): "; read -r KEYBOARD_LAYOUT
            ;;
        6)  # Username
            echo -n "Enter the username: "; read -r USER
            ;;
        7)  # Passwords
            echo -e "\n=== Password Configuration ==="
            get_password "Enter the password for user $USER" USERPASS
            get_password "Enter the password for user root" ROOTPASS
            ;;
        c|C)
            break
            ;;
        *)
            echo -en "Invalid option. Please enter a number between 1-7 or 'c' to continue: "
            ;;
    esac
    
    # Update the summary after each change
    display_summary
done

echo -en "\nDo you want to proceed with installation? [y/N]: "
read confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "⚠ Installation aborted."
    exit 1
fi
echo "✓ Proceeding with installation..."

echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Clean System Disk"
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
echo -e "# Format/Mount Partitions"
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
echo -e "# Install Base"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

pacstrap /mnt linux-lts linux-lts-headers booster base base-devel linux-firmware zram-generator reflector sudo networkmanager efibootmgr $CPU_MICROCODE wget


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Generate Fstab"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

genfstab -U /mnt > /mnt/etc/fstab
echo -e "\nFstab file generated:\n"
cat /mnt/etc/fstab


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Chroot"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

env \
    DISK=$DISK \
    HOSTNAME="$HOSTNAME" \
    KEYBOARD_LAYOUT="$KEYBOARD_LAYOUT" \
    USER="$USER" \
    USERPASS="$USERPASS" \
    ROOTPASS="$ROOTPASS" \
    CPU_MICROCODE="$CPU_MICROCODE" \
    boot_choice="$boot_choice" \
    de_choice="$de_choice" \
    GPU_TYPE="$GPU_TYPE" \
    NVIDIA_DRIVER_TYPE="$NVIDIA_DRIVER_TYPE" \
    arch-chroot /mnt /bin/bash <<END


echo -e "In chroot...\n"

echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Configure Mirrors"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

reflector --country "Italy" --latest 10 --sort rate --protocol https --age 7 --save /etc/pacman.d/mirrorlist
cat /etc/pacman.d/mirrorlist


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Setup ZFS"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

echo -e "
[archzfs]
Server = https://archzfs.com/$repo/x86_64" >> /etc/pacman.conf

# ArchZFS GPG keys (see https://wiki.archlinux.org/index.php/Unofficial_user_repositories#archzfs)
pacman-key -r DDF7DB817396A49B2A2723F7403BD972F75D9D76
pacman-key --lsign-key DDF7DB817396A49B2A2723F7403BD972F75D9D76

pacman -Sy --noconfirm zfs-dkms
systemctl enable zfs.target zfs-import-cache zfs-mount zfs-import.target


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# EFI"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

echo "Setting up boot method ($boot_choice)..."

case $boot_choice in
        1)
                echo "Setting up EFISTUB..."
                efibootmgr --create --disk $DISK --part 1 \
                                     --label "Arch" \
                                     --loader /vmlinuz-linux-lts \
                                     --unicode "root=UUID=$(blkid -s UUID -o value ${DISK}${PARTITION_2}) rw initrd=\\$CPU_MICROCODE.img initrd=\initramfs-linux-lts.img"
                ;;
        2)
                echo "Setting up ZFSBootMenu..."
                mkdir -p /boot/EFI/zbm
                wget https://get.zfsbootmenu.org/latest.EFI -O /boot/EFI/zbm/zfsbootmenu.EFI
                
                efibootmgr --disk $DISK --part 1 --create \
                                     --label "Arch" \
                                     --loader '\EFI\zbm\zfsbootmenu.EFI' \
                                     --unicode "spl_hostid=$(hostid) zbm.timeout=3 zbm.prefer=zroot zbm.import_policy=hostid" \
                                     --verbose
                zfs set org.zfsbootmenu:commandline="noresume init_on_alloc=0 rw spl.spl_hostid=$(hostid)" zroot/rootfs
                ;;
esac


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Configure mkinitcpio"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

sed -i 's/\(filesystems\) \(fsck\)/\1 zfs \2/' /etc/mkinitcpio.conf

mkinitcpio -p linux-lts


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Configure ZRAM"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

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


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Enable Multilib Repo"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

sed -i '/\[multilib\]/,/Include/ s/^#//' /etc/pacman.conf
pacman -Syy


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Install Utilities"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

pacman -S --noconfirm flatpak firefox man nano git


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Configure Audio"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

pacman -S --noconfirm pipewire wireplumber pipewire-pulse alsa-plugins alsa-firmware sof-firmware alsa-card-profiles pavucontrol-qt


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# GPU Drivers"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

# Install appropriate GPU drivers based on earlier selection
if [ "$GPU_TYPE" = "NVIDIA" ]; then
    if [ "$NVIDIA_DRIVER_TYPE" = "open" ]; then
        echo "Installing NVIDIA open drivers..."
        pacman -S --noconfirm nvidia-open-lts nvidia-settings nvidia-utils opencl-nvidia libxnvctrl
    else
        echo "Installing NVIDIA proprietary drivers..."
        pacman -S --noconfirm nvidia-lts nvidia-settings nvidia-utils opencl-nvidia libxnvctrl
    fi
elif [ "$GPU_TYPE" = "AMD/Intel" ]; then
    echo "Installing AMD/Intel GPU drivers..."
    pacman -S --noconfirm mesa lib32-mesa vulkan-radeon lib32-vulkan-radeon libva-mesa-driver lib32-libva-mesa-driver mesa-vdpau lib32-mesa-vdpau
elif [ "$GPU_TYPE" = "None/VM" ]; then
    echo "Installing basic video drivers for VM/basic system..."
    pacman -S --noconfirm mesa xf86-video-fbdev
fi


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Desktop Environment"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

echo "Installing desktop environment ($de_choice)..."

case $de_choice in
        1)
                echo "Installing Hyprland..."
                pacman -S --noconfirm hyprland egl-wayland sddm
                find /usr/share/wayland-sessions -type f -not -name "hyprland.desktop" -delete
                mkdir -p /etc/sddm.conf.d/
                sed -i 's/^.*$/[Theme]\nCurrent=breeze/' /etc/sddm.conf.d/theme.conf 2>/dev/null || sed -e '$a[Theme]\nCurrent=breeze' -i /etc/sddm.conf.d/theme.conf
                systemctl enable sddm
                wget -P /home/$USER https://raw.githubusercontent.com/mylinuxforwork/dotfiles/main/setup-arch.sh 
                ;;
        2)
                echo "Installing XFCE4..."
                pacman -S --noconfirm xfce4 xfce4-goodies lightdm lightdm-gtk-greeter
                systemctl enable lightdm
                ;;
        3)
                echo "Installing KDE Plasma..."
                pacman -S --noconfirm plasma sddm
                mkdir -p /etc/sddm.conf.d/
                sed -i 's/^.*$/[Theme]\nCurrent=breeze/' /etc/sddm.conf.d/theme.conf 2>/dev/null || sed -e '$a[Theme]\nCurrent=breeze' -i /etc/sddm.conf.d/theme.conf
                systemctl enable sddm
                ;;
        4)
                echo "Installing GNOME..."
                pacman -S --noconfirm gnome gdm
                systemctl enable gdm
                ;;
        *)
                echo "Invalid choice. Installing Hyprland as default..."
                pacman -S --noconfirm hyprland egl-wayland
                find /usr/share/wayland-sessions -type f -not -name "hyprland.desktop" -delete
                ;;
esac


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# System setup"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

echo "$HOSTNAME" > /etc/hostname
echo -e "127.0.0.1   localhost\n::1         localhost\n127.0.1.1   $HOSTNAME.localdomain   $HOSTNAME" > /etc/hosts

localectl set-keymap --no-convert "$KEYBOARD_LAYOUT"

ln -sf /usr/share/zoneinfo/Europe/Rome /etc/localtime

hwclock --systohc

timedatectl set-ntp true

sed -i '/^#en_US.UTF-8/s/^#//g' /etc/locale.gen && locale-gen



echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Create User"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

useradd -m $USER
echo "$USER:$USERPASS" | chpasswd
echo -e "\n\n$USER ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers

echo "root:$ROOTPASS" | chpasswd


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Install Yay"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

su -c "cd /tmp && git clone https://aur.archlinux.org/yay.git && cd yay && echo $USERPASS | makepkg -si --noconfirm" $USER
echo "Yay installation completed"


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Configure Services"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

systemctl enable NetworkManager
systemctl mask ldconfig.service
systemctl mask geoclue


END


# --------------------------------------------------------------------------------------------------------------------------
# Umount and reboot
# --------------------------------------------------------------------------------------------------------------------------

