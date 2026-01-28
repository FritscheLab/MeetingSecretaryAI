import os
import re
import glob
import configparser
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

CONFIG_ENV_VAR = "MEETING_SECRETARY_CONFIG"
DEFAULT_CONFIG_NAME = "config.ini"
_WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")
CONFIG_PERSIST_FILE = Path.home() / ".meeting_secretary_config"


def resolve_config_path(config_path=None):
    """Resolve the config path, honoring MEETING_SECRETARY_CONFIG if set."""
    env_path = os.environ.get(CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser()
    if config_path:
        return Path(config_path).expanduser()
    persisted = get_persisted_config_path()
    if persisted:
        return persisted
    return Path(__file__).resolve().parent / DEFAULT_CONFIG_NAME


def get_persisted_config_path():
    """Return a persisted config path if available."""
    try:
        if CONFIG_PERSIST_FILE.exists():
            value = CONFIG_PERSIST_FILE.read_text(encoding="utf-8").strip()
            if value:
                return Path(value).expanduser()
    except Exception:
        return None
    return None


def set_persisted_config_path(config_path):
    """Persist the config path for future launches."""
    try:
        CONFIG_PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PERSIST_FILE.write_text(f"{config_path}\n", encoding="utf-8")
        return True
    except Exception as exc:
        print(f"Warning: failed to persist config path: {exc}")
        return False


def _config_get(config, section, option, fallback=None):
    try:
        value = config.get(section, option, fallback=fallback)
    except (configparser.Error, KeyError, ValueError):
        return fallback
    if value is None:
        return fallback
    value = str(value).strip()
    return value if value else fallback


def _is_windows_abs(path_value):
    return bool(_WINDOWS_ABS_RE.match(path_value)) or path_value.startswith("\\\\")


def _resolve_path(value, base_dir):
    if not value:
        return None
    expanded = os.path.expandvars(os.path.expanduser(value))
    if os.path.isabs(expanded) or _is_windows_abs(expanded):
        return expanded
    return os.path.abspath(os.path.join(base_dir, expanded))


def load_app_config(config_path=None):
    """Load config.ini (or override) and return (config, config_path)."""
    config_path = resolve_config_path(config_path)
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path)
    return config, config_path


def get_app_paths(config_path=None):
    """Resolve commonly used paths from config with sensible defaults."""
    config, config_path = load_app_config(config_path)
    base_dir = str(config_path.parent)

    data_dir = _resolve_path(
        _config_get(config, "paths", "data_dir", "../MeetingSecretaryAI_Data"),
        base_dir,
    )
    zoom_dir = _resolve_path(
        _config_get(config, "paths", "zoom_dir", "~/Documents/Zoom"),
        base_dir,
    )
    context_dir = _resolve_path(
        _config_get(config, "paths", "context_dir", os.path.join(data_dir, "context")),
        base_dir,
    )
    output_dir = _resolve_path(
        _config_get(config, "paths", "output_dir", os.path.join(data_dir, "output")),
        base_dir,
    )
    token_file = _resolve_path(
        _config_get(config, "paths", "token_file", os.path.join(data_dir, ".hf_token.txt")),
        base_dir,
    )

    return {
        "config_path": str(config_path),
        "data_dir": data_dir,
        "zoom_dir": zoom_dir,
        "context_dir": context_dir,
        "output_dir": output_dir,
        "token_file": token_file,
    }

def round_time_to_15_min(time_obj):
    """Round time down to the closest 15-minute mark."""
    minute = time_obj.minute
    rounded_minute = (minute // 15) * 15
    return time_obj.replace(minute=rounded_minute, second=0, microsecond=0)

class ZoomMeetingScanner:
    """Utility class for scanning Zoom meetings and extracting information."""
    
    def __init__(self, zoom_dir=None, config_path=None):
        if zoom_dir is None:
            zoom_dir = get_app_paths(config_path).get("zoom_dir")
        self.zoom_dir = os.path.expanduser(zoom_dir) if zoom_dir else ""
        if self.zoom_dir and not os.path.exists(self.zoom_dir):
            print(f"Warning: Zoom directory not found at {self.zoom_dir}")
        
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
                    vtt_files = sorted(glob.glob(os.path.join(item_path, "*.vtt")))
                    txt_files = sorted(glob.glob(os.path.join(item_path, "meeting_saved_closed_caption.txt")))
                    transcript_candidates = vtt_files + txt_files
                    if transcript_candidates:
                        transcript_file = transcript_candidates[0]
                        meeting_info = self._extract_meeting_info(item, item_path, transcript_file)
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
    
    def _extract_meeting_info(self, folder_name, folder_path, transcript_file):
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
            
        # Extract participants from transcript
        participants = self._extract_participants(transcript_file)
        
        return {
            'folder_name': folder_name,
            'folder_path': folder_path,
            'meeting_name': meeting_name,
            'date': date_str,
            'time': datetime_obj.strftime("%H:%M:%S"),  # Use rounded time
            'datetime': datetime_obj,
            'participants': participants,
            'transcript_file': transcript_file
        }
    
    def _extract_participants(self, caption_file):
        """Extract participant names from the caption file."""
        participants = set()
        
        try:
            with open(caption_file, 'r', encoding='utf-8', errors='replace') as file:
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

No agenda items were submitted for this meeting. Please derive agenda items and action items from the transcript.

## Next meeting
Next meeting: {meeting_name}
Scheduled: Derive from transcript otherwise TBD
Location: Derive from transcript otherwise TBD
"""
        
        return agenda_content


class ContextManager:
    """Manages context files for different meeting types."""
    
    def __init__(self, context_dir=None, config_path=None):
        if context_dir is None:
            context_dir = get_app_paths(config_path).get("context_dir")
        self.context_dir = os.path.expanduser(context_dir) if context_dir else ""
        
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
    
    def __init__(self, token_file=None, config_path=None):
        if token_file is None:
            token_file = get_app_paths(config_path).get("token_file")
        self.token_file = os.path.expanduser(token_file) if token_file else ""
        
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

    @staticmethod
    def _coerce_int(value, default):
        try:
            return int(value)
        except Exception:
            return default

    @staticmethod
    def _coerce_bool(value, default):
        if value is None:
            return default
        return str(value).strip().lower() not in ("0", "false", "no", "off")

    @staticmethod
    def _maybe_transcode_audio(audio_file, output_dir):
        """Downsample large audio files to 16kHz mono to reduce size and memory pressure."""
        import os
        import shutil
        import subprocess
        from pathlib import Path

        if not AudioProcessor._coerce_bool(os.environ.get("WHISPERX_TRANSCODE"), True):
            return audio_file

        try:
            size_mb = os.path.getsize(audio_file) / (1024 * 1024)
        except OSError:
            return audio_file

        try:
            threshold_mb = float(os.environ.get("WHISPERX_TRANSCODE_MB", "500"))
        except ValueError:
            threshold_mb = 500.0
        if size_mb < threshold_mb:
            return audio_file

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            print("ffmpeg not found; skipping audio transcode.")
            return audio_file

        target_rate = os.environ.get("WHISPERX_TRANSCODE_RATE", "16000")
        target_format = os.environ.get("WHISPERX_TRANSCODE_FORMAT", "flac").lower()
        if target_format not in ("flac", "wav"):
            target_format = "flac"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{Path(audio_file).stem}.whisperx_16k.{target_format}"

        try:
            if output_path.exists() and output_path.stat().st_size > 0:
                return str(output_path)
        except OSError:
            pass

        cmd = [
            ffmpeg_path,
            "-y",
            "-loglevel",
            "error",
            "-i",
            audio_file,
            "-ac",
            "1",
            "-ar",
            str(target_rate),
            "-sample_fmt",
            "s16",
            "-vn",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg transcode failed; using original audio. {e.stderr}")
            return audio_file

    @staticmethod
    def _auto_whisperx_settings():
        """Pick reasonable WhisperX CLI settings for the current machine.

        This aims for portable defaults across CPU-only Macs/PCs and CUDA machines.
        Users can override any setting via environment variables:
          - WHISPERX_MODEL
          - WHISPERX_DEVICE (cpu|cuda|auto)
          - WHISPERX_COMPUTE_TYPE (float16|float32|int8|int8_float32)
          - WHISPERX_BATCH_SIZE (int)
          - WHISPERX_THREADS (int)
          - WHISPERX_VAD_METHOD (pyannote|silero)
        """

        import os
        import platform

        cpu_count = os.cpu_count() or 4

        # Defaults that work well on CPU-only systems.
        settings = {
            "model": os.environ.get("WHISPERX_MODEL", "large-v3"),
            "device": os.environ.get("WHISPERX_DEVICE"),
            "compute_type": os.environ.get("WHISPERX_COMPUTE_TYPE"),
            "batch_size": os.environ.get("WHISPERX_BATCH_SIZE"),
            "threads": os.environ.get("WHISPERX_THREADS"),
            "vad_method": os.environ.get("WHISPERX_VAD_METHOD"),
        }

        # Autodetect device if not overridden.
        # IMPORTANT:
        # - WhisperX uses Faster-Whisper (CTranslate2) for ASR, which typically supports
        #   only "cpu" and "cuda" in many builds.
        # - WhisperX also uses torch.device(device) for VAD/pyannote, so values like
        #   "auto" will crash (torch has no "auto" device).
        if not settings["device"]:
            device = "cpu"
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
            except Exception:
                device = "cpu"
            settings["device"] = device

        # Validate device against the Faster-Whisper backend (CTranslate2) where possible.
        # If unsupported (e.g., "mps"), fall back to CPU.
        try:
            if settings["device"] not in ("cpu", "cuda"):
                settings["device"] = "cpu"
        except Exception:
            settings["device"] = "cpu"

        # Autodetect compute_type if not overridden.
        if not settings["compute_type"]:
            # CUDA generally benefits from float16.
            if settings["device"] == "cuda":
                settings["compute_type"] = "float16"
            else:
                # CPU: int8 is usually the best speed/quality tradeoff.
                settings["compute_type"] = "int8"

        # Autodetect batch_size if not overridden.
        if not settings["batch_size"]:
            # Conservative default for stability across machines.
            # Larger batch sizes can be faster but may increase memory pressure.
            settings["batch_size"] = str(16 if cpu_count >= 8 else 8)

        # Autodetect threads if not overridden.
        if not settings["threads"]:
            # WhisperX's --threads=0 lets torch choose; this is generally safest.
            # If you want to hard-pin threads, set WHISPERX_THREADS.
            settings["threads"] = "0"

        # VAD choice: default to silero for maximum compatibility.
        # (pyannote VAD model loading can be sensitive to torch serialization changes)
        if not settings["vad_method"]:
            settings["vad_method"] = "silero"

        # Normalize numeric fields to strings for CLI.
        settings["batch_size"] = str(AudioProcessor._coerce_int(settings["batch_size"], 8))
        settings["threads"] = str(AudioProcessor._coerce_int(settings["threads"], 0))
        return settings
        
    def process_audio(self, audio_file, output_dir, callback=None):
        """Process audio file with WhisperX."""
        import subprocess
        import threading
        
        token = self.token_manager.get_token()
        if not token:
            raise ValueError("HuggingFace token not found. Please set it in the settings.")
            
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        audio_file = self._maybe_transcode_audio(audio_file, output_dir)
        
        # WhisperX command - try to find the correct whisperx executable
        import shutil
        # Prefer the whisperx that matches the current Python interpreter first
        import sys
        python_dir = os.path.dirname(sys.executable)
        candidate = os.path.join(python_dir, "whisperx")
        if os.path.exists(candidate):
            whisperx_path = candidate
        else:
            # Then try PATH
            whisperx_path = shutil.which("whisperx")
            if not whisperx_path:
                # Last resort - let the system resolve from PATH
                whisperx_path = "whisperx"

        settings = self._auto_whisperx_settings()
        
        # Note: WhisperX uses Faster-Whisper (CTranslate2). Valid devices are typically: auto, cpu, cuda, rocm, metal.
        # "mps" is not supported here; use "auto" to let it select Metal if available, else fall back to CPU.
        cmd = [
            whisperx_path, audio_file,
            "--model", settings["model"],
            "--vad_method", settings["vad_method"],
            "--diarize",
            "--hf_token", token,
            "--language", "en",
            "--device", settings["device"],
            "--compute_type", settings["compute_type"],
            "--batch_size", settings["batch_size"],
            "--output_dir", output_dir,
            "--threads", settings["threads"],
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
