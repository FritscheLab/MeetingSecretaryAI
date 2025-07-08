# `json2word.py`

## Overview
`json2word.py` converts the structured JSON meeting minutes into formatted DOCX and/or Markdown documents, ideal for sharing and archiving.

---

## Usage

```bash
python scripts/json2word.py \
  --input_json <minutes.json> \
  [--output_dir <output_directory>] \
  [--output_prefix <file_prefix>] \
  [--output_format <docx|md|both>]
```

---

## Arguments

| Argument         | Description                                   | Required | Default                  |
|------------------|-----------------------------------------------|----------|--------------------------|
| `--input_json`  | Path to the structured minutes JSON file.     | ✅       | N/A                      |
| `--output_dir`  | Directory to save the outputs.                | ❌       | `.` (current directory)  |
| `--output_prefix`| Prefix for output filenames.                 | ❌       | `meeting_minutes`        |
| `--output_format`| Output format: `docx`, `md`, or `both`.      | ❌       | `both`                   |

---

## Outputs

- `meeting_minutes.docx`: Formatted Microsoft Word document.
- `meeting_minutes.md`: Markdown-formatted minutes.
- Both files include:
  - Title and meeting details.
  - Attendees and absentees.
  - Reflections and main sections.
  - Action items, decisions, and recommendations.
  - Footer with version info and page numbers (DOCX only).

---

## Formatting Features

- Styles optimized for professional appearance (Arial, 11pt).
- Bullet lists for clarity.
- Automatic date and time formatting.
- Pagination and footer metadata.

---

## Error Handling

- Validates the input JSON.
- Ensures output directories exist.
- Handles date/time parsing errors gracefully.

---

## Best Practices

- Verify JSON validity against `minutes_schema.JSON`.
- Use consistent naming conventions for outputs.
- Run in the same environment as `transcript2json.py` to ensure compatibility.
