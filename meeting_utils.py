import os
import re
import glob
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

def round_time_to_15_min(time_obj):
    """Round time down to the closest 15-minute mark."""
    minute = time_obj.minute
    rounded_minute = (minute // 15) * 15
    return time_obj.replace(minute=rounded_minute, second=0, microsecond=0)

class ZoomMeetingScanner:
    """Utility class for scanning Zoom meetings and extracting information."""
    
    def __init__(self, zoom_dir="~/Documents/Zoom"):
        self.zoom_dir = os.path.expanduser(zoom_dir)
        
    def get_latest_meetings(self, limit=5):
        """Get the latest Zoom meetings sorted by date.
        
        Args:
            limit: Number of meetings to return. If None, returns all meetings.
        """
        meetings = []
        
        if not os.path.exists(self.zoom_dir):
            return meetings
            
        try:
            # Get all directories in Zoom folder
            for item in os.listdir(self.zoom_dir):
                item_path = os.path.join(self.zoom_dir, item)
                if os.path.isdir(item_path):
                    # Check if it contains meeting_saved_closed_caption.txt
                    caption_file = os.path.join(item_path, "meeting_saved_closed_caption.txt")
                    if os.path.exists(caption_file):
                        meeting_info = self._extract_meeting_info(item, item_path)
                        if meeting_info:
                            meetings.append(meeting_info)
        except PermissionError as e:
            # Handle macOS privacy restrictions
            print(f"Permission denied accessing Zoom folder: {e}")
            print("To fix this issue:")
            print("1. Go to System Preferences > Security & Privacy > Privacy")
            print("2. Select 'Files and Folders' on the left")
            print("3. Find Terminal (or Python) in the list and check 'Documents Folder'")
            print("4. Restart the application")
            # Return empty list so the app continues to work
            return meetings
        except Exception as e:
            print(f"Error accessing Zoom meetings: {e}")
            return meetings
        
        # Sort by date (most recent first)
        meetings.sort(key=lambda x: x['datetime'], reverse=True)
        return meetings[:limit] if limit is not None else meetings
    
    def _extract_meeting_info(self, folder_name, folder_path):
        """Extract meeting information from folder name and contents."""
        # Parse folder name: "2025-03-27 10.14.08 COMPASS PI Meeting"
        match = re.match(r'(\d{4}-\d{2}-\d{2}) (\d{2}\.\d{2}\.\d{2}) (.+)', folder_name)
        if not match:
            return None
            
        date_str, time_str, meeting_name = match.groups()
        
        # Convert time format from HH.MM.SS to HH:MM:SS
        time_str = time_str.replace('.', ':')
        
        try:
            datetime_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            # Round time down to closest 15-minute mark
            datetime_obj = round_time_to_15_min(datetime_obj)
        except ValueError:
            return None
            
        caption_file = os.path.join(folder_path, "meeting_saved_closed_caption.txt")
        
        # Extract participants from transcript
        participants = self._extract_participants(caption_file)
        
        return {
            'folder_name': folder_name,
            'folder_path': folder_path,
            'meeting_name': meeting_name,
            'date': date_str,
            'time': datetime_obj.strftime("%H:%M:%S"),  # Use rounded time
            'datetime': datetime_obj,
            'participants': participants,
            'transcript_file': caption_file
        }
    
    def _extract_participants(self, caption_file):
        """Extract participant names from the caption file."""
        participants = set()
        
        try:
            with open(caption_file, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Look for speaker patterns like "[Speaker Name] timestamp"
            # This pattern matches: [Name] HH:MM:SS or [Name] HH:MM:SS AM/PM
            speaker_pattern = r'\[([^\]]+)\]\s+\d{1,2}:\d{2}:\d{2}'
            matches = re.findall(speaker_pattern, content)
            
            for match in matches:
                name = match.strip()
                # Filter out common non-name patterns
                if (len(name) > 1 and 
                    not name.lower() in ['transcript', 'recording', 'meeting', 'zoom'] and
                    not re.match(r'^\d+$', name)):
                    participants.add(name)
            
            # Fallback: try the original pattern for other formats
            if not participants:
                speaker_pattern = r'^([A-Za-z\s]+):\s'
                matches = re.findall(speaker_pattern, content, re.MULTILINE)
                
                for match in matches:
                    name = match.strip()
                    if (len(name) > 1 and 
                        not name.lower() in ['transcript', 'recording', 'meeting', 'zoom'] and
                        not re.match(r'^\d+$', name)):
                        participants.add(name)
                    
        except Exception as e:
            print(f"Error reading caption file {caption_file}: {e}")
            
        return sorted(list(participants))
    
    def generate_auto_agenda(self, meeting_info):
        """Generate an auto-agenda based on meeting information."""
        meeting_name = meeting_info['meeting_name']
        date_str = meeting_info['date']
        time_str = meeting_info['time']
        participants = meeting_info['participants']
        
        # Format date and time
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
        except ValueError:
            formatted_date = date_str
            
        try:
            time_obj = datetime.strptime(time_str, "%H:%M:%S")
            # Round time down to closest 15-minute mark
            time_obj = round_time_to_15_min(time_obj)
            formatted_time = time_obj.strftime("%I:%M %p")
        except ValueError:
            formatted_time = time_str
            
        # Create agenda content
        agenda_content = f"""# {meeting_name}

{formatted_date}, {formatted_time}

Attendees: {', '.join(participants)}

## Agenda

No agenda items were submitted for this meeting. Please derive from the transcript.

## Next meeting
Next meeting: {meeting_name}
Scheduled: TBD
Location: TBD
"""
        
        return agenda_content


class ContextManager:
    """Manages context files for different meeting types."""
    
    def __init__(self, context_dir="../MeetingSecretaryAI_Data/context/"):
        self.context_dir = os.path.expanduser(context_dir)
        
    def get_available_contexts(self):
        """Get list of available context files."""
        contexts = []
        
        if not os.path.exists(self.context_dir):
            return contexts
            
        for file in os.listdir(self.context_dir):
            if file.endswith('.md'):
                context_name = file[:-3]  # Remove .md extension
                contexts.append({
                    'name': context_name,
                    'file_path': os.path.join(self.context_dir, file),
                    'display_name': context_name.replace('_', ' ')
                })
                
        return sorted(contexts, key=lambda x: x['display_name'])
    
    def get_context_content(self, context_file):
        """Get content of a specific context file."""
        try:
            with open(context_file, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading context file {context_file}: {e}")
            return ""


class TokenManager:
    """Manages HuggingFace token for WhisperX."""
    
    def __init__(self, token_file="../MeetingSecretaryAI_Data/.hf_token.txt"):
        self.token_file = os.path.expanduser(token_file)
        
    def get_token(self):
        """Get the HuggingFace token."""
        try:
            with open(self.token_file, 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error reading token file: {e}")
            return None
    
    def set_token(self, token):
        """Save the HuggingFace token."""
        try:
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, 'w') as file:
                file.write(token.strip())
            return True
        except Exception as e:
            print(f"Error saving token: {e}")
            return False


class AudioProcessor:
    """Handles audio processing with WhisperX."""
    
    def __init__(self, token_manager):
        self.token_manager = token_manager
        
    def process_audio(self, audio_file, output_dir, callback=None):
        """Process audio file with WhisperX."""
        import subprocess
        import threading
        
        token = self.token_manager.get_token()
        if not token:
            raise ValueError("HuggingFace token not found. Please set it in the settings.")
            
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # WhisperX command - try to find the correct whisperx executable
        import shutil
        whisperx_path = shutil.which("whisperx")
        if not whisperx_path:
            # Try the expected path in the meetingsecretaryai_env environment
            whisperx_path = "/Users/larsf/miniforge3/envs/meetingsecretaryai_env/bin/whisperx"
            if not os.path.exists(whisperx_path):
                # Fallback to trying to find it in the current Python environment
                import sys
                python_dir = os.path.dirname(sys.executable)
                whisperx_path = os.path.join(python_dir, "whisperx")
                if not os.path.exists(whisperx_path):
                    whisperx_path = "whisperx"  # Last resort - use system PATH
        
        cmd = [
            whisperx_path, audio_file,
            "--model", "large-v3",
            "--diarize",
            "--hf_token", token,
            "--language", "en",
            "--device", "cpu",
            "--compute_type", "int8",
            "--batch_size", "16",
            "--output_dir", output_dir,
            "--threads", "8"
        ]
        
        def run_whisperx():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                if callback:
                    callback(True, "Audio processing completed successfully")
            except subprocess.CalledProcessError as e:
                error_msg = f"WhisperX failed: {e.stderr}"
                if callback:
                    callback(False, error_msg)
            except Exception as e:
                error_msg = f"Error running WhisperX: {str(e)}"
                if callback:
                    callback(False, error_msg)
        
        # Run in separate thread
        thread = threading.Thread(target=run_whisperx, daemon=True)
        thread.start()
        
        return thread
