# Installation & First Run Tutorial

> This walkthrough is written for people who are **new to Python, coming from Windows/macOS/Linux, or simply unsure where to start**. Follow the numbered steps in order—each ends with a quick checklist so you know you are ready to move on.

---

## 1. Before You Begin

| What you need | Why you need it |
| --- | --- |
| A computer with Windows 10/11, macOS 12+, or Ubuntu/Debian (or WSL on Windows) | Supported platforms |
| Internet access | To download dependencies and WhisperX models |
| A Hugging Face account (optional but recommended) | Required for WhisperX medium/large models |

**Terminology recap (for newcomers):**
- **Conda / Mamba** – tools that create isolated Python environments so you can install packages without breaking system Python.
- **ffmpeg** – command-line utility WhisperX uses to read audio/video files.
- **LibreOffice / Word** – lets you open the generated `.docx` minutes.

---

## 2. Step-by-Step Installation

### Step 2.1 – Install the system tools

#### Windows 10/11 (PowerShell)
1. **Open PowerShell as Administrator** (right-click → *Run as administrator*).
2. **Install Git and ffmpeg** via Windows Package Manager:
   ```powershell
   winget install --id Git.Git -e
   winget install --id Gyan.FFmpeg -e
   ```
   (If `winget` is unavailable, install [Git for Windows](https://git-scm.com/download/win) and download ffmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).)
3. **Install Miniforge (recommended)**
   - Download the latest `Miniforge3-Windows-x86_64.exe` from the [conda-forge releases page](https://github.com/conda-forge/miniforge#miniforge3).
   - Run the installer → keep “Add Miniforge3 to PATH” checked.
4. **Initialize Conda for PowerShell**:
   ```powershell
   conda init powershell
   ```
   Close and reopen PowerShell so the change takes effect.
5. *(Optional)* Install LibreOffice:
   ```powershell
   winget install --id TheDocumentFoundation.LibreOffice -e
   ```

> *Prefer WSL?* Run `wsl --install`, reboot, then follow the **Linux** instructions below inside the Ubuntu shell. WSL is great if you want the same experience as Linux/macOS.

#### macOS 12+ (zsh)
1. Install the Apple Command Line Tools once:
   ```zsh
   xcode-select --install
   ```
2. Install [Homebrew](https://brew.sh):
   ```zsh
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
   eval "$(/opt/homebrew/bin/brew shellenv)"
   ```
3. Install Miniforge or Mambaforge:
   ```zsh
   brew install miniforge   # or: brew install mambaforge
   conda init zsh
   exec $SHELL
   ```
4. Install system utilities:
   ```zsh
   brew install ffmpeg
   brew install --cask libreoffice   # optional but helpful
   ```

#### Ubuntu/Debian (bash)
```bash
sudo apt update
sudo apt install -y git ffmpeg libreoffice
```
Install Miniforge:
```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
source ~/miniforge3/bin/activate
conda init bash
exec $SHELL
```

✅ **Checkpoint:** `git --version`, `conda --version`, and `ffmpeg -version` all work in your terminal.

---

### Step 2.2 – Create a workspace and clone the repo

```bash
mkdir -p ~/Projects && cd ~/Projects
git clone https://github.com/FritscheLab/MeetingSecretaryAI.git
cd MeetingSecretaryAI
```

On Windows, run the same commands in PowerShell (paths will be under `C:\Users\<you>\Projects`). If Git prompts for credentials, use your GitHub username or PAT.

✅ **Checkpoint:** `pwd` (or `Get-Location`) ends with `MeetingSecretaryAI`.

---

### Step 2.3 – Create the Python environment

We test with Python 3.9. Create an isolated environment so dependencies do not fight with system Python.

```bash
conda create -n meetingsecretaryai_env python=3.9 -y
conda activate meetingsecretaryai_env
```

Prefer mamba? Swap `conda create` with `mamba create`. Prefer `venv`? See Appendix B.

✅ **Checkpoint:** `python --version` prints `3.9.x` and the prompt shows `(meetingsecretaryai_env)`.

---

### Step 2.4 – Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If installation fails because of Torch/onnxruntime on Windows, make sure the Miniforge (not Microsoft Store) Python is active. For Apple Silicon, Conda automatically installs the correct arm64 wheels.

✅ **Checkpoint:** `python - <<'PY' ...` snippet below runs without errors:
```bash
python - <<'PY'
import tkinter, whisperx
print("tkinter OK, whisperx OK")
PY
```

---

### Step 2.5 – Configure optional services

1. **Hugging Face token (for larger WhisperX models)**
   ```bash
   mkdir -p ../MeetingSecretaryAI_Data
   echo "hf_your_token_here" > ../MeetingSecretaryAI_Data/.hf_token.txt
   ```
   You can also paste the token into the GUI (Settings → WhisperX).
2. **Azure OpenAI credentials**
   - Copy `.env.example` to `.env` and fill in the Azure endpoint/key values.
3. **Custom templates**
   - Place DOCX/Markdown templates under `doc/templates/` and update `config.ini` if needed.

✅ **Checkpoint:** `.env` exists and contains your keys (or plan to enter them through the GUI later).

---

### Step 2.6 – Verify the installation

```bash
python - <<'PY'
import tkinter, whisperx
print("Python deps OK")
PY

ffmpeg -version
pytest -q   # optional smoke test
```

If `pytest` is missing, install it with `pip install pytest`.

✅ **Checkpoint:** No errors from the commands above.

---

### Step 2.7 – Launch the app

- **GUI (easiest)**
  ```bash
  conda activate meetingsecretaryai_env
  python meeting_secretary_gui.py
  ```
  On macOS you can also double-click `launch_with_diagnostics.command`.

- **CLI workflow**
  ```bash
  python scripts/transcript2json.py sample.vtt > meeting.json
  python scripts/json_refine.py --input_json meeting.json --output_json meeting_refined.json
  python scripts/json2word.py meeting_refined.json
  bash scripts/generate_minutes.sh   # convenience wrapper
  ```

Keep `meetingsecretaryai_env` activated whenever you work with the project.

---

## 3. Keeping the Installation Healthy

- Update dependencies occasionally:
  ```bash
  conda activate meetingsecretaryai_env
  conda update --all
  pip install --upgrade -r requirements.txt
  ```
- Back up your `.env`, templates, and generated data (output lives in `output/` by default).
- If you switch machines, copy the whole repo plus the `../MeetingSecretaryAI_Data` folder that stores tokens.

---

## 4. Troubleshooting / FAQ

| Issue | Fix |
| --- | --- |
| `conda` command not found | Re-run `conda init <shell>` and restart the terminal. On Windows ensure you launched the *Miniforge Prompt* or PowerShell **after** running `conda init`. |
| `ffmpeg` missing or wrong version | Verify `ffmpeg -version`. If not found, reinstall via winget/brew/apt. Add it to PATH on Windows if you unpacked a ZIP manually. |
| `ImportError: No module named whisperx` | Confirm the env is active (`conda activate meetingsecretaryai_env`) and reinstall `pip install whisperx`. |
| GUI cannot access Zoom folder on macOS | System Settings → Privacy & Security → Files and Folders → allow Terminal or Python to access Documents. |
| Long path errors on Windows | Enable long paths once: run `reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f` from an elevated PowerShell and reboot. |
| Slow installs on Windows | Use Mambaforge so `mamba` resolves dependencies faster: `winget install --id CondaForge.Mambaforge -e`. |

Need more help? Open an issue with your OS version, Python version, and the exact command/output.

---

## 5. Uninstall / Reset

```bash
conda deactivate || true
conda env remove -n meetingsecretaryai_env -y
```

Remove optional system packages with `winget uninstall`, `brew uninstall`, or `sudo apt remove` as needed. You can delete the repo folder to remove code, and delete `../MeetingSecretaryAI_Data` if you no longer need cached tokens/models.

---

## Appendix A – Windows Tips

- **Use the Miniforge Prompt** (installed with Miniforge) if PowerShell keeps launching the wrong Python.
- **File paths**: When commands show `~/Projects`, translate to `C:\Users\<you>\Projects`.
- **GPU acceleration**: WhisperX can use NVIDIA GPUs if you install CUDA-enabled PyTorch inside the same environment. Follow the [official instructions](https://pytorch.org/get-started/locally/) and then reinstall WhisperX.

---

## Appendix B – Installing without Conda (advanced)

Conda handles native dependencies (onnxruntime, PyTorch) for you. If you cannot use Conda:

```bash
python3.9 -m venv .venv
source .venv/bin/activate      # PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

You must manually install ffmpeg and ensure the correct wheel builds exist for your platform.
