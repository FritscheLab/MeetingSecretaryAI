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
if [ "$CONDA_CMD" = "mamba" ]; then
    eval "$($CONDA_CMD shell hook --shell bash)"
else
    eval "$($CONDA_CMD shell.bash hook)"
fi
$CONDA_CMD activate meetingsecretaryai_env

# Ensure Tkinter support (required for the GUI)
echo "Ensuring Tkinter libraries are available..."
$CONDA_CMD install -n meetingsecretaryai_env tk -y

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

# Install WhisperX (if not already installed)
echo "Installing WhisperX..."
pip install whisperx

# Check for ffmpeg
echo "Checking for ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✓ ffmpeg is installed"
else
    echo "⚠ ffmpeg is not installed"
    echo "Installing ffmpeg with Homebrew..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
        echo "✓ ffmpeg installed successfully"
    else
        echo "❌ Homebrew not found. Please install ffmpeg manually:"
        echo "   1. Install Homebrew from https://brew.sh/"
        echo "   2. Run: brew install ffmpeg"
        echo "   3. Or install ffmpeg from https://ffmpeg.org/download.html"
        echo ""
        echo "ffmpeg is required for audio processing with WhisperX."
    fi
fi

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
    echo "Creating response_settings config.ini..."
    cat > config.ini << 'EOF'
[response_settings]
temperature = 0
max_tokens = 30384
max_completion_tokens = 80000
top_p = 1.0
frequency_penalty = 0.0
presence_penalty = 0.0
EOF
    echo "Config with response_settings created. Update values if your deployment needs different defaults."
fi

# Provide an .env template when missing so downstream scripts have the required vars
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env template..."
    cat > .env << 'EOF'
# Azure OpenAI deployment settings
MODEL=gpt-5.1
OPENAI_API_BASE=https://your-azure-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=replace-with-your-key
OPENAI_ORGANIZATION=replace-with-your-org
API_VERSION=2025-04-01-preview
EOF
    echo ".env template created. Replace placeholder values with your deployment details."
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
