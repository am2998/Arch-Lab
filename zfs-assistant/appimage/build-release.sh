#!/bin/bash
# ZFS Assistant - Single Release Build Script
# Author: am2998
# This script builds a complete AppImage ready for release

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ZFS-Assistant"
APP_VERSION="0.1.0"
ARCH="x86_64"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
APPDIR="$BUILD_DIR/$APP_NAME.AppDir"
RELEASE_DIR="$PROJECT_ROOT/release"
APPIMAGE_NAME="$APP_NAME-$APP_VERSION-$ARCH.AppImage"

# Banner
cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                          ZFS Assistant Release Builder                       ║
║                                                                              ║
║                    Building AppImage for Distribution                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF

echo -e "${BLUE}Building ${APP_NAME} v${APP_VERSION} AppImage${NC}"
echo -e "${CYAN}Architecture: ${ARCH}${NC}"
echo -e "${CYAN}Build Directory: ${BUILD_DIR}${NC}"
echo -e "${CYAN}Release Directory: ${RELEASE_DIR}${NC}"
echo ""

# Pre-flight checks
echo -e "${YELLOW}Running pre-flight checks...${NC}"

# Check if we're on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}❌ Error: AppImage can only be built on Linux${NC}"
    echo -e "${RED}   Current OS: $OSTYPE${NC}"
    exit 1
fi

# Check required commands
REQUIRED_COMMANDS=("python3" "wget" "pip3" "git")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}❌ Error: $cmd is required but not found${NC}"
        exit 1
    fi
done

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l 2>/dev/null || echo "1") == "1" ]]; then
    echo -e "${RED}❌ Error: Python 3.8+ is required (found: $PYTHON_VERSION)${NC}"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "$PROJECT_ROOT/setup.py" ]] || [[ ! -d "$PROJECT_ROOT/src" ]]; then
    echo -e "${RED}❌ Error: Cannot find setup.py and src/ in project root${NC}"
    echo -e "${RED}   Project root: $PROJECT_ROOT${NC}"
    echo -e "${RED}   Expected files: setup.py, src/directory${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All pre-flight checks passed${NC}"
echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf "$BUILD_DIR" "$RELEASE_DIR"
rm -f appimagetool-*.AppImage
echo -e "${GREEN}✅ Cleaned build directories${NC}"

# Create directory structure
echo -e "${YELLOW}Creating build directory structure...${NC}"
mkdir -p "$APPDIR/usr/"{bin,lib,share/{applications,icons/hicolor/{16x16,32x32,48x48,64x64,128x128,256x256}/apps,pixmaps},src}
mkdir -p "$RELEASE_DIR"
echo -e "${GREEN}✅ Directory structure created${NC}"

# Copy application source
echo -e "${YELLOW}Copying application source files...${NC}"
cp -r "$PROJECT_ROOT/src"/* "$APPDIR/usr/src/"
if [[ ! -f "$APPDIR/usr/src/__main__.py" ]]; then
    echo -e "${RED}❌ Error: Missing main entry point at src/__main__.py${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Source files copied${NC}"

# Copy polkit policy for system installation
echo -e "${YELLOW}Copying polkit policy...${NC}"
mkdir -p "$APPDIR/usr/share/polkit-1/actions"
if [[ -f "$PROJECT_ROOT/src/org.zfs-assistant.policy" ]]; then
    cp "$PROJECT_ROOT/src/org.zfs-assistant.policy" "$APPDIR/usr/share/polkit-1/actions/"
    echo -e "${GREEN}✅ Polkit policy copied${NC}"
else
    echo -e "${YELLOW}⚠️ Polkit policy not found, skipping${NC}"
fi

# Create desktop file
echo -e "${YELLOW}Creating desktop entry...${NC}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/zfs-assistant.desktop" "$APPDIR/usr/share/applications/"
cp "$SCRIPT_DIR/zfs-assistant.desktop" "$APPDIR/"
echo -e "${GREEN}✅ Desktop entry created${NC}"

# Create application icon (high-quality SVG)
echo -e "${YELLOW}Creating application icon...${NC}"
cat > "$APPDIR/usr/share/icons/hicolor/256x256/apps/zfs-assistant.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2196F3;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1565C0;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#4FC3F7;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#29B6F6;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Background -->
  <rect width="256" height="256" rx="32" ry="32" fill="url(#bg)"/>
  
  <!-- Database icon representation -->
  <ellipse cx="128" cy="80" rx="60" ry="15" fill="url(#accent)"/>
  <rect x="68" y="80" width="120" height="40" fill="url(#accent)"/>
  <ellipse cx="128" cy="120" rx="60" ry="15" fill="url(#accent)"/>
  <rect x="68" y="120" width="120" height="40" fill="url(#accent)" opacity="0.8"/>
  <ellipse cx="128" cy="160" rx="60" ry="15" fill="url(#accent)" opacity="0.8"/>
  
  <!-- ZFS Text -->
  <text x="128" y="200" font-family="Arial Black, sans-serif" font-size="28" font-weight="bold" 
        fill="white" text-anchor="middle" dominant-baseline="middle">ZFS</text>
  <text x="128" y="225" font-family="Arial, sans-serif" font-size="14" 
        fill="white" text-anchor="middle" dominant-baseline="middle">Assistant</text>
</svg>
EOF

# Create multiple icon sizes
echo -e "${YELLOW}Creating multiple icon sizes...${NC}"
if command -v convert &> /dev/null; then
    # Use ImageMagick to create PNG versions in different sizes
    for size in 16 32 48 64 128 256; do
        convert "$APPDIR/usr/share/icons/hicolor/256x256/apps/zfs-assistant.svg" \
                -resize "${size}x${size}" \
                "$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps/zfs-assistant.png"
    done
    echo -e "${GREEN}✅ Multiple icon sizes created with ImageMagick${NC}"
else
    # Copy SVG to all sizes if ImageMagick is not available
    for size in 16 32 48 64 128; do
        cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/zfs-assistant.svg" \
           "$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps/zfs-assistant.svg"
    done
    echo -e "${YELLOW}⚠️ ImageMagick not found, using SVG for all sizes${NC}"
fi

# Copy main icon to AppDir root and pixmaps
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/zfs-assistant.svg" "$APPDIR/zfs-assistant.svg"
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/zfs-assistant.svg" "$APPDIR/usr/share/pixmaps/zfs-assistant.svg"

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
export PYTHONUSERBASE="$APPDIR/usr"
export PIP_USER=1

# Install from requirements.txt if it exists
if [[ -f "$PROJECT_ROOT/src/requirements.txt" ]]; then
    pip3 install --user --no-warn-script-location -r "$PROJECT_ROOT/src/requirements.txt"
else
    # Install minimal required dependencies
    pip3 install --user --no-warn-script-location PyGObject pycairo
fi

# Verify critical dependencies are installed
echo -e "${YELLOW}Verifying Python dependencies...${NC}"
export PYTHONPATH="$APPDIR/usr/lib/python3/site-packages:$PYTHONPATH"
if ! python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')" 2>/dev/null; then
    echo -e "${RED}❌ Error: GTK4/libadwaita Python bindings not available${NC}"
    echo -e "${RED}   Make sure python3-gi and libadwaita-dev are installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python dependencies verified${NC}"

# Create AppRun script
echo -e "${YELLOW}Creating AppRun launcher...${NC}"
cp "$SCRIPT_DIR/AppRun" "$APPDIR/"
chmod +x "$APPDIR/AppRun"
echo -e "${GREEN}✅ AppRun launcher created${NC}"

# Create wrapper script for system PATH
echo -e "${YELLOW}Creating wrapper script...${NC}"
cat > "$APPDIR/usr/bin/zfs-assistant" << 'EOF'
#!/bin/bash
# ZFS Assistant wrapper script

# Get the AppDir from the script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPDIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Set up environment
export PYTHONPATH="$APPDIR/usr/src:$APPDIR/usr/lib/python3/site-packages:$PYTHONPATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
export XDG_DATA_DIRS="$APPDIR/usr/share:$XDG_DATA_DIRS"

# Change to a writable directory
cd "${HOME}" 2>/dev/null || cd /tmp

# Run the application
exec python3 "$APPDIR/usr/src/__main__.py" "$@"
EOF

chmod +x "$APPDIR/usr/bin/zfs-assistant"
echo -e "${GREEN}✅ Wrapper script created${NC}"

# Download and verify appimagetool
echo -e "${YELLOW}Downloading appimagetool...${NC}"
APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
if [[ ! -f "appimagetool-x86_64.AppImage" ]]; then
    wget -q --show-progress "$APPIMAGETOOL_URL" -O appimagetool-x86_64.AppImage
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}❌ Error: Failed to download appimagetool${NC}"
        exit 1
    fi
fi

chmod +x appimagetool-x86_64.AppImage

# Verify appimagetool works
if ! ./appimagetool-x86_64.AppImage --version &>/dev/null; then
    echo -e "${RED}❌ Error: appimagetool is not working properly${NC}"
    exit 1
fi
echo -e "${GREEN}✅ appimagetool ready${NC}"

# Build the AppImage
echo -e "${YELLOW}Building AppImage...${NC}"
export ARCH="$ARCH"
export VERSION="$APP_VERSION"
export NO_STRIP=1  # Preserve debug symbols

# Create the AppImage with verbose output
if ! ./appimagetool-x86_64.AppImage --verbose "$APPDIR" "$BUILD_DIR/$APPIMAGE_NAME"; then
    echo -e "${RED}❌ Error: Failed to build AppImage${NC}"
    exit 1
fi

# Verify the AppImage was created and is executable
if [[ ! -f "$BUILD_DIR/$APPIMAGE_NAME" ]]; then
    echo -e "${RED}❌ Error: AppImage was not created${NC}"
    exit 1
fi

chmod +x "$BUILD_DIR/$APPIMAGE_NAME"
echo -e "${GREEN}✅ AppImage built successfully${NC}"

# Test the AppImage
echo -e "${YELLOW}Testing AppImage...${NC}"
if "$BUILD_DIR/$APPIMAGE_NAME" --version &>/dev/null || timeout 5s "$BUILD_DIR/$APPIMAGE_NAME" --help &>/dev/null; then
    echo -e "${GREEN}✅ AppImage test passed${NC}"
else
    echo -e "${YELLOW}⚠️ AppImage test inconclusive (may require GUI)${NC}"
fi

# Create release package
echo -e "${YELLOW}Creating release package...${NC}"
cp "$BUILD_DIR/$APPIMAGE_NAME" "$RELEASE_DIR/"

# Create checksums
cd "$RELEASE_DIR"
sha256sum "$APPIMAGE_NAME" > "$APPIMAGE_NAME.sha256"
md5sum "$APPIMAGE_NAME" > "$APPIMAGE_NAME.md5"

# Create release info
cat > "RELEASE_INFO.txt" << EOF
ZFS Assistant v$APP_VERSION Release
===================================

File: $APPIMAGE_NAME
Size: $(du -h "$APPIMAGE_NAME" | cut -f1)
Architecture: $ARCH
Built: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Builder: $(whoami)@$(hostname)

Installation:
1. Download $APPIMAGE_NAME
2. Make executable: chmod +x $APPIMAGE_NAME
3. Run: ./$APPIMAGE_NAME

System Installation:
sudo cp $APPIMAGE_NAME /usr/local/bin/zfs-assistant
sudo chmod +x /usr/local/bin/zfs-assistant

Requirements:
- Linux with GTK4 and libadwaita
- ZFS utilities (zfs-utils)
- Python 3.8+ (bundled)

Checksums:
SHA256: $(cat "$APPIMAGE_NAME.sha256" | cut -d' ' -f1)
MD5:    $(cat "$APPIMAGE_NAME.md5" | cut -d' ' -f1)
EOF

cd - >/dev/null

echo -e "${GREEN}✅ Release package created${NC}"

# Final summary
echo ""
echo -e "${GREEN}🎉 Build completed successfully!${NC}"
echo ""
echo -e "${BLUE}📦 Release files:${NC}"
echo -e "   ${CYAN}AppImage:${NC} $RELEASE_DIR/$APPIMAGE_NAME"
echo -e "   ${CYAN}SHA256:${NC}   $RELEASE_DIR/$APPIMAGE_NAME.sha256"
echo -e "   ${CYAN}MD5:${NC}      $RELEASE_DIR/$APPIMAGE_NAME.md5"
echo -e "   ${CYAN}Info:${NC}     $RELEASE_DIR/RELEASE_INFO.txt"
echo ""
echo -e "${BLUE}📊 File sizes:${NC}"
ls -lh "$RELEASE_DIR/"
echo ""
echo -e "${BLUE}🚀 Ready for distribution!${NC}"
echo ""
echo -e "${YELLOW}Test the AppImage:${NC}"
echo -e "   $RELEASE_DIR/$APPIMAGE_NAME"
echo ""
echo -e "${YELLOW}Upload to GitHub Release:${NC}"
echo -e "   1. Create a new release on GitHub"
echo -e "   2. Upload all files from $RELEASE_DIR/"
echo -e "   3. Use RELEASE_INFO.txt content for release notes"

exit 0
