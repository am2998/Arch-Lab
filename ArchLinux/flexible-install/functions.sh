#!/bin/bash

# Function to handle command failures
handle_error() {
    local desc="$1"
    local retry_prompt="${2:-true}"
    
    echo -e "\033[1;31m❌ Error: Failed to $desc\033[0m" >&2
    
    if [ "$retry_prompt" = "true" ]; then
        while true; do
            read -p $'\n\033[1;33mRetry? (y), Skip (s), or Abort (a): \033[0m' choice
            case "$choice" in
                [Yy]*)
                    echo -e "\n\033[1;34m🔄 Retrying\033[0m"
                    return 0  # Return code to indicate retry
                    ;;
                [Ss]*)
                    echo -e "\n\033[1;33m⏩ Skipping\033[0m"
                    return 1  # Return code to indicate skip
                    ;;
                [Aa]*)
                    echo -e "\n\033[1;31m🛑 Aborting installation\033[0m"
                    exit 1
                    ;;
                *)
                    echo -e "\n\033[1;35m❓ Invalid choice. Please enter 'y', 's', or 'a'\033[0m"
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
                    read -p $'\n\033[1;33mRetry? (y) or Abort installation (a): \033[0m' choice
                    case "$choice" in
                        [Yy]*)
                            echo -e "\n\033[1;34m🔄 Retrying\033[0m"
                            break
                            ;;
                        [Aa]*)
                            echo -e "\n\033[1;31m🛑 Aborting installation\033[0m"
                            exit 1
                            ;;
                        *)
                            echo -e "\n\033[1;35m❓ Invalid choice. Please enter 'y' or 'a'\033[0m"
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