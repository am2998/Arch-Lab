#!/bin/bash

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


# Define commands script
CHECK_FUNCTIONS_SCRIPT="functions.sh"

# Check if the script exists
if [ ! -f "$CHECK_FUNCTIONS_SCRIPT" ]; then
    echo "Error: Required file $CHECK_FUNCTIONS_SCRIPT not found."
    echo "Please make sure the file exists in the current directory."
    exit 1
fi

# Source the check-commands functions
source $CHECK_FUNCTIONS_SCRIPT

# echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
# echo -e "# Initial configuration                                                               "
# echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

# ----------------------------------------
# DESKTOP ENVIRONMENT SELECTION
# ----------------------------------------
print_section_header "DESKTOP ENVIRONMENT SELECTION"

echo -e "\033[1;33mChoose your desktop environment:\033[0m"
echo "  \033[1;37m1)\033[0m Hyprland"
echo "  \033[1;37m2)\033[0m XFCE4"
echo "  \033[1;37m3)\033[0m KDE Plasma"
echo "  \033[1;37m4)\033[0m GNOME"
echo
read -p "Enter your choice (1-4): " de_choice

case $de_choice in
    1)
        DE_TYPE="Hyprland"
        echo -e "\033[1;32m✓ Selected Hyprland for desktop environment.\033[0m\n"
        ;;
    2)
        DE_TYPE="XFCE4"
        echo -e "\033[1;32m✓ Selected XFCE4 for desktop environment.\033[0m\n"
        ;;
    3)
        DE_TYPE="KDE Plasma"
        echo -e "\033[1;32m✓ Selected KDE Plasma for desktop environment.\033[0m\n"
        ;;
    4)
        DE_TYPE="GNOME"
        echo -e "\033[1;32m✓ Selected GNOME for desktop environment.\033[0m\n"
        ;;
    *)
        echo -e "\033[1;33m⚠ Invalid choice. Defaulting to Hyprland.\033[0m\n"
        de_choice=1
        DE_TYPE="Hyprland"
        ;;
esac

# ----------------------------------------
# SYSTEM INFORMATION
# ----------------------------------------
print_section_header "SYSTEM INFORMATION"

echo -e "\033[1;33mEnter system hostname:\033[0m"
echo -n "Hostname: "; read -r HOSTNAME
echo -e "\033[1;32m✓ Hostname set to: \033[1;37m$HOSTNAME\033[0m"

# ----------------------------------------
# MIRROR COUNTRY SELECTION
# ----------------------------------------
print_section_header "MIRROR COUNTRY SELECTION"

echo -e "\033[1;33mSelect your country for repository mirrors:\033[0m"
echo "  \033[1;37m1)\033[0m Italy"
echo "  \033[1;37m2)\033[0m Germany"
echo "  \033[1;37m3)\033[0m United States"
echo "  \033[1;37m4)\033[0m United Kingdom"
echo "  \033[1;37m5)\033[0m France"
echo "  \033[1;37m6)\033[0m Spain"
echo "  \033[1;37m7)\033[0m Netherlands"
echo "  \033[1;37m8)\033[0m Other (specify)"
echo "  \033[1;37m9)\033[0m Worldwide (no specific country)"
echo
read -p "Enter your choice (1-9): " mirror_choice

case $mirror_choice in
    1)
        MIRROR_COUNTRY="Italy"
        echo -e "\033[1;32m✓ Selected mirrors from: \033[1;37mItaly\033[0m"
        ;;
    2)
        MIRROR_COUNTRY="Germany"
        echo -e "\033[1;32m✓ Selected mirrors from: \033[1;37mGermany\033[0m"
        ;;
    3)
        MIRROR_COUNTRY="United States"
        echo -e "\033[1;32m✓ Selected mirrors from: \033[1;37mUnited States\033[0m"
        ;;
    4)
        MIRROR_COUNTRY="United Kingdom"
        echo -e "\033[1;32m✓ Selected mirrors from: \033[1;37mUnited Kingdom\033[0m"
        ;;
    5)
        MIRROR_COUNTRY="France"
        echo -e "\033[1;32m✓ Selected mirrors from: \033[1;37mFrance\033[0m"
        ;;
    6)
        MIRROR_COUNTRY="Spain"
        echo -e "\033[1;32m✓ Selected mirrors from: \033[1;37mSpain\033[0m"
        ;;
    7)
        MIRROR_COUNTRY="Netherlands"
        echo -e "\033[1;32m✓ Selected mirrors from: \033[1;37mNetherlands\033[0m"
        ;;
    8)
        echo -e "\033[1;33mPlease specify your country name (in English):\033[0m"
        echo -n "Country: "; read -r MIRROR_COUNTRY
        echo -e "\033[1;32m✓ Selected mirrors from: \033[1;37m$MIRROR_COUNTRY\033[0m"
        ;;
    9)
        MIRROR_COUNTRY=""
        echo -e "\033[1;32m✓ Using worldwide mirrors\033[0m"
        ;;
    *)
        echo -e "\033[1;33m⚠ Invalid choice. Defaulting to worldwide mirrors.\033[0m"
        MIRROR_COUNTRY=""
        ;;
esac

# List available keyboard layouts and let user select one
echo -e "\n=== Keyboard Layout Selection ==="
# Get available keyboard layouts and filter to show only one entry per language
mapfile -t ALL_KEYBOARD_LAYOUTS < <(localectl list-keymaps | sort)

# Create a filtered array with only one variant per base language
declare -a KEYBOARD_LAYOUTS
declare -A seen_layouts

for layout in "${ALL_KEYBOARD_LAYOUTS[@]}"; do
    # Extract the base language code (e.g., "us" from "us-euro")
    base_lang=$(echo "$layout" | cut -d'-' -f1)
    
    # If we haven't seen this base language yet, add it to our filtered list
    if [[ -z "${seen_layouts[$base_lang]}" ]]; then
        seen_layouts[$base_lang]=1
        KEYBOARD_LAYOUTS+=("$layout")
    fi
done

# Set the number of columns for display
COLUMNS=4
TOTAL_LAYOUTS=${#KEYBOARD_LAYOUTS[@]}

echo -e "\nAvailable keyboard layouts (primary variants only):"
# Display available layouts in multiple columns
for ((i=0; i<TOTAL_LAYOUTS; i++)); do
    # Format each entry with fixed width for alignment
    printf "  %3d) %-20s" "$((i+1))" "${KEYBOARD_LAYOUTS[$i]}"
    # Add a newline after every COLUMNS items
    if (( (i+1) % COLUMNS == 0 )); then
        echo ""
    fi
done
# Add a final newline if needed
if (( TOTAL_LAYOUTS % COLUMNS != 0 )); then
    echo ""
fi

# Let user select a layout by number
while true; do
    echo -n "Enter the number of your keyboard layout: "
    read -r layout_choice
    
    # Validate input
    if [[ "$layout_choice" =~ ^[0-9]+$ && "$layout_choice" -ge 1 && "$layout_choice" -le "${#KEYBOARD_LAYOUTS[@]}" ]]; then
        KEYBOARD_LAYOUT="${KEYBOARD_LAYOUTS[$((layout_choice-1))]}"
        echo "✓ Selected keyboard layout: $KEYBOARD_LAYOUT"
        break
    else
        echo "⚠ Invalid choice. Please enter a number between 1 and ${#KEYBOARD_LAYOUTS[@]}."
    fi
done

# List available locales and let user select one
echo -e "\n=== Locale Selection ==="
# Get available locales and store them in an array
mapfile -t ALL_AVAILABLE_LOCALES < <(grep -E "^#[a-zA-Z]" /etc/locale.gen | sed 's/^#//' | sort)

# Create a filtered array with only one variant per base language
declare -a AVAILABLE_LOCALES
declare -A seen_locales

for locale in "${ALL_AVAILABLE_LOCALES[@]}"; do
    # Extract the base language code (e.g., "en_US" from "en_US.UTF-8")
    base_lang=$(echo "$locale" | cut -d'.' -f1 | cut -d'@' -f1)
    
    # If we haven't seen this base language yet, add it to our filtered list
    if [[ -z "${seen_locales[$base_lang]}" ]]; then
        seen_locales[$base_lang]=1
        AVAILABLE_LOCALES+=("$locale")
    fi
done

# Set the number of columns for display
LOCALE_COLUMNS=4
TOTAL_LOCALES=${#AVAILABLE_LOCALES[@]}

echo -e "\nAvailable locales (primary variants only):"
# Display available locales in multiple columns
for ((i=0; i<TOTAL_LOCALES; i++)); do
    # Format each entry with fixed width for alignment
    printf "  %3d) %-20s" "$((i+1))" "${AVAILABLE_LOCALES[$i]}"
    # Add a newline after every LOCALE_COLUMNS items
    if (( (i+1) % LOCALE_COLUMNS == 0 )); then
        echo ""
    fi
done
# Add a final newline if needed
if (( TOTAL_LOCALES % LOCALE_COLUMNS != 0 )); then
    echo ""
fi

# Let user select a locale by number
while true; do
    echo -n "Enter the number of your desired locale: "
    read -r locale_choice
    
    # Validate input
    if [[ "$locale_choice" =~ ^[0-9]+$ && "$locale_choice" -ge 1 && "$locale_choice" -le "${#AVAILABLE_LOCALES[@]}" ]]; then
        SYSTEM_LOCALE="${AVAILABLE_LOCALES[$((locale_choice-1))]}"
        echo "✓ Selected locale: $SYSTEM_LOCALE"
        break
    else
        echo "⚠ Invalid choice. Please enter a number between 1 and ${#AVAILABLE_LOCALES[@]}."
    fi
done

echo -en "\nEnter the username: "; read -r USER

# --------------------------------------------------------------------------------------------------------------------------
# Password Configuration
# --------------------------------------------------------------------------------------------------------------------------

echo -e "\n=== Password Configuration ==="
get_password "Enter the password for user $USER" USERPASS
get_password "Enter the password for user root" ROOTPASS

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
    echo "║ 1) Desktop Environment: $(printf "%-21s" "$DE_TYPE") ║"
    echo "║ 2) Hostname:            $(printf "%-21s" "$HOSTNAME") ║"
    echo "║ 3) Keyboard Layout:     $(printf "%-21s" "$KEYBOARD_LAYOUT") ║"
    echo "║ 4) Locale:              $(printf "%-21s" "$SYSTEM_LOCALE") ║"
    echo "║ 5) Mirror Country:      $(printf "%-21s" "${MIRROR_COUNTRY:-Worldwide}") ║"
    echo "║ 6) Username:            $(printf "%-21s" "$USER") ║"
    echo "║ 7) Passwords:           $(printf "%-21s" "[Hidden]") ║"
    echo "║ 8) CPU Type:            $(printf "%-21s" "$CPU_TYPE") ║"
    echo "║ 9) GPU Type:            $(printf "%-21s" "$GPU_TYPE") ║"
    if [ "$GPU_TYPE" = "NVIDIA" ]; then
    echo "║ 10) NVIDIA Driver:      $(printf "%-21s" "$NVIDIA_DRIVER_TYPE") ║"
    fi
    echo "╚═══════════════════════════════════════════════╝"
}

# Display initial summary
display_summary

# Allow user to modify choices
while true; do
    echo -en "\nWould you like to modify any settings? (Enter the number to change, 'c' to confirm, 'a' to abort): "
    read choice
    
    case $choice in
        1)  # Desktop Environment
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
        2)  # Hostname
            echo -n "Enter hostname: "; read -r HOSTNAME
            ;;
        3)  # Keyboard Layout
            echo -e "\n=== Keyboard Layout Selection ==="
            # Get available keyboard layouts and filter to show only one entry per language
            mapfile -t ALL_KEYBOARD_LAYOUTS < <(localectl list-keymaps | sort)

            # Create a filtered array with only one variant per base language
            declare -a KEYBOARD_LAYOUTS
            declare -A seen_layouts

            for layout in "${ALL_KEYBOARD_LAYOUTS[@]}"; do
                # Extract the base language code (e.g., "us" from "us-euro")
                base_lang=$(echo "$layout" | cut -d'-' -f1)
                
                # If we haven't seen this base language yet, add it to our filtered list
                if [[ -z "${seen_layouts[$base_lang]}" ]]; then
                    seen_layouts[$base_lang]=1
                    KEYBOARD_LAYOUTS+=("$layout")
                fi
            done

            # Set the number of columns for display
            COLUMNS=4
            TOTAL_LAYOUTS=${#KEYBOARD_LAYOUTS[@]}

            echo -e "\nAvailable keyboard layouts (primary variants only):"
            # Display available layouts in multiple columns
            for ((i=0; i<TOTAL_LAYOUTS; i++)); do
                # Format each entry with fixed width for alignment
                printf "  %3d) %-20s" "$((i+1))" "${KEYBOARD_LAYOUTS[$i]}"
                # Add a newline after every COLUMNS items
                if (( (i+1) % COLUMNS == 0 )); then
                    echo ""
                fi
            done
            # Add a final newline if needed
            if (( TOTAL_LAYOUTS % COLUMNS != 0 )); then
                echo ""
            fi

            # Let user select a layout by number
            while true; do
                echo -n "Enter the number of your keyboard layout: "
                read -r layout_choice
                
                # Validate input
                if [[ "$layout_choice" =~ ^[0-9]+$ && "$layout_choice" -ge 1 && "$layout_choice" -le "${#KEYBOARD_LAYOUTS[@]}" ]]; then
                    KEYBOARD_LAYOUT="${KEYBOARD_LAYOUTS[$((layout_choice-1))]}"
                    echo "✓ Selected keyboard layout: $KEYBOARD_LAYOUT"
                    break
                else
                    echo "⚠ Invalid choice. Please enter a number between 1 and ${#KEYBOARD_LAYOUTS[@]}."
                fi
            done
            ;;
        4)  # Locale
            echo -e "\n=== Locale Selection ==="
            # Get available locales and store them in an array
            mapfile -t ALL_AVAILABLE_LOCALES < <(grep -E "^#[a-zA-Z]" /etc/locale.gen | sed 's/^#//' | sort)

            # Create a filtered array with only one variant per base language
            declare -a AVAILABLE_LOCALES
            declare -A seen_locales

            for locale in "${ALL_AVAILABLE_LOCALES[@]}"; do
                # Extract the base language code (e.g., "en_US" from "en_US.UTF-8")
                base_lang=$(echo "$locale" | cut -d'.' -f1 | cut -d'@' -f1)
                
                # If we haven't seen this base language yet, add it to our filtered list
                if [[ -z "${seen_locales[$base_lang]}" ]]; then
                    seen_locales[$base_lang]=1
                    AVAILABLE_LOCALES+=("$locale")
                fi
            done

            # Set the number of columns for display
            LOCALE_COLUMNS=4
            TOTAL_LOCALES=${#AVAILABLE_LOCALES[@]}

            echo -e "\nAvailable locales (primary variants only):"
            # Display available locales in multiple columns
            for ((i=0; i<TOTAL_LOCALES; i++)); do
                # Format each entry with fixed width for alignment
                printf "  %3d) %-20s" "$((i+1))" "${AVAILABLE_LOCALES[$i]}"
                # Add a newline after every LOCALE_COLUMNS items
                if (( (i+1) % LOCALE_COLUMNS == 0 )); then
                    echo ""
                fi
            done
            # Add a final newline if needed
            if (( TOTAL_LOCALES % LOCALE_COLUMNS != 0 )); then
                echo ""
            fi

            # Let user select a locale by number
            while true; do
                echo -n "Enter the number of your desired locale: "
                read -r locale_choice
                
                # Validate input
                if [[ "$locale_choice" =~ ^[0-9]+$ && "$locale_choice" -ge 1 && "$locale_choice" -le "${#AVAILABLE_LOCALES[@]}" ]]; then
                    SYSTEM_LOCALE="${AVAILABLE_LOCALES[$((locale_choice-1))]}"
                    echo "✓ Selected locale: $SYSTEM_LOCALE"
                    break
                else
                    echo "⚠ Invalid choice. Please enter a number between 1 and ${#AVAILABLE_LOCALES[@]}."
                fi
            done
            ;;
        5)  # Mirror Country
            echo -e "\n=== Mirror Country Selection ==="
            echo "Select your country for repository mirrors:"
            echo "  1) Italy"
            echo "  2) Germany"
            echo "  3) United States"
            echo "  4) United Kingdom"
            echo "  5) France"
            echo "  6) Spain"
            echo "  7) Netherlands"
            echo "  8) Other (specify)"
            echo "  9) Worldwide (no specific country)"
            read -p "Enter your choice (1-9): " mirror_choice
            case $mirror_choice in
                1) MIRROR_COUNTRY="Italy" ;;
                2) MIRROR_COUNTRY="Germany" ;;
                3) MIRROR_COUNTRY="United States" ;;
                4) MIRROR_COUNTRY="United Kingdom" ;;
                5) MIRROR_COUNTRY="France" ;;
                6) MIRROR_COUNTRY="Spain" ;;
                7) MIRROR_COUNTRY="Netherlands" ;;
                8) 
                   echo -n "Enter your country name (in English): "
                   read -r MIRROR_COUNTRY
                   ;;
                9) MIRROR_COUNTRY="" ;;
                *) echo "⚠ Invalid choice. No changes made." ;;
            esac
            ;;
        6)  # Username
            echo -n "Enter the username: "; read -r USER
            ;;
        7)  # Passwords
            echo -e "\n=== Password Configuration ==="
            get_password "Enter the password for user $USER" USERPASS
            get_password "Enter the password for user root" ROOTPASS
            ;;
        8)  # CPU Type
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
        9)  # GPU Type
            echo -e "\n=== GPU Selection ==="
            echo "  1) NVIDIA"
            echo "  2) AMD/Intel (Open Source)"
            echo "  3) None/VM"
            read -p "Enter your choice (1-3): " gpu_choice
            case $gpu_choice in
                1)
                    GPU_TYPE="NVIDIA"
                    echo "  Do you want to use NVIDIA open drivers?"
                    echo "  (No will install proprietary drivers)"
                    read -p "Use NVIDIA open drivers? [y/N]: " nvidia_open_choice
                    case $nvidia_open_choice in
                        [Yy]*) NVIDIA_DRIVER_TYPE="Open" ;;
                        *) NVIDIA_DRIVER_TYPE="Proprietary" ;;
                    esac
                    ;;
                2) GPU_TYPE="AMD/Intel"; NVIDIA_DRIVER_TYPE="none" ;;
                3) GPU_TYPE="None/VM"; NVIDIA_DRIVER_TYPE="none" ;;
                *) echo "⚠ Invalid choice. No changes made." ;;
            esac
            ;;
        c|C)
            echo "✓ Proceeding with installation..."
            break
            ;;
        a|A)
            echo "⚠ Installation aborted."
            exit 1
            ;;
        *)
            echo -en "Invalid option. Please enter a valid number, 'c' to confirm, 'a' to abort: "
            ;;
    esac
    
    # Update the summary after each change
    display_summary
done


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

run_command "wipefs -a -f $DISK" "wipe disk signatures"
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
) | run_command "fdisk $DISK" "create partitions"


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Format/Mount Partitions"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

run_command "zpool create \
    -o ashift=12 \
    -O acltype=posixacl -O canmount=off -O compression=lz4 \
    -O dnodesize=auto -O normalization=formD -o autotrim=on \
    -O atime=off -O xattr=sa -O mountpoint=none \
    -R /mnt zroot ${DISK}${PARTITION_2} -f" "create ZFS pool"

run_command "zfs create -o canmount=noauto -o mountpoint=/ zroot/rootfs" "create ZFS root dataset"

run_command "zpool set bootfs=zroot/rootfs zroot" "set bootfs property"

run_command "zfs mount zroot/rootfs" "mount the root dataset"

mkdir -p /mnt/etc/zfs
run_command "zpool set cachefile=/etc/zfs/zpool.cache zroot" "set ZFS pool cache file"
cp /etc/zfs/zpool.cache /mnt/etc/zfs/zpool.cache

run_command "mkfs.fat -F32 ${DISK}${PARTITION_1}" "format EFI partition with FAT32"
mkdir -p /mnt/efi && mount ${DISK}${PARTITION_1} /mnt/efi


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Install Base"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

run_command "pacstrap /mnt linux-lts linux-lts-headers mkinitcpio base base-devel linux-firmware zram-generator reflector sudo networkmanager efibootmgr $CPU_MICROCODE wget" "install base packages"


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Generate Fstab"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

genfstab -U /mnt > /mnt/etc/fstab
echo -e "\nFstab file generated:\n"
cat /mnt/etc/fstab


echo -e "\n\n# --------------------------------------------------------------------------------------------------------------------------"
echo -e "# Chroot"
echo -e "# --------------------------------------------------------------------------------------------------------------------------\n"

# Create a temporary directory in the chroot environment
mkdir -p /mnt/install

# Copy the chroot script and check-commands script to the temporary directory in the chroot
cp ./"$CHECK_FUNCTIONS_SCRIPT" /mnt/install/
cp ./chroot.sh /mnt/install/

# Make scripts executable
chmod +x /mnt/install/chroot.sh /mnt/install/"$CHECK_FUNCTIONS_SCRIPT"

# Export all environment variables needed by the chroot script
run_command "env \
    DISK=$DISK \
    HOSTNAME=\"$HOSTNAME\" \
    KEYBOARD_LAYOUT=\"$KEYBOARD_LAYOUT\" \
    SYSTEM_LOCALE=\"$SYSTEM_LOCALE\" \
    USER=\"$USER\" \
    USERPASS=\"$USERPASS\" \
    ROOTPASS=\"$ROOTPASS\" \
    CPU_MICROCODE=\"$CPU_MICROCODE\" \
    de_choice=\"$de_choice\" \
    GPU_TYPE=\"$GPU_TYPE\" \
    NVIDIA_DRIVER_TYPE=\"$NVIDIA_DRIVER_TYPE\" \
    MIRROR_COUNTRY=\"$MIRROR_COUNTRY\" \
    arch-chroot /mnt /install/chroot.sh" "chroot into the new system"


# --------------------------------------------------------------------------------------------------------------------------
# Umount and reboot
# --------------------------------------------------------------------------------------------------------------------------
rm -rf /mnt/install
umount -R /mnt
zfs umount -a
zpool export -a
reboot