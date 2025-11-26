
# AGENTS.md

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Configuration Reference](#configuration-reference)
6. [Agents](#agents)
7. [Directory Map](#directory-map)
8. [Supporting Files](#supporting-files)
9. [Tests](#tests)
10. [Contributing](#contributing)
11. [License](#license)
12. [Changelog](#changelog)
13. [Troubleshooting / FAQ](#troubleshooting--faq)
14. [Roadmap & Contact](#roadmap--contact)

---

## Overview

This repository automates meeting documentation: transcript processing, agenda generation, and meeting minutes creation. It is designed for researchers, admins, and teams who want to streamline meeting records with minimal manual effort.

---

## Architecture

![Workflow diagram](doc/architecture.md)

**Data flow:**
1. **Transcript ingestion** → `scripts/transcript2json.py`
2. **Structuring** → `meeting_utils.py` (e.g., `parse_transcript()`)
3. **Minutes generation** → `scripts/json2word.py`

*See [doc/](doc/) for more details and templates.*

---

## Installation

```sh
pip install -r requirements.txt
# For DOCX export: install LibreOffice or Microsoft Word
# macOS: brew install --cask libreoffice
```

---

## Quick Start

```sh
# Convert transcript to JSON
python scripts/transcript2json.py sample.vtt > meeting.json

# Generate Word minutes from JSON
python scripts/json2word.py meeting.json

# Launch the GUI
python meeting_secretary_gui.py
```

---

## Configuration Reference

See `config.ini` for all options. Example keys:

| Section         | Key              | Default         | Description                        |
|-----------------|------------------|-----------------|------------------------------------|
| `[general]`     | language         | en              | Language for output                |
| `[output]`      | template         | template_agenda | Template file for minutes          |
| `[paths]`       | output_dir       | ./output        | Where to save generated files      |

*You can override most options with environment variables (see `README.md`).*

---

## Agents

### meeting_secretary_gui.py
- **Purpose:** Main graphical user interface for the Meeting Secretary AI system.
- **Functionality:** Provides a user-friendly interface to interact with the meeting documentation tools, including transcript processing and minutes generation.

### meeting_utils.py
- **Purpose:** Utility functions for meeting data processing.
- **Functionality:** Contains helper functions used by other scripts for tasks such as parsing, formatting, and data manipulation.

### scripts/json2word.py
- **Purpose:** Converts meeting minutes in JSON format to Microsoft Word documents.
- **Functionality:** Reads a JSON file (following the minutes schema) and generates a `.docx` file using a template.

### scripts/transcript2json.py
- **Purpose:** Converts meeting transcripts to structured JSON format.
- **Functionality:** Processes raw transcript text and outputs a JSON file suitable for further processing or conversion to minutes.

### scripts/generate_minutes.sh
- **Purpose:** Automates the process of generating meeting minutes from transcripts.
- **Functionality:** Shell script that chains together transcript processing and document generation steps.

---

## Directory Map

- `scripts/` – CLI tools for conversion and automation
- `doc/` – Documentation, templates, and architecture diagrams
- `__pycache__/` – Python bytecode cache (ignored)
- `requirements.txt` – Python dependencies
- `config.ini` – Main configuration file
- `meeting_secretary_gui.py` – Main GUI
- `meeting_utils.py` – Utility functions

---

## Supporting Files

- **`requirements.txt`**: Lists Python dependencies for the project.
- **`config.ini`**: Configuration file for customizing agent behavior.
- **`doc/`**: Documentation and templates for agenda and context generation.
- **`scripts/minutes_schema.JSON`**: JSON schema for meeting minutes structure.

---

## Tests

Tests use `pytest`. To run:

```sh
pytest
```

*CI/CD status: ![Build Status](https://img.shields.io/badge/build-passing-brightgreen)*

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Please:
- Use feature branches (`feature/your-feature`)
- Run `black .` and `flake8` before PRs
- Sign the CLA if prompted

---

## License

SPDX-License-Identifier: MIT

See [LICENSE](LICENSE) for details.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes and version history. Releases follow semantic versioning.

---

## Troubleshooting / FAQ

- **Missing FFmpeg or LibreOffice:** Install via `brew install ffmpeg libreoffice`
- **Permission errors:** Ensure scripts are executable: `chmod +x scripts/*.sh`
- **Encoding errors:** Use UTF-8 encoded input files

For more, see [doc/FAQ.md](doc/FAQ.md) or open an issue.

---

## Roadmap & Contact

**Vision:** Streamline and automate meeting documentation for research and professional teams. Planned: web interface, more export formats, and AI-powered summarization.

See [GitHub Issues](https://github.com/FritscheLab/MeetingSecretaryAI/issues) for the roadmap.

---
