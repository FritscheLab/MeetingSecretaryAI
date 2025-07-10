#!/bin/bash

# Alternative launcher that may help with permission issues
# This runs the app in a way that may inherit better permissions

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

echo "=== Meeting Secretary AI Launcher ==="
echo "Working directory: $SCRIPT_DIR"

# Check for required files
if [ ! -f "meeting_secretary_gui.py" ]; then
    echo "ERROR: meeting_secretary_gui.py not found"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check conda installation
if ! command -v conda &> /dev/null; then
    echo "ERROR: conda not found in PATH"
    echo "Please install conda/miniconda first"
    read -p "Press Enter to exit..."
    exit 1
fi

# Initialize conda
echo "Initializing conda environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"

# Check if environment exists
if ! conda env list | grep -q "meetingsecretaryai_env"; then
    echo "ERROR: Environment 'meetingsecretaryai_env' not found"
    echo "Please create it with: conda create -n meetingsecretaryai_env python=3.9"
    read -p "Press Enter to exit..."
    exit 1
fi

# Activate environment
echo "Activating environment: meetingsecretaryai_env"
conda activate meetingsecretaryai_env

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate environment"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Python and required modules
echo "Checking Python environment..."
python -c "import tkinter; print('✓ tkinter available')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: tkinter not available"
    read -p "Press Enter to exit..."
    exit 1
fi

# Test Documents folder access
echo "Testing Documents folder access..."
if [ -d "$HOME/Documents/Zoom" ]; then
    if ls "$HOME/Documents/Zoom" > /dev/null 2>&1; then
        echo "✓ Documents folder access: OK"
    else
        echo "⚠ Documents folder access: Limited (app will still work)"
        echo "  To fix: System Preferences > Security & Privacy > Files and Folders"
        echo "  Grant Terminal access to Documents folder"
    fi
else
    echo "⚠ Zoom folder not found (app will still work)"
fi

echo ""
echo "Starting Meeting Secretary AI..."
echo "================================"

# Launch the application
python meeting_secretary_gui.py
exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "Meeting Secretary AI closed normally."
else
    echo "Meeting Secretary AI closed with error code: $exit_code"
    read -p "Press Enter to exit..."
fi
