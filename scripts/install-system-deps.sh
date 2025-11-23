#!/bin/bash
# Install system dependencies for pdf-table-extractor
# Required by Camelot for PDF processing

set -e

echo "Installing system dependencies..."

# Detect package manager
if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    sudo apt-get update
    sudo apt-get install -y \
        ghostscript \
        python3-tk \
        libgomp1 \
        libglib2.0-0 \
        libgl1
elif command -v yum &> /dev/null; then
    # RHEL/CentOS
    sudo yum install -y \
        ghostscript \
        python3-tkinter \
        libgomp \
        glib2 \
        mesa-libGL
elif command -v brew &> /dev/null; then
    # macOS
    brew install ghostscript
else
    echo "Warning: Unknown package manager. Please install manually:"
    echo "  - ghostscript"
    echo "  - python3-tk (or tkinter)"
    echo "  - OpenGL libraries"
fi

echo "✓ System dependencies installed!"
