#!/bin/bash

# ----------------------------------------
# LOGGING SETUP
# ----------------------------------------
# Create log directory and file
LOG_DIR="/var/log/arch-install"
LOG_FILE="${LOG_DIR}/install-$(date +%Y%m%d-%H%M%S).log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"
touch "$LOG_FILE"

# Function to log messages
log_message() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $message" | tee -a "$LOG_FILE"
}

# Redirect stdout and stderr to both console and log file, but strip ANSI escape sequences for log file
exec > >(tee >(sed -E "s/\x1B\[[0-9;]*[a-zA-Z]|\x1B\[[0-9;]*[mK]//g" > "$LOG_FILE")) 2>&1

# Log start of installation
log_message "Installation script started"
log_message "Log file created at: $LOG_FILE"

# Print info about logging
echo -e "\033[1;94m📝 \033[1;38;5;87mLogging:\033[0m \033[1;38;5;195mAll output is being saved to $LOG_FILE\033[0m"

# ----------------------------------------
# DEFINE FUNCTIONS
# ----------------------------------------

# Function to handle command failures
handle_error() {
    local desc="$1"
    local retry_prompt="${2:-true}"
    
    echo -e "\033[1;31m❌ Error: Failed to $desc\033[0m" >&2
    
    if [ "$retry_prompt" = "true" ]; then
        while true; do
            read -p $'\n\033[1;33mRetry? (r), Skip (s), or Abort (a): \033[0m' choice
            case "$choice" in
                [Rr]*)
                    echo -e "\n\033[1;34m🔄 Retrying\033[0m"
                    return 0  # Return code to indicate retry
                    ;;
                [Ss]*)
                    echo -e "\n\033[1;33m⏩ Skipping\033[0m"
                    return 1  # Return code to indicate skip
                    ;;
                [Aa]*)
                    echo -e "\n\033[1;31m🛑 Aborting installation\033[0m"
                    # Create a flag file to indicate installation was aborted
                    touch "/tmp/install_aborted"
                    exit 1
                    ;;
                *)
                    echo -e "\n\033[1;35m⚠️ Invalid choice. Please enter 'r', 's', or 'a'\033[0m"
                    ;;
            esac
        done
    else
        return 1  # Skip if retry is not enabled
    fi
}

# Function to print section headers with formatting
print_section_header() {
    local title="$1"
    # Create a header with a gradient-like effect using bold cyan for better visibility
    echo -e "\n\n\033[1;36m╔════════════════════════════════════════════════╗\033[0m"
    local title_length=${#title}
    local padding=$(( (49 - title_length) / 2 ))
    local pad_str=$(printf "%${padding}s" "")
    echo -e "\033[1;36m${pad_str}\033[1;97m${title}\033[1;36m${pad_str}$([ $(( title_length % 2 )) -eq 1 ] && echo " ")\033[0m"
    echo -e "\033[1;36m╚════════════════════════════════════════════════╝\033[0m\n"
}

# Function to securely get passwords with confirmation
get_password() {
        local prompt=$1
        local password_var
        local password_recheck_var

        while true; do
                echo -en "\033[1;93m$prompt: \033[0m"; read -r -s password_var; echo
                echo -en "\033[1;93mRe-enter password: \033[0m"; read -r -s password_recheck_var; echo
                if [ "$password_var" = "$password_recheck_var" ]; then
                        eval "$2='$password_var'"
                        break
                else
                        echo -e "\033[1;91m❌ Passwords do not match. Please enter a new password.\033[0m"
                fi
        done
}

# Function to run commands and handle errors
run_command() {
    local cmd="$1"
    local desc="$2"
    local retry_prompt="${3:-true}"
    local silent="${4:-false}"
    
    # Check if this is a critical command that should not be skipped
    local is_critical=false
    if [[ "$desc" == *"zfs"* ]] || [[ "$desc" == *"ZFS"* ]] || 
       [[ "$desc" == *"disk"* ]] || [[ "$desc" == *"partition"* ]] || 
       [[ "$desc" == *"mkinitcpio"* ]] || [[ "$desc" == *"ZFSBootMenu"* ]] ||
       [[ "$desc" == *"format"* ]] || [[ "$desc" == *"mount"* ]] || 
       [[ "$desc" == *"bootloader"* ]] || [[ "$desc" == *"boot"* ]]; then
        is_critical=true
        retry_prompt="critical"
    fi
    
    if [ "$silent" != "true" ]; then
        echo -e "\n\033[1;94m⚙️ \033[1;38;5;87mExecuting:\033[0m \033[1;38;5;195m$desc\033[0m"
    fi
    
    while true; do
        if [ "$silent" = "true" ]; then
            eval "$cmd" >/dev/null 2>&1
        else
            eval "$cmd"
        fi
        
        local status=$?
        if [ $status -eq 0 ]; then
            if [ "$silent" != "true" ]; then
                echo -e "\033[1;92m✅ Successfully completed\033[0m\n"
            fi
            return 0
        else
            if [ "$retry_prompt" = "critical" ]; then
                echo -e "\033[1;31m❌ Error: Failed to $desc\033[0m" >&2
                echo -e "\033[1;31m⚠️  This is a critical operation and cannot be skipped.\033[0m" >&2
                while true; do
                    read -p $'\n\033[1;33mRetry? (r) or Abort installation (a): \033[0m' choice
                    case "$choice" in
                        [Rr]*)
                            echo -e "\n\033[1;34m🔄 Retrying\033[0m"
                            break
                            ;;
                        [Aa]*)
                            echo -e "\n\033[1;31m🛑 Aborting installation\033[0m"
                            # Create a flag file to indicate installation was aborted
                            touch "/tmp/install_aborted"
                            exit 1
                            ;;
                        *)
                            echo -e "\n\033[1;35m⚠️ Invalid choice. Please enter 'r' or 'a'\033[0m"
                            ;;
                    esac
                done
                # Continue retrying since this is a critical command
                continue
            else
                handle_error "$desc" "$retry_prompt"
                local retry_status=$?
                
                if [ $retry_status -eq 0 ]; then
                    # User chose to retry
                    continue
                else
                    # User chose to skip
                    return 1
                fi
            fi
        fi
    done
}

# Display welcome banner with enhanced colors
clear
echo -e "\033[1;38;5;75m"
echo "    _             _       _     _                   "
echo "   / \   _ __ ___| |__   | |   (_)_ __  _   ___  __ "
echo "  / _ \ | '__/ __| '_ \  | |   | | '_ \| | | \ \/ / "
echo " / ___ \| | | (__| | | | | |___| | | | | |_| |>  <  "
echo "/_/   \_\_|  \___|_| |_| |_____|_|_| |_|\__,_/_/\_\ "
echo -e "\033[0m"
echo -e "\033[1;38;5;45m           Flexible Installation Script\033[0m"


# ----------------------------------------
# NETWORK VERIFICATION
# ----------------------------------------
print_section_header "NETWORK VERIFICATION"

# Verify network connection
echo -e "\033[1;94m🌐 Checking network connection...\033[0m"
if ping -c 1 archlinux.org &> /dev/null; then
    echo -e "\033[1;92m✅ Network is working properly\033[0m\n"
else
    echo -e "\033[1;91m❌ No network connection detected.\033[0m"
    
    # Check if we're using a wireless interface
    if [ -d "/sys/class/net/wlan0" ] || [ -d "/sys/class/net/wlp*" ]; then
        echo -e "\033[1;94m🔄 Wireless interface detected. Scanning for WiFi networks...\033[0m"
        
        # Find the wireless interface name
        WIRELESS_INTERFACE=$(ls /sys/class/net/ | grep -E '^wlan0|^wlp')
        
        if [ -z "$WIRELESS_INTERFACE" ]; then
            echo -e "\033[1;91m❌ Could not determine wireless interface name.\033[0m"
            exit 1
        fi
        
        # Make sure iwd service is running
        systemctl start iwd
        
        # Scan for networks using iwctl
        echo -e "\033[1;94m📡 Scanning for networks...\033[0m"
        iwctl station $WIRELESS_INTERFACE scan
        sleep 3 # Give it some time to scan
        
        # Get available networks and store them in an array
        mapfile -t WIFI_NETWORKS < <(iwctl station $WIRELESS_INTERFACE get-networks | grep -v -e "^    " -e "^$" -e "Available" -e "----" | awk '{print $1}' | sort -u)
        
        if [ ${#WIFI_NETWORKS[@]} -eq 0 ]; then
            echo -e "\033[1;91m❌ No WiFi networks found. Please check your wireless adapter.\033[0m"
            exit 1
        fi
        
        # Display available networks
        echo -e "\033[1;94m📶 Available WiFi networks:\033[0m"
        for i in "${!WIFI_NETWORKS[@]}"; do
            echo -e "  \033[1;37m$((i+1)))\033[0m ${WIFI_NETWORKS[$i]}"
        done
        echo
        
        # Let user select a network
        while true; do
            echo -en "\033[1;94mEnter the number of the network to connect to (1-${#WIFI_NETWORKS[@]}): \033[0m"
            read -r wifi_choice
            
            if [[ "$wifi_choice" =~ ^[0-9]+$ && "$wifi_choice" -ge 1 && "$wifi_choice" -le "${#WIFI_NETWORKS[@]}" ]]; then
                WIFI_SSID="${WIFI_NETWORKS[$((wifi_choice-1))]}"
                echo -e "\033[1;92m✅ Selected WiFi network: \033[1;97m$WIFI_SSID\033[0m\n"
                
                # Get password
                echo -en "\033[1;94mEnter password for $WIFI_SSID: \033[0m"
                read -rs WIFI_PASSWORD
                echo
                
                # Connect to the network
                echo -e "\033[1;94m🔄 Connecting to $WIFI_SSID...\033[0m"
                iwctl station $WIRELESS_INTERFACE connect "$WIFI_SSID" --passphrase "$WIFI_PASSWORD"
                
                # Wait for connection and verify
                echo -e "\033[1;94m🔄 Waiting for connection to establish...\033[0m"
                sleep 5
                
                if ping -c 1 archlinux.org &> /dev/null; then
                    echo -e "\033[1;92m✅ Successfully connected to WiFi!\033[0m\n"
                    break
                else
                    echo -e "\033[1;91m❌ Failed to connect. Check your password and try again.\033[0m"
                fi
            else
                echo -e "\033[1;91m❌ Invalid selection. Please enter a number between 1 and ${#WIFI_NETWORKS[@]}.\033[0m"
            fi
        done
    else
        echo -e "\033[1;93m💡 Please check your network connection and try again.\033[0m"
        echo -e "\033[1;93m💡 You may need to run 'iwctl' to configure your wireless connection.\033[0m"
        exit 1
    fi
fi

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
    read -r MODE_CHOICE
    
    case $MODE_CHOICE in
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
            echo -e "\033[1;91m⚠️ Invalid choice. Please enter 1 or 2.\033[0m"
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

# Get available disks and store in an array
mapfile -t DISK_PATHS < <(lsblk -dpno NAME | grep -E "/dev/(sd|nvme|vd)")
# Get disk details for display
mapfile -t DISK_DETAILS < <(lsblk -dpno NAME,SIZE,MODEL | grep -E "/dev/(sd|nvme|vd)")

# Check if any disks were found
if [ ${#DISK_PATHS[@]} -eq 0 ]; then
    echo -e "\033[1;91m❌ No disks found. Please check your hardware and try again.\033[0m"
    exit 1
fi

# Display disks with numbers
echo -e "\033[1;38;5;195mAvailable disks:\033[0m"
for i in "${!DISK_DETAILS[@]}"; do
    echo -e "  \033[1;37m$((i+1)))\033[0m ${DISK_DETAILS[$i]}"
done
echo ""

# Let user select a disk by number
while true; do
    echo -en "\033[1;94mEnter the number of the disk to install to (1-${#DISK_PATHS[@]}): \033[0m"
    read -r disk_choice
    
    # Verify choice is valid
    if [[ "$disk_choice" =~ ^[0-9]+$ && "$disk_choice" -ge 1 && "$disk_choice" -le "${#DISK_PATHS[@]}" ]]; then
        DEVICE="${DISK_PATHS[$((disk_choice-1))]}"
        if [[ "$DEVICE" == /dev/nvme* ]]; then
            PARTITION_1="p1"
            PARTITION_2="p2"
        else
            PARTITION_1="1"
            PARTITION_2="2"
        fi
        echo -e "\033[1;92m✅ Selected device: \033[1;97m$DEVICE\033[0m\n"
        
        if [ "$INSTALL_MODE" = "simple" ]; then
            # Show confirmation for dangerous operation
            echo -e "\033[1;93m⚠️  CONFIRMATION: You are about to erase all data on $DEVICE\033[0m"
            echo -en "\033[1;94mAre you sure you want to continue? (y/N): \033[0m"
            read -r confirm        

            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                echo -e "\033[1;92m✅ Installation will proceed on $DEVICE\033[0m\n"
                break
            else
                echo -e "\033[1;93m🔄 Disk selection cancelled. Please select again.\033[0m\n"
                # Loop continues to prompt again
            fi
        fi
        break  
    else
        echo -e "\033[1;91m❌ Invalid selection. Please enter a number between 1 and ${#DISK_PATHS[@]}.\033[0m"
    fi
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
                echo -e "\033[1;91m⚠️ Invalid choice. Please enter 1 or 2.\033[0m"
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
                echo -e "\033[1;91m⚠️ Invalid choice. Please enter 1 or 2.\033[0m"
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
                echo -e "\033[1;91m⚠️ Invalid choice. Please enter 1 or 2.\033[0m"
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
                echo -e "\033[1;32m✅ Selected lz4 compression\033[0m"
                break
                ;;
            2)
                ZFS_COMPRESSION="zstd"
                echo -e "\033[1;32m✅ Selected zstd compression\033[0m"
                break
                ;;
            3)
                ZFS_COMPRESSION="gzip"
                echo -e "\033[1;32m✅ Selected gzip compression\033[0m"
                break
                ;;
            4)
                ZFS_COMPRESSION="off"
                echo -e "\033[1;32m✓ Compression disabled\033[0m"
                break
                ;;
            *)
                echo -e "\033[1;91m⚠️ Invalid choice. Please enter a number between 1 and 4.\033[0m"
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
                echo -e "\033[1;32m✅ Selected simple dataset structure\033[0m"
                break
                ;;
            2|"")
                SEPARATE_DATASETS="yes"
                echo -e "\033[1;32m✅ Selected advanced dataset structure\033[0m"
                break
                ;;
            *)
                echo -e "\033[1;91m⚠️ Invalid choice. Please enter 1 or 2.\033[0m"
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
                echo -e "\033[1;32m✅ Selected automatic ZRAM sizing\033[0m"
                break
                ;;
            2)
                ZRAM_SIZE="ram / 2"
                echo -e "\033[1;32m✅ Selected half of RAM for ZRAM\033[0m"
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
                echo -e "\033[1;91m⚠️ Invalid choice. Please enter a number between 1 and 3.\033[0m"
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
                echo -e "\033[1;32m✅ Selected zstd compression algorithm\033[0m\n"
                break
                ;;
            2)
                ZRAM_COMPRESSION="lz4"
                echo -e "\033[1;32m✅ Selected lz4 compression algorithm\033[0m\n"
                break
                ;;
            3)
                ZRAM_COMPRESSION="lzo-rle"
                echo -e "\033[1;32m✅ Selected lzo-rle compression algorithm\033[0m\n"
                break
                ;;
            4)
                ZRAM_COMPRESSION="lzo"
                echo -e "\033[1;32m✅ Selected lzo compression algorithm\033[0m\n"
                break
                ;;
            *)
                echo -e "\033[1;91m⚠️ Invalid choice. Please enter a number between 1 and 4.\033[0m"
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
        echo -e "\033[1;32m✅ Selected Hyprland for desktop environment.\033[0m\n"
        ;;
    2)
        DE_TYPE="XFCE4"
        echo -e "\033[1;32m✅ Selected XFCE4 for desktop environment.\033[0m\n"
        ;;
    3)
        DE_TYPE="KDE Plasma"
        echo -e "\033[1;32m✅ Selected KDE Plasma for desktop environment.\033[0m\n"
        ;;
    4)
        DE_TYPE="GNOME"
        echo -e "\033[1;32m✅ Selected GNOME for desktop environment.\033[0m\n"
        ;;
    *)
        echo -e "\033[1;33m⚠️ Invalid choice. Defaulting to Hyprland.\033[0m\n"
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
        echo -e "\033[1;32m✅ Selected mirrors from: \033[1;37mItaly\033[0m"
        ;;
    2)
        MIRROR_COUNTRY="Germany"
        echo -e "\033[1;32m✅ Selected mirrors from: \033[1;37mGermany\033[0m"
        ;;
    3)
        MIRROR_COUNTRY="United States"
        echo -e "\033[1;32m✅ Selected mirrors from: \033[1;37mUnited States\033[0m"
        ;;
    4)
        MIRROR_COUNTRY="United Kingdom"
        echo -e "\033[1;32m✅ Selected mirrors from: \033[1;37mUnited Kingdom\033[0m"
        ;;
    5)
        MIRROR_COUNTRY="France"
        echo -e "\033[1;32m✅ Selected mirrors from: \033[1;37mFrance\033[0m"
        ;;
    6)
        MIRROR_COUNTRY="Spain"
        echo -e "\033[1;32m✅ Selected mirrors from: \033[1;37mSpain\033[0m"
        ;;
    7)
        MIRROR_COUNTRY="Netherlands"
        echo -e "\033[1;32m✅ Selected mirrors from: \033[1;37mNetherlands\033[0m"
        ;;
    8)
        echo -e "\033[1;33mPlease specify your country name (in English):\033[0m"
        echo -n "Country: "; read -r MIRROR_COUNTRY
        echo -e "\033[1;32m✅ Selected mirrors from: \033[1;37m$MIRROR_COUNTRY\033[0m"
        ;;
    9)
        MIRROR_COUNTRY=""
        echo -e "\033[1;32m✓ Using worldwide mirrors\033[0m"
        ;;
    *)
        echo -e "\033[1;33m⚠️ Invalid choice. Defaulting to worldwide mirrors.\033[0m"
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
        echo -e "\033[1;32m✅ Selected keyboard layout: \033[1;37m$KEYBOARD_LAYOUT\033[0m\n"
        break
    else
        echo -e "\033[1;33m⚠️ Invalid choice. Please enter a number between 1 and ${#KEYBOARD_LAYOUTS[@]}.\033[0m"
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
                echo -e "\033[1;32m✅ Selected locale: \033[1;37m$SYSTEM_LOCALE\033[0m\n"
                break 2  # Break out of both loops
            else
                echo -e "\033[1;33m⚠️ Invalid choice. Please enter a number between 1 and ${#AVAILABLE_LOCALES[@]}.\033[0m"
            fi
        done
    elif [[ "$locale_choice" =~ ^[0-9]+$ && "$locale_choice" -ge 1 && "$locale_choice" -le "${#ESSENTIAL_LOCALES[@]}" ]]; then
        # User selected from the essential locales list
        SYSTEM_LOCALE="${ESSENTIAL_LOCALES[$((locale_choice-1))]}"
        echo -e "\033[1;32m✅ Selected locale: \033[1;37m$SYSTEM_LOCALE\033[0m\n"
        break
    else
        echo -e "\033[1;33m⚠️ Invalid choice. Please enter a valid number.\033[0m"
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
        echo -e "\033[1;32m✅ Selected Intel CPU. Will install intel-ucode.\033[0m\n"
        ;;
    2)
        CPU_MICROCODE="amd-ucode"
        CPU_TYPE="AMD"
        echo -e "\033[1;32m✅ Selected AMD CPU. Will install amd-ucode.\033[0m\n"
        ;;
    *)
        echo -e "\033[1;33m⚠️ Invalid choice. Defaulting to AMD.\033[0m\n"
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
        echo -e "\033[1;32m✅ Selected NVIDIA GPU.\033[0m"
        
        echo -e "\n\033[1;33mNVIDIA Driver Selection:\033[0m"
        echo -e "  Do you want to use NVIDIA open drivers?"
        echo -e "  (No will install proprietary drivers)"
        echo
        read -p "Use NVIDIA open drivers? [y/N]: " nvidia_open_choice
        
        case $nvidia_open_choice in
            [Yy]*)
                NVIDIA_DRIVER_TYPE="open"
                echo -e "\033[1;32m✅ Selected NVIDIA open source drivers.\033[0m\n"
                ;;
            *)
                NVIDIA_DRIVER_TYPE="proprietary"
                echo -e "\033[1;32m✅ Selected NVIDIA proprietary drivers.\033[0m\n"
                ;;
        esac
        ;;
    2)
        GPU_TYPE="AMD/Intel"
        NVIDIA_DRIVER_TYPE="none"
        echo -e "\033[1;32m✅ Selected AMD/Intel GPU. Will use open source drivers.\033[0m\n"
        ;;
    3)
        GPU_TYPE="None/VM"
        NVIDIA_DRIVER_TYPE="none"
        echo -e "\033[1;32m✅ Selected None/VM. Will use basic drivers.\033[0m\n"
        ;;
    *)
        echo -e "\033[1;33m⚠️ Invalid choice. Defaulting to AMD/Intel.\033[0m\n"
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
            echo -e "\033[1;91m⚠️ Invalid choice. Please enter 1 or 2.\033[0m"
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
    echo -e "┌──────────────────────────────────────────────────┐"

    # Helper for printing aligned lines
    print_entry() {
        local index="$1"
        local label="$2"
        local value="$3"
        local formatted_index
        formatted_index=$(printf "%2s" "$index")
        echo -e " \033[1;97m${formatted_index})\033[0m ${label} \033[1;38;5;81m${value}\033[0m"
    }

    # System-critical choices
    print_entry 1 "Target Device:          " "$DEVICE"

    # Hardware settings
    print_entry 2 "CPU Type:               " "$CPU_TYPE"
    print_entry 3 "GPU Type:               " "$GPU_TYPE"

    if [ "$GPU_TYPE" = "NVIDIA" ]; then
        print_entry 4 "NVIDIA Driver:          " "$NVIDIA_DRIVER_TYPE"
        NVIDIA_OFFSET=1

    else
        NVIDIA_OFFSET=0
    fi

    print_entry $((4+NVIDIA_OFFSET)) "Audio Server:           " "$AUDIO_SERVER"
    print_entry $((5+NVIDIA_OFFSET)) "Desktop Environment:    " "$DE_TYPE"

    # User configuration
    print_entry $((6+NVIDIA_OFFSET)) "Hostname:               " "$HOSTNAME"
    print_entry $((7+NVIDIA_OFFSET)) "Username:               " "$USER"
    print_entry $((8+NVIDIA_OFFSET)) "User & Root Passwords:  " "[hidden]"

    # System preferences
    print_entry $((9+NVIDIA_OFFSET)) "Keyboard Layout:        " "$KEYBOARD_LAYOUT"
    print_entry $((10+NVIDIA_OFFSET)) "System Locale:          " "$SYSTEM_LOCALE"
    print_entry $((11+NVIDIA_OFFSET)) "Mirror Country:         " "${MIRROR_COUNTRY:-Worldwide}"

    # Advanced partition settings
    if [ "$INSTALL_MODE" = "advanced" ]; then
        print_entry $((12+NVIDIA_OFFSET)) "EFI Partition Size:     " "$EFI_PART_SIZE"
        print_entry $((13+NVIDIA_OFFSET)) "Root Partition Size:    " "$ROOT_PART_SIZE"
        print_entry $((14+NVIDIA_OFFSET)) "Disk Encryption:        " "${ENCRYPT_DISK^}"
        print_entry $((15+NVIDIA_OFFSET)) "ZFS Compression:        " "$ZFS_COMPRESSION"
        print_entry $((16+NVIDIA_OFFSET)) "Separate Datasets:      " "${SEPARATE_DATASETS^}"
        print_entry $((17+NVIDIA_OFFSET)) "ZRAM Size:              " "$ZRAM_SIZE"
        print_entry $((18+NVIDIA_OFFSET)) "ZRAM Compression:       " "$ZRAM_COMPRESSION"
    fi

    echo -e "└──────────────────────────────────────────────────┘"
}


# Allow user to modify choices
while true; do
    clear
    # Display initial summary
     display_summary

     echo -e "\n\033[1;93mReview your configuration:\033[0m"
     echo -e " - Enter 'c' to confirm and proceed with installation"
     echo -e " - Enter 'a' to abort installation"
     echo -e " - Enter 'm' to modify a configuration value"

     echo -en "\n\033[1;94mYour choice: \033[0m"
     read choice

     if [[ "$choice" == "c" || "$choice" == "C" ]]; then
          echo -e "\033[1;92m✅ Configuration confirmed! Proceeding with installation...\033[0m"
          break
     elif [[ "$choice" == "a" || "$choice" == "A" ]]; then
          echo -e "\033[1;91m❌ Installation aborted by user.\n\033[0m"
          exit 1
     elif [[ "$choice" == "m" || "$choice" == "M" ]]; then
          # Start modification loop
          while true; do
               clear
               # Show options to modify
               display_summary
               
               echo -e "\n\033[1;94mEnter the number of the setting you want to modify (or 0 to finish editing):\033[0m"
               read -p "Setting number (0 to finish): " setting_num
               
               # Check if user is done with modifications
               if [[ "$setting_num" == "0" ]]; then
                    echo -e "\033[1;92m✅ Done with modifications.\033[0m"
                    sleep 1
                    break
               fi
               
               if [[ "$setting_num" =~ ^[0-9]+$ ]]; then
                    # Handle setting modification based on the number
                    case $setting_num in
                            
                         1) # Target Device
                              echo -e "\n\033[1;94m💾 Available disks for installation:\033[0m"
                              available_disks=$(lsblk -dpno NAME,SIZE,MODEL | grep -E "/dev/(sd|nvme|vd)")
                              echo -e "\033[1;38;5;195m$available_disks\033[0m\n"
  
                              # Get available disks and store in an array
                              mapfile -t DISK_PATHS < <(lsblk -dpno NAME | grep -E "/dev/(sd|nvme|vd)")
                              # Get disk details for display
                              mapfile -t DISK_DETAILS < <(lsblk -dpno NAME,SIZE,MODEL | grep -E "/dev/(sd|nvme|vd)")  
                              # Check if any disks were found
                              if [ ${#DISK_PATHS[@]} -eq 0 ]; then
                                  echo -e "\033[1;91m❌ No disks found. Please check your hardware and try again.\033[0m"
                                  exit 1
                              fi  
                              # Display disks with numbers
                              echo -e "\033[1;38;5;195mAvailable disks:\033[0m"
                              for i in "${!DISK_DETAILS[@]}"; do
                                  echo -e "  \033[1;37m$((i+1)))\033[0m ${DISK_DETAILS[$i]}"
                              done
                              echo ""  
                              # Let user select a disk by number
                              while true; do
                                  echo -en "\033[1;94mEnter the number of the disk to install to (1-${#DISK_PATHS[@]}): \033[0m"
                                  read -r disk_choice
                                  
                                  # Verify choice is valid
                                  if [[ "$disk_choice" =~ ^[0-9]+$ && "$disk_choice" -ge 1 && "$disk_choice" -le "${#DISK_PATHS[@]}" ]]; then
                                      DEVICE="${DISK_PATHS[$((disk_choice-1))]}"
                                      echo -e "\033[1;92m✅ Target device successfully changed to $DEVICE\033[0m"
                                      break
                                  else
                                      echo -e "\033[1;91m❌ Invalid device. Value not changed.\033[0m"
                                  fi
                              done
                              sleep 2
                              ;;
                         
                         2) # CPU Type
                              echo -e "\n\033[1;94mChoose your CPU type:\033[0m"
                              echo -e "  \033[1;37m1)\033[0m \033[1;38;5;39mIntel\033[0m"
                              echo -e "  \033[1;37m2)\033[0m \033[1;38;5;196mAMD\033[0m"
                              read -p "Enter choice (1-2): " cpu_choice
                              case $cpu_choice in
                                    1) 
                                         CPU_MICROCODE="intel-ucode"
                                         CPU_TYPE="Intel"
                                         echo -e "\033[1;92m✅ CPU type successfully set to Intel\033[0m"
                                         ;;
                                    2)
                                         CPU_MICROCODE="amd-ucode"
                                         CPU_TYPE="AMD"
                                         echo -e "\033[1;92m✅ CPU type successfully set to AMD\033[0m"
                                         ;;
                                    *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                              esac
                              sleep 2
                              ;;
                         
                         3) # GPU Type
                              echo -e "\n\033[1;94mChoose your GPU type:\033[0m"
                              echo -e "  \033[1;37m1)\033[0m \033[1;38;5;118mNVIDIA\033[0m"
                              echo -e "  \033[1;37m2)\033[0m \033[1;38;5;75mAMD/Intel\033[0m (Open Source)"
                              echo -e "  \033[1;37m3)\033[0m \033[1;38;5;250mNone/VM\033[0m"
                              read -p "Enter choice (1-3): " gpu_choice
                              
                              case $gpu_choice in
                                    1)
                                         GPU_TYPE="NVIDIA"
                                         echo -e "\033[1;92m✅ GPU type successfully set to NVIDIA\033[0m"
                                         echo -e "\n\033[1;94mNVIDIA Driver Selection:\033[0m"
                                         echo -e "  \033[1;37m1)\033[0m Open source drivers"
                                         echo -e "  \033[1;37m2)\033[0m Proprietary drivers"
                                         read -p "Enter choice (1-2): " nvidia_choice
                                         case $nvidia_choice in
                                              1) 
                                                    NVIDIA_DRIVER_TYPE="open" 
                                                    echo -e "\033[1;92m✅ NVIDIA driver successfully set to open source\033[0m"
                                                    ;;
                                              2) 
                                                    NVIDIA_DRIVER_TYPE="proprietary" 
                                                    echo -e "\033[1;92m✅ NVIDIA driver successfully set to proprietary\033[0m"
                                                    ;;
                                              *) 
                                                    echo -e "\033[1;91m⚠️ Invalid choice. Defaulting to proprietary.\033[0m"
                                                    NVIDIA_DRIVER_TYPE="proprietary"
                                                    ;;
                                         esac
                                         ;;
                                    2)
                                         GPU_TYPE="AMD/Intel"
                                         NVIDIA_DRIVER_TYPE="none"
                                         echo -e "\033[1;92m✅ GPU type successfully set to AMD/Intel\033[0m"
                                         ;;
                                    3)
                                         GPU_TYPE="None/VM"
                                         NVIDIA_DRIVER_TYPE="none"
                                         echo -e "\033[1;92m✅ GPU type successfully set to None/VM\033[0m"
                                         ;;
                                    *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                              esac
                              sleep 2
                              ;;
                         
                         4) # NVIDIA Driver (only if NVIDIA GPU)
                              if [ "$GPU_TYPE" = "NVIDIA" ]; then
                                    echo -e "\n\033[1;94mNVIDIA Driver Type:\033[0m"
                                    echo -e "  \033[1;37m1)\033[0m Open source drivers"
                                    echo -e "  \033[1;37m2)\033[0m Proprietary drivers"
                                    read -p "Enter choice (1-2): " nvidia_choice
                                    case $nvidia_choice in
                                         1) 
                                              NVIDIA_DRIVER_TYPE="open"
                                              echo -e "\033[1;92m✅ NVIDIA driver successfully set to open source\033[0m"
                                              ;;
                                         2) 
                                              NVIDIA_DRIVER_TYPE="proprietary"
                                              echo -e "\033[1;92m✅ NVIDIA driver successfully set to proprietary\033[0m"
                                              ;;
                                         *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                                    esac
                                    sleep 2
                              else
                                   echo -e "\033[1;93m⚠️ This setting is only available for NVIDIA GPUs. Please select a NVIDIA GPU first.\033[0m"
                                   sleep 2
                              fi
                              ;;

                         # After this point, count NVIDIA_OFFSET to the case numbers
                         # First determine if we have an NVIDIA GPU (offset = 1) or not (offset = 0)
                         $((4+NVIDIA_OFFSET))) # Audio Server
                              echo -e "\n\033[1;94mChoose your audio server:\033[0m"
                              echo -e "  \033[1;37m1)\033[0m \033[1;38;5;86mPipeWire\033[0m (Modern, low-latency)"
                              echo -e "  \033[1;37m2)\033[0m \033[1;38;5;208mPulseAudio\033[0m (Traditional)"
                              read -p "Enter choice (1-2): " audio_choice
                              case $audio_choice in
                                    1) 
                                         AUDIO_SERVER="pipewire"
                                         echo -e "\033[1;92m✅ Audio server successfully set to PipeWire\033[0m"
                                         ;;
                                    2) 
                                         AUDIO_SERVER="pulseaudio"
                                         echo -e "\033[1;92m✅ Audio server successfully set to PulseAudio\033[0m"
                                         ;;
                                    *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                              esac
                              sleep 2
                              ;;
                         
                         $((5+NVIDIA_OFFSET))) # Desktop Environment
                              echo -e "\n\033[1;94mChoose your desktop environment:\033[0m"
                              echo -e "  \033[1;37m1)\033[0m \033[1;38;5;51mHyprland\033[0m"
                              echo -e "  \033[1;37m2)\033[0m \033[1;38;5;220mXFCE4\033[0m"
                              echo -e "  \033[1;37m3)\033[0m \033[1;38;5;39mKDE Plasma\033[0m"
                              echo -e "  \033[1;37m4)\033[0m \033[1;38;5;202mGNOME\033[0m"
                              read -p "Enter choice (1-4): " de_choice
                              case $de_choice in
                                   1) 
                                        DE_TYPE="Hyprland"; DE_CHOICE=1 
                                        echo -e "\033[1;92m✅ Desktop environment successfully set to Hyprland\033[0m"
                                        ;;
                                   2) 
                                        DE_TYPE="XFCE4"; DE_CHOICE=2 
                                        echo -e "\033[1;92m✅ Desktop environment successfully set to XFCE4\033[0m"
                                        ;;
                                   3) 
                                        DE_TYPE="KDE Plasma"; DE_CHOICE=3 
                                        echo -e "\033[1;92m✅ Desktop environment successfully set to KDE Plasma\033[0m"
                                        ;;
                                   4) 
                                        DE_TYPE="GNOME"; DE_CHOICE=4 
                                        echo -e "\033[1;92m✅ Desktop environment successfully set to GNOME\033[0m"
                                        ;;
                                   *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                              esac
                          sleep 2
                          ;;
                     
                         $((6+NVIDIA_OFFSET))) # Hostname
                              echo -e "\n\033[1;94mEnter system hostname:\033[0m"
                              read -p "Hostname: " new_hostname
                              if [[ -n "$new_hostname" ]]; then
                                    HOSTNAME="$new_hostname"
                                    echo -e "\033[1;92m✅ Hostname successfully updated to $HOSTNAME\033[0m"
                              else
                                    echo -e "\033[1;91m❌ Invalid hostname. Value not changed.\033[0m"
                              fi
                              sleep 1
                              ;;
                     
                         $((7+NVIDIA_OFFSET))) # Username
                              echo -e "\n\033[1;94mEnter username:\033[0m"
                              read -p "Username: " new_user
                              if [[ -n "$new_user" && "$new_user" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
                                    USER="$new_user"
                                    echo -e "\033[1;92m✅ Username successfully updated to $USER\033[0m"
                              else
                                    echo -e "\033[1;91m❌ Invalid username format. Value not changed.\033[0m"
                              fi
                              sleep 1
                              ;;
                     
                         $((8+NVIDIA_OFFSET))) # Passwords
                              echo -e "\n\033[1;94mUpdate passwords:\033[0m"
                              get_password "Enter the password for user $USER" USERPASS
                              echo -e "\033[1;92m✅ User password successfully updated\033[0m"
                              get_password "Enter the password for root" ROOTPASS
                              echo -e "\033[1;92m✅ Root password successfully updated\033[0m"
                              sleep 1
                              ;;
                     
                         $((9+NVIDIA_OFFSET))) # Keyboard layout
                              echo -e "\n\033[1;94mSelect keyboard layout:\033[0m"
                              # Display some common layouts
                              echo -e "  \033[1;37m1)\033[0m us (US English)"
                              echo -e "  \033[1;37m2)\033[0m uk (UK English)"
                              echo -e "  \033[1;37m3)\033[0m de (German)"
                              echo -e "  \033[1;37m4)\033[0m fr (French)"
                              echo -e "  \033[1;37m5)\033[0m it (Italian)"
                              echo -e "  \033[1;37m6)\033[0m es (Spanish)"
                              echo -e "  \033[1;37m7)\033[0m Show all layouts"
                              echo -e "  \033[1;37m8)\033[0m Enter custom layout"
                              
                              read -p "Enter choice: " keyboard_choice
                              
                              case $keyboard_choice in
                                    1) 
                                         KEYBOARD_LAYOUT="us"
                                         echo -e "\033[1;92m✅ Keyboard layout successfully set to US English\033[0m"
                                         ;;
                                    2) 
                                         KEYBOARD_LAYOUT="uk"
                                         echo -e "\033[1;92m✅ Keyboard layout successfully set to UK English\033[0m"
                                         ;;
                                    3) 
                                         KEYBOARD_LAYOUT="de"
                                         echo -e "\033[1;92m✅ Keyboard layout successfully set to German\033[0m"
                                         ;;
                                    4) 
                                         KEYBOARD_LAYOUT="fr"
                                         echo -e "\033[1;92m✅ Keyboard layout successfully set to French\033[0m"
                                         ;;
                                    5) 
                                         KEYBOARD_LAYOUT="it"
                                         echo -e "\033[1;92m✅ Keyboard layout successfully set to Italian\033[0m"
                                         ;;
                                    6) 
                                         KEYBOARD_LAYOUT="es"
                                         echo -e "\033[1;92m✅ Keyboard layout successfully set to Spanish\033[0m"
                                         ;;
                                    7)
                                         # Show all layouts as before
                                         mapfile -t ALL_KEYBOARD_LAYOUTS < <(localectl list-keymaps | sort)
                                         # Create filtered array
                                         declare -a KEYBOARD_LAYOUTS
                                         declare -A seen_layouts
                                         for layout in "${ALL_KEYBOARD_LAYOUTS[@]}"; do
                                              base_lang=$(echo "$layout" | cut -d'-' -f1)
                                              if [[ -z "${seen_layouts[$base_lang]}" ]]; then
                                                    seen_layouts[$base_lang]=1
                                                    KEYBOARD_LAYOUTS+=("$layout")
                                              fi
                                         done
                                         
                                         COLUMNS=4                                         TOTAL_LAYOUTS=${#KEYBOARD_LAYOUTS[@]}
                                         
                                         echo -e "\nAvailable keyboard layouts:"
                                         for ((i=0; i<TOTAL_LAYOUTS; i++)); do
                                              # Format each entry with fixed width for alignment
                                              printf "  \033[1;37m%3d)\033[0m %-20s" "$((i+1))" "${KEYBOARD_LAYOUTS[$i]}"
                                              # Add a newline after every COLUMNS items
                                              if (( (i+1) % COLUMNS == 0 )); then
                                                    echo ""
                                              fi
                                         done
                                         if (( TOTAL_LAYOUTS % COLUMNS != 0 )); then
                                              echo ""
                                         fi
                                         
                                         read -p "Enter layout number: " layout_num
                                         if [[ "$layout_num" =~ ^[0-9]+$ && "$layout_num" -ge 1 && "$layout_num" -le "$TOTAL_LAYOUTS" ]]; then
                                              KEYBOARD_LAYOUT="${KEYBOARD_LAYOUTS[$((layout_num-1))]}"
                                              echo -e "\033[1;92m✅ Keyboard layout successfully set to $KEYBOARD_LAYOUT\033[0m"
                                         else
                                              echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m"
                                         fi
                                         ;;
                                    8)
                                         read -p "Enter custom keyboard layout: " custom_layout
                                         if [[ -n "$custom_layout" ]]; then
                                              KEYBOARD_LAYOUT="$custom_layout"
                                              echo -e "\033[1;92m✅ Keyboard layout successfully set to $KEYBOARD_LAYOUT\033[0m"
                                         else
                                              echo -e "\033[1;91m❌ Invalid input. Value not changed.\033[0m"
                                         fi
                                         ;;
                                    *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                              esac
                              sleep 2
                              ;;
                     
                         $((10+NVIDIA_OFFSET))) # System locale
                              echo -e "\n\033[1;94mSelect system locale:\033[0m"
                              # Display some common locales
                              echo -e "  \033[1;37m1)\033[0m en_US.UTF-8"
                              echo -e "  \033[1;37m2)\033[0m en_GB.UTF-8"
                              echo -e "  \033[1;37m3)\033[0m de_DE.UTF-8"
                              echo -e "  \033[1;37m4)\033[0m fr_FR.UTF-8"
                              echo -e "  \033[1;37m5)\033[0m it_IT.UTF-8"
                              echo -e "  \033[1;37m6)\033[0m es_ES.UTF-8"
                              echo -e "  \033[1;37m7)\033[0m Show all locales"
                              echo -e "  \033[1;37m8)\033[0m Enter custom locale"
                              
                              read -p "Enter choice: " locale_choice
                              
                              case $locale_choice in
                                    1) 
                                         SYSTEM_LOCALE="en_US.UTF-8"
                                         echo -e "\033[1;92m✅ System locale successfully set to en_US.UTF-8\033[0m"
                                         ;;
                                    2) 
                                         SYSTEM_LOCALE="en_GB.UTF-8"
                                         echo -e "\033[1;92m✅ System locale successfully set to en_GB.UTF-8\033[0m"
                                         ;;
                                    3) 
                                         SYSTEM_LOCALE="de_DE.UTF-8"
                                         echo -e "\033[1;92m✅ System locale successfully set to de_DE.UTF-8\033[0m"
                                         ;;
                                    4) 
                                         SYSTEM_LOCALE="fr_FR.UTF-8"
                                         echo -e "\033[1;92m✅ System locale successfully set to fr_FR.UTF-8\033[0m"
                                         ;;
                                    5) 
                                         SYSTEM_LOCALE="it_IT.UTF-8"
                                         echo -e "\033[1;92m✅ System locale successfully set to it_IT.UTF-8\033[0m"
                                         ;;
                                    6) 
                                         SYSTEM_LOCALE="es_ES.UTF-8"
                                         echo -e "\033[1;92m✅ System locale successfully set to es_ES.UTF-8\033[0m"
                                         ;;
                                    7)
                                         # Show all locales (simplified from original code)
                                         mapfile -t AVAILABLE_LOCALES < <(grep -E "^#[a-zA-Z]" /etc/locale.gen | sed 's/^#//' | sort)
                                         
                                         LOCALE_COLUMNS=3
                                         TOTAL_LOCALES=${#AVAILABLE_LOCALES[@]}
                                         
                                         echo -e "\nAvailable locales:"
                                         for ((i=0; i<TOTAL_LOCALES && i<30; i++)); do
                                              printf "  \033[1;37m%3d)\033[0m %-20s" "$((i+1))" "${AVAILABLE_LOCALES[$i]}"
                                              if (( (i+1) % LOCALE_COLUMNS == 0 )); then
                                                    echo ""
                                              fi
                                         done
                                         echo -e "\n... (showing first 30 only)"
                                         
                                         read -p "Enter locale number: " locale_input
                                         if [[ "$locale_input" =~ ^[0-9]+$ && "$locale_input" -ge 1 && "$locale_input" -le 30 ]]; then
                                              SYSTEM_LOCALE="${AVAILABLE_LOCALES[$((locale_input-1))]}"
                                              echo -e "\033[1;92m✅ System locale successfully set to $SYSTEM_LOCALE\033[0m"
                                         else
                                              echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m"
                                         fi
                                         ;;
                                    8)
                                         read -p "Enter custom locale: " custom_locale
                                         if [[ -n "$custom_locale" && "$custom_locale" =~ ^[a-zA-Z_]+\.UTF-8$ ]]; then
                                              SYSTEM_LOCALE="$custom_locale"
                                              echo -e "\033[1;92m✅ System locale successfully set to $SYSTEM_LOCALE\033[0m"
                                         else
                                              echo -e "\033[1;91m❌ Invalid locale format. Value not changed.\033[0m"
                                         fi
                                         ;;
                                    *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                              esac
                              sleep 2
                              ;;
                     
                         $((11+NVIDIA_OFFSET))) # Mirror country
                              echo -e "\n\033[1;94mSelect mirror country:\033[0m"
                              echo -e "  \033[1;37m1)\033[0m Italy"
                              echo -e "  \033[1;37m2)\033[0m Germany"
                              echo -e "  \033[1;37m3)\033[0m United States"
                              echo -e "  \033[1;37m4)\033[0m United Kingdom"
                              echo -e "  \033[1;37m5)\033[0m France"
                              echo -e "  \033[1;37m6)\033[0m Spain"
                              echo -e "  \033[1;37m7)\033[0m Netherlands"
                              echo -e "  \033[1;37m8)\033[0m Other (specify)"
                              echo -e "  \033[1;37m9)\033[0m Worldwide (no specific country)"
                              
                              read -p "Enter choice: " mirror_choice
                              
                              case $mirror_choice in
                                    1) 
                                         MIRROR_COUNTRY="Italy"
                                         echo -e "\033[1;92m✅ Mirror country successfully set to Italy\033[0m"
                                         ;;
                                    2) 
                                         MIRROR_COUNTRY="Germany"
                                         echo -e "\033[1;92m✅ Mirror country successfully set to Germany\033[0m"
                                         ;;
                                    3) 
                                         MIRROR_COUNTRY="United States"
                                         echo -e "\033[1;92m✅ Mirror country successfully set to United States\033[0m"
                                         ;;
                                    4) 
                                         MIRROR_COUNTRY="United Kingdom"
                                         echo -e "\033[1;92m✅ Mirror country successfully set to United Kingdom\033[0m"
                                         ;;
                                    5) 
                                         MIRROR_COUNTRY="France"
                                         echo -e "\033[1;92m✅ Mirror country successfully set to France\033[0m"
                                         ;;
                                    6) 
                                         MIRROR_COUNTRY="Spain"
                                         echo -e "\033[1;92m✅ Mirror country successfully set to Spain\033[0m"
                                         ;;
                                    7) 
                                         MIRROR_COUNTRY="Netherlands"
                                         echo -e "\033[1;92m✅ Mirror country successfully set to Netherlands\033[0m"
                                         ;;
                                    8) 
                                         read -p "Enter country name: " custom_country
                                         if [[ -n "$custom_country" ]]; then
                                              MIRROR_COUNTRY="$custom_country"
                                              echo -e "\033[1;92m✅ Mirror country successfully set to $MIRROR_COUNTRY\033[0m"
                                         else
                                              echo -e "\033[1;91m❌ Invalid country name. Value not changed.\033[0m"
                                         fi
                                         ;;
                                    9) 
                                         MIRROR_COUNTRY="" 
                                         echo -e "\033[1;92m✅ Mirror selection successfully set to Worldwide\033[0m"
                                         ;;
                                    *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                              esac
                              sleep 2
                              ;;
                         
                         $((12+NVIDIA_OFFSET))) # EFI Partition Size (Advanced mode)
                              if [ "$INSTALL_MODE" = "advanced" ]; then
                                    echo -e "\n\033[1;94mEnter new EFI partition size (e.g. 512M, 1G):\033[0m"
                                    read -p "New size: " new_efi_size
                                    if [[ "$new_efi_size" =~ ^[0-9]+[MG]$ ]]; then
                                         EFI_PART_SIZE="$new_efi_size"
                                         echo -e "\033[1;92m✅ EFI partition size successfully updated to $EFI_PART_SIZE\033[0m"
                                    else
                                         echo -e "\033[1;91m❌ Invalid size format. Use format like 512M or 1G.\033[0m"
                                    fi
                                    sleep 2
                              else
                                    echo -e "\033[1;91m❌ Invalid setting number.\033[0m"; sleep 2
                              fi
                              ;;
                         
                         $((13+NVIDIA_OFFSET))) # Root Partition Size (Advanced mode)
                              if [ "$INSTALL_MODE" = "advanced" ]; then
                                    echo -e "\n\033[1;94mEnter new Root partition size (MAX for all available space, or e.g. 50G):\033[0m"
                                    read -p "New size: " new_root_size
                                    if [[ "$new_root_size" = "MAX" || "$new_root_size" =~ ^[0-9]+G$ ]]; then
                                         ROOT_PART_SIZE="$new_root_size"
                                         echo -e "\033[1;92m✅ Root partition size successfully updated to $ROOT_PART_SIZE\033[0m"
                                    else
                                         echo -e "\033[1;91m❌ Invalid size format. Use 'MAX' or format like '50G'.\033[0m"
                                    fi
                                    sleep 2
                              else
                                    echo -e "\033[1;91m❌ Invalid setting number.\033[0m"; sleep 2
                              fi
                              ;;
                         
                         $((14+NVIDIA_OFFSET))) # Disk Encryption (Advanced mode) 
                              if [ "$INSTALL_MODE" = "advanced" ]; then
                                    echo -e "\n\033[1;94mDisk encryption:\033[0m"
                                    echo -e "  \033[1;97m1)\033[0m Yes (More secure, requires passphrase)"
                                    echo -e "  \033[1;97m2)\033[0m No (More convenient, less secure)"
                                    read -p "Enter choice (1-2): " encrypt_choice
                                    case $encrypt_choice in
                                         1) 
                                              ENCRYPT_DISK="yes"
                                              get_password "Enter disk encryption passphrase" DISK_PASSWORD
                                              echo -e "\033[1;92m✅ Disk encryption successfully enabled and passphrase set\033[0m"
                                              ;;
                                         2) 
                                              ENCRYPT_DISK="no"
                                              DISK_PASSWORD=""
                                              echo -e "\033[1;92m✅ Disk encryption successfully disabled\033[0m"
                                              ;;
                                         *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                                    esac
                                    sleep 2
                              else
                                    echo -e "\033[1;91m❌ Invalid setting number.\033[0m"; sleep 2
                              fi
                              ;;
                         
                         $((15+NVIDIA_OFFSET))) # ZFS Compression (Advanced mode)
                              if [ "$INSTALL_MODE" = "advanced" ]; then
                                    echo -e "\n\033[1;94mSelect ZFS compression algorithm:\033[0m"
                                    echo -e "  \033[1;37m1)\033[0m \033[1;38;5;39mlz4\033[0m (Fast, good ratio)"
                                    echo -e "  \033[1;37m2)\033[0m \033[1;38;5;202mzstd\033[0m (Better compression, slightly slower)"
                                    echo -e "  \033[1;37m3)\033[0m \033[1;38;5;118mgzip\033[0m (Best compression, slowest)"
                                    echo -e "  \033[1;37m4)\033[0m \033[1;38;5;196mNone\033[0m (No compression)"
                                    read -p "Enter choice (1-4): " compression_choice
                                    case $compression_choice in
                                         1) 
                                              ZFS_COMPRESSION="lz4"
                                              echo -e "\033[1;92m✅ ZFS compression successfully set to lz4\033[0m"
                                              ;;
                                         2) 
                                              ZFS_COMPRESSION="zstd"
                                              echo -e "\033[1;92m✅ ZFS compression successfully set to zstd\033[0m"
                                              ;;
                                         3) 
                                              ZFS_COMPRESSION="gzip"
                                              echo -e "\033[1;92m✅ ZFS compression successfully set to gzip\033[0m"
                                              ;;
                                         4) 
                                              ZFS_COMPRESSION="off"
                                              echo -e "\033[1;92m✅ ZFS compression successfully disabled\033[0m"
                                              ;;
                                         *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                                    esac
                                    sleep 2
                              else
                                    echo -e "\033[1;91m❌ Invalid setting number.\033[0m"; sleep 2
                              fi
                              ;;
                         
                         $((16+NVIDIA_OFFSET))) # Separate Datasets (Advanced mode)
                              if [ "$INSTALL_MODE" = "advanced" ]; then
                                    echo -e "\n\033[1;94mConfigure ZFS datasets structure:\033[0m"
                                    echo -e "  \033[1;37m1)\033[0m Simple (Single root dataset only)"
                                    echo -e "  \033[1;37m2)\033[0m Advanced (Separate datasets for system directories)"
                                    read -p "Enter choice (1-2): " datasets_choice
                                    case $datasets_choice in
                                         1) 
                                              SEPARATE_DATASETS="no" 
                                              echo -e "\033[1;92m✅ ZFS dataset structure successfully set to simple\033[0m"
                                              ;;
                                         2) 
                                              SEPARATE_DATASETS="yes" 
                                              echo -e "\033[1;92m✅ ZFS dataset structure successfully set to advanced\033[0m"
                                              ;;
                                         *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                                    esac
                                    sleep 2
                              else
                                    echo -e "\033[1;91m❌ Invalid setting number.\033[0m"; sleep 2
                              fi
                              ;;
                         
                         $((17+NVIDIA_OFFSET))) # ZRAM Size (Advanced mode)
                              if [ "$INSTALL_MODE" = "advanced" ]; then
                                    echo -e "\n\033[1;94mSelect ZRAM size:\033[0m"
                                    echo -e "  \033[1;37m1)\033[0m Auto (min(RAM, 32GB))"
                                    echo -e "  \033[1;37m2)\033[0m Half of RAM"
                                    echo -e "  \033[1;37m3)\033[0m Custom value (specify in MB)"
                                    read -p "Enter choice (1-3): " zram_size_choice
                                    case $zram_size_choice in
                                         1) 
                                              ZRAM_SIZE="min(ram, 32768)"
                                              echo -e "\033[1;92m✅ ZRAM size successfully set to automatic sizing\033[0m"
                                              ;;
                                         2) 
                                              ZRAM_SIZE="ram / 2"
                                              echo -e "\033[1;92m✅ ZRAM size successfully set to half of RAM\033[0m"
                                              ;;
                                         3) 
                                              read -p "Enter ZRAM size in MB (e.g., 8192 for 8GB): " custom_zram_size
                                              if [[ "$custom_zram_size" =~ ^[0-9]+$ ]]; then
                                                    ZRAM_SIZE="$custom_zram_size"
                                                    echo -e "\033[1;92m✅ ZRAM size successfully set to ${custom_zram_size}MB\033[0m"
                                              else
                                                    echo -e "\033[1;91m❌ Invalid size. Value not changed.\033[0m"
                                              fi
                                              ;;
                                         *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                                    esac
                                    sleep 2
                              else
                                    echo -e "\033[1;91m❌ Invalid setting number.\033[0m"; sleep 2
                              fi
                              ;;
                         
                         $((18+NVIDIA_OFFSET))) # ZRAM Compression (Advanced mode)
                              if [ "$INSTALL_MODE" = "advanced" ]; then
                                    echo -e "\n\033[1;94mSelect ZRAM compression algorithm:\033[0m"
                                    echo -e "  \033[1;37m1)\033[0m zstd (Best balance of speed/compression)"
                                    echo -e "  \033[1;37m2)\033[0m lz4 (Faster, lower compression ratio)"
                                    echo -e "  \033[1;37m3)\033[0m lzo-rle"
                                    echo -e "  \033[1;37m4)\033[0m lzo"
                                    read -p "Enter choice (1-4): " zram_compression_choice
                                    case $zram_compression_choice in
                                         1) 
                                              ZRAM_COMPRESSION="zstd"
                                              echo -e "\033[1;92m✅ ZRAM compression successfully set to zstd\033[0m"
                                              ;;
                                         2) 
                                              ZRAM_COMPRESSION="lz4"
                                              echo -e "\033[1;92m✅ ZRAM compression successfully set to lz4\033[0m"
                                              ;;
                                         3) 
                                              ZRAM_COMPRESSION="lzo-rle"
                                              echo -e "\033[1;92m✅ ZRAM compression successfully set to lzo-rle\033[0m"
                                              ;;
                                         4) 
                                              ZRAM_COMPRESSION="lzo"
                                              echo -e "\033[1;92m✅ ZRAM compression successfully set to lzo\033[0m"
                                              ;;
                                         *) echo -e "\033[1;91m⚠️ Invalid choice. Value not changed.\033[0m" ;;
                                    esac
                                    sleep 2
                              else
                                    echo -e "\033[1;91m❌ Invalid setting number.\033[0m"; sleep 2
                              fi
                              ;;

                     *) echo -e "\033[1;91m❌ Invalid setting number.\033[0m"; sleep 2 ;;
                esac
          fi
          done
     elif [[ "$choice" != "c" && "$choice" != "C" && "$choice" != "a" && "$choice" != "A" ]]; then
          echo -e "\033[1;93m⚠️ Invalid choice. Please enter 'c' to confirm, 'm' to modify, or 'a' to abort.\033[0m"
          sleep 2
          # Loop will continue and prompt again in the next iteration
     fi
done




# ----------------------------------------
# CLEAN SYSTEM DISK
# ----------------------------------------
print_section_header "CLEAN SYSTEM DISK"

run_command "wipefs -a -f $DEVICE" "wipe disk signatures"

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
    ) | run_command "fdisk $DEVICE" "create partitions"

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
    ) | run_command "fdisk $DEVICE" "create partitions"
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
    chmod 600 /etc/zfs/zroot.key
    chown root:root /etc/zfs/zroot.key

    
    # Create ZFS pool with encryption and user-defined compression if in advanced mode
    run_command "zpool create \
        -o ashift=12 \
        -O acltype=posixacl -O canmount=off -O compression=$ZFS_COMPRESSION \
        -O dnodesize=auto -O normalization=formD -o autotrim=on \
        -O atime=off -O xattr=sa -O mountpoint=none \
        -O encryption=aes-256-gcm -O keylocation=file:///etc/zfs/zroot.key -O keyformat=passphrase \
        -R /mnt zroot ${DEVICE}${PARTITION_2} -f" "create encrypted ZFS pool with $ZFS_COMPRESSION compression"



else
    echo -e "\033[1;94m🌊 Creating standard ZFS pool...\033[0m"
    run_command "zpool create \
        -o ashift=12 \
        -O acltype=posixacl -O canmount=off -O compression=$ZFS_COMPRESSION \
        -O dnodesize=auto -O normalization=formD -o autotrim=on \
        -O atime=off -O xattr=sa -O mountpoint=none \
        -R /mnt zroot ${DEVICE}${PARTITION_2} -f" "create ZFS pool with $ZFS_COMPRESSION compression"
fi

run_command "zfs create -o canmount=noauto -o mountpoint=/ zroot/root" "create ZFS root dataset"

run_command "zpool set bootfs=zroot/root zroot" "set bootfs property"

run_command "zfs mount zroot/root" "mount the root dataset"

# Create additional ZFS datasets if separate datasets option was selected
if [ "$SEPARATE_DATASETS" = "yes" ]; then
    
    # Create datasets for various system directories
    run_command "zfs create -o mountpoint=/home zroot/home" "create ZFS home dataset"
    zfs mount zroot/home
    run_command "zfs create -o mountpoint=/var zroot/var" "create ZFS var dataset"
    zfs mount zroot/var
fi

mkdir -p /mnt/etc/zfs
run_command "zpool set cachefile=/etc/zfs/zpool.cache zroot" "set ZFS pool cache file"
cp /etc/zfs/zpool.cache /mnt/etc/zfs/zpool.cache
cp /etc/zfs/zroot.key /mnt/etc/zfs/zroot.key


run_command "mkfs.fat -F32 ${DEVICE}${PARTITION_1}" "format EFI partition with FAT32"
mkdir -p /mnt/efi && mount ${DEVICE}${PARTITION_1} /mnt/efi

# ----------------------------------------
# INSTALL BASE
# ----------------------------------------
print_section_header "INSTALL BASE"

run_command "pacstrap /mnt linux-lts linux-lts-headers mkinitcpio base git base-devel linux-firmware zram-generator reflector sudo networkmanager efibootmgr $CPU_MICROCODE wget unzip" "install base packages" 


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

echo -e "\n\033[1;94m⚙️ \033[1;38;5;87mExecuting:\033[0m \033[1;38;5;195march-chroot into the new system\033[0m"


# Export all functions needed by the chroot script
run_command_definition=$(declare -f run_command)
handle_error_definition=$(declare -f handle_error)
print_section_header_definition=$(declare -f print_section_header)


chroot_script=$(cat <<EOF
$run_command_definition
$handle_error_definition
$print_section_header_definition


echo -e "\033[1;92m✅ Successfully arch-chrooted in new installation\033[0m\n"


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
run_command "efibootmgr --disk $DEVICE --part 1 --create \
                 --label \"ZFSBootMenu\" \
                 --loader '\\EFI\\zbm\\zfsbootmenu.EFI' \
                 --unicode \"spl_hostid=$(hostid) zbm.timeout=3 zbm.prefer=zroot zbm.import_policy=hostid\" \
                 --verbose" "create EFI boot entry for ZFSBootMenu"


run_command "zfs set org.zfsbootmenu:commandline=\"noresume init_on_alloc=0 rw spl.spl_hostid=$(hostid)\" zroot/root" "set ZFSBootMenu commandline property"

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
    run_command "sed -i '/^FILES=.*|FILES=(/etc/zfs/zroot.key)/d' /etc/mkinitcpio.conf" "add encryption key to mkinitcpio FILES array"
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

echo -e "\033[1;94m💻 Setting hostname to: \033[1;97m$HOSTNAME\033[0m"
echo "$HOSTNAME" > /etc/hostname
echo -e "127.0.0.1   localhost\n::1         localhost\n127.0.1.1   $HOSTNAME.localdomain   $HOSTNAME" > /etc/hosts

echo -e "\033[1;94m🔣 Configuring keyboard layout: \033[1;97m$KEYBOARD_LAYOUT\033[0m"
run_command "localectl set-keymap "$KEYBOARD_LAYOUT" && echo "KEYMAP=$KEYBOARD_LAYOUT" > /etc/vconsole.conf" "set keyboard layout"

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

case \$DE_CHOICE in
        "1")
                echo -e "\033[1;92m✨ Installing Hyprland...\033[0m"
                run_command "pacman -S --noconfirm hyprland egl-wayland sddm qt6-svg qt6-declarative qt5-quickcontrols2" "install Hyprland, SDDM and dependencies"
                run_command "systemctl enable sddm" "enable SDDM"

                run_command "find /usr/share/wayland-sessions -type f -not -name \"hyprland.desktop\" -delete" "clean up wayland sessions"

                run_command "wget https://github.com/catppuccin/sddm/releases/download/v1.0.0/catppuccin-frappe.zip && unzip catppuccin-frappe.zip -d /usr/share/sddm/themes/ && rm -f catppuccin-frappe.zip" "download SDDM theme"
                run_command "mkdir -p /etc/sddm.conf.d/ && echo -e '[Theme]\nCurrent=catppuccin-frappe' > /etc/sddm.conf.d/theme.conf" "configure SDDM theme"

                # Ask which dotfiles to install
                echo -e "\033[1;94mSelect dotfiles to install:\033[0m"
                echo -e "  \033[1;37m1)\033[0m \033[1;38;5;39mML4W dotfiles\033[0m (mylinuxforwork dotfiles)"
                echo -e "  \033[1;37m2)\033[0m \033[1;38;5;208mEnd-4 dotfiles\033[0m (end-4's Hyprland dotfiles)"
                echo -e "  \033[1;37m3)\033[0m \033[1;38;5;196mNone\033[0m (No dotfiles, vanilla installation)"
                echo
                
                while true; do
                    echo -en "\033[1;94mEnter your choice (1-3): \033[0m"
                    while read -r -t 0; do read -r; done
                    read -r dotfiles_choice
                    
                    case \$dotfiles_choice in
                        1)
                            echo -e "\033[1;92m✅ Selected ML4W dotfiles\033[0m"
                            run_command "su -c \"cd && wget https://raw.githubusercontent.com/mylinuxforwork/dotfiles/main/setup-arch.sh && chmod +x setup-arch.sh\" $USER" "download ml4w dotfiles"
                            break
                            ;;
                        2)
                            echo -e "\033[1;92m✅ Selected End-4 dotfiles\033[0m"
                            run_command "su -c \"cd && wget https://end-4.github.io/dots-hyprland-wiki/setup.sh && chmod +x setup.sh\" $USER" "download end-4 dotfiles"
                            break
                            ;;
                        3)
                            echo -e "\033[1;92m✅ No dotfiles will be installed\033[0m"
                            break
                            ;;
                        *)
                            echo -e "\033[1;91m⚠️ Invalid choice. Please enter 1, 2, or 3.\033[0m"
                            ;;
                    esac
                done
                ;;
        "2")
                echo -e "\033[1;92m✨ Installing XFCE4...\033[0m"
                run_command "pacman -S --noconfirm xfce4 xfce4-goodies lightdm lightdm-gtk-greeter" "install XFCE4"
                run_command "systemctl enable lightdm" "enable LightDM"
                ;;
        "3")
                echo -e "\033[1;92m✨ Installing KDE Plasma...\033[0m"
                run_command "pacman -S --noconfirm plasma sddm konsole okular dolphin" "install KDE Plasma"
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
                echo -e "\033[1;91m⚠️ Invalid choice '$DE_CHOICE'. Installing Hyprland as default...\033[0m"
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

# Remove the no more needed NOPASSWD entry and add a proper sudoers entry
sed -i "/^$USER ALL=(ALL:ALL) NOPASSWD: ALL/d" /etc/sudoers
echo -e "\n$USER ALL=(ALL:ALL) ALL" >> /etc/sudoers


# ----------------------------------------
# UTILITIES INSTALLATION
# ----------------------------------------
print_section_header "INSTALLING UTILITIES"

run_command "pacman -S --noconfirm flatpak firefox man nano git" "install base utilities"

# ----------------------------------------
# AUDIO CONFIGURATION
# ----------------------------------------
print_section_header "CONFIGURING AUDIO"

echo -e "\033[1;94m🔊 Setting up audio server: \033[1;97m$AUDIO_SERVER\033[0m"

if [ "$AUDIO_SERVER" = "pipewire" ]; then
    echo -e "\033[1;92m✨ Installing PipeWire audio system...\033[0m"
    run_command "pacman -S --noconfirm wireplumber pipewire-pulse pipewire-alsa pavucontrol-qt" "install PipeWire and related packages"
else
    echo -e "\033[1;92m✨ Installing PulseAudio audio system...\033[0m"
    run_command "pacman -S --noconfirm pulseaudio pulseaudio-alsa pulseaudio-bluetooth pavucontrol-qt" "install PulseAudio and related packages" 
fi

chown -R $USER:$USER /home/$USER/.config 2>/dev/null

# ----------------------------------------
# GPU DRIVERS CONFIGURATION
# ----------------------------------------
print_section_header "CONFIGURING GPU DRIVERS"

# Install appropriate GPU drivers based on earlier selection
if [ "$GPU_TYPE" = "NVIDIA" ]; then
    if [ "$NVIDIA_DRIVER_TYPE" = "open" ]; then
        echo -e "\033[1;94m🎮 Installing NVIDIA open drivers...\033[0m"
        run_command "pacman -S --noconfirm nvidia-open-lts nvidia-settings nvidia-utils opencl-nvidia libxnvctrl" "install NVIDIA open drivers"
    else
        echo -e "\033[1;94m🎮 Installing NVIDIA proprietary drivers...\033[0m"
        run_command "pacman -S --noconfirm nvidia-lts nvidia-settings nvidia-utils opencl-nvidia libxnvctrl" "install NVIDIA proprietary drivers"
    fi
elif [ "$GPU_TYPE" = "AMD/Intel" ]; then
    echo -e "\033[1;94m🎮 Installing AMD/Intel GPU drivers...\033[0m"
    run_command "pacman -S --noconfirm mesa lib32-mesa vulkan-radeon lib32-vulkan-radeon libva-mesa-driver lib32-libva-mesa-driver mesa-vdpau lib32-mesa-vdpau" "install AMD/Intel GPU drivers"
elif [ "$GPU_TYPE" = "None/VM" ]; then
    echo -e "\033[1;94m🎮 Installing basic video drivers for VM/basic system...\033[0m"
    run_command "pacman -S --noconfirm mesa xf86-video-fbdev" "install basic video drivers"
fi

# ----------------------------------------
# CUSTOM PACKAGES INSTALLATION
# ----------------------------------------
print_section_header "CUSTOM PACKAGES INSTALLATION"

echo -e "\033[1;94mWould you like to install additional custom packages?\033[0m"
echo -e "\033[1;93mThis is your chance to add any specific software before completing the installation.\033[0m\n"
echo -e "  \033[1;37m1)\033[0m \033[1;38;5;82mYes\033[0m (Specify packages to install)"
echo -e "  \033[1;37m2)\033[0m \033[1;38;5;203mNo\033[0m (Skip this step)"
echo

while true; do
    echo -en "\033[1;94mEnter your choice (1-2): \033[0m"
    while read -r -t 0; do read -r; done
    read -r custom_packages_choice
    
    case $custom_packages_choice in
        1)
            echo -e "\n\033[1;94mEnter the package names separated by spaces:\033[0m"
            echo -e "\033[1;93mExample: neofetch htop vlc gimp\033[0m"
            echo -en "\033[1;94mPackages: \033[0m"
            while read -r -t 0; do read -r; done
            read -r custom_packages
            
            if [ -n "$custom_packages" ]; then
                echo -e "\n\033[1;92m✨ Installing custom packages: \033[1;97m$custom_packages\033[0m"
                run_command "pacman -S --noconfirm --needed $custom_packages" "install custom packages"
            else
                echo -e "\n\033[1;93m⚠️ No packages specified. Skipping custom package installation.\033[0m"
            fi
            break
            ;;
        2|"")
            echo -e "\033[1;92m✅ Skipping custom package installation\033[0m"
            break
            ;;
        *)
            echo -e "\033[1;91m⚠️ Invalid choice. Please enter 1 or 2.\033[0m"
            ;;
    esac
done

EOF


)

# Export values into chroot via env, delay expansion until inside chroot
env \
DISK="$DEVICE" \
HOSTNAME="$HOSTNAME" \
KEYBOARD_LAYOUT="$KEYBOARD_LAYOUT" \
SYSTEM_LOCALE="$SYSTEM_LOCALE" \
USER="$USER" \
USERPASS="$USERPASS" \
ROOTPASS="$ROOTPASS" \
CPU_MICROCODE="$CPU_MICROCODE" \
DE_CHOICE="$DE_CHOICE" \
GPU_TYPE="$GPU_TYPE" \
NVIDIA_DRIVER_TYPE="$NVIDIA_DRIVER_TYPE" \
MIRROR_COUNTRY="$MIRROR_COUNTRY" \
AUDIO_SERVER="$AUDIO_SERVER" \
INSTALL_MODE="$INSTALL_MODE" \
ZRAM_SIZE="$ZRAM_SIZE" \
ZRAM_COMPRESSION="$ZRAM_COMPRESSION" \
arch-chroot /mnt /bin/bash -c "$chroot_script"


# --------------------------------------------------------------------------------------------------------------------------
# Cleanup and Finalize Installation
# --------------------------------------------------------------------------------------------------------------------------

# Set a flag to indicate if installation completed successfully
INSTALL_SUCCESS=true

# Check if we had a critical error that caused installation to abort
if [ -f "/tmp/install_aborted" ]; then
    INSTALL_SUCCESS=false
    rm -f "/tmp/install_aborted"
fi

# Remove installation files from the mounted system
rm -rf /mnt/install

# Stop redirecting to log file before the final steps
exec > /dev/tty 2>&1

# Only show completion message if installation was successful
if [ "$INSTALL_SUCCESS" = true ]; then
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
    echo -e "  \033[1;97m💻\033[0m Hostname: \033[1;97m$HOSTNAME\033[0m"
    echo -e "  \033[1;97m👤\033[0m Username: \033[1;97m$USER\033[0m"
    echo -e "  \033[1;97m🔣\033[0m Keyboard: \033[1;97m$KEYBOARD_LAYOUT\033[0m"
    echo -e "  \033[1;97m🌐\033[0m Locale: \033[1;97m$SYSTEM_LOCALE\033[0m"
    echo -e "  \033[1;97m🌍\033[0m Mirrors: \033[1;97m${MIRROR_COUNTRY:-Worldwide}\033[0m"
    echo

    # Hardware Configuration
    echo -e "\033[1;38;5;117m⚙️ Hardware Configuration:\033[0m"
    echo -e "  \033[1;97m💽\033[0m Target Device: \033[1;97m$DEVICE\033[0m"
    echo -e "  \033[1;97m🧠\033[0m CPU: \033[1;97m$CPU_TYPE ($CPU_MICROCODE)\033[0m"
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
    echo -e "  \033[1;97m💻\033[0m Desktop Environment: \033[1;97m$DE_TYPE\033[0m"
    echo -e "  \033[1;97m📇\033[0m Install Mode: \033[1;97m${INSTALL_MODE^}\033[0m"
    echo

    # Performance Configuration
    echo -e "\033[1;38;5;208m⚡ Performance Configuration:\033[0m"
    echo -e "  \033[1;97m💿\033[0m ZRAM Size: \033[1;97m$ZRAM_SIZE\033[0m"
    echo -e "  \033[1;97m📁\033[0m ZRAM Compression: \033[1;97m$ZRAM_COMPRESSION\033[0m"
    echo

    echo -e "\033[1;38;5;87m🚀 Your new Arch Linux system is ready!\033[0m"

    # Ask user if they want to reboot now
    while true; do
        echo -en "\033[1;93mDo you want to reboot now? [Y/n/s(show log)]: \033[0m"
        # Clear input buffer before reading
        while read -r -t 0; do read -r; done
        read -r reboot_choice
        
        case $reboot_choice in
            [Yy])
                echo -e "\n\033[1;94m🔄 Unmounting filesystems and rebooting system...\033[0m"
                umount -R /mnt 2>/dev/null
                zfs umount -a 2>/dev/null
                zpool export -a 2>/dev/null
                
                # Reboot the system
                echo -e "\033[1;92m👋 Rebooting now. See you on the other side!\033[0m"
                sleep 1
                reboot
                exit 0  # Ensure the script exits immediately
                ;;
            [Ss])
                echo -e "\033[1;94mShowing installation log. Press q to return to reboot prompt.\033[0m"
                less "$LOG_FILE"
                echo -e "\033[1;93mReturning to reboot prompt...\033[0m"
                # Continue with the reboot prompt after viewing log
                continue
                ;;
            [Nn])
                echo -e "\n\033[1;94mSystem is ready. You can reboot manually when ready with 'reboot' command.\033[0m"
                echo -e "\033[1;93m⚠️  Remember to properly unmount filesystems before rebooting:\033[0m"
                echo -e "  \033[1;37m•\033[0m umount -R /mnt"
                echo -e "  \033[1;37m•\033[0m zfs umount -a"
                echo -e "  \033[1;37m•\033[0m zpool export -a\n\n"
                exit 0
                ;;
            *)
                echo -e "\033[1;91m⚠️ Invalid choice. Please answer Y, N, or S.\033[0m"
                # The loop will continue and repeat the question
                ;;
        esac
    done
else
    # Display message if installation was aborted
    echo -e "\n\033[1;91m❌ Installation was aborted due to errors.\033[0m"
    echo -e "\033[1;93mCheck the log file for details: $LOG_FILE\033[0m"
    echo -e "\033[1;37mYou can view the log with: less $LOG_FILE\033[0m\n"
    exit 1
fi