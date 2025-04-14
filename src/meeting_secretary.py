#!/usr/bin/env python3
"""
Meeting Secretary AI 2.0 - Main Script

This script orchestrates the meeting minutes generation pipeline by running:
1. extract_agenda_items.py - Extract agenda items from meeting transcripts
2. transcript2json.py - Process transcript to structured JSON using selected prompt style
3. json2word.py - Generate final meeting minutes in DOCX or MD format
"""

import argparse
import os
import logging
import subprocess
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate meeting minutes from transcripts using AI"
    )

    # Main arguments
    parser.add_argument("--transcripts", required=True, nargs='+',
                      help="Path(s) to meeting transcript file(s). Provide in order.")
    parser.add_argument("--output_dir", required=True,
                      help="Directory where all intermediate output files will be saved")
    parser.add_argument("--meeting_title", required=True,
                      help="Title of the meeting")
    parser.add_argument("--output_file",
                      help="Optional: Full path and filename for the final output file. "
                           "If not provided, defaults to '[output_dir_name]_minutes.[format]' inside --output_dir.")

    # Optional meeting details arguments
    parser.add_argument("--context_file",
                      help="Path to meeting context file (optional)")
    parser.add_argument("--agenda_file",
                      help="Path to the planned agenda file (optional)")
    parser.add_argument("--meeting_date",
                      help="Date of the meeting in YYYYMMDD format (e.g., 20250415). Defaults to today if not provided.")
    parser.add_argument("--meeting_time",
                      help="Time of the meeting in 12-hour format (e.g., '1:00 PM - 3:00 PM EST')")
    parser.add_argument("--meeting_location",
                      help="Location of the meeting (e.g., 'Virtual', 'Conference Room A')")
    # Next meeting details
    parser.add_argument("--next_meeting_date",
                      help="Date of the next meeting in YYYYMMDD format (e.g., 20250430)")
    parser.add_argument("--next_meeting_time",
                      help="Time of the next meeting in 12-hour format (e.g., '1:00 PM EST')")
    parser.add_argument("--next_meeting_location",
                      help="Location of the next meeting (e.g., 'Virtual', 'Conference Room A')")
    parser.add_argument("--exclude_next_meeting", action="store_true",
                      help="Exclude next meeting information from the minutes")

    # Prompt selection
    parser.add_argument("--prompt_style", choices=["concise", "moderate", "high", "high_inperson"], default="moderate",
                      help="Select prompt style: concise (minimal detail), moderate (balanced), "
                           "high (maximum detail), high_inperson (maximum detail without speaker attribution)")

    # Output customization
    parser.add_argument("--output_format", choices=["docx", "md", "both"], default="docx",
                      help="Output format: 'docx', 'md', or 'both' (default: docx)")
    parser.add_argument("--include_rationale", action="store_true",
                      help="Include general rationale sections in final minutes")
    parser.add_argument("--include_recommendations", action="store_true",
                      help="Include key recommendation sections in final minutes")

    # Config files
    parser.add_argument("--config_file", default="src/config.ini",
                      help="Path to the configuration file (default: src/config.ini)")

    # Gap merging threshold from extract_agenda_items.py (pass through if needed)
    parser.add_argument("--gap_threshold_seconds", type=int, default=30,
                        help="Minimum duration (seconds) for a gap between items to be merged in extraction step (default: 30).")
    parser.add_argument("--match_threshold", type=int, default=85,
                        help="Similarity threshold (0-100) for title matching in extraction step (default: 85).")

    return parser.parse_args()

def run_pipeline(args):
    """Run the full meeting minutes generation pipeline."""
    # Create output directories
    os.makedirs(args.output_dir, exist_ok=True)
    processed_dir = os.path.join(args.output_dir, "processed_items")
    os.makedirs(processed_dir, exist_ok=True)
    json_output_dir = os.path.join(args.output_dir, "json_output")
    os.makedirs(json_output_dir, exist_ok=True)

    # Intermediate files
    agenda_items_json = os.path.join(args.output_dir, "agenda_items.json")
    consolidated_json = os.path.join(json_output_dir, "meeting_minutes.json")

    # Map prompt style to file path
    prompt_file_map = {
        "concise": "src/prompts/prompt_concise.md",
        "moderate": "src/prompts/prompt_moderate.md",
        "high": "src/prompts/prompt_high.md",
        "high_inperson": "src/prompts/prompt_high_inperson.md"
    }
    selected_prompt = prompt_file_map[args.prompt_style]

    # Determine the final output path and file prefix
    if args.output_file:
        # User specified an exact path and filename
        output_file = args.output_file
        output_prefix = os.path.splitext(os.path.basename(output_file))[0]
        output_dir = os.path.dirname(output_file) or args.output_dir
        
        # Ensure the directory exists
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                logging.info(f"Created directory for output: {output_dir}")
            except OSError as e:
                logging.error(f"Could not create directory for --output_file: {output_dir}. Error: {e}")
                logging.warning("Falling back to default naming scheme in --output_dir.")
                output_dir = args.output_dir
                output_prefix = os.path.basename(os.path.normpath(args.output_dir))
    else:
        # Default behavior
        output_dir = args.output_dir
        output_prefix = os.path.basename(os.path.normpath(args.output_dir))

    # Step 1: Extract agenda items from transcripts
    logging.info("Step 1: Extracting agenda items from transcripts...")
    extract_args = [
        "python", "src/extract_agenda_items.py",
        "--input_file"] + args.transcripts + [
        "--output_file", agenda_items_json,
        "--output_dir", processed_dir,
        "--prompt_file", "src/prompts/system_prompt.txt",
        "--schema_file", "src/schemas/agenda_schema.json",
        "--config_file", args.config_file,
        "--match_threshold", str(args.match_threshold),
        "--gap_threshold_seconds", str(args.gap_threshold_seconds)
    ]

    if args.context_file:
        extract_args.extend(["--context_file", args.context_file])
    if args.agenda_file:
        extract_args.extend(["--agenda_file", args.agenda_file])

    try:
        subprocess.run(extract_args, check=True, capture_output=True, text=True)
        logging.info("Step 1: extract_agenda_items.py completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Step 1 Failed: extract_agenda_items.py exited with error code {e.returncode}")
        logging.error(f"Stderr:\n{e.stderr}")
        logging.error(f"Stdout:\n{e.stdout}")
        print("\n--- ERROR: Step 1 (Extraction) failed. See logs above. ---")
        return None
    except FileNotFoundError:
        logging.error("Step 1 Failed: Could not find python or src/extract_agenda_items.py. Check paths and environment.")
        print("\n--- ERROR: Step 1 (Extraction) failed. Could not find script. ---")
        return None

    # Step 2: Convert to structured JSON using transcript2json.py
    logging.info("Step 2: Processing transcript to structured JSON...")
    
    # Find all transcript segment files
    transcript_segments = []
    for filename in os.listdir(processed_dir):
        if filename.endswith(".txt") and not filename.startswith("00_"):
            transcript_segments.append(os.path.join(processed_dir, filename))
    
    if not transcript_segments:
        logging.error("No transcript segments found in the processed directory.")
        return None
    
    # Sort segments by their numeric prefix
    transcript_segments.sort(key=lambda f: int(os.path.basename(f).split("_")[0]))
    
    # Process each transcript segment with transcript2json.py
    segment_jsons = []
    for i, segment_file in enumerate(transcript_segments):
        segment_name = os.path.splitext(os.path.basename(segment_file))[0]
        json_output = os.path.join(json_output_dir, f"{segment_name}.json")
        segment_jsons.append(json_output)
        
        # Skip context file for the first segment, as it already has context
        # Extract agenda title from file for context
        with open(segment_file, 'r') as f:
            first_line = f.readline().strip()
            agenda_title = first_line.replace("Agenda Item: ", "") if first_line.startswith("Agenda Item:") else ""
        
        logging.info(f"Processing segment {i+1}/{len(transcript_segments)}: {segment_name}")
        
        # Run transcript2json.py for this segment
        transcript2json_args = [
            "python", "src/transcript2json.py",
            "--input_file", segment_file,
            "--context_file", args.context_file if args.context_file else "",
            "--output_file", json_output,
            "--prompt_file", selected_prompt,
            "--schema_file", "src/schemas/minutes_schema.JSON",
            "--config_file", args.config_file
        ]
        
        try:
            subprocess.run(transcript2json_args, check=True, capture_output=True, text=True)
            logging.info(f"Successfully processed segment {segment_name}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to process segment {segment_name}: {e.returncode}")
            logging.error(f"Stderr:\n{e.stderr}")
            logging.error(f"Stdout:\n{e.stdout}")
            # Continue with other segments
        except FileNotFoundError:
            logging.error("Could not find python or src/transcript2json.py. Check paths and environment.")
            return None
    
    # Consolidate JSON segments (to be implemented)
    logging.info("Consolidating JSON segments...")
    consolidate_args = [
        "python", "src/consolidate_json.py",
        "--input_files"] + segment_jsons + [
        "--output_file", consolidated_json,
        "--meeting_title", args.meeting_title
    ]
    
    if args.meeting_date:
        consolidate_args.extend(["--meeting_date", args.meeting_date])
    if args.meeting_time:
        consolidate_args.extend(["--meeting_time", args.meeting_time])
    if args.meeting_location:
        consolidate_args.extend(["--meeting_location", args.meeting_location])
        
    # Add next meeting information if not excluded
    if not args.exclude_next_meeting:
        if args.next_meeting_date:
            consolidate_args.extend(["--next_meeting_date", args.next_meeting_date])
        if args.next_meeting_time:
            consolidate_args.extend(["--next_meeting_time", args.next_meeting_time])
        if args.next_meeting_location:
            consolidate_args.extend(["--next_meeting_location", args.next_meeting_location])
    
    try:
        subprocess.run(consolidate_args, check=True, capture_output=True, text=True)
        logging.info("Successfully consolidated JSON segments")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to consolidate JSON segments: {e.returncode}")
        logging.error(f"Stderr:\n{e.stderr}")
        logging.error(f"Stdout:\n{e.stdout}")
        # Proceed with json2word.py anyway, as we might have a valid consolidated file
    except FileNotFoundError:
        logging.error("Could not find python or src/consolidate_json.py. Check paths and environment.")
        # We'll create a simple implementation below to handle this case
    
    # Step 3: Generate the final output using json2word.py
    logging.info(f"Step 3: Generating meeting minutes in {args.output_format} format...")
    json2word_args = [
        "python", "src/json2word.py",
        "--input_json", consolidated_json,
        "--output_dir", output_dir,
        "--output_prefix", output_prefix,
        "--output_format", args.output_format
    ]
    
    if args.include_rationale:
        json2word_args.append("--include_rationale")
    if args.include_recommendations:
        json2word_args.append("--include_recommendations")
    
    try:
        subprocess.run(json2word_args, check=True, capture_output=True, text=True)
        logging.info(f"Step 3: json2word.py completed successfully.")
        
        # Determine the actual output file paths
        output_files = []
        if args.output_format in ("docx", "both"):
            output_files.append(os.path.join(output_dir, f"{output_prefix}.docx"))
        if args.output_format in ("md", "both"):
            output_files.append(os.path.join(output_dir, f"{output_prefix}.md"))
            
        return output_files
    except subprocess.CalledProcessError as e:
        logging.error(f"Step 3 Failed: json2word.py exited with error code {e.returncode}")
        logging.error(f"Stderr:\n{e.stderr}")
        logging.error(f"Stdout:\n{e.stdout}")
        print("\n--- ERROR: Step 3 (Document Generation) failed. See logs above. ---")
        return None
    except FileNotFoundError:
        logging.error("Step 3 Failed: Could not find python or src/json2word.py. Check paths and environment.")
        print("\n--- ERROR: Step 3 (Document Generation) failed. Could not find script. ---")
        return None

def main():
    args = parse_arguments()
    output_files = run_pipeline(args)
    if output_files:
        print(f"\nMeeting minutes generation pipeline completed successfully!")
        for file_path in output_files:
            print(f"Output file: {file_path}")
        print(f"Intermediate files are in: {args.output_dir}")
    else:
        print("\nMeeting minutes generation pipeline failed. Please check the logs for errors.")

if __name__ == "__main__":
    main()