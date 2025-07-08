#!/bin/bash

echo "Meeting Secretary AI - Enhanced Setup"
echo "====================================="

# Check if we're in the right directory
if [ ! -f "meeting_secretary_gui.py" ]; then
    echo "Error: Please run this script from the MeetingSecretaryAI_1.0 directory"
    exit 1
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p "../MeetingSecretaryAI_Data/context"
mkdir -p "../MeetingSecretaryAI_Data/data"
mkdir -p "../MeetingSecretaryAI_Data/output"
mkdir -p "./output"

# Check for conda/mamba
if command -v mamba &> /dev/null; then
    echo "Using mamba for environment management..."
    CONDA_CMD="mamba"
else
    echo "Using conda for environment management..."
    CONDA_CMD="conda"
fi

# Create conda environment
echo "Creating conda environment 'meetingsecretaryai_env'..."
$CONDA_CMD create -n meetingsecretaryai_env python=3.9 -y

# Activate environment
echo "Activating environment..."
eval "$($CONDA_CMD shell.bash hook)"
$CONDA_CMD activate meetingsecretaryai_env

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

# Install WhisperX (if not already installed)
echo "Installing WhisperX..."
pip install whisperx

# Check for HuggingFace token
if [ ! -f "../MeetingSecretaryAI_Data/.hf_token.txt" ]; then
    echo ""
    echo "HuggingFace Token Setup"
    echo "======================"
    echo "For audio processing with WhisperX, you need a HuggingFace token."
    echo "You can get one from: https://huggingface.co/settings/tokens"
    echo ""
    read -p "Do you have a HuggingFace token? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your HuggingFace token: " -s hf_token
        echo ""
        echo "$hf_token" > "../MeetingSecretaryAI_Data/.hf_token.txt"
        echo "Token saved successfully!"
    else
        echo "You can set the token later through the GUI Settings tab."
    fi
fi

# Check for config.ini
if [ ! -f "config.ini" ]; then
    echo ""
    echo "Creating basic config.ini..."
    cat > config.ini << EOF
[DEFAULT]
# OpenAI API Configuration
api_key = your_api_key_here
api_base = https://your-azure-openai-resource.openai.azure.com/
api_version = 2024-02-01
model = gpt-4

# Processing settings
max_tokens = 4000
temperature = 0.3
EOF
    echo "Basic config.ini created. Please edit it with your OpenAI/Azure settings."
fi

echo ""
echo "Setup Complete!"
echo "==============="
echo ""
echo "To run the enhanced GUI:"
echo "  conda activate meetingsecretaryai_env"
echo "  python meeting_secretary_gui.py"
echo ""
echo "To test the enhanced features:"
echo "  python test_enhanced_features.py"
echo ""
echo "Documentation: ENHANCED_FEATURES.md"
echo ""
echo "Don't forget to:"
echo "1. Configure your OpenAI/Azure API settings in config.ini"
echo "2. Set your HuggingFace token in the GUI Settings tab (if not done already)"
echo "3. Add context files to ../MeetingSecretaryAI_Data/context/ directory"
