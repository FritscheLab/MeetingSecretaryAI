# Installation Guide (macOS)

This guide walks you through a clean setup of MeetingSecretaryAI on macOS, including Homebrew, Conda/Mamba, Python dependencies, and system tools required for audio processing and document generation.

If you get stuck, see Troubleshooting at the end.

---

## What you’ll install

- Homebrew (package manager for macOS)
- Miniforge (Conda) or Mambaforge (Conda + Mamba) for Python envs
- A project-specific Conda environment with Python 3.9
- Python packages from `requirements.txt` (includes WhisperX)
- System tools: ffmpeg (required), LibreOffice (optional but recommended for DOCX viewing)

---

## 0) Prerequisites

- macOS 12+ (Apple Silicon supported)
- Internet access
- Terminal app (zsh is the default shell on macOS)

Optional (recommended): install Apple Command Line Tools once

```zsh
xcode-select --install
```

---

## 1) Install Homebrew

Homebrew is used to install system tools like ffmpeg and LibreOffice.

```zsh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to your shell (Apple Silicon)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Verify
brew --version
```

If you’re on an Intel Mac, Homebrew lives in `/usr/local` instead of `/opt/homebrew`.

---

## 2) Install Conda (Miniforge or Mambaforge)

Miniforge is a lightweight Conda distribution from conda-forge (best for Apple Silicon). Mambaforge includes mamba, a faster drop-in replacement for conda.

Option A: Install via Homebrew (easy)

```zsh
# Choose one (Miniforge or Mambaforge)
brew install miniforge   # conda
# or
brew install mambaforge  # conda + mamba
```

Option B: Install via official installers

- Miniforge: https://github.com/conda-forge/miniforge
- Mambaforge: https://github.com/conda-forge/miniforge#mambaforge

Initialize Conda for zsh and restart the shell:

```zsh
conda init zsh
exec $SHELL
```

Verify:

```zsh
conda --version
```

---

## 3) Clone the repository

```zsh
git clone https://github.com/FritscheLab/MeetingSecretaryAI.git
cd MeetingSecretaryAI
```

---

## 4) Create the Conda environment

We use Python 3.9 to match the project’s tested dependencies.

With conda:

```zsh
conda create -n meetingsecretaryai_env python=3.9 -y
conda activate meetingsecretaryai_env
```

With mamba (if you installed Mambaforge):

```zsh
mamba create -n meetingsecretaryai_env python=3.9 -y
conda activate meetingsecretaryai_env
```

Verify Python and tkinter (for the GUI):

```zsh
python --version
python - <<'PY'
import tkinter
print('✓ tkinter available')
PY
```

---

## 5) Install Python dependencies

```zsh
# From the repo root
pip install --upgrade pip
pip install -r requirements.txt
```

Notes:
- `requirements.txt` includes WhisperX and all needed libraries.
- On first install this may download large packages (PyTorch, ONNXRuntime, etc.).

Optional developer tools:

```zsh
pip install pytest black flake8
```

---

## 6) Install system dependencies

ffmpeg is required for audio processing with WhisperX. LibreOffice is useful for viewing DOCX outputs.

```zsh
brew install ffmpeg
brew install --cask libreoffice   # optional (or use Microsoft Word)
```

---

## 7) Create data folders and set permissions

The GUI expects a sibling data directory and local output folder. Also ensure launcher scripts are executable.

```zsh
# From repo root
mkdir -p ../MeetingSecretaryAI_Data/context
mkdir -p ../MeetingSecretaryAI_Data/data
mkdir -p ../MeetingSecretaryAI_Data/output
mkdir -p ./output

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x launch_with_diagnostics.command 2>/dev/null || true
```

---

## 8) Configure API settings and tokens

### Azure OpenAI / OpenAI

You can configure via `.env` or `config.ini` (both supported). Examples:

`.env` (recommended for secrets):

```ini
MODEL=gpt-5
OPENAI_API_BASE=https://api.umgpt.umich.edu/azure-openai-api
AZURE_OPENAI_API_KEY=your_api_key
OPENAI_ORGANIZATION=your_org_id
API_VERSION=2025-04-01-preview
```

`config.ini` (used by some scripts):

```ini
[DEFAULT]
api_key = your_api_key_here
api_base = https://your-azure-openai-resource.openai.azure.com/
api_version = 2024-02-01
model = gpt-4
```

### HuggingFace token (for WhisperX diarization)

- Create a token at https://huggingface.co/settings/tokens
- Store it so the GUI can find it later:

```zsh
echo "hf_xxx_your_token_here" > ../MeetingSecretaryAI_Data/.hf_token.txt
```

You can also set the token in the GUI Settings tab.

---

## 9) Verify the installation

Quick checks:

```zsh
# GUI dependency
python - <<'PY'
import tkinter
print('tkinter OK')
PY

# WhisperX import (ffmpeg must be installed on PATH)
python - <<'PY'
import whisperx
print('whisperx OK')
PY

# Optional: run tests
pytest -q
```

If `pytest` isn’t installed, run:

```zsh
pip install pytest
pytest -q
```

---

## 10) Launch the app

Option A: Double-click launcher (handles permissions and env checks)

- In Finder, double-click: `launch_with_diagnostics.command`

Option B: Launch from Terminal

```zsh
conda activate meetingsecretaryai_env
python meeting_secretary_gui.py
```

---

## 11) CLI usage (without GUI)

Convert a transcript to structured JSON and then to DOCX/Markdown:

```zsh
# Transcript → JSON
python scripts/transcript2json.py sample.vtt > meeting.json

# JSON → DOCX
python scripts/json2word.py meeting.json

# Or run the convenience script
bash scripts/generate_minutes.sh
```

---

## Troubleshooting

- Homebrew not found
  - Re-run shell env step: `eval "$(/opt/homebrew/bin/brew shellenv)"`
  - Intel Macs use `/usr/local` instead of `/opt/homebrew`

- Conda not found after install
  - Run `conda init zsh` then `exec $SHELL`

- ffmpeg not found
  - `brew install ffmpeg`
  - Verify with `ffmpeg -version`

- tkinter missing
  - Ensure you’re in the conda env created above
  - Install tk if needed: `conda install -n meetingsecretaryai_env tk -y`

- Permission errors accessing `~/Documents/Zoom`
  - macOS Privacy: System Settings → Privacy & Security → Files and Folders
  - Grant “Terminal” access to “Documents Folder”
  - You can still use the app by selecting files manually

- WhisperX model errors
  - Ensure HuggingFace token is set
  - ffmpeg must be present

- On Apple Silicon performance
  - The installed PyTorch wheel targets Metal/CPU. For GPU acceleration, see PyTorch’s Apple Silicon docs. WhisperX will still work on CPU.

---

## Uninstall / Clean up

```zsh
conda deactivate || true
conda env remove -n meetingsecretaryai_env -y
# Optional: remove Homebrew installs
# brew uninstall ffmpeg
# brew uninstall --cask libreoffice
```

---

## Appendix: Alternative using Python venv (no Conda)

This project is tested with Conda. If you prefer `venv`, you can try:

```zsh
# Use Python 3.9 installed on your system
python3.9 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Note: Some packages (e.g., onnxruntime, torch) may be more tedious on Apple Silicon without conda-forge wheels. Prefer Conda/Mamba on macOS.
