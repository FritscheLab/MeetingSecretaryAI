#!/usr/bin/env python3
"""
Small runner to execute meeting_utils.AudioProcessor on a given audio file.

Usage:
  python scripts/run_audio_processor.py /path/to/audio.m4a [--out output_dir]

Requires:
  - A valid HuggingFace token at ../MeetingSecretaryAI_Data/.hf_token.txt (relative to repo root)
  - whisperx installed in the active Python environment
"""

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run AudioProcessor on an audio file")
    parser.add_argument("audio_file", help="Path to the audio file (e.g., .m4a, .wav)")
    parser.add_argument(
        "--out",
        dest="output_dir",
        default="output/whisperx_run",
        help="Output directory for WhisperX results (default: output/whisperx_run)",
    )
    args = parser.parse_args()

    # Make paths absolute relative to repo root if needed
    repo_root = Path(__file__).resolve().parents[1]
    audio_path = Path(args.audio_file).expanduser().resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (repo_root / output_dir).resolve()

    if not audio_path.exists():
        print(f"Error: audio file not found: {audio_path}")
        sys.exit(1)

    # Import from repo root
    sys.path.insert(0, str(repo_root))
    from meeting_utils import TokenManager, AudioProcessor

    token_manager = TokenManager()  # default path ../MeetingSecretaryAI_Data/.hf_token.txt
    token = token_manager.get_token()
    if not token:
        print("Error: HuggingFace token not found. Please create ../MeetingSecretaryAI_Data/.hf_token.txt")
        sys.exit(2)

    print(f"Running WhisperX on: {audio_path}")
    print(f"Output directory: {output_dir}")

    processor = AudioProcessor(token_manager)

    done = {"status": None, "message": None}

    def cb(success: bool, message: str):
        done["status"] = success
        done["message"] = message
        print("Callback:", "SUCCESS" if success else "FAIL", message)

    try:
        thread = processor.process_audio(str(audio_path), str(output_dir), callback=cb)
        # Wait for completion
        thread.join()
    except Exception as e:
        print("Error while starting AudioProcessor:", e)
        sys.exit(3)

    if done["status"]:
        print("Completed successfully.")
        sys.exit(0)
    else:
        print("Processing failed.")
        sys.exit(4)


if __name__ == "__main__":
    main()
