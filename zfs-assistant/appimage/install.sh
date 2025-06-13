#!/bin/bash
# ZFS Assistant - Installation Script for AppImage
# Author: am2998

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ZFS-Assistant"
APP_VERSION="0.1.0"
ARCH="x86_64"
APPIMAGE_NAME="$APP_NAME-$APP_VERSION-$ARCH.AppImage"
INSTALL_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"

echo -e "${BLUE}ZFS Assistant AppImage Installer${NC}"
echo "=================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}Running as root - will install system-wide${NC}"
    SYSTEM_INSTALL=true
else
    echo -e "${YELLOW}Running as user - will install to user directory${NC}"
    SYSTEM_INSTALL=false
    INSTALL_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
fi

# Check if AppImage exists
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APPIMAGE_LOCATIONS=("$PROJECT_ROOT/release/$APPIMAGE_NAME" "$PROJECT_ROOT/build/$APPIMAGE_NAME")
APPIMAGE_PATH=""

for location in "${APPIMAGE_LOCATIONS[@]}"; do
    if [ -f "$location" ]; then
        APPIMAGE_PATH="$location"
        break
    fi
done

if [ -z "$APPIMAGE_PATH" ]; then
    echo -e "${RED}Error: AppImage not found at any of these locations:${NC}"
    for location in "${APPIMAGE_LOCATIONS[@]}"; do
        echo -e "${RED}  - $location${NC}"
    done
    echo "Please run 'make release' or './build-release.sh' first"
    exit 1
fi

echo -e "${BLUE}Found AppImage at: $APPIMAGE_PATH${NC}"

# Create directories if they don't exist
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$INSTALL_DIR" "$DESKTOP_DIR" "$ICON_DIR"

# Copy AppImage
echo -e "${YELLOW}Installing AppImage...${NC}"
cp "$APPIMAGE_PATH" "$INSTALL_DIR/zfs-assistant"
chmod +x "$INSTALL_DIR/zfs-assistant"

# Install polkit policy if running as root
if [ "$SYSTEM_INSTALL" = true ]; then
    echo -e "${YELLOW}Installing polkit policy...${NC}"
    POLICY_DIR="/usr/share/polkit-1/actions"
    mkdir -p "$POLICY_DIR"
    
    # Try to extract policy from AppImage or use project file
    POLICY_SOURCE=""
    if [ -f "$PROJECT_ROOT/src/org.zfs-assistant.policy" ]; then
        POLICY_SOURCE="$PROJECT_ROOT/src/org.zfs-assistant.policy"
    elif [ -f "$PROJECT_ROOT/build/ZFS-Assistant.AppDir/usr/share/polkit-1/actions/org.zfs-assistant.policy" ]; then
        POLICY_SOURCE="$PROJECT_ROOT/build/ZFS-Assistant.AppDir/usr/share/polkit-1/actions/org.zfs-assistant.policy"
    fi
    
    if [ -n "$POLICY_SOURCE" ]; then
        cp "$POLICY_SOURCE" "$POLICY_DIR/"
        echo -e "${GREEN}✅ Polkit policy installed${NC}"
        echo -e "${BLUE}Note: ZFS Assistant will now request authentication when needed${NC}"
    else
        echo -e "${YELLOW}⚠️ Polkit policy not found - you may need to run as root${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Running as user - polkit policy not installed${NC}"
    echo -e "${YELLOW}   For full functionality, run installer as root: sudo ./install.sh${NC}"
fi

# Copy desktop file
echo -e "${YELLOW}Installing desktop file...${NC}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/zfs-assistant.desktop" "$DESKTOP_DIR/"

# Extract and copy icon from AppImage (try both locations)
echo -e "${YELLOW}Installing icon...${NC}"
ICON_SOURCE=""
if [ -f "$PROJECT_ROOT/release/ZFS-Assistant.AppDir/zfs-assistant.svg" ]; then
    ICON_SOURCE="$PROJECT_ROOT/release/ZFS-Assistant.AppDir/zfs-assistant.svg"
elif [ -f "$PROJECT_ROOT/build/ZFS-Assistant.AppDir/zfs-assistant.svg" ]; then
    ICON_SOURCE="$PROJECT_ROOT/build/ZFS-Assistant.AppDir/zfs-assistant.svg"
fi

if [ -n "$ICON_SOURCE" ]; then
    if command -v convert &> /dev/null; then
        # Convert SVG to PNG if ImageMagick is available
        convert "$ICON_SOURCE" "$ICON_DIR/zfs-assistant.png"
    else
        # Just copy the SVG
        cp "$ICON_SOURCE" "$ICON_DIR/zfs-assistant.svg"
    fi
else
    echo -e "${YELLOW}⚠️ Icon not found, skipping icon installation${NC}"
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    echo -e "${YELLOW}Updating desktop database...${NC}"
    if [ "$SYSTEM_INSTALL" = true ]; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    else
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    fi
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    echo -e "${YELLOW}Updating icon cache...${NC}"
    if [ "$SYSTEM_INSTALL" = true ]; then
        gtk-update-icon-cache -t /usr/share/icons/hicolor 2>/dev/null || true
    else
        gtk-update-icon-cache -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    fi
fi

echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""
echo -e "${BLUE}ZFS Assistant is now installed and can be:${NC}"
echo "  • Run from terminal: zfs-assistant"
echo "  • Launched from application menu"
echo "  • Run directly: $INSTALL_DIR/zfs-assistant"
echo ""

if [ "$SYSTEM_INSTALL" = false ]; then
    echo -e "${YELLOW}Note: Make sure $INSTALL_DIR is in your PATH${NC}"
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo -e "${BLUE}To uninstall:${NC}"
echo "  rm -f $INSTALL_DIR/zfs-assistant"
echo "  rm -f $DESKTOP_DIR/zfs-assistant.desktop"
echo "  rm -f $ICON_DIR/zfs-assistant.*"
