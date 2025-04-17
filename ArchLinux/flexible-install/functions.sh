#!/bin/bash

# Function to handle command failures
handle_error() {
    local desc="$1"
    local retry_prompt="${2:-true}"
    
    echo -e "❌ Error: Failed to $desc" >&2
    
    if [ "$retry_prompt" = "true" ]; then
        while true; do
            read -p "\nRetry? (y), Skip (s), or Abort (a): " choice
            case "$choice" in
                [Yy]*)
                    echo -e "\n🔄 Retrying"
                    return 0  # Return code to indicate retry
                    ;;
                [Ss]*)
                    echo -e "\n⏩ Skipping"
                    return 1  # Return code to indicate skip
                    ;;
                [Aa]*)
                    echo -e "\n🛑 Aborting installation"
                    exit 1
                    ;;
                *)
                    echo -e "\n❓ Invalid choice. Please enter 'y', 's', or 'a'"
                    ;;
            esac
        done
    else
        return 1  # Skip if retry is not enabled
    fi
}

# Function to print section headers with formatting
print_section_header() {
    echo -e "\n\n\033[1;34m====================================================================\033[0m"
    echo -e "\033[1;34m   $1\033[0m"
    echo -e "\033[1;34m====================================================================\033[0m\n"
}

# Function to securely get passwords with confirmation
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

# Function to run commands and handle errors
run_command() {
    local cmd="$1"
    local desc="$2"
    local retry_prompt="${3:-true}"
    local silent="${4:-false}"
    
    if [ "$silent" != "true" ]; then
        echo -e "\n⚙️ Executing: $desc"
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
                echo -e "✅ Successfully completed"
            fi
            return 0
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
    done
}