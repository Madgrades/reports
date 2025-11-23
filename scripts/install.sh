#!/bin/bash
# Install script for pdf-table-extractor
# Used by: devcontainer, CI, and manual setup

set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "Installing package in editable mode..."
pip install -e .

echo "✓ Installation complete!"
