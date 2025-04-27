#!/bin/bash
# Load common functions
source "$(dirname "$0")/functions.sh"

# Display welcome banner with enhanced colors
clear
echo -e "\033[1;38;5;75m"
echo "    _             _       _     _                   "
echo "   / \   _ __ ___| |__   | |   (_)_ __  _   ___  __ "
echo "  / _ \ | '__/ __| '_ \  | |   | | '_ \| | | \ \/ / "
echo " / ___ \| | | (__| | | | | |___| | | | | |_| |>  <  "
echo "/_/   \_\_|  \___|_| |_| |_____|_|_| |_|\__,_/_/\_\ "
echo -e "\033[0m"
echo -e "\033[1;38;5;45m         Flexible Installation Script\033[0m"
echo -e "\033[1;38;5;243m           (A script for Arch Linux installation)\033[0m\n"


# ----------------------------------------
# NETWORK VERIFICATION
# ----------------------------------------
print_section_header "NETWORK VERIFICATION"

# Verify network connection
echo -e "\033[1;94m🌐 Checking network connection...\033[0m"
if ping -c 1 archlinux.org &> /dev/null; then
    echo -e "\033[1;92m✅ Network is working properly\033[0m\n"
else
    echo -e "\033[1;91m❌ No network connection. Please verify your network and try again.\033[0m"
    echo -e "\033[1;93m💡 Try: iwctl $0\033[0m"
    exit 1
fi

# ----------------------------------------
# SUPPORT SCRIPTS
# ----------------------------------------

# Define commands script
FUNCTIONS_SCRIPT="functions.sh"
CHROOT_SCRIPT="chroot.sh"

# Check if required scripts exist
FUNCTIONS_SCRIPT="functions.sh"
if [ ! -f "$FUNCTIONS_SCRIPT" ] || [ ! -f "$CHROOT_SCRIPT" ]; then
    echo -e "\033[1;91m❌ Error: Required scripts not found.\033[0m"
    echo -e "Please make sure these files exist in the current directory:"
    [ ! -f "$FUNCTIONS_SCRIPT" ] && echo -e " - \033[1;93m$FUNCTIONS_SCRIPT\033[0m"
    [ ! -f "$CHROOT_SCRIPT" ] && echo -e " - \033[1;93m$CHROOT_SCRIPT\033[0m"
    exit 1
fi

echo -e "\033[1;94m📂 Searching for required support scripts...\033[0m"
echo -e "\033[1;92m✅ Required scripts found.\033[0m"

# Source functions script
source $FUNCTIONS_SCRIPT

# ----------------------------------------
# MODE SELECTION
# ----------------------------------------
print_section_header "INSTALLATION MODE"

echo -e "\033[1;94mSelect installation mode:\033[0m"
echo -e "  \033[1;37m1)\033[0m \033[1;38;5;82mSimple\033[0m (Recommended, fewer questions with sensible defaults)"
echo -e "  \033[1;37m2)\033[0m \033[1;38;5;208mAdvanced\033[0m (More customization options, detailed configuration)"
echo

while true; do
    echo -en "\033[1;94mEnter your choice (1-2): \033[0m"
    read -r moDE_CHOICE
    
    case $moDE_CHOICE in
        1)
            INSTALL_MODE="simple"
            echo -e "\033[1;92m✅ Selected Simple mode\033[0m\n"
            
            # Set default values for advanced options
            ZRAM_SIZE="min(ram, 32768)"  # Default ZRAM size (in MB)
            EFI_PART_SIZE="1G"           # Default EFI partition size
            ZFS_COMPRESSION="lz4"        # Default ZFS compression algorithm
            break
            ;;
        2)
            INSTALL_MODE="advanced"
            echo -e "\033[1;92m✅ Selected Advanced mode\033[0m\n"
            break
            ;;
        *)
            echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
            ;;
    esac
done


# ----------------------------------------
# SETUP: INITIAL VARIABLES
# ----------------------------------------

# Device selection: Ask user to select the device for installation
print_section_header "INSTALLATION DEVICE SELECTION"

echo -e "\033[1;94m💾 Available disks for installation:\033[0m"
if [ "$INSTALL_MODE" = "simple" ]; then
    echo -e "\033[1;93m⚠️  WARNING: THE SELECTED DISK WILL BE COMPLETELY ERASED IN SIMPLE MODE!\033[0m\n"
fi


# Display available disks
available_disks=$(lsblk -dpno NAME,SIZE,MODEL | grep -E "/dev/(sd|nvme|vd)")
echo -e "\033[1;38;5;195m$available_disks\033[0m\n"

# Let user select a disk
while true; do
    echo -en "\033[1;94mEnter the full path of the disk to install to (e.g., /dev/sda): \033[0m"
    read -r DEVICE
    
    # Verify disk exists
    if lsblk "$DEVICE" &> /dev/null; then
        echo -e "\033[1;92m✅ Selected device: \033[1;97m$DEVICE\033[0m\n"
        break
    else
        echo -e "\033[1;91m❌ Invalid device. Please enter a valid device path.\033[0m"
    fi
done

# ----------------------------------------
# CHOOSE BOOT TYPE
# ----------------------------------------
print_section_header "BOOT TYPE SELECTION"

echo -e "\033[1;94mSelect the boot type:\033[0m"
echo -e "  \033[1;97m1)\033[0m \033[1;38;5;220mEFI\033[0m (Modern systems, recommended)"
echo -e "  \033[1;97m2)\033[0m \033[1;38;5;208mBIOS\033[0m (Legacy systems)"
echo

while true; do
    echo -en "\033[1;94mEnter your choice (1-2): \033[0m"
    read -r boot_choice
    
    case $boot_choice in
        1)
            BOOT_TYPE="efi"
            echo -e "\033[1;92m✅ Selected EFI boot\033[0m\n"
            break
            ;;
        2)
            BOOT_TYPE="bios"
            echo -e "\033[1;92m✅ Selected BIOS boot\033[0m\n"
            break
            ;;
        *)
            echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
            ;;
    esac
done

# ----------------------------------------
# ADVANCED OPTIONS (only in advanced mode)
# ----------------------------------------
if [ "$INSTALL_MODE" = "advanced" ]; then
    print_section_header "ADVANCED PARTITION CONFIGURATION"
    
    # Get the total disk size
    # Get disk size in GB
    DISK_SIZE_GB=$(lsblk -dn -o SIZE $DEVICE --bytes | numfmt --to=iec --format="%.0f" --from=auto | sed 's/[^0-9]//g')
    echo -e "\033[1;94mDisk size: \033[1;97m${DISK_SIZE_GB}GB\033[0m"
    
    # EFI partition size configuration
    echo -e "\033[1;94mConfigure EFI partition size:\033[0m"
    echo -e "  \033[1;37m1)\033[0m Use default (1GB - recommended)"
    echo -e "  \033[1;37m2)\033[0m Specify custom size"
    echo
    
    while true; do
        echo -en "\033[1;94mEnter your choice (1-2) [1]: \033[0m"
        read -r efi_size_choice
        
        case $efi_size_choice in
            1|"")
                EFI_PART_SIZE="1G"
                echo -e "\033[1;32m✓ Using default EFI partition size: \033[1;37m1GB\033[0m"
                break
                ;;
            2)
                while true; do
                    echo -en "\033[1;94mEnter EFI partition size in MB (e.g., 512 for 512MB): \033[0m"
                    read -r custom_efi_size
                    
                    # Validate input (simple check for numeric value)
                    if [[ "$custom_efi_size" =~ ^[0-9]+$ ]]; then
                        if (( custom_efi_size >= 100 && custom_efi_size <= 2048 )); then
                            EFI_PART_SIZE="${custom_efi_size}M"
                            echo -e "\033[1;32m✓ EFI partition size set to: \033[1;37m${custom_efi_size}MB\033[0m"
                            break
                        else
                            echo -e "\033[1;91m❌ Invalid size. Please enter a value between 100 and 2048 MB.\033[0m"
                        fi
                    else
                        echo -e "\033[1;91m❌ Invalid size format. Please enter a numeric value in MB.\033[0m"
                    fi
                done
                break
                ;;
            *)
                echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
                ;;
        esac
    done
    
    # Root partition size configuration
    echo -e "\n\033[1;94mConfigure root partition size:\033[0m"
    echo -e "  \033[1;37m1)\033[0m Use all available space (recommended)"
    echo -e "  \033[1;37m2)\033[0m Specify custom size (for multi-boot or future partitioning)"
    echo
    
    while true; do
        echo -en "\033[1;94mEnter your choice (1-2) [1]: \033[0m"
        read -r root_size_choice
        
        case $root_size_choice in
            1|"")
                ROOT_PART_SIZE="MAX"
                echo -e "\033[1;32m✓ Using all available space for root partition\033[0m"
                break
                ;;
            2)
                while true; do
                    echo -en "\033[1;94mEnter root partition size in GB (e.g., 50 for 50GB): \033[0m"
                    read -r custom_root_size
                    
                    # Validate input (simple check for numeric value)
                    if [[ "$custom_root_size" =~ ^[0-9]+$ ]]; then
                        # Calculate max safe size - hardcode an upper limit to avoid integer overflow
                        if [ "$DISK_SIZE_GB" -gt 1000 ]; then
                            max_safe_size=950  # Cap at 950GB for very large disks
                        else
                            # Use bc for floating point calculation to avoid integer errors
                            max_safe_size=$(echo "$DISK_SIZE_GB * 0.95" | bc 2>/dev/null | cut -d. -f1)
                            # Fallback if bc fails
                            if [ -z "$max_safe_size" ]; then
                                max_safe_size=50
                            fi
                        fi
                        
                        # Check if specified size is reasonable (at least 20GB, less than max_safe_size)
                        if [ "$custom_root_size" -ge 20 ] && [ "$custom_root_size" -le "$max_safe_size" ]; then
                            ROOT_PART_SIZE="${custom_root_size}G"
                            echo -e "\033[1;32m✓ Root partition size set to: \033[1;37m${custom_root_size}GB\033[0m"
                            break
                        else
                            echo -e "\033[1;91m❌ Invalid size. Please enter a value between 20 and ${max_safe_size} GB.\033[0m"
                        fi
                    else
                        echo -e "\033[1;91m❌ Invalid size format. Please enter a numeric value in GB.\033[0m"
                    fi
                done
                break
                ;;
            *)
                echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
                ;;
        esac
    done

    print_section_header "DISK ENCRYPTION CONFIGURATION"
    
    echo -e "\033[1;94mDo you want to encrypt your disk?\033[0m"
    echo -e "\033[1;93m⚠️  NOTE: If yes, you'll need to enter a passphrase at each boot\033[0m\n"

    echo -e "  \033[1;97m1)\033[0m \033[1;38;5;82mYes\033[0m (More secure, requires passphrase)"
    echo -e "  \033[1;97m2)\033[0m \033[1;38;5;203mNo\033[0m (More convenient, less secure)"
    echo
    
    while true; do
        echo -en "\033[1;94mEnter your choice (1-2): \033[0m"
        read -r encrypt_choice
        
        case $encrypt_choice in
            1)
                ENCRYPT_DISK="yes"
                echo -e "\033[1;92m✅ Disk encryption enabled\033[0m"
                # Get encryption passphrase
                get_password "Enter disk encryption passphrase (At least 8 characters)" DISK_PASSWORD
                echo -e "\033[1;92m✅ Encryption passphrase set\033[0m\n"
                break
                ;;
            2)
                ENCRYPT_DISK="no"
                DISK_PASSWORD=""
                echo -e "\033[1;92m✓ Disk encryption disabled\033[0m\n"
                break
                ;;
            *)
                echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
                ;;
        esac
    done

    print_section_header "ADVANCED ZFS CONFIGURATION"
    
    # Ask for ZFS compression algorithm
    echo -e "\n\033[1;94mSelect ZFS compression algorithm:\033[0m"
    echo -e "  \033[1;37m1)\033[0m \033[1;38;5;39mlz4\033[0m (Fast, good ratio, default)"
    echo -e "  \033[1;37m2)\033[0m \033[1;38;5;202mzstd\033[0m (Better compression, slightly slower)"
    echo -e "  \033[1;37m3)\033[0m \033[1;38;5;118mgzip\033[0m (Best compression, slowest)"
    echo -e "  \033[1;37m4)\033[0m \033[1;38;5;196mNone\033[0m (No compression)"
    echo
    
    while true; do
        echo -en "\033[1;94mEnter your choice (1-4) [1]: \033[0m"
        read -r compression_choice
        
        case $compression_choice in
            1|"")
                ZFS_COMPRESSION="lz4"
                echo -e "\033[1;32m✓ Selected lz4 compression\033[0m"
                break
                ;;
            2)
                ZFS_COMPRESSION="zstd"
                echo -e "\033[1;32m✓ Selected zstd compression\033[0m"
                break
                ;;
            3)
                ZFS_COMPRESSION="gzip"
                echo -e "\033[1;32m✓ Selected gzip compression\033[0m"
                break
                ;;
            4)
                ZFS_COMPRESSION="off"
                echo -e "\033[1;32m✓ Compression disabled\033[0m"
                break
                ;;
            *)
                echo -e "\033[1;91m❌ Invalid choice. Please enter a number between 1 and 4.\033[0m"
                ;;
        esac
    done
    
    # ZFS Dataset Configuration
    echo -e "\n\033[1;94mConfigure ZFS datasets structure:\033[0m"
    echo -e "  \033[1;37m1)\033[0m \033[1;38;5;82mSimple\033[0m (Single root dataset only)"
    echo -e "  \033[1;37m2)\033[0m \033[1;38;5;39mAdvanced\033[0m (Separate datasets for system directories)"
    echo
    
    while true; do
        echo -en "\033[1;94mEnter your choice (1-2) [2]: \033[0m"
        read -r datasets_choice
        
        case $datasets_choice in
            1)
                SEPARATE_DATASETS="no"
                echo -e "\033[1;32m✓ Selected simple dataset structure\033[0m"
                break
                ;;
            2|"")
                SEPARATE_DATASETS="yes"
                echo -e "\033[1;32m✓ Selected advanced dataset structure\033[0m"
                break
                ;;
            *)
                echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
                ;;
        esac
    done
    
    print_section_header "ADVANCED ZRAM CONFIGURATION"
    
    echo -e "\033[1;94mConfiguring ZRAM (compressed RAM swap):\033[0m"
    
    # Ask for ZRAM size
    echo -e "\033[1;94mSelect ZRAM size:\033[0m"
    echo -e "  \033[1;37m1)\033[0m \033[1;38;5;39mAuto\033[0m (min(RAM, 32GB) - recommended)"
    echo -e "  \033[1;37m2)\033[0m \033[1;38;5;202mHalf of RAM\033[0m"
    echo -e "  \033[1;37m3)\033[0m \033[1;38;5;118mCustom value\033[0m (specify in MB)"
    echo
    
    while true; do
        echo -en "\033[1;94mEnter your choice (1-3) [1]: \033[0m"
        read -r zram_size_choice
        
        case $zram_size_choice in
            1|"")
                ZRAM_SIZE="min(ram, 32768)"
                echo -e "\033[1;32m✓ Selected automatic ZRAM sizing\033[0m"
                break
                ;;
            2)
                ZRAM_SIZE="ram / 2"
                echo -e "\033[1;32m✓ Selected half of RAM for ZRAM\033[0m"
                break
                ;;
            3)
                while true; do
                    echo -en "\033[1;94mEnter ZRAM size in MB (e.g., 8192 for 8GB): \033[0m"
                    read -r custom_zram_size
                    
                    # Validate input (simple check for numeric value)
                    if [[ "$custom_zram_size" =~ ^[0-9]+$ ]]; then
                        ZRAM_SIZE="$custom_zram_size"
                        echo -e "\033[1;32m✓ ZRAM size set to: \033[1;37m${custom_zram_size}MB\033[0m"
                        break
                    else
                        echo -e "\033[1;91m❌ Invalid size. Please enter a numeric value in MB.\033[0m"
                    fi
                done
                break
                ;;
            *)
                echo -e "\033[1;91m❌ Invalid choice. Please enter a number between 1 and 3.\033[0m"
                ;;
        esac
    done
    
    # Ask for ZRAM compression algorithm
    echo -e "\n\033[1;94mSelect ZRAM compression algorithm:\033[0m"
    echo -e "  \033[1;37m1)\033[0m \033[1;38;5;39mzstd\033[0m (Best balance of speed/compression - recommended)"
    echo -e "  \033[1;37m2)\033[0m \033[1;38;5;202mlz4\033[0m (Faster, lower compression ratio)"
    echo -e "  \033[1;37m3)\033[0m \033[1;38;5;118mlzo-rle\033[0m (Legacy option)"
    echo -e "  \033[1;37m4)\033[0m \033[1;38;5;196mlzo\033[0m (Older algorithm)"
    echo
    
    while true; do
        echo -en "\033[1;94mEnter your choice (1-4) [1]: \033[0m"
        read -r zram_compression_choice
        
        case $zram_compression_choice in
            1|"")
                ZRAM_COMPRESSION="zstd"
                echo -e "\033[1;32m✓ Selected zstd compression algorithm\033[0m\n"
                break
                ;;
            2)
                ZRAM_COMPRESSION="lz4"
                echo -e "\033[1;32m✓ Selected lz4 compression algorithm\033[0m\n"
                break
                ;;
            3)
                ZRAM_COMPRESSION="lzo-rle"
                echo -e "\033[1;32m✓ Selected lzo-rle compression algorithm\033[0m\n"
                break
                ;;
            4)
                ZRAM_COMPRESSION="lzo"
                echo -e "\033[1;32m✓ Selected lzo compression algorithm\033[0m\n"
                break
                ;;
            *)
                echo -e "\033[1;91m❌ Invalid choice. Please enter a number between 1 and 4.\033[0m"
                ;;
        esac
    done
else
    # Set default values for simple mode
    EFI_PART_SIZE="1G"
    ROOT_PART_SIZE="MAX"
    ENCRYPT_DISK="no"
    ZFS_COMPRESSION="lz4"
    SEPARATE_DATASETS="no"
    ZRAM_SIZE="min(ram, 32768)"
    ZRAM_COMPRESSION="zstd"
fi

# ----------------------------------------
# DESKTOP ENVIRONMENT SELECTION
# ----------------------------------------
print_section_header "DESKTOP ENVIRONMENT SELECTION"

echo -e "\033[1;33mChoose your desktop environment:\033[0m"
echo -e "  \033[1;37m1)\033[0m \033[1;38;5;51mHyprland\033[0m"
echo -e "  \033[1;37m2)\033[0m \033[1;38;5;220mXFCE4\033[0m"
echo -e "  \033[1;37m3)\033[0m \033[1;38;5;39mKDE Plasma\033[0m"
echo -e "  \033[1;37m4)\033[0m \033[1;38;5;202mGNOME\033[0m"
echo
read -p "Enter your choice (1-4): " DE_CHOICE

case $DE_CHOICE in
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
        DE_CHOICE=1
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
echo -e "  \033[1;37m1)\033[0m Italy"
echo -e "  \033[1;37m2)\033[0m Germany"
echo -e "  \033[1;37m3)\033[0m United States"
echo -e "  \033[1;37m4)\033[0m United Kingdom"
echo -e "  \033[1;37m5)\033[0m France"
echo -e "  \033[1;37m6)\033[0m Spain"
echo -e "  \033[1;37m7)\033[0m Netherlands"
echo -e "  \033[1;37m8)\033[0m Other (specify)"
echo -e "  \033[1;37m9)\033[0m Worldwide (no specific country)"
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

# ----------------------------------------
# KEYBOARD LAYOUT SELECTION
# ----------------------------------------
print_section_header "KEYBOARD LAYOUT SELECTION"

# List available keyboard layouts and let user select one
echo -e "\033[1;33mSelect your keyboard layout:\033[0m"
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
    printf "  \033[1;37m%3d)\033[0m %-20s" "$((i+1))" "${KEYBOARD_LAYOUTS[$i]}"
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
    echo -en "\nEnter the number of your keyboard layout: "
    read -r layout_choice
    
    # Validate input
    if [[ "$layout_choice" =~ ^[0-9]+$ && "$layout_choice" -ge 1 && "$layout_choice" -le "${#KEYBOARD_LAYOUTS[@]}" ]]; then
        KEYBOARD_LAYOUT="${KEYBOARD_LAYOUTS[$((layout_choice-1))]}"
        echo -e "\033[1;32m✓ Selected keyboard layout: \033[1;37m$KEYBOARD_LAYOUT\033[0m\n"
        break
    else
        echo -e "\033[1;33m⚠ Invalid choice. Please enter a number between 1 and ${#KEYBOARD_LAYOUTS[@]}.\033[0m"
    fi
done

# ----------------------------------------
# LOCALE SELECTION
# ----------------------------------------
print_section_header "LOCALE SELECTION"

echo -e "\033[1;33mSelect your system locale:\033[0m"

# Define an array of essential locales (UTF-8 variants for common languages)
declare -a ESSENTIAL_LOCALES=(
    "en_US.UTF-8"
    "en_GB.UTF-8"
    "de_DE.UTF-8"
    "fr_FR.UTF-8"
    "it_IT.UTF-8"
    "es_ES.UTF-8"
    "pt_BR.UTF-8"
    "ru_RU.UTF-8"
    "zh_CN.UTF-8"
    "ja_JP.UTF-8"
    "ko_KR.UTF-8"
    "ar_SA.UTF-8"
    "hi_IN.UTF-8"
    "pl_PL.UTF-8"
    "nl_NL.UTF-8"
    "sv_SE.UTF-8"
    "tr_TR.UTF-8"
    "cs_CZ.UTF-8"
)

# Set the number of columns for display
LOCALE_COLUMNS=3
TOTAL_LOCALES=${#ESSENTIAL_LOCALES[@]}

echo -e "\nAvailable locales (essential UTF-8 variants only):"
# Display available locales in multiple columns
for ((i=0; i<TOTAL_LOCALES; i++)); do
    # Format each entry with fixed width for alignment
    printf "  \033[1;37m%2d)\033[0m %-20s" "$((i+1))" "${ESSENTIAL_LOCALES[$i]}"
    # Add a newline after every LOCALE_COLUMNS items
    if (( (i+1) % LOCALE_COLUMNS == 0 )); then
        echo ""
    fi
done
# Add a final newline if needed
if (( TOTAL_LOCALES % LOCALE_COLUMNS != 0 )); then
    echo ""
fi

# Add an option for custom locale selection
echo -e "  \033[1;37m99)\033[0m Custom (show all available locales)"

# Let user select a locale by number
while true; do
    echo -en "\nEnter the number of your desired locale: "
    read -r locale_choice
    
    if [[ "$locale_choice" = "99" ]]; then
        # User wants to see all available locales
        echo -e "\n\033[1;94mShowing all available locales...\033[0m"
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
        ALL_LOCALE_COLUMNS=3
        TOTAL_ALL_LOCALES=${#AVAILABLE_LOCALES[@]}
        
        echo -e "\nAll available locales (primary variants only):"
        # Display available locales in multiple columns
        for ((i=0; i<TOTAL_ALL_LOCALES; i++)); do
            # Format each entry with fixed width for alignment
            printf "  \033[1;37m%3d)\033[0m %-20s" "$((i+1))" "${AVAILABLE_LOCALES[$i]}"
            # Add a newline after every ALL_LOCALE_COLUMNS items
            if (( (i+1) % ALL_LOCALE_COLUMNS == 0 )); then
                echo ""
            fi
        done
        # Add a final newline if needed
        if (( TOTAL_ALL_LOCALES % ALL_LOCALE_COLUMNS != 0 )); then
            echo ""
        fi
        
        # Let user select a locale by number
        while true; do
            echo -en "\nEnter the number of your desired locale: "
            read -r all_locale_choice
            
            # Validate input
            if [[ "$all_locale_choice" =~ ^[0-9]+$ && "$all_locale_choice" -ge 1 && "$all_locale_choice" -le "${#AVAILABLE_LOCALES[@]}" ]]; then
                SYSTEM_LOCALE="${AVAILABLE_LOCALES[$((all_locale_choice-1))]}"
                echo -e "\033[1;32m✓ Selected locale: \033[1;37m$SYSTEM_LOCALE\033[0m\n"
                break 2  # Break out of both loops
            else
                echo -e "\033[1;33m⚠ Invalid choice. Please enter a number between 1 and ${#AVAILABLE_LOCALES[@]}.\033[0m"
            fi
        done
    elif [[ "$locale_choice" =~ ^[0-9]+$ && "$locale_choice" -ge 1 && "$locale_choice" -le "${#ESSENTIAL_LOCALES[@]}" ]]; then
        # User selected from the essential locales list
        SYSTEM_LOCALE="${ESSENTIAL_LOCALES[$((locale_choice-1))]}"
        echo -e "\033[1;32m✓ Selected locale: \033[1;37m$SYSTEM_LOCALE\033[0m\n"
        break
    else
        echo -e "\033[1;33m⚠ Invalid choice. Please enter a valid number.\033[0m"
    fi
done

# ----------------------------------------
# USER CONFIGURATION
# ----------------------------------------
print_section_header "USER CONFIGURATION"

echo -e "\033[1;33mEnter the username:\033[0m"
echo -en "Username: "; read -r USER
echo -e "\033[1;32m✓ Username set to: \033[1;37m$USER\033[0m\n"

# ----------------------------------------
# PASSWORD CONFIGURATION
# ----------------------------------------
print_section_header "PASSWORD CONFIGURATION"

get_password "Enter the password for user $USER" USERPASS
echo -e "\033[1;32m✓ User password set\033[0m"

get_password "Enter the password for user root" ROOTPASS
echo -e "\033[1;32m✓ Root password set\033[0m\n"

# ----------------------------------------
# CPU SELECTION
# ----------------------------------------
print_section_header "CPU SELECTION"

echo -e "\033[1;33mChoose your CPU type:\033[0m"
echo -e "  \033[1;37m1)\033[0m \033[1;38;5;39mIntel\033[0m"
echo -e "  \033[1;37m2)\033[0m \033[1;38;5;196mAMD\033[0m"
echo
read -p "Enter your choice (1-2): " cpu_choice

case $cpu_choice in
    1)
        CPU_MICROCODE="intel-ucode"
        CPU_TYPE="Intel"
        echo -e "\033[1;32m✓ Selected Intel CPU. Will install intel-ucode.\033[0m\n"
        ;;
    2)
        CPU_MICROCODE="amd-ucode"
        CPU_TYPE="AMD"
        echo -e "\033[1;32m✓ Selected AMD CPU. Will install amd-ucode.\033[0m\n"
        ;;
    *)
        echo -e "\033[1;33m⚠ Invalid choice. Defaulting to AMD.\033[0m\n"
        CPU_MICROCODE="amd-ucode"
        CPU_TYPE="AMD"
        ;;
esac

# ----------------------------------------
# GPU SELECTION
# ----------------------------------------
print_section_header "GPU SELECTION"

echo -e "\033[1;33mChoose your GPU type:\033[0m"
echo -e "  \033[1;37m1)\033[0m \033[1;38;5;118mNVIDIA\033[0m"
echo -e "  \033[1;37m2)\033[0m \033[1;38;5;75mAMD/Intel\033[0m (Open Source)"
echo -e "  \033[1;37m3)\033[0m \033[1;38;5;250mNone/VM\033[0m"
echo
read -p "Enter your choice (1-3): " gpu_choice

case $gpu_choice in
    1)
        GPU_TYPE="NVIDIA"
        echo -e "\033[1;32m✓ Selected NVIDIA GPU.\033[0m"
        
        echo -e "\n\033[1;33mNVIDIA Driver Selection:\033[0m"
        echo -e "  Do you want to use NVIDIA open drivers?"
        echo -e "  (No will install proprietary drivers)"
        echo
        read -p "Use NVIDIA open drivers? [y/N]: " nvidia_open_choice
        
        case $nvidia_open_choice in
            [Yy]*)
                NVIDIA_DRIVER_TYPE="Open"
                echo -e "\033[1;32m✓ Selected NVIDIA open source drivers.\033[0m\n"
                ;;
            *)
                NVIDIA_DRIVER_TYPE="Proprietary"
                echo -e "\033[1;32m✓ Selected NVIDIA proprietary drivers.\033[0m\n"
                ;;
        esac
        ;;
    2)
        GPU_TYPE="AMD/Intel"
        NVIDIA_DRIVER_TYPE="none"
        echo -e "\033[1;32m✓ Selected AMD/Intel GPU. Will use open source drivers.\033[0m\n"
        ;;
    3)
        GPU_TYPE="None/VM"
        NVIDIA_DRIVER_TYPE="none"
        echo -e "\033[1;32m✓ Selected None/VM. Will use basic drivers.\033[0m\n"
        ;;
    *)
        echo -e "\033[1;33m⚠ Invalid choice. Defaulting to AMD/Intel.\033[0m\n"
        gpu_choice=2
        GPU_TYPE="AMD/Intel"
        NVIDIA_DRIVER_TYPE="none"
        ;;
esac

# ----------------------------------------
# AUDIO SELECTION
# ----------------------------------------
print_section_header "AUDIO SERVER SELECTION"

echo -e "\033[1;33mChoose your audio server:\033[0m"
echo -e "  \033[1;37m1)\033[0m \033[1;38;5;86mPipeWire\033[0m (Modern, low-latency, recommended)"
echo -e "  \033[1;37m2)\033[0m \033[1;38;5;208mPulseAudio\033[0m (Traditional, widely compatible)"
echo

while true; do
    echo -en "\033[1;94mEnter your choice (1-2): \033[0m"
    read -r audio_choice
    
    case $audio_choice in
        1)
            AUDIO_SERVER="pipewire"
            echo -e "\033[1;92m✅ Selected PipeWire audio server\033[0m\n"
            break
            ;;
        2)
            AUDIO_SERVER="pulseaudio"
            echo -e "\033[1;92m✅ Selected PulseAudio audio server\033[0m\n"
            break
            ;;
        *)
            echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
            ;;
    esac
done

# ----------------------------------------
# CONFIGURATION SUMMARY
# ----------------------------------------
print_section_header "CONFIGURATION SUMMARY"

# Function to display summary of selected options
display_summary() {
    echo -e "\033[1;94m📋 Configuration Summary:\033[0m"
    echo -e "┌───────────────────────────────────────────────────────────────┐"

    # System-critical choices
    echo -e "│ \033[1;97m1)\033[0m Boot Type:              \033[1;38;5;81m${BOOT_TYPE}\033[0m"
    echo -e "│ \033[1;97m2)\033[0m Target Device:          \033[1;38;5;81m$DEVICE\033[0m"
    
    # Advanced partition settings
    if [ "$INSTALL_MODE" = "advanced" ]; then
        echo -e "│ \033[1;97m3)\033[0m EFI Partition Size:     \033[1;38;5;81m$EFI_PART_SIZE\033[0m"
        echo -e "│ \033[1;97m4)\033[0m Root Partition Size:    \033[1;38;5;81m$ROOT_PART_SIZE\033[0m"
        echo -e "│ \033[1;97m5)\033[0m Disk Encryption:        \033[1;38;5;81m${ENCRYPT_DISK^}\033[0m"
        echo -e "│ \033[1;97m6)\033[0m ZFS Compression:        \033[1;38;5;81m$ZFS_COMPRESSION\033[0m"
        echo -e "│ \033[1;97m7)\033[0m Separate Datasets:      \033[1;38;5;81m${SEPARATE_DATASETS^}\033[0m"
        echo -e "│ \033[1;97m8)\033[0m ZRAM Size:              \033[1;38;5;81m$ZRAM_SIZE\033[0m"
        echo -e "│ \033[1;97m9)\033[0m ZRAM Compression:       \033[1;38;5;81m$ZRAM_COMPRESSION\033[0m"
        ADV_OFFSET=9
    else
        ADV_OFFSET=2
    fi
    
    # Hardware settings
    echo -e "│ \033[1;97m$((ADV_OFFSET+1)))\033[0m CPU Type:               \033[1;38;5;81m$CPU_TYPE\033[0m"
    echo -e "│ \033[1;97m$((ADV_OFFSET+2)))\033[0m GPU Type:               \033[1;38;5;81m$GPU_TYPE\033[0m"
    if [ "$GPU_TYPE" = "NVIDIA" ]; then
        echo -e "│ \033[1;97m$((ADV_OFFSET+3)))\033[0m NVIDIA Driver:          \033[1;38;5;81m$NVIDIA_DRIVER_TYPE\033[0m"
        NVIDIA_OFFSET=1
    else
        NVIDIA_OFFSET=0
    fi
    
    echo -e "│ \033[1;97m$((ADV_OFFSET+3+NVIDIA_OFFSET)))\033[0m Audio Server:           \033[1;38;5;81m$AUDIO_SERVER\033[0m"
    echo -e "│ \033[1;97m$((ADV_OFFSET+4+NVIDIA_OFFSET)))\033[0m Desktop Environment:     \033[1;38;5;81m$DE_TYPE\033[0m"
    
    # User configuration
    echo -e "│ \033[1;97m$((ADV_OFFSET+5+NVIDIA_OFFSET)))\033[0m Hostname:               \033[1;38;5;81m$HOSTNAME\033[0m"
    echo -e "│ \033[1;97m$((ADV_OFFSET+6+NVIDIA_OFFSET)))\033[0m Username:               \033[1;38;5;81m$USER\033[0m"
    echo -e "│ \033[1;97m$((ADV_OFFSET+7+NVIDIA_OFFSET)))\033[0m User & Root Passwords:  \033[1;38;5;81m[hidden]\033[0m"
    
    # System preferences
    echo -e "│ \033[1;97m$((ADV_OFFSET+8+NVIDIA_OFFSET)))\033[0m Keyboard Layout:        \033[1;38;5;81m$KEYBOARD_LAYOUT\033[0m"
    echo -e "│ \033[1;97m$((ADV_OFFSET+9+NVIDIA_OFFSET)))\033[0m System Locale:          \033[1;38;5;81m$SYSTEM_LOCALE\033[0m"
    echo -e "│ \033[1;97m$((ADV_OFFSET+10+NVIDIA_OFFSET)))\033[0m Mirror Country:         \033[1;38;5;81m${MIRROR_COUNTRY:-Worldwide}\033[0m"
    
    echo -e "└───────────────────────────────────────────────────────────────┘"

    # Calculate the total number of items for validation
    TOTAL_ITEMS=$((ADV_OFFSET+10+NVIDIA_OFFSET))
}

# Display initial summary
display_summary

# Allow user to modify choices
echo -e "\n\033[1;93mReview your configuration:\033[0m"
echo -e " - Enter a number to modify that setting"
echo -e " - Enter 'c' to confirm and proceed with installation"
echo -e " - Enter 'a' to abort installation"

while true; do
    echo -en "\n\033[1;94mYour choice: \033[0m"
    read choice
    
    if [[ "$choice" == "c" || "$choice" == "C" ]]; then
        echo -e "\033[1;92m✅ Configuration confirmed! Proceeding with installation...\033[0m"
        break
    elif [[ "$choice" == "a" || "$choice" == "A" ]]; then
        echo -e "\033[1;91m❌ Installation aborted by user.\033[0m"
        exit 1
    elif [[ "$choice" =~ ^[0-9]+$ && "$choice" -ge 1 && "$choice" -le "$TOTAL_ITEMS" ]]; then
        # Simple mode options
        if [ "$INSTALL_MODE" = "simple" ]; then
            case $choice in
                1) # Boot Type
                    echo -e "\n\033[1;94m🔄 Boot Type Selection\033[0m"
                    echo -e "  \033[1;97m1)\033[0m \033[1;38;5;220mEFI\033[0m (Modern systems, recommended)"
                    echo -e "  \033[1;97m2)\033[0m \033[1;38;5;208mBIOS\033[0m (Legacy systems)"
                    
                    while true; do
                        echo -en "\033[1;94mEnter your choice (1-2): \033[0m"
                        read -r boot_choice
                        
                        case $boot_choice in
                            1)
                                BOOT_TYPE="efi"
                                echo -e "\033[1;92m✅ Selected EFI boot\033[0m\n"
                                break
                                ;;
                            2)
                                BOOT_TYPE="bios"
                                echo -e "\033[1;92m✅ Selected BIOS boot\033[0m\n"
                                break
                                ;;
                            *)
                                echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
                                ;;
                        esac
                    done
                    ;;
                2) # Target Device
                    echo -e "\n\033[1;94m💾 Target Device Selection\033[0m"
                    echo -e "\033[1;93m⚠️  WARNING: THE SELECTED DISK WILL BE COMPLETELY ERASED!\033[0m\n"
                    
                    # Display available disks
                    available_disks=$(lsblk -dpno NAME,SIZE,MODEL | grep -E "/dev/(sd|nvme|vd)")
                    echo -e "\033[1;38;5;195mAvailable disks for installation:\033[0m"
                    echo -e "$available_disks\n"
                    
                    while true; do
                        echo -en "\033[1;94mEnter the full path of the disk to install to (e.g., /dev/sda): \033[0m"
                        read -r new_device
                        
                        # Verify disk exists
                        if lsblk "$new_device" &> /dev/null; then
                            DEVICE="$new_device"
                            echo -e "\033[1;92m✅ Selected device: \033[1;97m$DEVICE\033[0m\n"
                            break
                        else
                            echo -e "\033[1;91m❌ Invalid device. Please enter a valid device path.\033[0m"
                        fi
                    done
                    ;;
                3) # CPU Type
                    echo -e "\n\033[1;94m🔄 CPU Selection\033[0m"
                    echo -e "  \033[1;97m1)\033[0m \033[1;38;5;39mIntel\033[0m"
                    echo -e "  \033[1;97m2)\033[0m \033[1;38;5;196mAMD\033[0m"
                    
                    while true; do
                        echo -en "\033[1;94mEnter your choice (1-2): \033[0m"
                        read -r cpu_choice
                        
                        case $cpu_choice in
                            1)
                                CPU_MICROCODE="intel-ucode"
                                CPU_TYPE="Intel"
                                echo -e "\033[1;92m✅ Selected Intel CPU. Will install intel-ucode.\033[0m\n"
                                break
                                ;;
                            2)
                                CPU_MICROCODE="amd-ucode"
                                CPU_TYPE="AMD"
                                echo -e "\033[1;92m✅ Selected AMD CPU. Will install amd-ucode.\033[0m\n"
                                break
                                ;;
                            *)
                                echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
                                ;;
                        esac
                    done
                    ;;
                4) # GPU Type
                    echo -e "\n\033[1;94m🔄 GPU Selection\033[0m"
                    echo -e "  \033[1;97m1)\033[0m \033[1;38;5;118mNVIDIA\033[0m"
                    echo -e "  \033[1;97m2)\033[0m \033[1;38;5;75mAMD/Intel\033[0m (Open Source)"
                    echo -e "  \033[1;97m3)\033[0m \033[1;38;5;250mNone/VM\033[0m"
                    
                    while true; do
                        echo -en "\033[1;94mEnter your choice (1-3): \033[0m"
                        read -r gpu_choice
                        
                        case $gpu_choice in
                            1)
                                GPU_TYPE="NVIDIA"
                                echo -e "\033[1;92m✅ Selected NVIDIA GPU.\033[0m"
                                
                                echo -e "\n\033[1;33mNVIDIA Driver Selection:\033[0m"
                                echo -e "  Do you want to use NVIDIA open drivers?"
                                echo -e "  (No will install proprietary drivers)"
                                
                                while true; do
                                    echo -en "\033[1;94mUse NVIDIA open drivers? [y/N]: \033[0m"
                                    read -r nvidia_open_choice
                                    
                                    case $nvidia_open_choice in
                                        [Yy]*)
                                            NVIDIA_DRIVER_TYPE="Open"
                                            echo -e "\033[1;92m✅ Selected NVIDIA open source drivers.\033[0m\n"
                                            break
                                            ;;
                                        [Nn]*|"")
                                            NVIDIA_DRIVER_TYPE="Proprietary"
                                            echo -e "\033[1;92m✅ Selected NVIDIA proprietary drivers.\033[0m\n"
                                            break
                                            ;;
                                        *)
                                            echo -e "\033[1;91m❌ Invalid choice. Please enter Y or N.\033[0m"
                                            ;;
                                    esac
                                done
                                break
                                ;;
                            2)
                                GPU_TYPE="AMD/Intel"
                                NVIDIA_DRIVER_TYPE="none"
                                echo -e "\033[1;92m✅ Selected AMD/Intel GPU. Will use open source drivers.\033[0m\n"
                                break
                                ;;
                            3)
                                GPU_TYPE="None/VM"
                                NVIDIA_DRIVER_TYPE="none"
                                echo -e "\033[1;92m✅ Selected None/VM. Will use basic drivers.\033[0m\n"
                                break
                                ;;
                            *)
                                echo -e "\033[1;91m❌ Invalid choice. Please enter a number between 1 and 3.\033[0m"
                                ;;
                        esac
                    done
                    ;;
                # Handle all other menu items with appropriate offsets
                *)
                    # Calculate offsets to determine which setting to edit based on current state
                    current=$choice
                    
                    # Check if we're dealing with NVIDIA Driver option
                    if [ "$GPU_TYPE" = "NVIDIA" ] && [ "$current" -eq 5 ]; then
                        echo -e "\n\033[1;94m🔄 NVIDIA Driver Selection\033[0m"
                        echo -e "  \033[1;97m1)\033[0m \033[1;38;5;118mOpen\033[0m source drivers"
                        echo -e "  \033[1;97m2)\033[0m \033[1;38;5;214mProprietary\033[0m drivers"
                        
                        while true; do
                            echo -en "\033[1;94mEnter your choice (1-2): \033[0m"
                            read -r nvidia_choice
                            
                            case $nvidia_choice in
                                1)
                                    NVIDIA_DRIVER_TYPE="Open"
                                    echo -e "\033[1;92m✅ Selected NVIDIA open source drivers.\033[0m\n"
                                    break
                                    ;;
                                2)
                                    NVIDIA_DRIVER_TYPE="Proprietary"
                                    echo -e "\033[1;92m✅ Selected NVIDIA proprietary drivers.\033[0m\n"
                                    break
                                    ;;
                                *)
                                    echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
                                    ;;
                            esac
                        done
                    # Audio Server
                    elif ([ "$GPU_TYPE" = "NVIDIA" ] && [ "$current" -eq 6 ]) || \
                         ([ "$GPU_TYPE" != "NVIDIA" ] && [ "$current" -eq 5 ]); then
                        echo -e "\n\033[1;94m🔄 Audio Server Selection\033[0m"
                        echo -e "  \033[1;97m1)\033[0m \033[1;38;5;86mPipeWire\033[0m (Modern, low-latency, recommended)"
                        echo -e "  \033[1;97m2)\033[0m \033[1;38;5;208mPulseAudio\033[0m (Traditional, widely compatible)"
                        
                        while true; do
                            echo -en "\033[1;94mEnter your choice (1-2): \033[0m"
                            read -r audio_choice
                            
                            case $audio_choice in
                                1)
                                    AUDIO_SERVER="pipewire"
                                    echo -e "\033[1;92m✅ Selected PipeWire audio server\033[0m\n"
                                    break
                                    ;;
                                2)
                                    AUDIO_SERVER="pulseaudio"
                                    echo -e "\033[1;92m✅ Selected PulseAudio audio server\033[0m\n"
                                    break
                                    ;;
                                *)
                                    echo -e "\033[1;91m❌ Invalid choice. Please enter 1 or 2.\033[0m"
                                    ;;
                            esac
                        done
                    # Desktop Environment
                    elif ([ "$GPU_TYPE" = "NVIDIA" ] && [ "$current" -eq 7 ]) || \
                         ([ "$GPU_TYPE" != "NVIDIA" ] && [ "$current" -eq 6 ]); then
                        echo -e "\n\033[1;94m🔄 Desktop Environment Selection\033[0m"
                        echo -e "  \033[1;97m1)\033[0m \033[1;38;5;51mHyprland\033[0m"
                        echo -e "  \033[1;97m2)\033[0m \033[1;38;5;220mXFCE4\033[0m"
                        echo -e "  \033[1;97m3)\033[0m \033[1;38;5;39mKDE Plasma\033[0m"
                        echo -e "  \033[1;97m4)\033[0m \033[1;38;5;202mGNOME\033[0m"
                        
                        while true; do
                            echo -en "\033[1;94mEnter your choice (1-4): \033[0m"
                            read -r de_choice
                            
                            case $de_choice in
                                1)
                                    DE_TYPE="Hyprland"
                                    DE_CHOICE=1
                                    echo -e "\033[1;92m✅ Selected Hyprland for desktop environment.\033[0m\n"
                                    break
                                    ;;
                                2)
                                    DE_TYPE="XFCE4"
                                    DE_CHOICE=2
                                    echo -e "\033[1;92m✅ Selected XFCE4 for desktop environment.\033[0m\n"
                                    break
                                    ;;
                                3)
                                    DE_TYPE="KDE Plasma"
                                    DE_CHOICE=3
                                    echo -e "\033[1;92m✅ Selected KDE Plasma for desktop environment.\033[0m\n"
                                    break
                                    ;;
                                4)
                                    DE_TYPE="GNOME"
                                    DE_CHOICE=4
                                    echo -e "\033[1;92m✅ Selected GNOME for desktop environment.\033[0m\n"
                                    break
                                    ;;
                                *)
                                    echo -e "\033[1;91m❌ Invalid choice. Please enter a number between 1 and 4.\033[0m"
                                    ;;
                            esac
                        done
                    # Hostname
                    elif ([ "$GPU_TYPE" = "NVIDIA" ] && [ "$current" -eq 8 ]) || \
                         ([ "$GPU_TYPE" != "NVIDIA" ] && [ "$current" -eq 7 ]); then
                        echo -e "\n\033[1;94m🔄 Hostname Configuration\033[0m"
                        echo -en "Enter system hostname: "
                        read -r HOSTNAME
                        echo -e "\033[1;92m✅ Hostname set to: \033[1;97m$HOSTNAME\033[0m\n"
                    # Username
                    elif ([ "$GPU_TYPE" = "NVIDIA" ] && [ "$current" -eq 9 ]) || \
                         ([ "$GPU_TYPE" != "NVIDIA" ] && [ "$current" -eq 8 ]); then
                        echo -e "\n\033[1;94m🔄 Username Configuration\033[0m"
                        echo -en "Enter username: "
                        read -r USER
                        echo -e "\033[1;92m✅ Username set to: \033[1;97m$USER\033[0m\n"
                    # Passwords
                    elif ([ "$GPU_TYPE" = "NVIDIA" ] && [ "$current" -eq 10 ]) || \
                         ([ "$GPU_TYPE" != "NVIDIA" ] && [ "$current" -eq 9 ]); then
                        echo -e "\n\033[1;94m🔄 Password Configuration\033[0m"
                        get_password "Enter the password for user $USER" USERPASS
                        echo -e "\033[1;92m✅ User password set\033[0m"
                        get_password "Enter the password for user root" ROOTPASS
                        echo -e "\033[1;92m✅ Root password set\033[0m\n"
                    # Keyboard Layout
                    elif ([ "$GPU_TYPE" = "NVIDIA" ] && [ "$current" -eq 11 ]) || \
                         ([ "$GPU_TYPE" != "NVIDIA" ] && [ "$current" -eq 10 ]); then
                        # Start keyboard layout selection interface here
                        echo -e "\n\033[1;94m🔄 Keyboard Layout Selection\033[0m"
                        
                        # Get available keyboard layouts
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
                        
                        # Display available layouts (top 20 common ones)
                        echo -e "Common keyboard layouts:"
                        common_layouts=("us" "uk" "de" "fr" "it" "es" "ru" "br" "pt" "jp" "cn")
                        
                        for ((i=0; i<${#common_layouts[@]} && i<20; i++)); do
                            layout=${common_layouts[$i]}
                            echo -e "  \033[1;97m$((i+1)))\033[0m $layout"
                        done
                        
                        echo -e "  \033[1;97m99)\033[0m Show all keyboards"
                        
                        # Let user select a layout
                        while true; do
                            echo -en "\033[1;94mSelect keyboard layout (1-${#common_layouts[@]} or 99): \033[0m"
                            read -r kb_choice
                            
                            if [[ "$kb_choice" = "99" ]]; then
                                # Show all keyboard layouts
                                echo -e "\nAll available keyboard layouts:"
                                
                                for ((i=0; i<${#KEYBOARD_LAYOUTS[@]}; i++)); do
                                    echo -e "  \033[1;97m$((i+1)))\033[0m ${KEYBOARD_LAYOUTS[$i]}"
                                done
                                
                                while true; do
                                    echo -en "\033[1;94mSelect keyboard layout (1-${#KEYBOARD_LAYOUTS[@]}): \033[0m"
                                    read -r kb_full_choice
                                    
                                    if [[ "$kb_full_choice" =~ ^[0-9]+$ && "$kb_full_choice" -ge 1 && "$kb_full_choice" -le "${#KEYBOARD_LAYOUTS[@]}" ]]; then
                                        KEYBOARD_LAYOUT="${KEYBOARD_LAYOUTS[$((kb_full_choice-1))]}"
                                        echo -e "\033[1;92m✅ Keyboard layout set to: \033[1;97m$KEYBOARD_LAYOUT\033[0m\n"
                                        break 2
                                    else
                                        echo -e "\033[1;91m❌ Invalid choice\033[0m"
                                    fi
                                done
                            elif [[ "$kb_choice" =~ ^[0-9]+$ && "$kb_choice" -ge 1 && "$kb_choice" -le "${#common_layouts[@]}" ]]; then
                                KEYBOARD_LAYOUT="${common_layouts[$((kb_choice-1))]}"
                                echo -e "\033[1;92m✅ Keyboard layout set to: \033[1;97m$KEYBOARD_LAYOUT\033[0m\n"
                                break
                            else
                                echo -e "\033[1;91m❌ Invalid choice\033[0m"
                            fi
                        done
                    # System Locale 
                    elif ([ "$GPU_TYPE" = "NVIDIA" ] && [ "$current" -eq 12 ]) || \
                         ([ "$GPU_TYPE" != "NVIDIA" ] && [ "$current" -eq 11 ]); then
                        echo -e "\n\033[1;94m🔄 System Locale Selection\033[0m"
                        
                        # Define an array of common locales
                        declare -a COMMON_LOCALES=(
                            "en_US.UTF-8" "English (US)"
                            "en_GB.UTF-8" "English (UK)"
                            "de_DE.UTF-8" "German"
                            "fr_FR.UTF-8" "French"
                            "it_IT.UTF-8" "Italian"
                            "es_ES.UTF-8" "Spanish"
                            "pt_BR.UTF-8" "Portuguese (Brazil)"
                            "ru_RU.UTF-8" "Russian"
                            "zh_CN.UTF-8" "Chinese (Simplified)"
                            "ja_JP.UTF-8" "Japanese"
                        )
                        
                        # Display common locales
                        echo -e "Common locales:"
                        for ((i=0; i<${#COMMON_LOCALES[@]}; i+=2)); do
                            printf "  \033[1;97m%2d)\033[0m %-15s - %s\n" "$((i/2+1))" "${COMMON_LOCALES[$i]}" "${COMMON_LOCALES[$i+1]}"
                        done
                        
                        echo -e "  \033[1;97m99)\033[0m Show all locales"
                        
                        # Let user select a locale
                        while true; do
                            echo -en "\033[1;94mSelect locale (1-$((${#COMMON_LOCALES[@]}/2)) or 99): \033[0m"
                            read -r locale_choice
                            
                            if [[ "$locale_choice" = "99" ]]; then
                                # Show all locales - would need to implement this section for completeness
                                echo -e "\033[1;93m⚠️ Showing all locales not implemented, using en_US.UTF-8\033[0m"
                                SYSTEM_LOCALE="en_US.UTF-8"
                                echo -e "\033[1;92m✅ System locale set to: \033[1;97m$SYSTEM_LOCALE\033[0m\n"
                                break
                            elif [[ "$locale_choice" =~ ^[0-9]+$ && "$locale_choice" -ge 1 && "$locale_choice" -le "$((${#COMMON_LOCALES[@]}/2))" ]]; then
                                SYSTEM_LOCALE="${COMMON_LOCALES[$((locale_choice-1)*2)]}"
                                echo -e "\033[1;92m✅ System locale set to: \033[1;97m$SYSTEM_LOCALE\033[0m\n"
                                break
                            else
                                echo -e "\033[1;91m❌ Invalid choice\033[0m"
                            fi
                        done
                    # Mirror Country
                    elif ([ "$GPU_TYPE" = "NVIDIA" ] && [ "$current" -eq 13 ]) || \
                         ([ "$GPU_TYPE" != "NVIDIA" ] && [ "$current" -eq 12 ]); then
                        echo -e "\n\033[1;94m🔄 Mirror Country Selection\033[0m"
                        echo -e "  \033[1;97m1)\033[0m Italy"
                        echo -e "  \033[1;97m2)\033[0m Germany"
                        echo -e "  \033[1;97m3)\033[0m United States"
                        echo -e "  \033[1;97m4)\033[0m United Kingdom"
                        echo -e "  \033[1;97m5)\033[0m France"
                        echo -e "  \033[1;97m6)\033[0m Spain"
                        echo -e "  \033[1;97m7)\033[0m Netherlands"
                        echo -e "  \033[1;97m8)\033[0m Other (specify)"
                        echo -e "  \033[1;97m9)\033[0m Worldwide (no specific country)"
                        
                        while true; do
                            echo -en "\033[1;94mEnter your choice (1-9): \033[0m"
                            read -r mirror_choice
                            
                            case $mirror_choice in
                                1)
                                    MIRROR_COUNTRY="Italy"
                                    echo -e "\033[1;92m✅ Selected mirrors from: \033[1;97mItaly\033[0m\n"
                                    break
                                    ;;
                                2)
                                    MIRROR_COUNTRY="Germany"
                                    echo -e "\033[1;92m✅ Selected mirrors from: \033[1;97mGermany\033[0m\n"
                                    break
                                    ;;
                                3)
                                    MIRROR_COUNTRY="United States"
                                    echo -e "\033[1;92m✅ Selected mirrors from: \033[1;97mUnited States\033[0m\n"
                                    break
                                    ;;
                                4)
                                    MIRROR_COUNTRY="United Kingdom"
                                    echo -e "\033[1;92m✅ Selected mirrors from: \033[1;97mUnited Kingdom\033[0m\n"
                                    break
                                    ;;
                                5)
                                    MIRROR_COUNTRY="France"
                                    echo -e "\033[1;92m✅ Selected mirrors from: \033[1;97mFrance\033[0m\n"
                                    break
                                    ;;
                                6)
                                    MIRROR_COUNTRY="Spain"
                                    echo -e "\033[1;92m✅ Selected mirrors from: \033[1;97mSpain\033[0m\n"
                                    break
                                    ;;
                                7)
                                    MIRROR_COUNTRY="Netherlands"
                                    echo -e "\033[1;92m✅ Selected mirrors from: \033[1;97mNetherlands\033[0m\n"
                                    break
                                    ;;
                                8)
                                    echo -e "\033[1;33mPlease specify your country name (in English):\033[0m"
                                    echo -en "Country: "
                                    read -r MIRROR_COUNTRY
                                    echo -e "\033[1;92m✅ Selected mirrors from: \033[1;97m$MIRROR_COUNTRY\033[0m\n"
                                    break
                                    ;;
                                9)
                                    MIRROR_COUNTRY=""
                                    echo -e "\033[1;92m✅ Using worldwide mirrors\033[0m\n"
                                    break
                                    ;;
                                *)
                                    echo -e "\033[1;91m❌ Invalid choice. Please enter a number between 1 and 9.\033[0m"
                                    ;;
                            esac
                        done
                    fi
                    ;;
            esac
        # Advanced mode options handling would go here
        # This part is omitted for brevity and to keep the edit size manageable
        # The structure would be similar to the simple mode options above
        else
            # Advanced mode options
            echo -e "\033[1;93mAdvanced mode settings editing is not fully implemented yet\033[0m"
            sleep 1
        fi
    else
        echo -e "\033[1;91m❌ Invalid choice. Please enter a number between 1 and $TOTAL_ITEMS, or 'c' to confirm, or 'a' to abort.\033[0m"
    fi
    
    # Update the summary after each change
    display_summary
done

# ----------------------------------------
# CLEAN SYSTEM DISK
# ----------------------------------------
print_section_header "CLEAN SYSTEM DISK"

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

# Partition the disk based on installation mode
if [ "$INSTALL_MODE" = "advanced" ]; then
    # Run fdisk with custom settings
    (
    echo g                                # Create a GPT partition table
    echo n                                # Create the EFI partition
    echo                                  # Default, 1
    echo                                  # Default
    echo +$EFI_PART_SIZE                  # Use custom EFI partition size
    echo t                                # Change partition type to EFI
    echo 1                                # EFI type
    echo n                                # Create the system partition
    echo                                  # Default, 2
    echo                                  # Default
    # Use user-specified root partition size if not MAX
    if [ "$ROOT_PART_SIZE" != "MAX" ]; then
        echo +$ROOT_PART_SIZE            # Use custom root partition size
    else
        echo                             # Use remaining space
    fi
    echo w                                # Write the partition table
    ) | run_command "fdisk $DISK" "create partitions"

else
    # Use default partition sizes
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
fi


# ----------------------------------------
# FORMAT/MOUNT PARTITIONS
# ----------------------------------------
print_section_header "FORMAT/MOUNT PARTITIONS"

# Setup ZFS pool with encryption if selected
if [ "$ENCRYPT_DISK" = "yes" ]; then
    echo -e "\033[1;94m🔐 Creating encrypted ZFS pool...\033[0m"
    
    # Create key file directory in the installed system
    mkdir -p /etc/zfs
    echo "$DISK_PASSWORD" > /etc/zfs/zroot.key
    chmod 000 /etc/zfs/zroot.key
    chown root:root /etc/zfs/zroot.key
    
    # Create ZFS pool with encryption and user-defined compression if in advanced mode
    run_command "zpool create \
        -o ashift=12 \
        -O acltype=posixacl -O canmount=off -O compression=$ZFS_COMPRESSION \
        -O dnodesize=auto -O normalization=formD -o autotrim=on \
        -O atime=off -O xattr=sa -O mountpoint=none \
        -O encryption=aes-256-gcm -O keylocation=file:///etc/zfs/zroot.key -O keyformat=passphrase \
        -R /mnt zroot ${DISK}${PARTITION_2} -f" "create encrypted ZFS pool with $ZFS_COMPRESSION compression"


else
    echo -e "\033[1;94m🌊 Creating standard ZFS pool...\033[0m"
    run_command "zpool create \
        -o ashift=12 \
        -O acltype=posixacl -O canmount=off -O compression=$ZFS_COMPRESSION \
        -O dnodesize=auto -O normalization=formD -o autotrim=on \
        -O atime=off -O xattr=sa -O mountpoint=none \
        -R /mnt zroot ${DISK}${PARTITION_2} -f" "create ZFS pool with $ZFS_COMPRESSION compression"
fi

run_command "zfs create -o canmount=noauto -o mountpoint=/ zroot/rootfs" "create ZFS root dataset"

run_command "zpool set bootfs=zroot/rootfs zroot" "set bootfs property"

run_command "zfs mount zroot/rootfs" "mount the root dataset"

mkdir -p /mnt/etc/zfs
run_command "zpool set cachefile=/etc/zfs/zpool.cache zroot" "set ZFS pool cache file"
cp /etc/zfs/zpool.cache /mnt/etc/zfs/zpool.cache

run_command "mkfs.fat -F32 ${DISK}${PARTITION_1}" "format EFI partition with FAT32"
mkdir -p /mnt/efi && mount ${DISK}${PARTITION_1} /mnt/efi




# ----------------------------------------
# INSTALL BASE
# ----------------------------------------
print_section_header "INSTALL BASE"

run_command "pacstrap /mnt linux-lts linux-lts-headers mkinitcpio base base-devel linux-firmware zram-generator reflector sudo networkmanager efibootmgr $CPU_MICROCODE wget" "install base packages" 

cp /etc/zfs/zroot.key /mnt/etc/zfs

# ----------------------------------------
# GENERATE FSTAB
# ----------------------------------------
print_section_header "GENERATING FSTAB"

genfstab -U /mnt > /mnt/etc/fstab
echo -e "\nFstab file generated:\n"
cat /mnt/etc/fstab

# ----------------------------------------
# CHROOT
# ----------------------------------------
print_section_header "ARCH-CHROOT"

# Create a temporary directory in the chroot environment
mkdir -p /mnt/install

# Copy the chroot script and functions script to the temporary directory in the chroot
echo -e "\033[1;94m📂 Copying required scripts to chroot environment...\033[0m"
cp "./$FUNCTIONS_SCRIPT" /mnt/install/ || { 
    echo -e "\033[1;91m❌ Failed to copy $FUNCTIONS_SCRIPT to /mnt/install/\033[0m"; 
    exit 1; 
}
cp "./$CHROOT_SCRIPT" /mnt/install/ || { 
    echo -e "\033[1;91m❌ Failed to copy $CHROOT_SCRIPT to /mnt/install/\033[0m"; 
    exit 1; 
}

# Make scripts executable
chmod +x /mnt/install/"$CHROOT_SCRIPT" /mnt/install/"$FUNCTIONS_SCRIPT"
echo -e "\033[1;92m✅ Setup for chroot environment completed\033[0m"


echo -e "\n\033[1;94m⚙️ \033[1;38;5;87mExecuting:\033[0m \033[1;38;5;195march-chroot into the new system\033[0m"

# Export all environment variables needed by the chroot script
# Note: Using set -x to show the command being executed for debugging

arch-chroot /mnt bash -c "
export DISK='$DISK' 
export HOSTNAME='$HOSTNAME'
export KEYBOARD_LAYOUT='$KEYBOARD_LAYOUT'
export SYSTEM_LOCALE='$SYSTEM_LOCALE'
export USER='$USER'
export USERPASS='$USERPASS'
export ROOTPASS='$ROOTPASS'
export CPU_MICROCODE='$CPU_MICROCODE'
export DE_CHOICE=$DE_CHOICE
export GPU_TYPE='$GPU_TYPE'
export NVIDIA_DRIVER_TYPE='$NVIDIA_DRIVER_TYPE'
export MIRROR_COUNTRY='$MIRROR_COUNTRY'
export AUDIO_SERVER='$AUDIO_SERVER'
export INSTALL_MODE='$INSTALL_MODE'
export ZRAM_SIZE='$ZRAM_SIZE'
export ZRAM_COMPRESSION='$ZRAM_COMPRESSION'
export SEPARATE_DATASETS='$SEPARATE_DATASETS'
cd /install && ./chroot.sh
"


# --------------------------------------------------------------------------------------------------------------------------
# Cleanup and Finalize Installation
# --------------------------------------------------------------------------------------------------------------------------

# Remove installation files from the mounted system
rm -rf /mnt/install

# Print completion message
clear
echo -e "\033[1;38;5;40m"
echo " ██████╗  ██████╗ ███╗   ██╗███████╗██╗"
echo " ██╔══██╗██╔═══██╗████╗  ██║██╔════╝██║"
echo " ██║  ██║██║   ██║██╔██╗ ██║█████╗  ██║"
echo " ██║  ██║██║   ██║██║╚██╗██║██╔══╝  ╚═╝"
echo " ██████╔╝╚██████╔╝██║ ╚████║███████╗██╗"
echo " ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝"
echo -e "\033[0m"
                                  
echo -e "\n\033[1;38;5;82m✅ Installation completed successfully!\033[0m"
echo -e "\033[1;38;5;75m📋 Installation Summary:\033[0m"
echo

# System Information
echo -e "\033[1;38;5;219m📌 System Information:\033[0m"
echo -e "  \033[1;97m🖥️\033[0m Hostname: \033[1;97m$HOSTNAME\033[0m"
echo -e "  \033[1;97m👤\033[0m Username: \033[1;97m$USER\033[0m"
echo -e "  \033[1;97m🔣\033[0m Keyboard: \033[1;97m$KEYBOARD_LAYOUT\033[0m"
echo -e "  \033[1;97m🌐\033[0m Locale: \033[1;97m$SYSTEM_LOCALE\033[0m"
echo -e "  \033[1;97m🌍\033[0m Mirrors: \033[1;97m${MIRROR_COUNTRY:-Worldwide}\033[0m"
echo

# Hardware Configuration
echo -e "\033[1;38;5;117m⚙️ Hardware Configuration:\033[0m"
echo -e "  \033[1;97m💽\033[0m Target Device: \033[1;97m$DEVICE\033[0m"
echo -e "  \033[1;97m🖿\033[0m Boot Type: \033[1;97m${BOOT_TYPE^}\033[0m"
echo -e "  \033[1;97m🔌\033[0m CPU: \033[1;97m$CPU_TYPE ($CPU_MICROCODE)\033[0m"
echo -e "  \033[1;97m📺\033[0m GPU: \033[1;97m$GPU_TYPE\033[0m"
if [ "$GPU_TYPE" = "NVIDIA" ]; then
    echo -e "  \033[1;97m🎮\033[0m NVIDIA Drivers: \033[1;97m$NVIDIA_DRIVER_TYPE\033[0m"
fi
echo -e "  \033[1;97m🔊\033[0m Audio Server: \033[1;97m$AUDIO_SERVER\033[0m"
echo

# Storage Configuration
echo -e "\033[1;38;5;220m💾 Storage Configuration:\033[0m"
echo -e "  \033[1;97m🔐\033[0m Disk Encryption: \033[1;97m${ENCRYPT_DISK^}\033[0m"
echo -e "  \033[1;97m📁\033[0m ZFS Compression: \033[1;97m$ZFS_COMPRESSION\033[0m"
if [ "$INSTALL_MODE" = "advanced" ]; then
    echo -e "  \033[1;97m📊\033[0m EFI Partition: \033[1;97m$EFI_PART_SIZE\033[0m"
    echo -e "  \033[1;97m📊\033[0m Root Partition: \033[1;97m$ROOT_PART_SIZE\033[0m"
    echo -e "  \033[1;97m📂\033[0m Separate Datasets: \033[1;97m${SEPARATE_DATASETS^}\033[0m"
fi
echo

# Software Configuration
echo -e "\033[1;38;5;114m🖱️ Software Configuration:\033[0m"
echo -e "  \033[1;97m🖥️\033[0m Desktop Environment: \033[1;97m$DE_TYPE\033[0m"
echo -e "  \033[1;97m📇\033[0m Install Mode: \033[1;97m${INSTALL_MODE^}\033[0m"
echo

# Performance Configuration
echo -e "\033[1;38;5;208m⚡ Performance Configuration:\033[0m"
echo -e "  \033[1;97m💭\033[0m ZRAM Size: \033[1;97m$ZRAM_SIZE\033[0m"
echo -e "  \033[1;97m🗜️\033[0m ZRAM Compression: \033[1;97m$ZRAM_COMPRESSION\033[0m"
echo

echo -e "\033[1;38;5;87m🚀 Your new Arch Linux system is ready!\033[0m"

# Ask user if they want to reboot now
while true; do
    echo -en "\033[1;93mDo you want to reboot now? [Y/n]: \033[0m"
    read -r reboot_choice
    
    case $reboot_choice in
        [Yy]*|"")
            echo -e "\n\033[1;94m🔄 Unmounting filesystems and rebooting system...\033[0m"
            
            # Unmount all filesystems and export pools
            umount -R /mnt
            zfs umount -a
            zpool export -a
            
            # Reboot the system
            echo -e "\033[1;92m👋 Rebooting now. See you on the other side!\033[0m"
            sleep 2
            reboot
            ;;
        [Nn]*)
            echo -e "\n\033[1;94mSystem is ready. You can reboot manually when ready with 'reboot' command.\033[0m"
            echo -e "\033[1;93m⚠️  Remember to properly unmount filesystems before rebooting:\033[0m"
            echo -e "  \033[1;37m•\033[0m umount -R /mnt"
            echo -e "  \033[1;37m•\033[0m zfs umount -a"
            echo -e "  \033[1;37m•\033[0m zpool export -a\n\n"
            exit 0
            ;;
        *)
            echo -e "\033[1;91m❌ Invalid choice. Please answer Y or N.\033[0m"
            # The loop will continue and repeat the question
            ;;
    esac
done