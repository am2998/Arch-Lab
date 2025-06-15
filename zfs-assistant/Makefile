# ZFS Assistant - Makefile for AppImage building
# Author: am2998

.PHONY: all build release install clean help test lint format

# Default target
all: release

# Build release AppImage (comprehensive single script)
release:
	@echo "Building ZFS Assistant Release AppImage..."
	@chmod +x appimage/build-release.sh
	@./appimage/build-release.sh

# Legacy build target (for compatibility)
build: release

# Install the AppImage (requires release first)
install: release
	@echo "Installing ZFS Assistant..."
	@chmod +x appimage/install.sh
	@./appimage/install.sh

# Install as root (system-wide)
install-system: release
	@echo "Installing ZFS Assistant system-wide..."
	@chmod +x appimage/install.sh
	@sudo ./appimage/install.sh

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ release/
	@rm -f appimagetool-x86_64.AppImage

# Test the application (requires Python environment)
test:
	@echo "Testing ZFS Assistant..."
	@cd src && python3 -m pytest tests/ || echo "No tests found"

# Lint the code
lint:
	@echo "Linting code..."
	@cd src && python3 -m flake8 . || echo "flake8 not installed"
	@cd src && python3 -m pylint *.py || echo "pylint not installed"

# Format the code
format:
	@echo "Formatting code..."
	@cd src && python3 -m black . || echo "black not installed"
	@cd src && python3 -m isort . || echo "isort not installed"

# Show help
help:
	@echo "ZFS Assistant AppImage Build System"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@echo "  release         Build release-ready AppImage (recommended)"
	@echo "  build           Alias for release (for compatibility)"
	@echo "  install         Build and install AppImage to user directory"
	@echo "  install-system  Build and install AppImage system-wide (requires sudo)"
	@echo "  clean           Remove build artifacts"
	@echo "  test            Run tests"
	@echo "  lint            Lint the code"
	@echo "  format          Format the code"
	@echo "  help            Show this help message"
	@echo ""
	@echo "Release process:"
	@echo "  make release    # Creates release/ directory with AppImage and checksums"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Linux system (for AppImage building)"
	@echo "  - Python 3.8+"
	@echo "  - GTK4 and libadwaita development packages"
	@echo "  - PyGObject and pycairo"
	@echo ""
	@echo "Usage:"
	@echo "  make release    # Build release AppImage"
	@echo "  make install    # Build and install to ~/.local/bin"
	@echo "  sudo make install-system  # Build and install system-wide"
