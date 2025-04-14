# Meeting Secretary AI 2.0 - Usage Guide

This guide provides detailed instructions on how to use the Meeting Secretary AI system to process your meeting transcripts and generate professional minutes.

## Setting Up Your Environment

### Environment Variables

Before running the system, set the following environment variables:

```bash
export OPENAI_API_KEY=your_api_key
export API_VERSION=your_api_version  # e.g., "2023-07-01-preview"
export OPENAI_API_BASE=your_azure_endpoint  # e.g., "https://your-resource.openai.azure.com"
export OPENAI_ORGANIZATION=your_organization_id  # if applicable
export MODEL=o3-mini  # Or your preferred model
```

You can add these to a `.env` file in the project root, and they'll be loaded automatically.

## Preparing Your Data

### Directory Structure

Create a directory for your meeting in the `data/` folder:

```
data/
└── your_meeting_name/
    ├── transcript_part1.txt
    ├── transcript_part2.txt (optional)
    ├── context.md (optional)
    └── agenda.md (optional)
```

### Transcript Format

Your transcript should include timestamps. For example:

```
[00:00:05] John: Welcome everyone to our weekly team meeting.
[00:01:30] Sarah: Let's start with the first agenda item: Project Updates.
```

Supported timestamp formats include:
- `[HH:MM:SS]`
- `(HH:MM:SS)`
- `HH:MM:SS`
- WebVTT format (`00:00:05.000 --> 00:00:10.000`)

### Context File (Optional)

Create a markdown file with background information about the meeting:

```markdown
# Meeting Context

This is a weekly team meeting for Project X. The team is discussing progress on the 
latest release, addressing customer feedback, and planning the next sprint.
```

### Agenda File (Optional)

Create a markdown file with the planned meeting agenda:

```markdown
# Meeting Agenda

1. Project Updates (10 min)
2. Customer Feedback Discussion (15 min)
3. Sprint Planning (20 min)
4. Open Items and Questions (15 min)
```

## Running the Pipeline

### Using the Convenience Script

The simplest way to run the pipeline is using the provided script:

```bash
./run_meeting_secretary.sh
```

Customize the script for your meeting by editing the parameters.

### Using the Main Script

For more control, use the main Python script:

```bash
python src/meeting_secretary.py \
  --transcripts data/your_meeting/transcript_part1.txt data/your_meeting/transcript_part2.txt \
  --output_dir data/your_meeting/output \
  --meeting_title "Your Meeting Title" \
  --meeting_date "2025-04-15" \
  --meeting_time "10:00 AM - 11:30 AM EST" \
  --meeting_location "Conference Room A" \
  --context_file data/your_meeting/context.md \
  --agenda_file data/your_meeting/agenda.md \
  --prompt_style "moderate" \
  --output_format "both" \
  --include_recommendations
```

### Command-Line Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `--transcripts` | Path(s) to transcript files | Yes |
| `--output_dir` | Directory for output files | Yes |
| `--meeting_title` | Title of the meeting | Yes |
| `--output_file` | Specific output file path | No |
| `--meeting_date` | Date in YYYYMMDD format | No |
| `--meeting_time` | Time of the meeting | No |
| `--meeting_location` | Location of the meeting | No |
| `--next_meeting_date` | Date of next meeting in YYYYMMDD format | No |
| `--next_meeting_time` | Time of the next meeting | No |
| `--next_meeting_location` | Location of the next meeting | No |
| `--exclude_next_meeting` | Exclude next meeting information | No |
| `--context_file` | Path to context file | No |
| `--agenda_file` | Path to agenda file | No |
| `--prompt_style` | Style: concise, moderate, high, high_inperson, high_subjective | No |
| `--output_format` | Format: docx, md, both | No |
| `--include_rationale` | Include rationale sections | No |
| `--include_recommendations` | Include recommendations | No |
| `--config_file` | Path to config file | No |
| `--gap_threshold_seconds` | Seconds threshold for merging agenda items | No |
| `--match_threshold` | Similarity threshold (0-100) for title matching | No |

## Prompt Styles

You can choose from five different prompt styles to control the detail level of your meeting minutes:

1. **concise**: Minimal detail focused on high-level takeaways. Best for executive summaries or when you need quick reference documentation.

2. **moderate** (default): Balanced level of detail that captures important discussions while summarizing less critical exchanges. Ideal for most regular meetings.

3. **high**: Maximum level of detail including virtually every exchange. Best when you need comprehensive documentation of the meeting.

4. **high_inperson**: Maximum detail but without speaker attribution. Use this when speaker identification in the transcript is unreliable or when you prefer to focus on content rather than who said what.

5. **high_subjective**: Highly detailed narrative with subjective analysis. Produces exhaustive, richly narrative minutes that preserve every detail while organizing content by discussion subtopics. Includes expanded rationale and reference tracking.

## Output Formats

You can generate meeting minutes in different formats:

- **docx**: Microsoft Word document (default)
- **md**: Markdown text file
- **both**: Generate both formats

## Output Files

After running the pipeline, you'll find the following:

```
data/your_meeting/output/
├── 00_meeting_info.txt                # Meeting metadata
├── 01_agenda_item_1.txt               # Individual transcript sections
├── 02_agenda_item_2.txt
├── ...
├── agenda_items.json                  # Combined agenda items
├── processed_items/                   # Transcript text split by agenda item
│   ├── 01_agenda_item_1.txt
│   ├── 02_agenda_item_2.txt
│   └── ...
├── json_output/                       # JSON output for each segment
│   ├── 01_agenda_item_1.json
│   ├── 02_agenda_item_2.json
│   ├── ...
│   └── meeting_minutes.json           # Consolidated JSON
└── your_meeting_name_minutes.docx     # Final minutes document (and/or .md)
```

## Customizing Output

### Controlling What's Included

- `--include_rationale`: Include detailed rationale sections
- `--include_recommendations`: Include key recommendations

### Next Meeting Information

You can include information about the next scheduled meeting in your minutes:

```bash
python src/meeting_secretary.py \
  --next_meeting_date "20250430" \
  --next_meeting_time "1:00 PM EST" \
  --next_meeting_location "Virtual Meeting" \
  ...
```

To exclude next meeting information from the minutes, use:

```bash
python src/meeting_secretary.py --exclude_next_meeting ...
```

### Configuring Agenda Extraction

The system provides options to fine-tune how agenda items are identified:

```bash
python src/meeting_secretary.py \
  --gap_threshold_seconds 30 \
  --match_threshold 85 \
  ...
```

- `--gap_threshold_seconds`: Controls how short gaps between discussions are handled. Lower values will create more separate agenda items, while higher values will merge nearby discussions.
- `--match_threshold`: Determines how strictly the system matches agenda titles. A higher value (0-100) requires closer matches.

### Modifying Format

To change the DOCX formatting, edit the templates in `src/json2word.py`.

## Troubleshooting

### Common Issues

1. **Missing timestamps**: Ensure your transcripts contain recognizable timestamps
2. **API errors**: Check your environment variables for Azure OpenAI access
3. **Empty agenda items**: Check that your transcript has clear topic transitions

### Logs

Check the logs during processing for warnings or errors. Increase verbosity by modifying the logging level in each script if needed.