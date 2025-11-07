# MeetingSecretaryAI

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

## Overview

**MeetingSecretaryAI** is a comprehensive automated pipeline designed to generate structured meeting minutes from raw transcripts using Azure OpenAI models. It transforms unstructured meeting transcripts into well-organized outputs, including JSON, DOCX, and Markdown formats, following a standardized schema.

This tool is especially tailored for academic and scientific meetings, such as NIH-style study sections, providing high-quality, reproducible documentation of discussions, decisions, and actions.

### 🚀 **NEW: Enhanced GUI with Smart Features**

The latest version includes a powerful GUI with automatic meeting detection, audio processing, and intelligent workflow management.

---

## ✨ Key Features

### Core Functionality
- 🤖 **AI-powered transcript summarization** using Azure OpenAI
- 📜 **JSON output** conforming to a strict meeting minutes schema
- 📝 **DOCX and Markdown** minutes generation with professional formatting
- 🛠️ **Configurable** via `.env` and `config.ini`
- 🔄 **Cross-platform** (Linux, MacOS) compatible via `conda`/`mamba`

### 🆕 Enhanced GUI Features
- � **Automatic Zoom Meeting Detection** - Scans and lists recent meetings
- 🎵 **Audio Processing** - Direct WhisperX integration for transcription
- 👥 **Participant Extraction** - Automatically identifies speakers
- 📅 **Smart Time Rounding** - Rounds meeting times to 15-minute intervals
- 🎯 **Context Management** - Easy selection from preset context files
- 📋 **Auto-Agenda Generation** - Creates formatted agendas automatically

### Multiple Input Methods
- **Zoom Meetings**: Browse and select from recent meetings
- **Audio Files**: Process with WhisperX for transcription
- **Transcript Files**: Upload existing transcripts
- **Folder Input**: Process entire folders containing transcripts

---

## 🎯 Quick Start

**Need a guided, beginner-friendly install (Windows/macOS/Linux)? Follow the full tutorial in [`doc/INSTALLATION.md`](doc/INSTALLATION.md).** It covers prerequisites, Conda/Mamba setup, ffmpeg installation, Hugging Face tokens, and the first GUI launch with checkpoints after each step.

### Snapshot of the install steps
1. Install Git, Miniforge/Mambaforge, and ffmpeg using the commands for your OS (PowerShell, zsh, or bash) in the tutorial.
2. Clone this repository and create the `meetingsecretaryai_env` Conda environment with Python 3.9.
3. Run `pip install -r requirements.txt`, add your Hugging Face and Azure credentials, and verify with the provided smoke tests.
4. Launch the GUI with `python meeting_secretary_gui.py` (or double-click `launch_with_diagnostics.command` on macOS).

### Fast commands (once prerequisites are in place)
```bash
git clone https://github.com/FritscheLab/MeetingSecretaryAI.git
cd MeetingSecretaryAI
conda create -n meetingsecretaryai_env python=3.9 -y
conda activate meetingsecretaryai_env
pip install --upgrade pip
pip install -r requirements.txt
python meeting_secretary_gui.py
```

### Automated helper (macOS/Linux/WSL)
```bash
chmod +x setup_enhanced.sh
./setup_enhanced.sh
```
The script installs ffmpeg, creates the Conda env, and runs dependency checks. Windows users can follow the PowerShell instructions in `doc/INSTALLATION.md` to achieve the same result manually.

## 🔧 Main Scripts

| Script | Description |
|--------|-------------|
| `meeting_secretary_gui.py` | Graphical interface for processing transcripts and generating minutes. |
| `meeting_utils.py` | Helper library for tasks such as Zoom meeting detection and token management. |
| `scripts/transcript2json.py` | Converts raw transcripts into structured JSON minutes. |
| `scripts/json2word.py` | Creates DOCX or Markdown minutes from JSON. |
| `scripts/generate_minutes.sh` | Convenience shell script that chains the two conversion steps. |

The typical workflow is to run `scripts/transcript2json.py` on a transcript file and then
`scripts/json2word.py` to produce documents. For a graphical experience, launch
`meeting_secretary_gui.py`, which orchestrates the full process. The shell
script `scripts/generate_minutes.sh` demonstrates how these pieces fit together.

---

## 📁 Repository Structure

```
MeetingSecretaryAI_1.0/
├── meeting_secretary_gui.py          # Main GUI application
├── meeting_utils.py                   # Utility classes
├── setup_enhanced.sh                  # Automated setup script
├── requirements.txt                   # Python dependencies
├── config.ini                         # Configuration file
├── CONTRIBUTING.md                    # How to contribute
├── CHANGELOG.md                       # Release history
├── .env                              # Environment variables
├── scripts/                          # Core processing scripts
│   ├── transcript2json.py            # Transcript to JSON conversion
│   ├── json2word.py                  # JSON to document conversion
│   ├── generate_minutes.sh           # Shell script pipeline
│   ├── prompt_*.md                   # Various detail level prompts
│   └── minutes_schema.JSON           # Output schema definition
├── doc/                              # Documentation
│   ├── templates/                    # Template files
│   ├── transcript2json.md            # Script documentation
│   ├── json2word.md                  # Script documentation
│   ├── FAQ.md                        # Frequently asked questions
│   └── architecture.md              # Workflow diagram
├── tests/                            # Test scripts
│   ├── test_enhanced_features.py     # Feature testing
│   └── test_time_rounding.py         # Time rounding tests
└── archive/                          # Archived files
    ├── old_gui/                      # Previous GUI versions
    └── development_docs/             # Development documentation

External Data Structure:
../MeetingSecretaryAI_Data/
├── .hf_token.txt                     # HuggingFace token (for WhisperX)
├── context/                          # Context files for different meeting types
│   ├── COMPASS_PRS.md
│   ├── COMPASS_Genetics.md
│   └── ...
├── data/                             # Meeting data
└── output/                           # Generated minutes (default)
```

---

## 🖥️ Using the GUI

### 1. Input Methods Tab
Choose your input method:
- **Latest Zoom Meetings**: Automatically detects recent meetings
- **Audio Files**: Select .m4a, .mp3, .wav files for processing
- **Transcript Files**: Upload existing transcript files
- **Input Folders**: Process folders containing transcripts

### 2. Meeting Details Tab
- Edit meeting information (auto-populated from Zoom)
- Auto-generate formatted agendas
- Manage participant lists

### 3. Context & Agenda Tab
- Select from preset context files
- Configure agenda input method
- Paste or upload custom content

### 4. Settings Tab
- Choose detail level (Concise, Moderate, High Detail, In-Person)
- Set output format (DOCX, Markdown, Both)
- Configure HuggingFace token for audio processing
- Set output directory

---

## 🎵 Audio Processing

### WhisperX Integration
The system includes built-in WhisperX support for high-quality transcription:

**Prerequisites:**
- **ffmpeg** must be installed on your system (handled automatically by setup script)
- **HuggingFace token** for speaker diarization models

**Usage:**
1. **Set HuggingFace Token**: Get token from [HuggingFace](https://huggingface.co/settings/tokens)
2. **Select Audio File**: Choose your audio file
3. **Process Audio**: Click "Process Audio" button
4. **Generate Minutes**: Transcript automatically loads

### Supported Audio Formats
- `.m4a` (Zoom recordings)
- `.mp3`
- `.wav`
- `.flac`

---

## 📝 Detail Levels

Choose from multiple detail levels:

| Level | Description | Use Case |
|-------|-------------|----------|
| **Concise** | Brief summaries | Quick overviews |
| **Moderate** | Balanced detail | Standard meetings |
| **High Detail** | Comprehensive coverage | Important decisions |
| **In-Person** | No speaker identification | Unreliable audio |

---

## 🔧 Configuration

### Environment Variables (`.env`)
```ini
MODEL=gpt-5
OPENAI_API_BASE=https://api.umgpt.umich.edu/azure-openai-api
AZURE_OPENAI_API_KEY=your_api_key
OPENAI_ORGANIZATION=your_org_id
API_VERSION=2025-04-01-preview
```

### Response Settings (`config.ini`)
```ini
[response_settings]
temperature = 0
max_tokens = 30384
max_completion_tokens = 80000
top_p = 1.0
frequency_penalty = 0.0
presence_penalty = 0.0
```

---

## 🚀 Advanced Usage

### Command Line Interface
For automation and batch processing:

```bash
# Generate minutes from transcript
python scripts/transcript2json.py \
  --input_file transcript.txt \
  --context_file context.md \
  --agenda_file agenda.md \
  --output_file minutes.json

# Convert to documents
python scripts/json2word.py \
  --input_json minutes.json \
  --output_dir output/ \
  --output_prefix meeting_minutes \
  --output_format both
```

### Shell Script Pipeline
```bash
bash scripts/generate_minutes.sh
```

---

## 🧪 Testing

### Test Enhanced Features
```bash
python tests/test_enhanced_features.py
```

### Test Time Rounding
```bash
python tests/test_time_rounding.py
```

---

## 📊 Smart Features

### Automatic Meeting Detection
- Scans `~/Documents/Zoom` for recent meetings
- Extracts meeting names, dates, and times
- Identifies participants from transcripts

### Intelligent Time Handling
- Rounds meeting times to 15-minute intervals
- Example: `13:07:22` → `13:00:00`

### Context Management
- Preset context files for different meeting types
- Easy switching between contexts
- Custom context support

---

## 🔍 Troubleshooting

### Common Issues

1. **Permission denied / Operation not permitted**: 
   - **Problem**: Cannot access `~/Documents/Zoom` folder
   - **Solution**: System Preferences > Security & Privacy > Privacy > Files and Folders
   - Find "Terminal" and check "Documents Folder"
   - Restart the application
   - **Alternative**: Use "Select Transcript File" or "Select Audio File" instead

2. **No Zoom meetings found**: Check `~/Documents/Zoom` directory exists

3. **Audio processing fails**: 
   - **Problem**: "No such file or directory 'whisperx'" or "ffmpeg not found"
   - **Solution**: 
     - Verify HuggingFace token in Settings tab
     - Install ffmpeg: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Ubuntu)
     - Ensure using correct Python environment: `conda activate meetingsecretaryai_env`

4. **API errors**: Check `.env` configuration file

5. **Import errors**: Ensure `conda activate meetingsecretaryai_env`

### Quick Launch

**Double-click**: `launch_with_diagnostics.command` for guided startup with permission checking

### Getting Help

1. Check the `archive/development_docs/` for detailed documentation
2. Run test scripts to verify functionality  
3. Review configuration files

---

## 📈 Output Examples

### JSON Structure
```json
{
  "meeting_info": {
    "title": "COMPASS PRS Meeting",
    "date": "2025-03-07",
    "time": "13:00:00",
    "participants": ["Dr. Smith", "Dr. Johnson"]
  },
  "agenda_items": [...],
  "decisions": [...],
  "action_items": [...]
}
```

### Generated Documents
- **DOCX**: Professional Word document with formatting
- **Markdown**: Clean text format for web publishing
- **JSON**: Structured data for further processing

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html).

---

## 👥 Author

**Fritsche Lab**  
[https://github.com/FritscheLab](https://github.com/FritscheLab)

---

## 🔄 Version History

- **v2.0**: Enhanced GUI with Zoom integration, audio processing, and smart features
- **v1.0**: Original command-line interface and basic functionality
