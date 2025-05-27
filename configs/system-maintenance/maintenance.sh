#!/bin/bash

# === CONFIGURATION ===
POOL="zroot/rootfs"
BACKUP_POOL="backupzroot/rootfs"
DATE=$(date +%m%d)
SNAP_PREFIX="weekly-${DATE}-v"
MAX_SNAPSHOTS=5
LOGFILE="/var/log/system-maintenance.log"

# === LOGGING HELPERS ===
banner_line="================================================================================"
log_snapshot_start() {
    local snapshot="$1"
    local timestamp=$(LC_TIME=it_IT.UTF-8 date +"%a %d %b %Y, %T, %Z")
    echo -e "${banner_line}\n=== SNAPSHOT: ${snapshot} START | ${timestamp} ===\n${banner_line}\n"
}

log_snapshot_end() {
    local snapshot="$1"
    local timestamp=$(LC_TIME=it_IT.UTF-8 date +"%a %d %b %Y, %T, %Z")
    echo -e "\n${banner_line}\n=== SNAPSHOT: ${snapshot} END | ${timestamp} ===\n${banner_line}"
}

log_header() {
    echo -e "\n==> $1\n"
}

log_msg() {
    echo "  [*] $1"
}

log_success() {
    echo "      [✓] $1"
}

log_warning() {
    echo "      [!] $1"
}

log_error() {
    echo "      [✗] $1"
}

cleanup_old_logs() {
    local old_snapshots=("$@")
    for snap in "${old_snapshots[@]}"; do
        sed -i "/=== SNAPSHOT: ${snap} START/,/=== SNAPSHOT: ${snap} END/d" "$LOGFILE"
    done
}

# === START MAIN LOGGING ===
{
# Determine snapshot version
latest_snap=$(zfs list -H -t snapshot -o name | grep "^${POOL}@${SNAP_PREFIX}" | sort -V | tail -n 1)

if [[ "$latest_snap" =~ ${POOL}@${SNAP_PREFIX}([0-9]+)\.([0-9]+) ]]; then
    major="${BASH_REMATCH[1]}"
    minor="${BASH_REMATCH[2]}"
    new_minor=$((minor + 1))
    if (( new_minor >= 10 )); then
        new_minor=0
        major=$((major + 1))
    fi
else
    major=1
    minor=0
fi

new_snapshot="${SNAP_PREFIX}${major}.${minor}"

log_snapshot_start "$new_snapshot"

# === SYSTEM CLEANUP ===
log_header "SYSTEM CLEANUP"

log_msg "Cleaning pacman cache..."
if pacman -Scc --noconfirm > /dev/null 2>&1; then
    log_success "Pacman cache cleaned successfully"
else
    log_error "Pacman cache cleanup failed"
fi

log_msg "Removing orphaned packages..."
orphans=$(pacman -Qtdq 2>/dev/null)
if [ -z "$orphans" ]; then
    log_success "No orphaned packages found"
else
    if echo "$orphans" | xargs -r sudo pacman -Rns --noconfirm > /dev/null 2>&1; then
        log_success "Orphaned packages removed successfully"
    else
        log_error "Failed to remove orphaned packages"
    fi
fi

log_msg "Cleaning systemd journal logs (older than 7 days)..."
if journalctl --vacuum-time=7d > /dev/null 2>&1; then
    log_success "Journal logs cleaned successfully"
else
    log_error "Journal log cleanup failed"
fi

log_msg "Cleaning user cache (~/.cache)..."
if rm -rf ~/.cache/* > /dev/null 2>&1; then
    log_success "User cache cleaned successfully"
else
    log_error "User cache cleanup failed"
fi

# === SNAPSHOT CREATION ===
log_header "SNAPSHOT CREATION"

log_msg "Creating snapshot: ${POOL}@${new_snapshot}"
if zfs snapshot "${POOL}@${new_snapshot}" 2>/tmp/snapshot_error.log; then
    log_success "Snapshot created successfully"
    SNAP_CREATED=true
else
    SNAP_CREATED=false
    err_msg=$(< /tmp/snapshot_error.log)
    if [[ "$err_msg" == *"dataset already exists"* ]]; then
        log_error "Snapshot creation failed: dataset already exists"
    else
        log_error "Snapshot creation failed: ${err_msg}"
    fi
fi
rm -f /tmp/snapshot_error.log

# === SNAPSHOT CLEANUP ===
log_header "SNAPSHOT CLEANUP"

snapshots=($(zfs list -H -t snapshot -o name | grep "^${POOL}@weekly-" | sort -V))
num_snapshots=${#snapshots[@]}

if (( num_snapshots > MAX_SNAPSHOTS )); then
    num_to_delete=$((num_snapshots - MAX_SNAPSHOTS))
    log_msg "Deleting $num_to_delete old snapshot(s)..."
    old_snapshots=()
    for ((i = 0; i < num_to_delete; i++)); do
        log_msg "Deleting old snapshot: ${snapshots[i]}"
        if zfs destroy "${snapshots[i]}" 2>/dev/null; then
            old_snapshots+=("${snapshots[i]##*@}")
            log_success "Deleted snapshot: ${snapshots[i]}"
        else
            log_error "Failed to delete snapshot: ${snapshots[i]}"
        fi
    done
    cleanup_old_logs "${old_snapshots[@]}"
else
    log_msg "No old snapshots to delete"
fi

# === BACKUP TO REMOTE POOL ===
log_header "BACKUP TO REMOTE POOL"

BACKUP_DONE=false

log_msg "Checking remote pool '${BACKUP_POOL}'..."
if zfs list "${BACKUP_POOL}" >/dev/null 2>&1; then
    last_backup_snap=$(zfs list -H -t snapshot -o name | grep "^${BACKUP_POOL}@weekly-" | sort -V | tail -n 1)
    if [[ -n "$last_backup_snap" ]]; then
        base_last_backup_snap=${last_backup_snap##*@}
        log_msg "Performing incremental send from $base_last_backup_snap to $new_snapshot..."
        if zfs send -i "${POOL}@${base_last_backup_snap}" "${POOL}@${new_snapshot}" | zfs receive -F "${BACKUP_POOL}" 2>/dev/null; then
            log_success "Incremental backup completed successfully"
            BACKUP_DONE=true
        else
            log_error "Incremental backup failed"
        fi
    else
        log_msg "No backup snapshot found. Performing full send of $new_snapshot..."
        if zfs send "${POOL}@${new_snapshot}" | zfs receive -F "${BACKUP_POOL}" 2>/dev/null; then
            log_success "Full backup completed successfully"
            BACKUP_DONE=true
        else
            log_error "Full backup failed"
        fi
    fi
else
    log_warning "Backup skipped: pool not found"
fi

# === SYSTEM UPDATE ===
log_header "SYSTEM UPDATE"

log_msg "Running full system update..."
if pacman -Syu --noconfirm > /dev/null 2>&1 && flatpak update -y > /dev/null 2>&1; then
    log_success "System update completed successfully"
    UPDATE_DONE=true
else
    log_error "System update failed"
    UPDATE_DONE=false
fi

log_snapshot_end "$new_snapshot"
echo -e "\n\n"
} >> "$LOGFILE" 2>&1