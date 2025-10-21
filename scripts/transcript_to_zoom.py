#!/usr/bin/env python3
"""Convert processed transcripts with placeholder speakers into Zoom caption format.

This tool reads a transcript (WebVTT or similar) that contains speaker labels in the
form ``[SPEAKER_00]:`` and produces a Zoom-style caption log. It guides the user
through assigning human-friendly names to the placeholder speakers by showing a
few example utterances for each speaker before prompting for the display name.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

SPEAKER_PLACEHOLDER_RE = re.compile(r"^SPEAKER_\d+$")
SPEAKER_LINE_RE = re.compile(r"^\[(?P<speaker>[^\]]+)\]:?\s*(?P<text>.*)$")
VOICE_TAG_RE = re.compile(r"^<v\s+(?P<speaker>[^>]+)>(?P<text>.*)</v>$")


@dataclass
class TranscriptEntry:
    """Container for a single transcript cue."""

    start: timedelta
    speaker_id: str
    text: str


def parse_timestamp(value: str) -> timedelta:
    """Convert a WebVTT timestamp into a ``timedelta`` object."""

    parts = value.strip().split(":")
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
    elif len(parts) == 2:
        hours = 0
        minutes = int(parts[0])
        seconds = float(parts[1])
    else:
        raise ValueError(f"Unsupported timestamp format: {value}")

    total_seconds = hours * 3600 + minutes * 60 + seconds
    return timedelta(seconds=total_seconds)


def extract_speaker_and_text(raw_text: str) -> tuple[str, str] | None:
    """Extract the speaker label and spoken text from a cue payload."""

    text = raw_text.strip()

    match = SPEAKER_LINE_RE.match(text)
    if match:
        speaker = match.group("speaker").strip()
        content = match.group("text").strip()
        return speaker, content

    match = VOICE_TAG_RE.match(text)
    if match:
        speaker = match.group("speaker").strip()
        content = match.group("text").strip()
        return speaker, content

    # If no speaker marker exists, we cannot map this cue.
    return None


def parse_transcript(path: Path) -> List[TranscriptEntry]:
    """Parse a transcript file into ordered ``TranscriptEntry`` objects."""

    lines = path.read_text(encoding="utf-8-sig").splitlines()
    entries: List[TranscriptEntry] = []

    i = 0
    total_lines = len(lines)
    while i < total_lines:
        line = lines[i].strip()

        if not line or line.upper() == "WEBVTT":
            i += 1
            continue

        if "-->" not in line:
            i += 1
            continue

        try:
            start_raw, _end_raw = [part.strip() for part in line.split("-->")]
            start_ts = parse_timestamp(start_raw)
        except ValueError:
            i += 1
            continue

        i += 1
        payload_lines: List[str] = []
        while i < total_lines and lines[i].strip():
            payload_lines.append(lines[i].strip())
            i += 1

        # Skip the blank line separator
        while i < total_lines and not lines[i].strip():
            i += 1

        if not payload_lines:
            continue

        payload = " ".join(payload_lines)
        extracted = extract_speaker_and_text(payload)
        if not extracted:
            # Store without a speaker label; callers can filter these out.
            speaker_id = "UNKNOWN"
            text = payload
        else:
            speaker_id, text = extracted

        entries.append(TranscriptEntry(start=start_ts, speaker_id=speaker_id, text=text))

    return entries


def collect_examples(entries: Sequence[TranscriptEntry]) -> Dict[str, List[str]]:
    """Collect example utterances for each speaker."""

    examples: Dict[str, List[str]] = {}
    for entry in entries:
        examples.setdefault(entry.speaker_id, []).append(entry.text)
    return examples



def prompt_for_speaker_names(
    placeholders: Iterable[str],
    examples: Dict[str, List[str]],
    batch_size: int,
) -> Dict[str, str]:
    """Interactively collect human-friendly names for each placeholder speaker."""

    batch_size = max(1, batch_size)
    name_mapping: Dict[str, str] = {}
    for speaker_id in sorted(placeholders):
        sample_lines = examples.get(speaker_id, [])
        total = len(sample_lines)
        shown = 0

        while True:
            print(f"\nExamples for {speaker_id}:")
            if sample_lines:
                end_idx = min(total, shown + batch_size)
                for example in sample_lines[shown:end_idx]:
                    print(f"  - {example}")
                if end_idx < total:
                    remaining = total - end_idx
                    plural = "s" if remaining != 1 else ""
                    print(f"  (+ {remaining} more example{plural} — press Enter to see more)")
            else:
                end_idx = shown
                print("  (No sample lines found.)")

            entered = input(f"Enter the display name for {speaker_id}: ").strip()
            if entered:
                name_mapping[speaker_id] = entered
                break

            if sample_lines and end_idx < total:
                shown = end_idx
                continue

            print("Name cannot be empty. Please provide a value.")

    return name_mapping


def format_timestamp_for_zoom(timestamp: timedelta, offset: timedelta | None = None) -> str:
    """Return an ``HH:MM:SS`` string optionally offset by a base start time."""

    base_seconds = int(timestamp.total_seconds())
    if offset:
        base_seconds += int(offset.total_seconds())

    hours = base_seconds // 3600
    minutes = (base_seconds % 3600) // 60
    seconds = base_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def build_zoom_log(
    entries: Sequence[TranscriptEntry],
    name_mapping: Dict[str, str],
    offset: timedelta | None = None,
) -> str:
    """Create the Zoom-style log output."""

    output_lines: List[str] = []
    for entry in entries:
        speaker_name = name_mapping.get(entry.speaker_id, entry.speaker_id)
        timestamp = format_timestamp_for_zoom(entry.start, offset)
        output_lines.append(f"[{speaker_name}] {timestamp}\n{entry.text}")

    return "\n\n".join(output_lines)


def parse_offset(value: str | None) -> timedelta | None:
    """Parse an optional ``HH:MM:SS`` offset string."""

    if not value:
        return None

    parts = value.strip().split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Offset must use HH:MM:SS format")

    hours, minutes, seconds = map(int, parts)
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return timedelta(seconds=total_seconds)


def resolve_output_path(input_path: Path, explicit_output: Path | None) -> Path:
    """Determine where to store the Zoom-formatted transcript."""

    if explicit_output:
        return explicit_output

    base_dir = input_path.parent
    stem = "meeting_saved_closed_caption"
    suffix = ".txt"

    candidate = base_dir / f"{stem}{suffix}"
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = base_dir / f"{stem}{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Reformat processed transcripts with SPEAKER placeholders into Zoom caption format",
    )
    parser.add_argument("input_file", type=Path, help="Path to the processed transcript (WebVTT)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Optional path to save the Zoom-formatted transcript "
            "(default: auto-create meeting_saved_closed_caption*.txt alongside the input file)"
        ),
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=7,
        help="Number of sample utterances to show per batch for each speaker (default: 7)",
    )
    parser.add_argument(
        "--offset",
        type=parse_offset,
        default=None,
        help="Optional HH:MM:SS offset to add to transcript timestamps",
    )

    args = parser.parse_args()

    entries = parse_transcript(args.input_file)
    if not entries:
        raise SystemExit("No transcript entries found.")

    placeholder_speakers = [
        entry.speaker_id
        for entry in entries
        if SPEAKER_PLACEHOLDER_RE.match(entry.speaker_id)
    ]

    placeholder_set = sorted(set(placeholder_speakers))
    if placeholder_set:
        examples = collect_examples(entries)
        name_mapping = prompt_for_speaker_names(placeholder_set, examples, batch_size=args.examples)
    else:
        print("No placeholder speakers detected; using existing speaker labels.")
        name_mapping = {}

    zoom_log = build_zoom_log(entries, name_mapping, offset=args.offset)

    output_path = resolve_output_path(args.input_file, args.output)
    output_path.write_text(zoom_log + "\n", encoding="utf-8")
    print(f"Zoom-formatted transcript saved to {output_path}")


if __name__ == "__main__":
    run_cli()
