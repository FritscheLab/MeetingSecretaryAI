# `transcript2json.py`

## Overview
`transcript2json.py` processes a raw meeting transcript using Azure OpenAI models and outputs a structured JSON file based on a predefined schema (`minutes_schema.JSON`). It uses contextual information and agenda details to enhance summary accuracy.

---

## Usage

```bash
python scripts/transcript2json.py \
  --input_file <path_to_transcript> \
  --context_file <path_to_context> \
  --agenda_file <path_to_agenda> \
  --output_file <output_minutes.json> \
  [--prompt_file scripts/prompt.md] \
  [--schema_file scripts/minutes_schema.JSON] \
  [--config_file config.ini]
```

---

## Arguments

| Argument          | Description                                           | Required | Default                     |
|-------------------|-------------------------------------------------------|----------|-----------------------------|
| `--input_file`   | Path to the raw transcript file (TXT).                | ✅       | N/A                         |
| `--context_file` | Path to the context file (`context.md`).              | ✅       | N/A                         |
| `--agenda_file`  | Path to the meeting agenda (Markdown).                | ✅       | N/A                         |
| `--output_file`  | Path to save the output JSON minutes.                 | ✅       | N/A                         |
| `--prompt_file`  | Custom system prompt file for the AI model.           | ❌       | `scripts/prompt.md`         |
| `--schema_file`  | Path to the JSON schema definition.                   | ❌       | `scripts/minutes_schema.JSON`|
| `--config_file`  | Path to configuration settings for the AI response.   | ❌       | `config.ini`                |

---

## Configuration (`config.ini`)

```ini
[response_settings]
temperature = 0
max_tokens = 16384
top_p = 1.0
frequency_penalty = 0.0
presence_penalty = 0.0
```

---

## Environment (`.env`)

```ini
MODEL=<ai model, e.g., o3-mini>
OPENAI_API_BASE=https://api.umgpt.umich.edu/azure-openai-api
OPENAI_API_KEY=<apikey>
OPENAI_ORGANIZATION=<shortcode>
API_VERSION=<api version, e.g., 2025-01-01-preview>
```

---

## Outputs

- JSON file (`minutes.json`) formatted according to `minutes_schema.JSON`.

---

## Error Handling

- Catches and reports:
  - JSON parsing errors from the AI response.
  - API call exceptions.
  - Missing or invalid environment variables.

---

## Best Practices

- Validate transcript clarity and structure.
- Regularly update `context.md` and `agenda.md`.
- Customize `prompt.md` to align the AI output with your meeting needs.
