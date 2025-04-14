#!/usr/bin/env python3
"""
Consolidate JSON - Utility to merge multiple agenda item JSON files into a single meeting minutes JSON.

This script takes multiple JSON files from processed agenda items and combines them into a single 
JSON that follows the minutes_schema.JSON structure. It preserves the meeting structure while 
consolidating individual sections into a coherent document.
"""

import argparse
import json
import os
import logging
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Consolidate multiple JSON files into a single meeting minutes JSON file.")
    parser.add_argument("--input_files", required=True, nargs='+', help="Paths to input JSON files")
    parser.add_argument("--output_file", required=True, help="Path to output consolidated JSON file")
    parser.add_argument("--meeting_title", required=True, help="Title of the meeting")
    parser.add_argument("--meeting_date", help="Date of the meeting (YYYY-MM-DD)")
    parser.add_argument("--meeting_time", help="Time of the meeting")
    parser.add_argument("--meeting_location", help="Location of the meeting")
    
    # Next meeting arguments
    parser.add_argument("--next_meeting_date", help="Date of the next meeting (YYYY-MM-DD)")
    parser.add_argument("--next_meeting_time", help="Time of the next meeting")
    parser.add_argument("--next_meeting_location", help="Location of the next meeting")
    
    return parser.parse_args()

def load_json_file(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return None

def create_base_structure(args):
    """Create the base structure for the consolidated JSON."""
    today = datetime.datetime.now().strftime("%Y%m%d")
    
    # Prepare next meeting info if available from command line
    next_meeting = {}
    if hasattr(args, 'next_meeting_date') and args.next_meeting_date:
        next_meeting["date"] = args.next_meeting_date
    else:
        next_meeting["date"] = ""
        
    if hasattr(args, 'next_meeting_time') and args.next_meeting_time:
        next_meeting["time"] = args.next_meeting_time
    else:
        next_meeting["time"] = ""
        
    if hasattr(args, 'next_meeting_location') and args.next_meeting_location:
        next_meeting["location"] = args.next_meeting_location
    else:
        next_meeting["location"] = ""
    
    return {
        "meeting_details": {
            "title": args.meeting_title,
            "date": args.meeting_date or today,
            "time": args.meeting_time or "00:00",
            "location": args.meeting_location or "Unknown",
            "attendees": [],
            "absentees": []
        },
        "sections": [],
        "next_meeting": next_meeting,
        "adjournment": {
            "time": ""
        },
        "reflection": "",
        "references": []
    }

def consolidate_attendees(json_files):
    """Combine attendees from all JSON files without duplicates."""
    all_attendees = []
    all_absentees = []
    seen_attendees = set()
    seen_absentees = set()
    
    for json_data in json_files:
        if not json_data or not isinstance(json_data, dict):
            continue
            
        meeting_details = json_data.get("meeting_details", {})
        
        # Process attendees
        for attendee in meeting_details.get("attendees", []):
            if not isinstance(attendee, dict):
                continue
                
            first_name = attendee.get("first_name", "")
            last_name = attendee.get("last_name", "")
            
            if not first_name or not last_name:
                continue
                
            attendee_key = f"{first_name}|{last_name}".lower()
            
            if attendee_key not in seen_attendees:
                seen_attendees.add(attendee_key)
                all_attendees.append(attendee)
        
        # Process absentees
        for absentee in meeting_details.get("absentees", []):
            if not isinstance(absentee, dict):
                continue
                
            first_name = absentee.get("first_name", "")
            last_name = absentee.get("last_name", "")
            
            if not first_name or not last_name:
                continue
                
            absentee_key = f"{first_name}|{last_name}".lower()
            
            if absentee_key not in seen_absentees:
                seen_absentees.add(absentee_key)
                all_absentees.append(absentee)
    
    return all_attendees, all_absentees

def consolidate_references(json_files):
    """Combine references from all JSON files without duplicates."""
    all_references = []
    seen_refs = set()
    
    for json_data in json_files:
        if not json_data or not isinstance(json_data, dict):
            continue
            
        for ref in json_data.get("references", []):
            if not isinstance(ref, dict):
                continue
                
            title = ref.get("title", "")
            ref_type = ref.get("reference_type", "")
            identifier = ref.get("identifier", "")
            
            if not title:
                continue
                
            ref_key = f"{title}|{ref_type}|{identifier}".lower()
            
            if ref_key not in seen_refs:
                seen_refs.add(ref_key)
                all_references.append(ref)
    
    return all_references

def extract_next_meeting_info(json_files, args=None):
    """
    Extract next meeting information. 
    Command line arguments take precedence, then look at JSON files.
    """
    # If we have command line arguments with next meeting info, use those
    if args and hasattr(args, 'next_meeting_date') and args.next_meeting_date:
        next_meeting = {
            "date": args.next_meeting_date,
            "time": args.next_meeting_time if hasattr(args, 'next_meeting_time') and args.next_meeting_time else "",
            "location": args.next_meeting_location if hasattr(args, 'next_meeting_location') and args.next_meeting_location else ""
        }
        return next_meeting
    
    # Otherwise, look in the processed JSON files
    for json_data in json_files:
        if not json_data or not isinstance(json_data, dict):
            continue
            
        next_meeting = json_data.get("next_meeting", {})
        
        if next_meeting and isinstance(next_meeting, dict):
            date_val = next_meeting.get("date", "")
            time_val = next_meeting.get("time", "")
            location_val = next_meeting.get("location", "")
            
            if date_val and time_val:
                return next_meeting
    
    # Default if no next meeting info found
    return {"date": "", "time": "", "location": ""}

def extract_adjournment_info(json_files):
    """Extract adjournment information from any JSON file that has it."""
    for json_data in json_files:
        if not json_data or not isinstance(json_data, dict):
            continue
            
        adjournment = json_data.get("adjournment", {})
        
        if adjournment and isinstance(adjournment, dict) and adjournment.get("time", ""):
            return adjournment
    
    # Default if no adjournment info found
    return {"time": ""}

def combine_reflection(json_files):
    """Combine reflection text from all JSON files."""
    reflections = []
    
    for json_data in json_files:
        if not json_data or not isinstance(json_data, dict):
            continue
            
        reflection = json_data.get("reflection", "")
        
        if reflection and isinstance(reflection, str) and reflection.strip():
            reflections.append(reflection.strip())
    
    if not reflections:
        return "No reflection available."
    
    if len(reflections) == 1:
        return reflections[0]
    
    # Combine multiple reflections
    return "Meeting Reflection: " + " ".join(reflections)

def main():
    """Main function to consolidate JSON files."""
    args = parse_arguments()
    
    # Load all JSON files
    json_files = []
    for file_path in args.input_files:
        json_data = load_json_file(file_path)
        if json_data:
            json_files.append(json_data)
    
    if not json_files:
        logging.error("No valid JSON files were loaded. Exiting.")
        return
    
    logging.info(f"Loaded {len(json_files)} JSON files out of {len(args.input_files)} provided.")
    
    # Create the base structure for the consolidated JSON
    consolidated_json = create_base_structure(args)
    
    # Sort input files by their filenames to maintain agenda order
    sorted_inputs = sorted(zip(args.input_files, json_files), 
                          key=lambda x: int(os.path.basename(x[0]).split('_')[0]))
    
    # Extract sections from each file in order
    for file_path, json_data in sorted_inputs:
        if not json_data or not isinstance(json_data, dict):
            continue
        
        logging.info(f"Processing {os.path.basename(file_path)}")
        
        # Each agenda item JSON may have multiple sections, but we're primarily interested in the 
        # first section which should correspond to the agenda item
        if 'sections' in json_data and json_data['sections']:
            for section in json_data['sections']:
                if isinstance(section, dict):
                    consolidated_json['sections'].append(section)
    
    # Consolidate attendees and absentees
    consolidated_json['meeting_details']['attendees'], consolidated_json['meeting_details']['absentees'] = \
        consolidate_attendees(json_files)
    
    # Consolidate references
    consolidated_json['references'] = consolidate_references(json_files)
    
    # Extract next meeting info - command line args take precedence
    consolidated_json['next_meeting'] = extract_next_meeting_info(json_files, args)
    
    # Extract adjournment info
    consolidated_json['adjournment'] = extract_adjournment_info(json_files)
    
    # Combine reflection text
    consolidated_json['reflection'] = combine_reflection(json_files)
    
    # Write consolidated JSON to output file
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated_json, f, indent=2)
        logging.info(f"Successfully wrote consolidated JSON to {args.output_file}")
    except Exception as e:
        logging.error(f"Error writing consolidated JSON: {e}")

if __name__ == "__main__":
    main()