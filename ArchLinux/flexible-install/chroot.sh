#!/bin/bash

echo -e "\033[1;92m✅ Successfully arch-chrooted in new installation\033[0m\n"

# Define commands script
FUNCTIONS_SCRIPT="/install/functions.sh"

# Check if the script exists
if [ ! -f "$FUNCTIONS_SCRIPT" ]; then
    echo -e "\033[1;91m❌ Error: Required file $FUNCTIONS_SCRIPT not found.\033[0m"
    echo -e "\033[1;93m💡 Please make sure the file exists in the current directory.\033[0m"
    exit 1
fi

# Source the check-commands functions
source $FUNCTIONS_SCRIPT

sleep 5

# ----------------------------------------
# CONFIGURING MIRRORS
# ----------------------------------------
print_section_header "CONFIGURING MIRRORS"

if [ -z "$MIRROR_COUNTRY" ]; then
    echo -e "\033[1;94m🌐 No country specified, using worldwide mirrors...\033[0m"
    run_command "reflector --latest 10 --sort rate --protocol https --age 7 --save /etc/pacman.d/mirrorlist" "configure mirrors with reflector using worldwide mirrors"
else
    echo -e "\033[1;94m🌐 Configuring mirrors for: \033[1;97m$MIRROR_COUNTRY\033[0m"
    run_command "reflector --country \"$MIRROR_COUNTRY\" --latest 10 --sort rate --protocol https --age 7 --save /etc/pacman.d/mirrorlist" "configure mirrors with reflector for country: $MIRROR_COUNTRY"
fi
echo -e "\033[1;38;5;117mMirror list:\033[0m"
echo -e "\033[1;38;5;195m$(cat /etc/pacman.d/mirrorlist)\033[0m"

# ----------------------------------------
# ZFS SETUP
# ----------------------------------------
print_section_header "SETTING UP ZFS"

echo -e "\033[1;94m🛠️ Adding ArchZFS repository...\033[0m"
echo -e '
[archzfs]
Server = https://github.com/archzfs/archzfs/releases/download/experimental' >> /etc/pacman.conf

# ArchZFS GPG keys (see https://wiki.archlinux.org/index.php/Unofficial_user_repositories#archzfs)
run_command "pacman-key -r DDF7DB817396A49B2A2723F7403BD972F75D9D76" "import ArchZFS GPG key"
run_command "pacman-key --lsign-key DDF7DB817396A49B2A2723F7403BD972F75D9D76" "sign ArchZFS GPG key"

run_command "pacman -Sy --noconfirm zfs-dkms" "install ZFS DKMS"
run_command "systemctl enable zfs.target zfs-import-cache zfs-mount zfs-import.target" "enable ZFS services"


# ----------------------------------------
# ZFSBOOTMENU SETUP
# ----------------------------------------
print_section_header "SETTING UP ZFSBOOTMENU"

echo -e "\033[1;94m💾 Downloading and configuring ZFSBootMenu...\033[0m"
mkdir -p /efi/EFI/zbm
run_command "wget https://get.zfsbootmenu.org/latest.EFI -O /efi/EFI/zbm/zfsbootmenu.EFI" "download ZFSBootMenu EFI file"

# Standard parameters
run_command "efibootmgr --disk $DISK --part 1 --create \
                 --label \"ZFSBootMenu\" \
                 --loader '\\EFI\\zbm\\zfsbootmenu.EFI' \
                 --unicode \"spl_hostid=$(hostid) zbm.timeout=3 zbm.prefer=zroot zbm.import_policy=hostid\" \
                 --verbose" "create EFI boot entry for ZFSBootMenu"


run_command "zfs set org.zfsbootmenu:commandline=\"noresume init_on_alloc=0 rw spl.spl_hostid=$(hostid)\" zroot/rootfs" "set ZFSBootMenu commandline property"

# ----------------------------------------
# MKINITCPIO CONFIGURATION
# ----------------------------------------
print_section_header "CONFIGURING MKINITCPIO"

run_command "sed -i 's/\(filesystems\) \(fsck\)/\1 zfs \2/' /etc/mkinitcpio.conf" "add ZFS hooks to mkinitcpio.conf"
run_command "mkinitcpio -p linux-lts" "generate initial ramdisk"

# Check if encryption was enabled
if [ -f "/etc/zfs/zroot.key" ]; then
    echo -e "\033[1;94m🔐 Setting up ZFS encryption keys...\033[0m"

    # Add zroot.key to the FILES array in mkinitcpio.conf
    run_command "sed -i 's|^FILES=.*|FILES=(/etc/zfs/zroot.key)|' /etc/mkinitcpio.conf" "add encryption key to mkinitcpio FILES array"
    run_command "mkinitcpio -p linux-lts" "regenerate initial ramdisk with encryption support"
    FILES=(/etc/zfs/zroot.key)
    
    
else
    echo -e "\033[1;94mℹ️ ZFS encryption not enabled, skipping encryption setup.\033[0m"
fi

# ----------------------------------------
# ZRAM CONFIGURATION
# ----------------------------------------
print_section_header "CONFIGURING ZRAM"

# Check if we're in advanced mode with custom ZRAM settings
if [ "$INSTALL_MODE" = "advanced" ]; then
    echo -e "\033[1;94m⚙️ Configuring ZRAM with custom settings...\033[0m"
    run_command "bash -c 'cat > /etc/systemd/zram-generator.conf <<EOF
[zram0]
zram-size = $ZRAM_SIZE
compression-algorithm = $ZRAM_COMPRESSION
EOF'" "create ZRAM configuration with custom settings"
else
    run_command "bash -c 'cat > /etc/systemd/zram-generator.conf <<EOF
[zram0]
zram-size = min(ram, 32768)
compression-algorithm = zstd
EOF'" "create ZRAM configuration with default settings"
fi

echo -e "\033[1;94m⚙️ Setting up ZRAM kernel parameters...\033[0m"
echo "vm.swappiness = 180" >> /etc/sysctl.d/99-vm-zram-parameters.conf
echo "vm.watermark_boost_factor = 0" >> /etc/sysctl.d/99-vm-zram-parameters.conf
echo "vm.watermark_scale_factor = 125" >> /etc/sysctl.d/99-vm-zram-parameters.conf
echo "vm.page-cluster = 0" >> /etc/sysctl.d/99-vm-zram-parameters.conf

run_command "sysctl --system" "apply sysctl settings"

# ----------------------------------------
# SYSTEM CONFIGURATION
# ----------------------------------------
print_section_header "CONFIGURING SYSTEM SETTINGS"

echo -e "\033[1;94m🖥️ Setting hostname to: \033[1;97m$HOSTNAME\033[0m"
echo "$HOSTNAME" > /etc/hostname
echo -e "127.0.0.1   localhost\n::1         localhost\n127.0.1.1   $HOSTNAME.localdomain   $HOSTNAME" > /etc/hosts

echo -e "\033[1;94m⌨️ Configuring keyboard layout: \033[1;97m$KEYBOARD_LAYOUT\033[0m"
run_command "localectl set-keymap --no-convert \"$KEYBOARD_LAYOUT\"" "set keyboard layout"

echo -e "\033[1;94m🕒 Setting up timezone and clock...\033[0m"
run_command "ln -sf /usr/share/zoneinfo/Europe/Rome /etc/localtime" "set timezone"
run_command "hwclock --systohc" "sync hardware clock"
run_command "timedatectl set-ntp true" "enable network time sync"

echo -e "\033[1;94m🌍 Configuring locale: \033[1;97m$SYSTEM_LOCALE\033[0m"
run_command "sed -i '/^#${SYSTEM_LOCALE}/s/^#//g' /etc/locale.gen && locale-gen" "generate locale: $SYSTEM_LOCALE"
echo "LANG=${SYSTEM_LOCALE}" > /etc/locale.conf

# ----------------------------------------
# USER CREATION
# ----------------------------------------
print_section_header "CREATING USER"

echo -e "\033[1;94m👤 Creating user: \033[1;97m$USER\033[0m"
run_command "useradd -m $USER" "create user"
run_command "echo \"$USER:$USERPASS\" | chpasswd" "set user password"
echo -e "\n\n$USER ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers

run_command "echo \"root:$ROOTPASS\" | chpasswd" "set root password"

# ----------------------------------------
# SERVICE CONFIGURATION
# ----------------------------------------
print_section_header "CONFIGURING SERVICES"

run_command "systemctl enable NetworkManager" "enable NetworkManager"


# ----------------------------------------
# DESKTOP ENVIRONMENT
# ----------------------------------------
print_section_header "INSTALLING DESKTOP ENVIRONMENT"

# Ensure the variable is a number for proper comparison
DE_CHOICE=$(echo "$DE_CHOICE" | tr -d '"') # Remove any quotes that might be present

case "$DE_CHOICE" in
        "1")
                echo -e "\033[1;92m✨ Installing Hyprland...\033[0m"
                run_command "pacman -S --noconfirm hyprland egl-wayland" "install Hyprland"
                run_command "find /usr/share/wayland-sessions -type f -not -name \"hyprland.desktop\" -delete" "clean up wayland sessions"
                mkdir -p /etc/systemd/system/getty@tty1.service.d 

                echo -e "\033[1;94m🔧 Setting up autologin for Hyprland...\033[0m"
                echo -e "
                [Service]
                ExecStart=
                ExecStart=-/sbin/agetty -o '-p -f -- \\u' --noclear --autologin $USER %I $TERM" >> /etc/systemd/system/getty@tty1.service.d/autologin.conf

                echo -e "Hyprland > /dev/null" >> /home/$USER/.bash_profile

                run_command "groupadd -r autologin" "create autologin group"
                run_command "gpasswd -a $USER autologin" "add user to autologin group"

                run_command "su -c \"cd && wget https://raw.githubusercontent.com/mylinuxforwork/dotfiles/main/setup-arch.sh && chmod +x setup-arch.sh\" $USER" "download setup script for user"
                ;;
        "2")
                echo -e "\033[1;92m✨ Installing XFCE4...\033[0m"
                run_command "pacman -S --noconfirm xfce4 xfce4-goodies lightdm lightdm-gtk-greeter" "install XFCE4"
                run_command "systemctl enable lightdm" "enable LightDM"
                ;;
        "3")
                echo -e "\033[1;92m✨ Installing KDE Plasma...\033[0m"
                run_command "pacman -S --noconfirm plasma sddm" "install KDE Plasma"
                mkdir -p /etc/sddm.conf.d/
                echo -e "[Theme]\nCurrent=breeze" > /etc/sddm.conf.d/theme.conf
                run_command "systemctl enable sddm" "enable SDDM"
                ;;
        "4")
                echo -e "\033[1;92m✨ Installing GNOME...\033[0m"
                run_command "pacman -S --noconfirm gnome gdm" "install GNOME"
                run_command "systemctl enable gdm" "enable GDM"
                ;;
        *)
                echo -e "\033[1;91m❌ Invalid choice '$DE_CHOICE'. Installing Hyprland as default...\033[0m"
                run_command "pacman -S --noconfirm hyprland egl-wayland" "install Hyprland"
                run_command "find /usr/share/wayland-sessions -type f -not -name \"hyprland.desktop\" -delete" "clean up wayland sessions"
                ;;
esac


# ----------------------------------------
# REPOSITORY SETUP
# ----------------------------------------
print_section_header "CONFIGURING REPOSITORIES"

run_command "sed -i '/\[multilib\]/,/Include/ s/^#//' /etc/pacman.conf" "enable multilib repository"
run_command "pacman -Syy" "refresh package databases"


# ----------------------------------------
# AUR HELPER SETUP
# ----------------------------------------
print_section_header "INSTALLING AUR HELPER"

run_command "su -c \"cd /tmp && git clone https://aur.archlinux.org/yay.git && cd yay && echo $USERPASS | makepkg -si --noconfirm\" $USER" "install Yay AUR helper"

# ----------------------------------------
# UTILITIES INSTALLATION
# ----------------------------------------
print_section_header "INSTALLING UTILITIES"

#run_command "pacman -S --noconfirm flatpak firefox man nano git" "install base utilities"


# ----------------------------------------
# AUDIO CONFIGURATION
# ----------------------------------------
print_section_header "CONFIGURING AUDIO"

echo -e "\033[1;94m🔊 Setting up audio server: \033[1;97m$AUDIO_SERVER\033[0m"

if [ "$AUDIO_SERVER" = "pipewire" ]; then
    echo -e "\033[1;92m✨ Installing PipeWire audio system...\033[0m"
    run_command "pacman -S --noconfirm pipewire wireplumber pipewire-pulse pipewire-alsa alsa-plugins alsa-firmware sof-firmware alsa-card-profiles pavucontrol" "install PipeWire and related packages"
    systemctl enable pipewire pipewire-pulse wireplumber 

else
    echo -e "\033[1;92m✨ Installing PulseAudio audio system...\033[0m"
    run_command "pacman -S --noconfirm pulseaudio pulseaudio-alsa pulseaudio-bluetooth alsa-utils alsa-plugins alsa-firmware sof-firmware alsa-card-profiles pavucontrol" "install PulseAudio and related packages"

# Set user permissions
chown -R $USER:$USER /home/$USER/.config

# ----------------------------------------
# GPU DRIVERS CONFIGURATION
# ----------------------------------------
print_section_header "CONFIGURING GPU DRIVERS"

#Install appropriate GPU drivers based on earlier selection
# if [ "$GPU_TYPE" = "NVIDIA" ]; then
#     if [ "$NVIDIA_DRIVER_TYPE" = "open" ]; then
#         echo -e "\033[1;94m🎮 Installing NVIDIA open drivers...\033[0m"
#         run_command "pacman -S --noconfirm nvidia-open-lts nvidia-settings nvidia-utils opencl-nvidia libxnvctrl" "install NVIDIA open drivers"
#     else
#         echo -e "\033[1;94m🎮 Installing NVIDIA proprietary drivers...\033[0m"
#         run_command "pacman -S --noconfirm nvidia-lts nvidia-settings nvidia-utils opencl-nvidia libxnvctrl" "install NVIDIA proprietary drivers"
#     fi
# elif [ "$GPU_TYPE" = "AMD/Intel" ]; then
#     echo -e "\033[1;94m🎮 Installing AMD/Intel GPU drivers...\033[0m"
#     run_command "pacman -S --noconfirm mesa lib32-mesa vulkan-radeon lib32-vulkan-radeon libva-mesa-driver lib32-libva-mesa-driver mesa-vdpau lib32-mesa-vdpau" "install AMD/Intel GPU drivers"
# elif [ "$GPU_TYPE" = "None/VM" ]; then
#     echo -e "\033[1;94m🎮 Installing basic video drivers for VM/basic system...\033[0m"
#     run_command "pacman -S --noconfirm mesa xf86-video-fbdev" "install basic video drivers"
# fi