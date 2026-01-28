import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import subprocess
import os
import tempfile
import shutil
import datetime
import sys
from meeting_utils import (
    ZoomMeetingScanner,
    ContextManager,
    TokenManager,
    AudioProcessor,
    round_time_to_15_min,
    get_app_paths,
    resolve_config_path,
    load_app_config,
    CONFIG_ENV_VAR,
    set_persisted_config_path,
)

# --- Backend Script Runner ---
def run_generation_process(transcript_data, transcript_is_file,
                           meeting_name, meeting_time,
                           context_data, context_is_file,
                           agenda_data, agenda_is_file,
                           minutes_style, output_folder, output_format, config_path,
                           status_bar_update_func, include_rationale=False,
                           include_recommendations=False, completion_callback=None):
    """
    Runs the transcript2json.py, json_refine.py, and json2word.py scripts with the provided inputs.
    Handles temporary file creation for pasted text.
    """
    status_bar_update_func("Starting generation...")
    print("--- Running Generation ---")

    temp_dir = None
    final_status = "Error during generation"

    try:
        # Create Output Directory
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
                print(f"Created output directory: {output_folder}")
            except OSError as e:
                raise OSError(f"Failed to create output directory '{output_folder}': {e}")

        # Setup Temporary Files if Needed
        temp_dir = tempfile.mkdtemp(prefix="meetingsecretary_")
        print(f"Using temporary directory: {temp_dir}")

        if transcript_is_file:
            transcript_input_arg = transcript_data
        else:
            fd, transcript_input_arg = tempfile.mkstemp(suffix=".txt", dir=temp_dir, text=True)
            with os.fdopen(fd, 'w') as tmp_file:
                tmp_file.write(transcript_data)
            print(f"Created temp transcript file: {transcript_input_arg}")

        if context_is_file:
            context_input_arg = context_data
        elif context_data:
            fd, context_input_arg = tempfile.mkstemp(suffix=".md", dir=temp_dir, text=True)
            with os.fdopen(fd, 'w') as tmp_file:
                tmp_file.write(context_data)
            print(f"Created temp context file: {context_input_arg}")
        else:
            # Create empty context file since transcript2json.py requires it
            fd, context_input_arg = tempfile.mkstemp(suffix=".md", dir=temp_dir, text=True)
            with os.fdopen(fd, 'w') as tmp_file:
                tmp_file.write("# Context\n\nNo specific context provided.")
            print(f"Created temp context file (empty): {context_input_arg}")

        if agenda_is_file:
            agenda_input_arg = agenda_data
        elif agenda_data:
            fd, agenda_input_arg = tempfile.mkstemp(suffix=".md", dir=temp_dir, text=True)
            with os.fdopen(fd, 'w') as tmp_file:
                tmp_file.write(agenda_data)
            print(f"Created temp agenda file: {agenda_input_arg}")
        else:
            # Create empty agenda file since transcript2json.py requires it
            fd, agenda_input_arg = tempfile.mkstemp(suffix=".md", dir=temp_dir, text=True)
            with os.fdopen(fd, 'w') as tmp_file:
                tmp_file.write("# Agenda\n\nNo specific agenda provided.")
            print(f"Created temp agenda file (empty): {agenda_input_arg}")

        # Determine Prompt File
        style_map = {
            "Concise": "scripts/prompt_concise.md",
            "Action-Focused": "scripts/prompt_action.md",
            "Moderate": "scripts/prompt_moderate.md",
            "High Detail": "scripts/prompt_high.md",
            "High Detail (In-Person/Unreliable ID)": "scripts/prompt_high_inperson.md"
        }
        prompt_file = style_map.get(minutes_style, "scripts/prompt_moderate.md")
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        print(f"Using prompt file: {prompt_file}")

        # Intermediate JSON File Path
        safe_meeting_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in meeting_name)
        json_output_file = os.path.join(output_folder, f"{safe_meeting_name}_interim_minutes.json")
        refined_json_file = os.path.join(output_folder, f"{safe_meeting_name}_refined_minutes.json")
        print(f"Intermediate JSON path: {json_output_file}")
        print(f"Refined JSON path: {refined_json_file}")

        # Step 1: transcript2json.py
        config_file_arg = os.path.abspath(config_path) if config_path else os.path.abspath("config.ini")
        cmd1 = [
            "python", os.path.abspath("scripts/transcript2json.py"),
            "--input_file", os.path.abspath(transcript_input_arg),
            "--output_file", os.path.abspath(json_output_file),
            "--prompt_file", os.path.abspath(prompt_file),
            "--schema_file", os.path.abspath("scripts/minutes_schema.JSON"),
            "--config_file", config_file_arg,
            "--context_file", os.path.abspath(context_input_arg),
            "--agenda_file", os.path.abspath(agenda_input_arg)
        ]

        status_bar_update_func("Running transcript to JSON conversion...")
        print(f"Executing: {' '.join(cmd1)}")
        result1 = subprocess.run(cmd1, capture_output=True, text=True, check=True, encoding='utf-8')
        print("transcript2json output:", result1.stdout)
        if result1.stderr:
            print("transcript2json errors:", result1.stderr)

        # Step 2: json_refine.py
        cmd2 = [
            "python", os.path.abspath("scripts/json_refine.py"),
            "--input_json", os.path.abspath(json_output_file),
            "--output_json", os.path.abspath(refined_json_file),
            "--prompt_file", os.path.abspath("scripts/prompt_refine.md"),
            "--schema_file", os.path.abspath("scripts/minutes_schema.JSON"),
            "--config_file", config_file_arg,
        ]

        status_bar_update_func("Refining JSON minutes for readability...")
        print(f"Executing: {' '.join(cmd2)}")
        result2 = subprocess.run(cmd2, capture_output=True, text=True, check=True, encoding='utf-8')
        print("json_refine output:", result2.stdout)
        if result2.stderr:
            print("json_refine errors:", result2.stderr)

        # Step 3: json2word.py
        datestamp = datetime.datetime.now().strftime("%Y%m%d")
        output_prefix = f"{safe_meeting_name}_Minutes_{datestamp}"
        
        # Map GUI format options to script format options
        format_mapping = {
            "both": "both",
            "docx": "docx", 
            "markdown": "md"
        }
        output_format_arg = format_mapping.get(output_format.lower(), "docx")

        if not os.path.exists(refined_json_file):
            raise FileNotFoundError(f"Refined JSON file was not created: {refined_json_file}")

        cmd3 = [
            "python", os.path.abspath("scripts/json2word.py"),
            "--input_json", os.path.abspath(refined_json_file),
            "--output_dir", os.path.abspath(output_folder),
            "--output_prefix", output_prefix,
            "--output_format", output_format_arg,
        ]
        
        if include_rationale:
            cmd3.append("--include_rationale")
        if include_recommendations:
            cmd3.append("--include_recommendations")
            
        status_bar_update_func("Running JSON to Document conversion...")
        print(f"Executing: {' '.join(cmd3)}")
        result3 = subprocess.run(cmd3, capture_output=True, text=True, check=True, encoding='utf-8')
        print("json2word output:", result3.stdout)
        if result3.stderr:
            print("json2word errors:", result3.stderr)

        final_status = f"Generation complete! Files in '{output_folder}' with prefix '{output_prefix}'"
        print("--- Generation Finished Successfully ---")
        
        # Open output folder in Finder when running on macOS
        if sys.platform == "darwin":
            try:
                subprocess.run(["open", output_folder], check=True)
                print(f"Opened output folder in Finder: {output_folder}")
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                print(f"Could not open output folder in Finder: {output_folder} ({exc})")
        else:
            print("Auto-opening the output folder is only available on macOS; skipping for this platform.")

    except subprocess.CalledProcessError as e:
        error_message = f"Error in script '{os.path.basename(e.cmd[1])}': Exit code {e.returncode}\n"
        if e.stdout:
            error_message += f"--- STDOUT ---\n{e.stdout}\n"
        if e.stderr:
            error_message += f"--- STDERR ---\n{e.stderr}\n"
        print(error_message)
        final_status = f"Error: Script {os.path.basename(e.cmd[1])} failed. See console log."

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        final_status = f"Error: Required file not found ({e}). Check paths."

    except OSError as e:
        print(f"Error: OS error - {e}")
        final_status = f"Error: File system error ({e}). Check permissions or paths."

    except Exception as e:
        import traceback
        error_message = f"An unexpected error occurred: {e}\n{traceback.format_exc()}"
        print(error_message)
        final_status = f"Error: An unexpected error occurred. See console log."

    finally:
        # Cleanup
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"Warning: Failed to cleanup temporary directory '{temp_dir}': {e}")

        status_bar_update_func(final_status)
        
        # Call completion callback if provided
        if completion_callback:
            completion_callback(final_status.startswith("Generation complete!"))


# --- GUI Application Class ---
class MeetingSecretaryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meeting Secretary AI")
        self.geometry("900x750")

        self.config_path = resolve_config_path()
        self._config_requires_restart = False
        self.config_path_label_text = tk.StringVar(value=f"Active config: {self.config_path}")
        self.app_config, _ = load_app_config(self.config_path)
        self.app_paths = get_app_paths(self.config_path)

        # Initialize utilities
        self.zoom_scanner = ZoomMeetingScanner(zoom_dir=self.app_paths.get("zoom_dir"))
        self.context_manager = ContextManager(context_dir=self.app_paths.get("context_dir"))
        self.token_manager = TokenManager(token_file=self.app_paths.get("token_file"))
        self.audio_processor = AudioProcessor(self.token_manager)

        # Store loaded meetings and selected meeting to avoid re-fetching
        self.loaded_meetings = []
        self.selected_meeting_data = None

        # Variables
        input_mode_default = self.app_config.get("gui", "input_mode", fallback="zoom").strip().lower()
        if input_mode_default not in ("zoom", "audio", "transcript", "folder"):
            input_mode_default = "zoom"
        self.input_mode = tk.StringVar(value=input_mode_default)
        self.transcript_source = tk.StringVar(value="paste")
        self.transcript_file_path = tk.StringVar()
        self.audio_file_path = tk.StringVar()
        self.folder_path = tk.StringVar()
        self.meeting_limit = tk.StringVar(value="5")  # Default to top 5 meetings

        self.meeting_name = tk.StringVar()
        self.meeting_time = tk.StringVar()
        self.meeting_date = tk.StringVar()
        self.participants = tk.StringVar()

        self.context_source = tk.StringVar(value="select")
        self.context_file_path = tk.StringVar()
        self.selected_context = tk.StringVar()
        self.default_context_dir = self.app_paths.get("context_dir")

        self.agenda_source = tk.StringVar(value="paste")
        self.agenda_file_path = tk.StringVar()

        self.minutes_style_options = ["Concise", "Action-Focused", "Moderate", "High Detail", "High Detail (In-Person/Unreliable ID)"]
        minutes_style_default = self.app_config.get("gui", "minutes_style", fallback="Moderate").strip()
        if minutes_style_default not in self.minutes_style_options:
            minutes_style_default = "Moderate"
        self.minutes_style = tk.StringVar(value=minutes_style_default)

        default_output_dir = self.app_paths.get("output_dir") or os.path.abspath("../MeetingSecretaryAI_Data/output")
        self.output_folder = tk.StringVar(value=default_output_dir)
        self.output_format_options = ["Both", "DOCX", "Markdown"]
        output_format_default = self.app_config.get("gui", "output_format", fallback="DOCX").strip().lower()
        if output_format_default in ("both", "all"):
            output_format_default = "Both"
        elif output_format_default in ("markdown", "md"):
            output_format_default = "Markdown"
        else:
            output_format_default = "DOCX"
        self.output_format = tk.StringVar(value=output_format_default)

        include_rationale_default = False
        include_recommendations_default = False
        try:
            include_rationale_default = self.app_config.getboolean("gui", "include_rationale", fallback=False)
        except ValueError:
            include_rationale_default = False
        try:
            include_recommendations_default = self.app_config.getboolean("gui", "include_recommendations", fallback=False)
        except ValueError:
            include_recommendations_default = False

        self.include_rationale = tk.BooleanVar(value=include_rationale_default)
        self.include_recommendations = tk.BooleanVar(value=include_recommendations_default)

        self.status_text = tk.StringVar(value="Ready")
        self.hf_token = tk.StringVar()

        # Load existing token
        existing_token = self.token_manager.get_token()
        if existing_token:
            self.hf_token.set(existing_token)

        # UI Setup
        self._create_widgets()
        self._load_zoom_meetings()
        self._load_contexts()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Bind tab change event to maintain meeting selection
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Input Methods Tab
        self.input_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.input_tab_frame, text="Input Methods")
        self._create_input_methods_tab(self.input_tab_frame)

        # Meeting Details Tab
        self.details_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.details_tab_frame, text="Meeting Details")
        self._create_meeting_details_tab(self.details_tab_frame)

        # Context & Agenda Tab
        self.context_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.context_tab_frame, text="Context & Agenda")
        self._create_context_agenda_tab(self.context_tab_frame)

        # Settings Tab
        self.settings_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab_frame, text="Settings")
        self._create_settings_tab(self.settings_tab_frame)

        # Generate Button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Process Audio (WhisperX)", command=self._process_audio).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Generate Minutes", command=self._generate_callback).pack(side=tk.RIGHT)

        # Status Bar
        status_bar = ttk.Label(self, textvariable=self.status_text, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_input_methods_tab(self, parent):
        # Input Method Selection
        method_frame = ttk.LabelFrame(parent, text="Input Method", padding="10")
        method_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(method_frame, text="Latest Zoom Meetings", variable=self.input_mode, value="zoom", command=self._toggle_input_mode).pack(anchor=tk.W)
        ttk.Radiobutton(method_frame, text="Select Audio File", variable=self.input_mode, value="audio", command=self._toggle_input_mode).pack(anchor=tk.W)
        ttk.Radiobutton(method_frame, text="Select Transcript File", variable=self.input_mode, value="transcript", command=self._toggle_input_mode).pack(anchor=tk.W)
        ttk.Radiobutton(method_frame, text="Select Input Folder", variable=self.input_mode, value="folder", command=self._toggle_input_mode).pack(anchor=tk.W)

        # Zoom Meetings Frame
        self.zoom_frame = ttk.LabelFrame(parent, text="Latest Zoom Meetings", padding="10")
        self.zoom_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Meeting limit controls
        limit_frame = ttk.Frame(self.zoom_frame)
        limit_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(limit_frame, text="Show:").pack(side=tk.LEFT)
        ttk.Radiobutton(limit_frame, text="Top 5", variable=self.meeting_limit, value="5", command=self._on_meeting_limit_changed).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(limit_frame, text="All", variable=self.meeting_limit, value="all", command=self._on_meeting_limit_changed).pack(side=tk.LEFT, padx=(10, 0))
        
        # Create Treeview for meetings
        columns = ("Meeting", "Date", "Time", "Participants")
        self.meetings_tree = ttk.Treeview(self.zoom_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.meetings_tree.heading(col, text=col)
            self.meetings_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(self.zoom_frame, orient=tk.VERTICAL, command=self.meetings_tree.yview)
        self.meetings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.meetings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.meetings_tree.bind("<<TreeviewSelect>>", self._on_meeting_select)
        
        refresh_btn = ttk.Button(self.zoom_frame, text="Refresh", command=self._load_zoom_meetings)
        refresh_btn.pack(pady=5)

        # Audio File Frame
        self.audio_frame = ttk.LabelFrame(parent, text="Audio File", padding="10")
        self.audio_frame.pack(fill=tk.X, pady=5)
        
        audio_entry_frame = ttk.Frame(self.audio_frame)
        audio_entry_frame.pack(fill=tk.X)
        ttk.Entry(audio_entry_frame, textvariable=self.audio_file_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(audio_entry_frame, text="Browse...", command=self._browse_audio_file).pack(side=tk.RIGHT)

        # Transcript File Frame
        self.transcript_frame = ttk.LabelFrame(parent, text="Transcript File", padding="10")
        self.transcript_frame.pack(fill=tk.X, pady=5)
        
        transcript_entry_frame = ttk.Frame(self.transcript_frame)
        transcript_entry_frame.pack(fill=tk.X)
        ttk.Entry(transcript_entry_frame, textvariable=self.transcript_file_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(transcript_entry_frame, text="Browse...", command=self._browse_transcript_file).pack(side=tk.RIGHT)

        # Folder Frame
        self.folder_frame = ttk.LabelFrame(parent, text="Input Folder", padding="10")
        self.folder_frame.pack(fill=tk.X, pady=5)
        
        folder_entry_frame = ttk.Frame(self.folder_frame)
        folder_entry_frame.pack(fill=tk.X)
        ttk.Entry(folder_entry_frame, textvariable=self.folder_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(folder_entry_frame, text="Browse...", command=self._browse_folder_input).pack(side=tk.RIGHT)

        self._toggle_input_mode()

    def _create_meeting_details_tab(self, parent):
        details_frame = ttk.LabelFrame(parent, text="Meeting Information", padding="10")
        details_frame.pack(fill=tk.X, pady=5)
        
        # Meeting Name
        ttk.Label(details_frame, text="Meeting Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(details_frame, textvariable=self.meeting_name, width=50).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Meeting Date
        ttk.Label(details_frame, text="Meeting Date:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(details_frame, textvariable=self.meeting_date, width=50).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Meeting Time
        ttk.Label(details_frame, text="Meeting Time:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(details_frame, textvariable=self.meeting_time, width=50).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Participants
        ttk.Label(details_frame, text="Participants:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(details_frame, textvariable=self.participants, width=50).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        
        details_frame.columnconfigure(1, weight=1)
        
        # Auto-generate agenda button
        ttk.Button(details_frame, text="Auto-Generate Agenda", command=self._auto_generate_agenda).grid(row=4, column=0, columnspan=2, pady=10)

    def _create_context_agenda_tab(self, parent):
        # Context Section
        context_frame = ttk.LabelFrame(parent, text="Context", padding="10")
        context_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(context_frame, text="Select from presets", variable=self.context_source, value="select", command=self._toggle_context_input).pack(anchor=tk.W)
        ttk.Radiobutton(context_frame, text="Paste text", variable=self.context_source, value="paste", command=self._toggle_context_input).pack(anchor=tk.W)
        ttk.Radiobutton(context_frame, text="Select file", variable=self.context_source, value="file", command=self._toggle_context_input).pack(anchor=tk.W)
        
        # Context preset dropdown
        self.context_preset_frame = ttk.Frame(context_frame)
        self.context_preset_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.context_preset_frame, text="Context:").pack(side=tk.LEFT)
        self.context_combo = ttk.Combobox(self.context_preset_frame, textvariable=self.selected_context, state="readonly", width=50)
        self.context_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Context paste area
        self.context_paste_area = scrolledtext.ScrolledText(context_frame, height=8, width=70)
        
        # Context file selection
        self.context_file_frame = ttk.Frame(context_frame)
        self.context_file_frame.pack(fill=tk.X, pady=5)
        ttk.Entry(self.context_file_frame, textvariable=self.context_file_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(self.context_file_frame, text="Browse...", command=self._browse_context_file).pack(side=tk.RIGHT)
        
        # Agenda Section
        agenda_frame = ttk.LabelFrame(parent, text="Agenda", padding="10")
        agenda_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Radiobutton(agenda_frame, text="Paste text", variable=self.agenda_source, value="paste", command=self._toggle_agenda_input).pack(anchor=tk.W)
        ttk.Radiobutton(agenda_frame, text="Select file", variable=self.agenda_source, value="file", command=self._toggle_agenda_input).pack(anchor=tk.W)
        
        # Agenda paste area
        self.agenda_paste_area = scrolledtext.ScrolledText(agenda_frame, height=8, width=70)
        
        # Agenda file selection
        self.agenda_file_frame = ttk.Frame(agenda_frame)
        self.agenda_file_frame.pack(fill=tk.X, pady=5)
        ttk.Entry(self.agenda_file_frame, textvariable=self.agenda_file_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(self.agenda_file_frame, text="Browse...", command=self._browse_agenda_file).pack(side=tk.RIGHT)
        
        self._toggle_context_input()
        self._toggle_agenda_input()

    def _create_settings_tab(self, parent):
        # Configuration
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        config_row = ttk.Frame(config_frame)
        config_row.pack(fill=tk.X)
        ttk.Label(
            config_row,
            textvariable=self.config_path_label_text,
            wraplength=620
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(config_row, text="Copy Path", command=self._copy_config_path).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(config_row, text="Select Config", command=self._select_config_file).pack(side=tk.RIGHT)

        # Minutes Style
        style_frame = ttk.LabelFrame(parent, text="Minutes Style", padding="10")
        style_frame.pack(fill=tk.X, pady=5)
        style_combo = ttk.Combobox(style_frame, textvariable=self.minutes_style, values=self.minutes_style_options, state="readonly", width=45)
        style_combo.pack(anchor=tk.W)

        # Output Settings
        output_frame = ttk.LabelFrame(parent, text="Output Settings", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        # Output Folder
        folder_frame = ttk.Frame(output_frame)
        folder_frame.pack(fill=tk.X, pady=2)
        ttk.Label(folder_frame, text="Output Folder:").pack(side=tk.LEFT)
        ttk.Entry(folder_frame, textvariable=self.output_folder, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        ttk.Button(folder_frame, text="Browse...", command=self._browse_output_folder).pack(side=tk.RIGHT)
        
        # Output Format
        format_frame = ttk.Frame(output_frame)
        format_frame.pack(fill=tk.X, pady=2)
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT)
        format_combo = ttk.Combobox(format_frame, textvariable=self.output_format, values=self.output_format_options, state="readonly", width=20)
        format_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Additional Options
        options_frame = ttk.Frame(output_frame)
        options_frame.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(options_frame, text="Include Rationale", variable=self.include_rationale).pack(side=tk.LEFT)
        ttk.Checkbutton(options_frame, text="Include Recommendations", variable=self.include_recommendations).pack(side=tk.LEFT, padx=(10, 0))

        # HuggingFace Token
        token_frame = ttk.LabelFrame(parent, text="HuggingFace Token (for WhisperX)", padding="10")
        token_frame.pack(fill=tk.X, pady=5)
        
        token_entry_frame = ttk.Frame(token_frame)
        token_entry_frame.pack(fill=tk.X)
        ttk.Entry(token_entry_frame, textvariable=self.hf_token, width=50, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(token_entry_frame, text="Save Token", command=self._save_token).pack(side=tk.RIGHT)

    def _copy_config_path(self):
        """Copy the active config path to the clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(str(self.config_path))
            self.update_idletasks()
            self._update_status("Config path copied to clipboard")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to copy config path: {exc}")

    def _select_config_file(self):
        """Select a config file and prompt for restart."""
        filepath = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")]
        )
        if not filepath:
            return

        self.config_path = os.path.abspath(filepath)
        os.environ[CONFIG_ENV_VAR] = self.config_path
        set_persisted_config_path(self.config_path)
        self._config_requires_restart = True
        self.config_path_label_text.set(f"Config selected (restart to apply): {self.config_path}")
        messagebox.showinfo(
            "Restart Required",
            "Config file selected. Please restart the application to apply new settings."
        )

    def _toggle_input_mode(self):
        """Toggle visibility of input frames based on selected mode."""
        mode = self.input_mode.get()
        
        # Hide all frames
        self.zoom_frame.pack_forget()
        self.audio_frame.pack_forget()
        self.transcript_frame.pack_forget()
        self.folder_frame.pack_forget()
        
        # Show selected frame
        if mode == "zoom":
            self.zoom_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            # Restore selection if we had one previously
            if self.selected_meeting_data:
                self._restore_meeting_selection()
        elif mode == "audio":
            self.audio_frame.pack(fill=tk.X, pady=5)
        elif mode == "transcript":
            self.transcript_frame.pack(fill=tk.X, pady=5)
        elif mode == "folder":
            self.folder_frame.pack(fill=tk.X, pady=5)

    def _toggle_context_input(self):
        """Toggle context input method."""
        mode = self.context_source.get()
        
        # Hide all
        self.context_preset_frame.pack_forget()
        self.context_paste_area.pack_forget()
        self.context_file_frame.pack_forget()
        
        # Show selected
        if mode == "select":
            self.context_preset_frame.pack(fill=tk.X, pady=5)
        elif mode == "paste":
            self.context_paste_area.pack(fill=tk.BOTH, expand=True, pady=5)
        elif mode == "file":
            self.context_file_frame.pack(fill=tk.X, pady=5)

    def _toggle_agenda_input(self):
        """Toggle agenda input method."""
        mode = self.agenda_source.get()
        
        # Hide all
        self.agenda_paste_area.pack_forget()
        self.agenda_file_frame.pack_forget()
        
        # Show selected
        if mode == "paste":
            self.agenda_paste_area.pack(fill=tk.BOTH, expand=True, pady=5)
        elif mode == "file":
            self.agenda_file_frame.pack(fill=tk.X, pady=5)

    def _load_zoom_meetings(self):
        """Load latest Zoom meetings into the tree."""
        try:
            # Get the limit setting
            limit_setting = self.meeting_limit.get()
            if limit_setting == "all":
                limit = None  # No limit
            else:
                limit = int(limit_setting)
            
            meetings = self.zoom_scanner.get_latest_meetings(limit=limit)
            self.loaded_meetings = meetings  # Store the meetings
            
            # Clear existing items
            for item in self.meetings_tree.get_children():
                self.meetings_tree.delete(item)
            
            # Add meetings
            for meeting in meetings:
                participants_str = ", ".join(meeting['participants'][:3])  # Show first 3 participants
                if len(meeting['participants']) > 3:
                    participants_str += f" (+{len(meeting['participants']) - 3} more)"
                
                self.meetings_tree.insert("", "end", values=(
                    meeting['meeting_name'],
                    meeting['date'],
                    meeting['time'],
                    participants_str
                ))
            
            # Adjust tree height based on number of meetings
            self._adjust_tree_height(len(meetings))
            
            if len(meetings) == 0:
                # Check if it's a permission issue
                import errno
                zoom_dir = os.path.expanduser("~/Documents/Zoom")
                if os.path.exists(zoom_dir):
                    try:
                        os.listdir(zoom_dir)
                        self._update_status("No recent Zoom meetings found")
                    except PermissionError:
                        self._update_status("Permission denied: Please grant access to Documents folder")
                        self._show_permission_dialog()
                else:
                    self._update_status("Zoom folder not found - you can still use other input methods")
            else:
                limit_text = "all" if limit is None else f"top {limit}"
                self._update_status(f"Loaded {len(meetings)} recent meetings ({limit_text})")
                
                # Restore selection if we had one previously
                if self.selected_meeting_data:
                    self._restore_meeting_selection()
                
        except Exception as e:
            error_msg = str(e)
            if "Permission denied" in error_msg or "Operation not permitted" in error_msg:
                self._update_status("Permission denied: Please grant access to Documents folder")
                self._show_permission_dialog()
            else:
                self._update_status(f"Error loading meetings: {error_msg}")
    
    def _show_permission_dialog(self):
        """Show dialog with instructions for granting permissions."""
        from tkinter import messagebox
        message = """macOS Privacy Settings Required
        
To access Zoom meetings, you need to grant permission:

1. Open System Preferences
2. Go to Security & Privacy > Privacy
3. Select 'Files and Folders' on the left
4. Find Terminal (or Python) in the list
5. Check the box for 'Documents Folder'
6. Restart this application

You can still use the app with other input methods (transcript files, audio files, etc.) without this permission."""
        
        messagebox.showinfo("Permission Required", message)

    def _load_contexts(self):
        """Load available context files."""
        try:
            contexts = self.context_manager.get_available_contexts()
            context_names = [ctx['display_name'] for ctx in contexts]
            self.context_combo['values'] = context_names
            
            # Store mapping for later use
            self.context_mapping = {ctx['display_name']: ctx for ctx in contexts}
            
        except Exception as e:
            self._update_status(f"Error loading contexts: {str(e)}")

    def _on_meeting_select(self, event):
        """Handle meeting selection from the tree."""
        selection = self.meetings_tree.selection()
        if not selection:
            self.selected_meeting_data = None
            return
            
        # Get meeting data
        item = self.meetings_tree.item(selection[0])
        meeting_name = item['values'][0]
        meeting_date = item['values'][1]
        meeting_time = item['values'][2]
        
        # Find the full meeting info from stored meetings (avoid re-fetching)
        selected_meeting = None
        for meeting in self.loaded_meetings:
            if meeting['meeting_name'] == meeting_name and meeting['date'] == meeting_date:
                selected_meeting = meeting
                break
        
        if selected_meeting:
            # Store the selected meeting data
            self.selected_meeting_data = selected_meeting
            
            # Populate meeting details
            self.meeting_name.set(selected_meeting['meeting_name'])
            self.meeting_date.set(selected_meeting['date'])
            self.meeting_time.set(selected_meeting['time'])  # This is already rounded from the scanner
            self.participants.set(", ".join(selected_meeting['participants']))
            
            # Set transcript file path
            self.transcript_file_path.set(selected_meeting['transcript_file'])
            
            # Auto-generate agenda
            self._auto_generate_agenda_for_meeting(selected_meeting)
        else:
            # Fallback: if meeting not found in stored data, try re-fetching
            self._update_status("Meeting not found in cached data, refreshing...")
            self._load_zoom_meetings()  # This will refresh the stored meetings
            self.selected_meeting_data = None

    def _auto_generate_agenda(self):
        """Auto-generate agenda based on current meeting info."""
        if not self.meeting_name.get():
            messagebox.showwarning("Warning", "Please enter a meeting name first")
            return
            
        # Get and round the time
        time_str = self.meeting_time.get() or "00:00:00"
        try:
            time_obj = datetime.datetime.strptime(time_str, "%H:%M:%S")
            time_obj = round_time_to_15_min(time_obj)
            rounded_time = time_obj.strftime("%H:%M:%S")
        except ValueError:
            rounded_time = time_str
            
        # Create a meeting info dict
        meeting_info = {
            'meeting_name': self.meeting_name.get(),
            'date': self.meeting_date.get() or datetime.date.today().strftime("%Y-%m-%d"),
            'time': rounded_time,
            'participants': [p.strip() for p in self.participants.get().split(',') if p.strip()]
        }
        
        agenda_content = self.zoom_scanner.generate_auto_agenda(meeting_info)
        self.agenda_paste_area.delete("1.0", tk.END)
        self.agenda_paste_area.insert("1.0", agenda_content)
        
        # Update the time field with rounded time
        self.meeting_time.set(rounded_time)
        
        # Switch to paste mode for agenda
        self.agenda_source.set("paste")
        self._toggle_agenda_input()

    def _auto_generate_agenda_for_meeting(self, meeting_info):
        """Auto-generate agenda for a specific meeting."""
        agenda_content = self.zoom_scanner.generate_auto_agenda(meeting_info)
        self.agenda_paste_area.delete("1.0", tk.END)
        self.agenda_paste_area.insert("1.0", agenda_content)
        
        # Switch to paste mode for agenda
        self.agenda_source.set("paste")
        self._toggle_agenda_input()

    def _browse_audio_file(self):
        """Browse for audio file."""
        filepath = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio files", "*.m4a *.mp3 *.wav *.flac"), ("All files", "*.*")]
        )
        if filepath:
            self.audio_file_path.set(os.path.abspath(filepath))

    def _browse_transcript_file(self):
        """Browse for transcript file."""
        filepath = filedialog.askopenfilename(
            title="Select Transcript File",
            filetypes=[("Transcript files", "*.vtt *.txt"), ("All files", "*.*")]
        )
        if filepath:
            self.transcript_file_path.set(os.path.abspath(filepath))

    def _browse_folder_input(self):
        """Browse for input folder."""
        folderpath = filedialog.askdirectory(title="Select Input Folder")
        if folderpath:
            self.folder_path.set(os.path.abspath(folderpath))

    def _browse_context_file(self):
        """Browse for context file."""
        initial_dir = self.default_context_dir if self.default_context_dir and os.path.isdir(self.default_context_dir) else None
        filepath = filedialog.askopenfilename(
            title="Select Context File",
            initialdir=initial_dir,
            filetypes=[("Context files", "*.md *.txt"), ("All files", "*.*")]
        )
        if filepath:
            self.context_file_path.set(os.path.abspath(filepath))
            self.context_source.set("file")
            self._toggle_context_input()

    def _browse_agenda_file(self):
        """Browse for agenda file."""
        filepath = filedialog.askopenfilename(
            title="Select Agenda File",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            self.agenda_file_path.set(os.path.abspath(filepath))

    def _browse_output_folder(self):
        """Browse for output folder."""
        folderpath = filedialog.askdirectory(title="Select Output Folder")
        if folderpath:
            self.output_folder.set(os.path.abspath(folderpath))

    def _save_token(self):
        """Save HuggingFace token."""
        token = self.hf_token.get().strip()
        if not token:
            messagebox.showwarning("Warning", "Please enter a token")
            return
            
        if self.token_manager.set_token(token):
            messagebox.showinfo("Success", "Token saved successfully")
            self._update_status("HuggingFace token saved")
        else:
            messagebox.showerror("Error", "Failed to save token")

    def _process_audio(self):
        """Process audio file with WhisperX."""
        if self.input_mode.get() != "audio":
            messagebox.showwarning("Warning", "Please select an audio file first")
            return
            
        audio_file = self.audio_file_path.get()
        if not audio_file or not os.path.exists(audio_file):
            messagebox.showerror("Error", "Please select a valid audio file")
            return
            
        # Check if token is set
        if not self.token_manager.get_token():
            messagebox.showerror("Error", "Please set your HuggingFace token in Settings")
            return
            
        # Create output directory
        output_dir = os.path.join(self.output_folder.get(), "audio_processing")
        os.makedirs(output_dir, exist_ok=True)
        
        def audio_callback(success, message):
            if success:
                self._update_status(message)
                # Look for generated transcript
                transcript_files = [f for f in os.listdir(output_dir) if f.endswith('.txt')]
                if transcript_files:
                    transcript_path = os.path.join(output_dir, transcript_files[0])
                    self.transcript_file_path.set(transcript_path)
                    self.input_mode.set("transcript")
                    self._toggle_input_mode()
                    messagebox.showinfo("Success", f"Audio processed successfully!\nTranscript saved to: {transcript_path}")
            else:
                self._update_status(f"Audio processing failed: {message}")
                messagebox.showerror("Error", f"Audio processing failed: {message}")
        
        self._update_status("Processing audio with WhisperX...")
        self.audio_processor.process_audio(audio_file, output_dir, audio_callback)

    def _get_transcript_data(self):
        """Get transcript data based on current input mode."""
        mode = self.input_mode.get()
        
        if mode == "zoom":
            # Get selected meeting transcript
            selection = self.meetings_tree.selection()
            if not selection:
                raise ValueError("Please select a meeting from the list")
            
            item = self.meetings_tree.item(selection[0])
            meeting_name = item['values'][0]
            meeting_date = item['values'][1]
            
            meetings = self.zoom_scanner.get_latest_meetings()
            for meeting in meetings:
                if meeting['meeting_name'] == meeting_name and meeting['date'] == meeting_date:
                    return meeting['transcript_file'], True
            
            raise ValueError("Selected meeting not found")
            
        elif mode == "transcript":
            transcript_file = self.transcript_file_path.get()
            if not transcript_file or not os.path.exists(transcript_file):
                raise ValueError("Please select a valid transcript file")
            return transcript_file, True
            
        elif mode == "folder":
            folder_path = self.folder_path.get()
            if not folder_path or not os.path.exists(folder_path):
                raise ValueError("Please select a valid input folder")
            
            # Look for transcript file in folder
            vtt_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.vtt')])
            txt_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.txt')])
            transcript_files = vtt_files + txt_files
            if not transcript_files:
                raise ValueError("No transcript files found in selected folder")
            
            return os.path.join(folder_path, transcript_files[0]), True
            
        else:
            raise ValueError("Please select a valid input method")

    def _get_context_data(self):
        """Get context data based on current settings."""
        mode = self.context_source.get()
        
        if mode == "select":
            selected = self.selected_context.get()
            if not selected or selected not in self.context_mapping:
                return None, False
            
            context_info = self.context_mapping[selected]
            return context_info['file_path'], True
            
        elif mode == "paste":
            content = self.context_paste_area.get("1.0", tk.END).strip()
            return content if content else None, False
            
        elif mode == "file":
            file_path = self.context_file_path.get()
            if not file_path or not os.path.exists(file_path):
                return None, False
            return file_path, True
            
        return None, False

    def _get_agenda_data(self):
        """Get agenda data based on current settings."""
        mode = self.agenda_source.get()
        
        if mode == "paste":
            content = self.agenda_paste_area.get("1.0", tk.END).strip()
            return content if content else None, False
            
        elif mode == "file":
            file_path = self.agenda_file_path.get()
            if not file_path or not os.path.exists(file_path):
                return None, False
            return file_path, True
            
        return None, False

    def _update_status(self, message):
        """Update status bar."""
        self.status_text.set(message)
        self.update_idletasks()

    def _generate_callback(self):
        """Handle generate minutes button click."""
        try:
            # Get transcript data
            transcript_data, transcript_is_file = self._get_transcript_data()
            
            # Get context data
            context_data, context_is_file = self._get_context_data()
            
            # Get agenda data
            agenda_data, agenda_is_file = self._get_agenda_data()
            
            # Validation
            meeting_name_val = self.meeting_name.get().strip()
            if not meeting_name_val:
                messagebox.showerror("Input Error", "Meeting Name is required.")
                return
            
            output_folder_val = self.output_folder.get().strip()
            if not output_folder_val:
                messagebox.showerror("Input Error", "Output Folder is required.")
                return
            
            # Check if script files exist
            if not os.path.exists("scripts/transcript2json.py") or not os.path.exists("scripts/json2word.py"):
                messagebox.showerror("Setup Error", "Core script files not found in 'scripts' directory.")
                return
            
            # Start processing
            self._update_status("Preparing generation...")
            thread = threading.Thread(target=run_generation_process, args=(
                transcript_data, transcript_is_file,
                meeting_name_val,
                self.meeting_time.get(),
                context_data, context_is_file,
                agenda_data, agenda_is_file,
                self.minutes_style.get(),
                output_folder_val,
                self.output_format.get(),
                self.config_path,
                self._update_status,
                self.include_rationale.get(),
                self.include_recommendations.get(),
                self._on_generation_complete
            ), daemon=True)
            thread.start()
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            self._update_status(f"Error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            self._update_status(f"Error: {str(e)}")

    def _on_tab_changed(self, event):
        """Handle tab change events to maintain meeting selection persistence."""
        # If we have a selected meeting and we're in zoom mode, ensure the selection is preserved
        if (self.selected_meeting_data and 
            self.input_mode.get() == "zoom" and 
            self.loaded_meetings):
            
            # Verify that the selection is still valid in the current tree
            selection = self.meetings_tree.selection()
            if not selection:
                # Try to restore the selection
                self._restore_meeting_selection()
    
    def _restore_meeting_selection(self):
        """Restore the previously selected meeting in the tree view."""
        if not self.selected_meeting_data:
            return
            
        # Find the item in the tree that matches our selected meeting
        for item in self.meetings_tree.get_children():
            item_values = self.meetings_tree.item(item)['values']
            if (item_values[0] == self.selected_meeting_data['meeting_name'] and
                item_values[1] == self.selected_meeting_data['date']):
                self.meetings_tree.selection_set(item)
                self.meetings_tree.focus(item)
                break

    def _on_meeting_limit_changed(self):
        """Handle meeting limit change and reload meetings."""
        self._load_zoom_meetings()

    def _adjust_tree_height(self, meeting_count):
        """Adjust the tree height based on the number of meetings."""
        # Set height based on number of meetings, with a minimum of 5 and maximum of 15
        if meeting_count == 0:
            height = 5
        elif meeting_count <= 5:
            height = max(5, meeting_count)
        elif meeting_count <= 10:
            height = meeting_count
        else:
            height = min(15, meeting_count)
        
        self.meetings_tree.configure(height=height)

    def _on_generation_complete(self, success):
        """Handle completion of minutes generation and show continue/quit popup."""
        def show_popup():
            if success:
                result = messagebox.askyesno(
                    "Generation Complete",
                    "Meeting minutes have been generated successfully!\n\n"
                    "Would you like to generate another minutes file?\n\n"
                    "Click 'Yes' to generate another file, or 'No' to quit the application.",
                    default='yes'
                )
                
                if not result:  # User clicked 'No' - quit the application
                    self._graceful_exit()
            else:
                result = messagebox.askyesno(
                    "Generation Failed",
                    "There was an error generating the meeting minutes.\n\n"
                    "Would you like to try again?\n\n"
                    "Click 'Yes' to continue using the application, or 'No' to quit.",
                    default='yes'
                )
                
                if not result:  # User clicked 'No' - quit the application
                    self._graceful_exit()
        
        # Schedule the popup to run on the main thread
        self.after(100, show_popup)

    def _graceful_exit(self):
        """Gracefully exit the application."""
        try:
            self.quit()
            self.destroy()
        except:
            pass
        # Force exit to ensure terminal closes
        sys.exit(0)

# --- Run the App ---
if __name__ == "__main__":
    # Basic checks
    if not os.path.isdir("scripts"):
        print("ERROR: 'scripts' directory not found. Please run from repository root.")
        exit(1)
    
    config_path = resolve_config_path()
    if not os.path.exists(config_path):
        print(f"WARNING: config file not found at {config_path}. Defaults might be used.")
    
    app = MeetingSecretaryApp()
    app.mainloop()
