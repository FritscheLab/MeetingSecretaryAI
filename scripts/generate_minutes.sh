#!/bin/bash

# Initialize conda for this shell session
if command -v mamba &> /dev/null; then
    eval "$(mamba shell hook --shell zsh)"
    mamba activate meetingsecretaryai_env
else
    eval "$(conda shell.zsh hook)"
    conda activate meetingsecretaryai_env
fi


datadir="../MeetingSecretaryAI_Data/data/"
outdir="../MeetingSecretaryAI_Data/output/"
zoomdir="~/Documents/Zoom"

# Define meeting parameters
topic="Study_Section"
meeting="MockSession"
date="20250307"

# Detail level: action, high, moderate, concise
detail_level="high"

# Uncomment the following line to transcribe audio using WhisperX
# HF_TOKEN=$(cat "../MeetingSecretaryAI_Data/.hf_token.txt")
# whisperx ${datadir}/${topic}/${meeting}_${date}/{audiofile}.m4a \
#     --model large-v3 \
#     --diarize \
#     --hf_token ${HF_TOKEN} \
#     --language en \
#     --device cpu \
#     --compute_type int8 \
#     --batch_size 16 \
#     --output_dir ${datadir}/${topic}/${meeting}_${date}/ \
#     --threads 8 

# Generate structured JSON minutes
python scripts/transcript2json.py \
    --input_file ${datadir}/${topic}/${meeting}_${date}/transcript.txt \
    --context_file ${datadir}/${topic}/context.md \
    --agenda_file ${datadir}/${topic}/${meeting}_${date}/agenda.md \
    --output_file ${datadir}/${topic}/${meeting}_${date}/minutes_${detail_level}.json \
    --prompt_file scripts/prompt_${detail_level}.md \
    --schema_file scripts/minutes_schema.JSON \
    --config_file config.ini

# Refine JSON minutes for readability
python scripts/json_refine.py \
    --input_json ${datadir}/${topic}/${meeting}_${date}/minutes_${detail_level}.json \
    --output_json ${datadir}/${topic}/${meeting}_${date}/minutes_${detail_level}_refined.json \
    --prompt_file scripts/prompt_refine.md \
    --schema_file scripts/minutes_schema.JSON \
    --config_file config.ini

# Convert refined JSON minutes into DOCX and Markdown
python scripts/json2word.py \
    --input_json ${datadir}/${topic}/${meeting}_${date}/minutes_${detail_level}_refined.json \
    --output_dir ${outdir} \
    --output_prefix ${meeting}_Minutes_${date} \
    --output_format docx \
    --include_rationale \
    --include_recommendations
