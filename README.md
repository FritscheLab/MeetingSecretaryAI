# Meeting Secretary AI 2.0

An AI-powered system for automatically processing meeting transcripts and generating structured meeting minutes.

## Overview

Meeting Secretary AI takes your meeting transcripts, extracts agenda items, analyzes the content of each item, and generates professional meeting minutes in DOCX or Markdown format. The system works in a three-step pipeline:

1. **Extract Agenda Items**: Processes meeting transcripts to identify agenda items and their timestamps
2. **Transform to JSON**: Processes each agenda item into structured JSON using selected prompt style 
3. **Generate Output**: Creates formatted DOCX and/or Markdown documents from the JSON content

## Directory Structure

```
meeting-secretary-ai/
├── src/                     # Source code
│   ├── extract_agenda_items.py   # Script to extract agenda items from transcripts
│   ├── transcript2json.py        # Script to convert transcript segments to structured JSON
│   ├── json2word.py              # Script to generate DOCX/MD from JSON
│   ├── consolidate_json.py       # Script to consolidate JSON segments
│   ├── meeting_secretary.py      # Main script that runs the full pipeline
│   ├── config.ini                # Configuration settings
│   ├── prompts/                  # LLM prompts
│   │   ├── prompt_concise.md     # Prompt for concise minutes
│   │   ├── prompt_moderate.md    # Prompt for moderate detail
│   │   ├── prompt_high.md        # Prompt for high detail
│   │   ├── prompt_high_inperson.md # Prompt for high detail without speaker attribution
│   │   ├── prompt_high_subjective.md # Prompt for highly detailed subjective minutes
│   │   └── system_prompt.txt     # System prompt for agenda extraction
│   └── schemas/                  # JSON schemas for structured output
│       ├── agenda_schema.json    # Schema for agenda extraction
│       └── minutes_schema.JSON   # Schema for meeting minutes
├── data/                   # Data directory (transcripts and outputs)
├── docs/                   # Documentation
├── run_meeting_secretary.sh   # Example script to run the pipeline
└── README.md               # This file
```

## Prerequisites

- Python 3.8+
- Azure OpenAI API access
- Required Python packages (see requirements below)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/MeetingSecretaryAI_2.0.git
   cd MeetingSecretaryAI_2.0
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   export OPENAI_API_KEY=your_api_key
   export API_VERSION=your_api_version
   export OPENAI_API_BASE=your_azure_endpoint
   export OPENAI_ORGANIZATION=your_organization_id
   export MODEL=o3-mini  # Or your preferred model
   ```

## Usage

### Basic Usage

Run the full pipeline using the provided script:

```bash
./run_meeting_secretary.sh
```

Or run with custom parameters:

```bash
python src/meeting_secretary.py \
  --transcripts data/my_meeting/transcript1.txt data/my_meeting/transcript2.txt \
  --output_dir data/my_meeting/output \
  --meeting_title "Project Kickoff Meeting" \
  --meeting_date "2025-04-15" \
  --meeting_time "10:00 AM - 11:30 AM EST" \
  --meeting_location "Conference Room A" \
  --prompt_style "moderate" \
  --output_format "both"
```

### Next Meeting Information

You can include details about the next scheduled meeting:

```bash
python src/meeting_secretary.py \
  --next_meeting_date "20250430" \
  --next_meeting_time "10:00 AM EST" \
  --next_meeting_location "Virtual Meeting"
```

To exclude next meeting information from the minutes, use the `--exclude_next_meeting` flag.

### Prompt Styles

You can choose from five different prompt styles:

- **concise**: Minimal detail, focuses on high-level takeaways
- **moderate**: Balanced level of detail (default)
- **high**: Maximum detail, includes all discussions verbatim
- **high_inperson**: Maximum detail but without speaker attribution (for unreliable speaker labels)
- **high_subjective**: Highly detailed narrative with subjective analysis

Select a prompt style with the `--prompt_style` option:

```bash
python src/meeting_secretary.py --prompt_style "concise" ...
```

### Output Formats

You can generate meeting minutes in two formats:

- **docx**: Microsoft Word document (default)
- **md**: Markdown text file
- **both**: Generate both formats

Select the output format with the `--output_format` option:

```bash
python src/meeting_secretary.py --output_format "both" ...
```

### Detailed Usage

For more control, you can run each script individually:

1. Extract agenda items:
   ```
   python src/extract_agenda_items.py \
     --input_file data/my_meeting/transcript.txt \
     --output_file data/my_meeting/agenda_items.json \
     --output_dir data/my_meeting \
     --prompt_file src/prompts/system_prompt.txt \
     --schema_file src/schemas/agenda_schema.json \
     --match_threshold 85 \
     --gap_threshold_seconds 30
   ```

2. Process each segment to JSON:
   ```
   python src/transcript2json.py \
     --input_file data/my_meeting/01_agenda_item.txt \
     --context_file data/my_meeting/context.md \
     --agenda_file data/my_meeting/agenda.md \
     --output_file data/my_meeting/01_agenda_item.json \
     --prompt_file src/prompts/prompt_moderate.md \
     --schema_file src/schemas/minutes_schema.JSON
   ```

3. Consolidate JSON segments:
   ```
   python src/consolidate_json.py \
     --input_files data/my_meeting/*.json \
     --output_file data/my_meeting/consolidated.json \
     --meeting_title "Project Kickoff Meeting" \
     --meeting_date "2025-04-15" \
     --meeting_time "10:00 AM - 11:30 AM EST" \
     --meeting_location "Conference Room A" \
     --next_meeting_date "20250430" \
     --next_meeting_time "10:00 AM EST" \
     --next_meeting_location "Virtual Meeting"
   ```

4. Generate output documents:
   ```
   python src/json2word.py \
     --input_json data/my_meeting/consolidated.json \
     --output_dir data/my_meeting \
     --output_prefix "minutes" \
     --output_format "both" \
     --include_rationale \
     --include_recommendations
   ```

## Features

- Handles multiple transcript files
- Multiple prompt styles to control level of detail
- Output in DOCX or Markdown format
- Preserves original agenda item titles
- Automatically identifies meeting segments by timestamps
- Manages gap detection and merging with configurable thresholds
- Extracts key information including:
  - Discussion points
  - Decisions
  - Action items with assignees
  - Participant information
  - Key recommendations and rationale
  - References
- Generates professionally formatted documents
- Customizable output
- Support for next meeting information

## File Formats

- **Transcripts**: Plain text files with timestamps
- **Context**: Optional markdown file with meeting context
- **Agenda**: Optional markdown file with planned agenda
- **Output**: Microsoft Word DOCX and/or Markdown format

## Configuration

Modify `config.ini` to adjust LLM parameters:

```ini
[response_settings]
temperature = 0
max_tokens = 30384
top_p = 1.0
frequency_penalty = 0.0
presence_penalty = 0.0
```

## License

[Insert your license information here]

## Acknowledgements

- This project uses Azure OpenAI for natural language processing
- Python-docx for DOCX generation
- thefuzz for string similarity matching