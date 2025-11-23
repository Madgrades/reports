#!/bin/bash
set -e

# Install system dependencies
bash scripts/install-system-deps.sh

# Install Python dependencies
pip install --no-cache-dir -r requirements.txt

# Install the package in editable mode
pip install -e .

