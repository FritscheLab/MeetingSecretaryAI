# `json_refine.py`

`json_refine.py` takes an existing meeting minutes JSON file and runs it through
an additional model to remove redundancy, reduce verbosity, and improve readability
while preserving the original schema.

## Usage

```sh
python scripts/json_refine.py \
  --input_json meeting.json \
  --output_json meeting_refined.json \
  --prompt_file scripts/prompt_refine.md \
  --schema_file scripts/minutes_schema.JSON \
  --config_file config.ini
```

## Configuration

- **Model selection:** set `REFINEMENT_MODEL` in your `.env`. If unset, the
  script falls back to `MODEL`.
- **Response settings:** shared with `transcript2json.py` via `config.ini`.
- **Reasoning effort:** set `reasoning_effort_refine` in `config.ini` to pass
  an optional reasoning effort level to the refinement model.

## Output

The refined JSON matches the same schema, so it can be passed directly into
`json2word.py` or any downstream tooling.
