# MeetingSecretaryAI_2.0/src/extract_agenda_items.py
import argparse
import os
import configparser
import json
import re
from datetime import datetime, timedelta # Added timedelta
from openai import AzureOpenAI
from dotenv import load_dotenv
import logging
from thefuzz import process as fuzz_process
from thefuzz import fuzz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

# --- Helper Functions ---
# (load_file_content, load_system_prompt, parse_agenda_titles - unchanged)
# (parse_timestamp, format_timestamp_from_seconds, extract_timestamp_from_line - unchanged)
# (remove_timestamp_from_line - unchanged)
# ... (Keep these functions as they were) ...
def load_file_content(file_path):
    """Load content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file: # Added encoding
            return file.read()
    except FileNotFoundError:
        logging.error(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return None

def load_system_prompt(prompt_file_path, context="", agenda=""):
    """
    Loads the system prompt from an external file and formats it with the provided context and agenda.
    """
    prompt_template = load_file_content(prompt_file_path)
    if prompt_template is None:
        raise ValueError(f"Could not load prompt template from {prompt_file_path}")
    prompt_template = prompt_template.replace("{context}", context or "")
    prompt_template = prompt_template.replace("{agenda}", agenda or "")
    return prompt_template

def parse_agenda_titles(agenda_content):
    """
    Parses an agenda markdown file and extracts item titles.
    Returns: list: List of agenda item titles in order
    """
    if not agenda_content: return []
    agenda_titles = []
    patterns = [
        r'^\s*(\d+)[.)\]]\s+(.+?)(?:\s+\((\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)\))?\s*$',
        r'^\s*[-*]\s+(.+?)(?:\s+\((\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)\))?\s*$'
    ]
    for line in agenda_content.split('\n'):
        for pattern in patterns:
            match = re.search(pattern, line.strip())
            if match:
                title = match.group(2) if len(match.groups()) > 1 else match.group(1)
                agenda_titles.append(title.strip())
                break
    logging.info(f"Parsed {len(agenda_titles)} agenda item titles from agenda file")
    return agenda_titles

def format_timestamp_from_seconds(total_seconds):
    """Converts total seconds back to HH:MM:SS format."""
    if total_seconds is None or total_seconds < 0: return "00:00:00"
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def parse_timestamp(timestamp):
    """Convert timestamp string (HH:MM:SS or HH:MM:SS.ms) to seconds."""
    if not timestamp or not isinstance(timestamp, str):
        logging.debug(f"Invalid timestamp received for parsing: {timestamp}")
        return None
    try:
        time_part = timestamp.split('.')[0]
        time_obj = datetime.strptime(time_part, "%H:%M:%S")
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
    except ValueError:
        logging.debug(f"Could not parse timestamp '{timestamp}' as HH:MM:SS. Trying HH:MM.")
        try:
            time_obj = datetime.strptime(timestamp, "%H:%M")
            return time_obj.hour * 3600 + time_obj.minute * 60
        except ValueError:
             logging.warning(f"Could not parse timestamp {timestamp} after multiple attempts. Returning None.")
             return None

def extract_timestamp_from_line(line):
    """Extract timestamp (HH:MM:SS format) from a transcript line if present"""
    webvtt_pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}'
    match = re.search(webvtt_pattern, line)
    if match:
        timestamp = match.group(1).split('.')[0]
        return timestamp
    patterns = [
        r'\[(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)\]', r'\((\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)\)',
        r'^(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)', r'\[(\d{1,2}:\d{2})\]', r'\((\d{1,2}:\d{2})\)',
        r'(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)\s*-', r'(\d{1,2}:\d{2}:\d{2})'
    ]
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            timestamp = match.group(1)
            if '.' in timestamp: timestamp = timestamp.split('.')[0]
            parts = timestamp.split(':')
            if len(parts) == 2:
                try:
                    h, m = int(parts[0]), int(parts[1])
                    if 0 <= h <= 23 and 0 <= m <= 59: timestamp = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:00"
                    else: continue
                except ValueError: continue
            elif len(parts) == 3: timestamp = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
            else: continue
            try:
                datetime.strptime(timestamp, "%H:%M:%S")
                return timestamp
            except ValueError:
                logging.debug(f"Timestamp {match.group(1)} -> {timestamp} failed final validation.")
                continue
    return None

def remove_timestamp_from_line(line):
    """Remove timestamp notations from a transcript line."""
    combined_pattern = r'^(\d{1,2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?)\s+(.*)$'
    match = re.match(combined_pattern, line.strip())
    if match: return match.group(2).rstrip() + "\n"
    webvtt_timestamp_pattern = r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}'
    if re.search(webvtt_timestamp_pattern, line): return "\n"
    if re.match(r'^\d+\s*$', line.strip()): return "\n"
    webvtt_speaker_pattern = r'^<v\s+([^>]+)>(.+?)</v>$'
    speaker_match = re.search(webvtt_speaker_pattern, line.strip())
    if speaker_match:
        speaker = speaker_match.group(1).strip()
        content = speaker_match.group(2).strip()
        content = re.sub(r'<[^>]+>', '', content)
        return f"{speaker}: {content}\n"
    simple_speaker_pattern = r'^([\w\s]+):\s*(.+)$'
    simple_match = re.match(simple_speaker_pattern, line.strip())
    if simple_match: return line
    patterns = [
        r'\[\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\]', r'\(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\)',
        r'^\d{1,2}:\d{2}:\d{2}(?:\.\d+)?', r'\[\d{1,2}:\d{2}\]', r'\(\d{1,2}:\d{2}\)',
        r'\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\s*-', r'^\d{1,2}:\d{2}:\d{2}\s+'
    ]
    cleaned_line = line
    for pattern in patterns:
        if pattern.startswith('^'): cleaned_line = re.sub(pattern, '', cleaned_line, count=1)
        else: cleaned_line = re.sub(pattern, '', cleaned_line)
    cleaned_line = cleaned_line.lstrip()
    if not cleaned_line.strip() and line.strip(): return line
    elif not cleaned_line.strip(): return "\n"
    if not cleaned_line.endswith("\n"): cleaned_line += "\n"
    return cleaned_line

# --- Core Logic Functions ---

def extract_agenda_items_from_content(system_prompt, transcript_content, model, response_settings, json_schema, client):
    """ Sends transcript content to the LLM and returns the structured agenda items. """
    # (LLM call logic - unchanged from previous version)
    if not transcript_content:
        logging.warning("Transcript content is empty. Skipping LLM call.")
        return None
    try:
        response_args = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"---\nMEETING TRANSCRIPT START\n---\n{transcript_content}\n---\nMEETING TRANSCRIPT END\n---"}
            ],
            "response_format": {"type": "json_schema", "json_schema": {"name": "agenda_structure", "strict": True, "schema": json_schema}}
        }
        if not (model.startswith("o1") or model.startswith("o3")):
             response_args.update({
                 "temperature": response_settings['temperature'], "max_tokens": response_settings['max_tokens'],
                 "top_p": response_settings['top_p'], "frequency_penalty": response_settings['frequency_penalty'],
                 "presence_penalty": response_settings['presence_penalty']
             })
        logging.info(f"Sending request to Azure OpenAI model {model} for agenda item extraction...")
        response = client.chat.completions.create(**response_args)
        raw_output = response.choices[0].message.content.strip()
        logging.info("Received response from Azure OpenAI.")
        logging.debug(f"Raw LLM Output:\n{raw_output}")
        structured_output = json.loads(raw_output)
        if not isinstance(structured_output, dict): raise ValueError("LLM output is not a JSON object.")
        if "agendaItems" not in structured_output or not isinstance(structured_output["agendaItems"], list):
             logging.warning("LLM output missing 'agendaItems' list. Assuming no items found.")
             if "meetingTitle" not in structured_output: structured_output["meetingTitle"] = "Meeting Part"
             if "meetingDate" not in structured_output: structured_output["meetingDate"] = ""
             structured_output["agendaItems"] = []
        valid_items = []
        for item in structured_output.get("agendaItems", []):
            if all(k in item for k in ["title", "startTimestamp", "endTimestamp", "summary"]):
                 if parse_timestamp(item["startTimestamp"]) is not None and parse_timestamp(item["endTimestamp"]) is not None:
                      valid_items.append(item)
                 else: logging.warning(f"Agenda item has invalid timestamp format: {item}. Skipping.")
            else: logging.warning(f"Agenda item missing required keys: {item}. Skipping.")
        structured_output["agendaItems"] = valid_items
        return structured_output
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from LLM response: {e}\nRaw Output: {raw_output}")
        return None
    except Exception as e:
        logging.error(f"Error during LLM processing or response handling: {e}")
        return None


def get_transcript_lines_with_timestamps(transcript_paths):
    """Reads all transcript files and returns a list of lines with timestamps."""
    all_lines = []
    global_line_index = 0
    last_valid_timestamp_sec = None
    first_valid_timestamp_sec = None

    for transcript_path in transcript_paths:
        logging.info(f"Reading transcript file for gap analysis: {transcript_path}")
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                for line_num, line_content in enumerate(f):
                    timestamp_str = extract_timestamp_from_line(line_content)
                    timestamp_sec = parse_timestamp(timestamp_str) if timestamp_str else None

                    current_line_timestamp_sec = timestamp_sec if timestamp_sec is not None else last_valid_timestamp_sec

                    if current_line_timestamp_sec is None and first_valid_timestamp_sec is None:
                        logging.debug(f"Skipping line {line_num+1} in {transcript_path} (no timestamp found yet)")
                        continue # Skip lines before any timestamp is found

                    if timestamp_sec is not None:
                         last_valid_timestamp_sec = timestamp_sec
                         if first_valid_timestamp_sec is None:
                              first_valid_timestamp_sec = timestamp_sec

                    all_lines.append({
                        'lineIndex': global_line_index,
                        'content': line_content,
                        'timestampSec': current_line_timestamp_sec if current_line_timestamp_sec is not None else -1, # Use -1 if still no timestamp
                        'timestampStr': timestamp_str # Store the original extracted string or None
                    })
                    global_line_index += 1
        except Exception as e:
            logging.error(f"Error reading transcript file {transcript_path}: {e}")
            continue

    # Filter out lines that couldn't be assigned a timestamp
    valid_lines = [line for line in all_lines if line['timestampSec'] != -1]
    if len(valid_lines) < len(all_lines):
         logging.warning(f"Discarded {len(all_lines) - len(valid_lines)} lines from start of transcript due to missing initial timestamps.")

    return valid_lines


def split_transcript_by_agenda(agenda_items, transcript_lines, output_dir):
    """Splits transcript lines into files based on adjusted agenda item timestamps."""
    logging.info(f"Splitting transcript into {len(agenda_items)} files based on adjusted timestamps...")
    os.makedirs(output_dir, exist_ok=True)

    # Add seconds to items for splitting
    for item in agenda_items:
         item['startSeconds'] = parse_timestamp(item['startTimestamp'])
         item['endSeconds'] = parse_timestamp(item['endTimestamp'])
         # Ensure seconds were parsed correctly
         if item['startSeconds'] is None or item['endSeconds'] is None:
              logging.error(f"Could not parse timestamps for item '{item['title']}' ({item['startTimestamp']} / {item['endTimestamp']}). Cannot split correctly.")
              # Handle this error - maybe skip the item? For now, set to 0
              item['startSeconds'] = 0
              item['endSeconds'] = 0

    item_content = {f"{i+1:02d}": [] for i in range(len(agenda_items))}

    # Assign lines to items based on the *final* adjusted timestamps
    for line in transcript_lines:
        line_ts_sec = line['timestampSec']
        assigned = False
        for i, item in enumerate(agenda_items):
            item_id = f"{i+1:02d}"
            # Check if line timestamp falls within the item's range (inclusive)
            if item['startSeconds'] <= line_ts_sec <= item['endSeconds']:
                item_content[item_id].append(line['content'])
                assigned = True
                break # Assign to the first matching item
        # if not assigned: # Should not happen if gaps were merged correctly
        #     logging.debug(f"Line at {line_ts_sec}s was not assigned to any item.")

    # Write files
    written_files_count = 0
    for i, item in enumerate(agenda_items):
        item_id = f"{i+1:02d}"
        content_lines = item_content[item_id]
        title = item['title']
        start_time = item['startTimestamp']
        end_time = item['endTimestamp']
        summary = item.get('summary', 'N/A')

        if not content_lines:
            logging.warning(f"No transcript lines found for item {item_id} ('{title}') in the final range {start_time}-{end_time}. Skipping file creation.")
            continue

        safe_title_part = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        max_len = 50
        if len(safe_title_part) > max_len: safe_title_part = safe_title_part[:max_len]
        if not safe_title_part: safe_title_part = f"item_{item_id}"

        file_name = f"{item_id}_{safe_title_part}.txt"
        file_path = os.path.join(output_dir, file_name)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Agenda Item: {title}\n")
                f.write(f"Original Time Range: {item.get('originalStartTimestamp', start_time)} - {item.get('originalEndTimestamp', end_time)}\n") # Show original if available
                f.write(f"Adjusted Time Range: {start_time} - {end_time}\n") # Show adjusted time
                f.write(f"Summary: {summary}\n")
                # f.write(f"Source Files Searched: {', '.join(map(os.path.basename, transcript_paths))}\n") # Need transcript_paths passed in
                f.write("\n--- TRANSCRIPT SECTION ---\n\n")
                cleaned_lines_written = 0
                for line_content in content_lines:
                    cleaned_line = remove_timestamp_from_line(line_content)
                    if cleaned_line.strip():
                        f.write(cleaned_line)
                        cleaned_lines_written += 1
            logging.info(f"Created item file: {file_path} ({cleaned_lines_written} cleaned lines)")
            written_files_count += 1
        except IOError as e:
            logging.error(f"Failed to write item file {file_path}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error writing file {file_path}: {e}")

    logging.info(f"Finished writing {written_files_count} item files.")


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Process meeting transcripts: extract agenda items, match titles, merge gaps, and split into segments.")
    parser.add_argument("--input_file", required=True, nargs='+', help="Path(s) to the meeting transcript file(s). Provide in order.")
    parser.add_argument("--context_file", help="Path to the context file (optional).")
    parser.add_argument("--agenda_file", help="Path to the planned agenda file (optional).")
    parser.add_argument("--output_file", required=True, help="Path for the consolidated JSON output (final items).")
    parser.add_argument("--output_dir", required=True, help="Directory for metadata and split transcript files (one per final item).")
    parser.add_argument("--prompt_file", default="src/prompts/system_prompt.txt", help="Path to the system prompt file.")
    parser.add_argument("--schema_file", default="src/schemas/agenda_schema.json", help="Path to the JSON schema file.")
    parser.add_argument("--config_file", default="src/config.ini", help="Path to the configuration file.")
    parser.add_argument("--match_threshold", type=int, default=85, help="Similarity threshold (0-100) for title matching (default: 85).")
    parser.add_argument("--gap_threshold_seconds", type=int, default=30, help="Minimum duration (seconds) for a gap between items to be merged (default: 30).")

    args = parser.parse_args()

    # --- Load Config, Schema, Init OpenAI Client ---
    # (Standard setup - unchanged)
    config = configparser.ConfigParser()
    try: config.read(args.config_file)
    except Exception as e: logging.error(f"Error reading config: {e}")
    response_settings = {
        'temperature': config.getfloat('response_settings', 'temperature', fallback=0.1), # Slightly lower temp may help consistency
        'max_tokens': config.getint('response_settings', 'max_tokens', fallback=8000), # Increase if needed for full coverage
        'top_p': config.getfloat('response_settings', 'top_p', fallback=1.0),
        'frequency_penalty': config.getfloat('response_settings', 'frequency_penalty', fallback=0.0),
        'presence_penalty': config.getfloat('response_settings', 'presence_penalty', fallback=0.0)
    }
    json_schema = None
    try:
        with open(args.schema_file, 'r', encoding='utf-8') as f: json_schema = json.load(f)
        logging.info(f"Loaded JSON schema from {args.schema_file}")
    except Exception as e: logging.error(f"Error loading schema {args.schema_file}: {e}")
    try:
        model = os.environ.get('MODEL', 'o3-mini')
        client = AzureOpenAI(
            api_key=os.environ['OPENAI_API_KEY'], api_version=os.environ['API_VERSION'],
            azure_endpoint=os.environ['OPENAI_API_BASE'], organization=os.environ.get('OPENAI_ORGANIZATION')
        )
        logging.info(f"Using model: {model} via endpoint: {os.environ['OPENAI_API_BASE']}")
    except Exception as e:
        logging.error(f"Error initializing AzureOpenAI client: {e}")
        return

    # --- Load Context, Agenda, Prompt ---
    # (Standard loading - unchanged)
    context = load_file_content(args.context_file) if args.context_file else ""
    agenda_content = load_file_content(args.agenda_file) if args.agenda_file else ""
    agenda_titles = parse_agenda_titles(agenda_content) if agenda_content else []
    try:
        # Use the UPDATED prompt from step 1 above
        system_prompt = load_system_prompt(args.prompt_file, context, agenda_content)
        logging.info(f"Loaded system prompt from: {args.prompt_file}")
    except Exception as e:
         logging.error(f"Failed to load system prompt: {e}")
         return

    # --- LLM Extraction ---
    # (Collects raw items - unchanged)
    all_llm_extracted_items = []
    combined_meeting_info = {}
    processed_any_successfully = False
    for i, input_file_path in enumerate(args.input_file):
        logging.info(f"--- Processing Transcript Part {i+1} for LLM Extraction: {input_file_path} ---")
        transcript_content = load_file_content(input_file_path)
        if not transcript_content: continue
        structured_output_part = extract_agenda_items_from_content(
            system_prompt, transcript_content, model, response_settings, json_schema, client
        )
        if structured_output_part and isinstance(structured_output_part.get("agendaItems"), list):
            items_in_part = structured_output_part["agendaItems"]
            logging.info(f"LLM extracted {len(items_in_part)} raw agenda items from {input_file_path}.")
            all_llm_extracted_items.extend(items_in_part)
            if not combined_meeting_info:
                 combined_meeting_info['meetingTitle'] = structured_output_part.get('meetingTitle', 'Meeting')
                 combined_meeting_info['meetingDate'] = structured_output_part.get('meetingDate', 'Unknown')
                 logging.info(f"Set meeting title/date from {input_file_path}.")
            processed_any_successfully = True
        else: logging.warning(f"LLM failed to extract valid items from {input_file_path}.")

    if not processed_any_successfully:
         logging.error("LLM failed to process any input files. No output generated.")
         return
    if not all_llm_extracted_items:
        logging.warning("LLM did not extract any agenda items.")
        final_agenda_items = []
    else:
         # --- Post-LLM Processing ---
         # 1. Sort items chronologically
         valid_llm_items = []
         for item in all_llm_extracted_items:
              item['startSeconds'] = parse_timestamp(item.get('startTimestamp'))
              item['endSeconds'] = parse_timestamp(item.get('endTimestamp'))
              if item['startSeconds'] is not None and item['endSeconds'] is not None and item['endSeconds'] >= item['startSeconds']:
                   valid_llm_items.append(item)
              else:
                   logging.warning(f"Removing item with invalid timestamps before sorting: {item.get('title')}")
         valid_llm_items.sort(key=lambda x: x['startSeconds'])
         logging.info(f"Sorted {len(valid_llm_items)} valid LLM items.")

         # 2. --- NEW: Gap Analysis and Merging ---
         items_after_gap_merge = []
         if len(valid_llm_items) > 0:
             # Add first item
             items_after_gap_merge.append(valid_llm_items[0])
             # Iterate through items to find gaps between them
             for i in range(len(valid_llm_items) - 1):
                 prev_item = items_after_gap_merge[-1] # Previous item *after potential merge*
                 curr_item = valid_llm_items[i+1]

                 gap_start_sec = prev_item['endSeconds']
                 gap_end_sec = curr_item['startSeconds']
                 gap_duration = gap_end_sec - gap_start_sec

                 if gap_duration > args.gap_threshold_seconds:
                     logging.warning(f"Found large gap ({gap_duration}s > {args.gap_threshold_seconds}s) between '{prev_item['title']}' (ends {prev_item['endTimestamp']}) and '{curr_item['title']}' (starts {curr_item['startTimestamp']}).")
                     # Merge gap into PREVIOUS item by extending its end time
                     new_end_sec = gap_end_sec - 1 # End just before the next item starts
                     if new_end_sec > prev_item['endSeconds']: # Ensure we are actually extending
                          new_end_timestamp_str = format_timestamp_from_seconds(new_end_sec)
                          logging.info(f"Extending end time of '{prev_item['title']}' from {prev_item['endTimestamp']} to {new_end_timestamp_str} to absorb gap.")
                          # Store original times for reference if needed
                          prev_item['originalEndTimestamp'] = prev_item['endTimestamp']
                          prev_item['originalEndSeconds'] = prev_item['endSeconds']
                          # Update the item
                          prev_item['endTimestamp'] = new_end_timestamp_str
                          prev_item['endSeconds'] = new_end_sec
                          # Add a note to the summary?
                          prev_item['summary'] = prev_item.get('summary','') + " [Note: Timestamp extended to include subsequent gap.]"
                     else:
                          logging.info(f"Gap detected but calculated new end time {new_end_sec}s is not after previous end {prev_item['endSeconds']}s. No merge performed.")
                     # Add the current item (which marks the end of the gap)
                     items_after_gap_merge.append(curr_item)
                 else:
                     # Gap is small or non-existent, just add the current item
                     items_after_gap_merge.append(curr_item)
             logging.info(f"Finished gap analysis. Item count: {len(items_after_gap_merge)}")
         else:
             items_after_gap_merge = valid_llm_items # No items, so no gaps

         # 3. Fuzzy Match Titles (on the potentially gap-merged items)
         if agenda_titles:
             logging.info(f"Attempting title matching for {len(items_after_gap_merge)} items...")
             matched_official_titles = set()
             for item in items_after_gap_merge:
                  original_title = item.get('title', '')
                  if not original_title: continue
                  available_titles = [t for t in agenda_titles if t not in matched_official_titles]
                  if not available_titles: break
                  best_match, score = fuzz_process.extractOne(original_title, available_titles, scorer=fuzz.ratio)
                  if score >= args.match_threshold:
                       logging.info(f"Matched title '{original_title}' to '{best_match}' (Score: {score}). Replacing.")
                       item['title'] = best_match # Replace title
                       matched_official_titles.add(best_match)
                  else:
                       logging.info(f"No confident match for title '{original_title}' (Best: '{best_match}', Score: {score}). Keeping.")
             logging.info(f"Finished title matching. {len(matched_official_titles)} official titles matched.")
         else:
             logging.info("No official agenda titles provided. Skipping title matching.")

         final_agenda_items = items_after_gap_merge # These are the final items


    # --- Save Final JSON Output ---
    final_json_output_structure = {
        "meetingTitle": combined_meeting_info.get('meetingTitle'),
        "meetingDate": combined_meeting_info.get('meetingDate'),
        # Store only the final items in the JSON, remove temporary seconds keys
        "agendaItems": [
             {k: v for k, v in item.items() if k not in ['startSeconds', 'endSeconds', 'originalEndSeconds']}
             for item in final_agenda_items
        ],
        # Initialize empty next_meeting and adjournment fields that will be filled by consolidate_json.py
        "next_meeting": {
            "date": "",
            "time": "",
            "location": ""
        },
        "adjournment": {
            "time": ""
        }
    }
    try:
        output_json_dir = os.path.dirname(args.output_file)
        if output_json_dir: os.makedirs(output_json_dir, exist_ok=True)
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(final_json_output_structure, f, indent=4)
        logging.info(f"Consolidated JSON for final agenda items saved to {args.output_file}")
    except Exception as e:
         logging.error(f"Failed to write consolidated JSON output: {e}")

    # --- Split Transcript Based on Final Agenda Items ---
    if final_agenda_items:
         logging.info("Reading full transcript for splitting...")
         transcript_lines = get_transcript_lines_with_timestamps(args.input_file)
         if transcript_lines:
              split_transcript_by_agenda(
                   agenda_items=final_agenda_items, # Use final, gap-merged items
                   transcript_lines=transcript_lines,
                   output_dir=args.output_dir
              )
              # --- Create metadata file (00_meeting_info.txt) ---
              metadata_path = os.path.join(args.output_dir, '00_meeting_info.txt')
              try:
                   with open(metadata_path, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {combined_meeting_info.get('meetingTitle', 'Meeting')}\n")
                        f.write(f"Date: {combined_meeting_info.get('meetingDate', 'Unknown Date')}\n")
                        f.write(f"Final Agenda Items Found: {len(final_agenda_items)}\n")
                        f.write(f"Source Transcript Files: {', '.join(args.input_file)}\n\n")
                        f.write("--- Final Agenda Items (after gap merging and title matching) ---\n")
                        for i, item in enumerate(final_agenda_items):
                             title = item['title']
                             start_ts = item['startTimestamp']
                             end_ts = item['endTimestamp']
                             f.write(f"\n{i+1:02d}. {title}\n")
                             f.write(f"   Time: {start_ts} - {end_ts}\n")
                             if 'originalEndTimestamp' in item:
                                  f.write(f"   (Original End: {item['originalEndTimestamp']})\n")
                   logging.info(f"Created final metadata file: {metadata_path}")
              except IOError as e: logging.error(f"Failed to write metadata file: {e}")
         else:
              logging.error("Could not read transcript lines for splitting.")
    else:
         logging.warning("No final agenda items to process for splitting.")


    logging.info("Script finished.")


if __name__ == "__main__":
    main()
    