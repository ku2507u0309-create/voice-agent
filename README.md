# AI Voice Agent

A production-ready, voice-controlled AI PC agent for Windows built with Python.
Speak a command and the agent opens websites, searches the web, controls
Windows applications, manages system power, takes notes, and more — all hands-free.

---

## What's New (v2)

| Feature | Details |
|---|---|
| **Wake word** | Say **"Kitty"** to activate; the assistant stays idle until called |
| **Notes** | "Note this…" / "Remember this…" saves notes to `notes.json`; "Show my notes" reads them back |
| **Natural-language commands** | "Let's code" → opens VS Code; "I want to watch something" → opens YouTube |
| **Modular codebase** | Split into `config`, `logger`, `listener`, `wake_word`, `actions`, `command_processor`, `notes_manager`, `main` |
| **Optional Claude NLU** | Set `CLAUDE_API_KEY` for smarter intent detection; falls back to built-in rules |
| **Debug log file** | `voice_agent.log` (rotated, 2 MB) |
| **VS Code launcher** | Opens via PATH or Windows registry lookup |
| **Backward compatible** | `python voice_agent.py` still works as before |

---

## Features

| Voice Command | Action |
|---|---|
| `kitty` (wake word) | Activates the assistant for 10 seconds |
| `open youtube` / `I want to watch something` | Opens YouTube in the default browser |
| `search youtube <query>` | Searches YouTube for the given query |
| `open google` | Opens Google in the default browser |
| `search google <query>` / `search for <query>` | Searches Google for the given query |
| `wikipedia <topic>` | Opens a Wikipedia search for the topic |
| `what time is it` | Speaks the current time |
| `what is today's date` | Speaks the current date |
| `open notepad` | Launches Notepad |
| `open calculator` | Launches Calculator |
| `open file explorer` | Launches File Explorer |
| `open vs code` / `let's code` | Launches Visual Studio Code |
| `take a screenshot` | Opens the Snipping Tool |
| `open settings` | Opens Windows Settings |
| `increase volume` / `volume up` | Increases system volume |
| `decrease volume` / `volume down` | Decreases system volume |
| `mute` | Toggles system mute |
| `note this <text>` / `remember this <text>` | Saves a timestamped note |
| `show my notes` | Reads all saved notes aloud |
| `lock computer` | Locks the workstation |
| `shutdown` | Shuts the PC down in 10 seconds |
| `cancel shutdown` | Cancels a pending shutdown |
| `restart` | Restarts the PC in 10 seconds |
| `help` | Lists all available commands |
| `exit` / `quit` / `goodbye` | Stops the agent |

---

## Requirements

- **Python** 3.10 or later
- **Windows** 10 / 11 (some commands such as `notepad.exe` are Windows-specific)
- A working **microphone**
- An active **internet connection** (for Google Speech Recognition)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/ku2507u0309-create/voice-agent.git
cd voice-agent

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

> **PyAudio trouble?**  If `pip install pyaudio` fails on Windows, download the
> pre-built wheel that matches your Python version from
> <https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio> and install it with:
> ```
> pip install PyAudio-0.2.13-cpXX-cpXX-win_amd64.whl
> ```

---

## Usage

### Full assistant with wake word (recommended)

```bash
python main.py
```

Say **"Kitty"** to wake the assistant, then speak your command.  
The assistant goes back to sleep after 10 seconds of inactivity.

### Backward-compatible mode (no wake word)

```bash
python voice_agent.py
```

The assistant starts listening immediately, just like v1.

### Optional: Claude-powered NLU

```bash
# Install the Anthropic library
pip install anthropic

# Set your API key (PowerShell)
$env:CLAUDE_API_KEY = "sk-ant-..."

python main.py
```

When the key is present the assistant uses Claude for smarter intent
detection.  It falls back to the built-in rule-based system automatically if
the API is unavailable.

---

## Project Structure

```
voice-agent/
├── main.py              # Entry point – wake-word loop and main orchestration
├── voice_agent.py       # Backward-compatible entry point (no wake word)
├── config.py            # All configuration constants
├── logger.py            # Logging setup (console + rotating file)
├── listener.py          # TTS (speak) and STT (listen) helpers
├── wake_word.py         # WakeWordDetector – background daemon thread
├── command_processor.py # Intent detection (Claude + rule-based) and dispatch
├── actions.py           # System action handlers (web, apps, volume, power)
├── notes_manager.py     # Persistent JSON notes storage
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## Architecture

```
                  ┌──────────────────────┐
                  │  WakeWordDetector    │  (background daemon thread)
                  │  listen_in_background│
                  └──────────┬───────────┘
                             │ wake word heard → _activation_event.set()
                             ▼
Microphone ──► listener.listen() ──► command text
                             │
                             ▼
                  command_processor.process_command()
                  ┌──────────┴───────────┐
                  │  Claude NLU (opt.)   │
                  │  Rule-based fallback │
                  └──────────┬───────────┘
                             │ intent + data
                  ┌──────────┴───────────┐
                  │  actions.py          │  webbrowser / subprocess / os
                  │  notes_manager.py    │  notes.json
                  └──────────┬───────────┘
                             │
                  listener.speak() ──► pyttsx3 TTS
```

### Module responsibilities

| Module | Role |
|---|---|
| `config.py` | Wake word, timeouts, TTS rate, file paths, API key |
| `logger.py` | Console + rotating-file logger factory |
| `listener.py` | `speak()` (pyttsx3) and `listen()` (Google STT) |
| `wake_word.py` | `WakeWordDetector` – detects wake word in a background thread |
| `command_processor.py` | Intent classification (Claude → rules) and action dispatch |
| `actions.py` | All system actions (web, apps, volume, power) |
| `notes_manager.py` | CRUD for `notes.json` with ISO-8601 timestamps |
| `main.py` | Wake-word loop, activation timer, command loop |
| `voice_agent.py` | Legacy entry point; delegates to new modules |

---

## Configuration

Edit `config.py` to customise the assistant:

| Constant | Default | Description |
|---|---|---|
| `WAKE_WORD` | `"kitty"` | Wake word (lower-case) |
| `ACTIVATION_TIMEOUT` | `10` | Seconds active after wake word |
| `TTS_RATE` | `170` | Speech rate (words per minute) |
| `ENERGY_THRESHOLD` | `300` | Microphone sensitivity |
| `SHUTDOWN_DELAY_SECONDS` | `10` | Grace period for shutdown/restart |
| `NOTES_FILE` | `"notes.json"` | Notes storage path |
| `LOG_FILE` | `"voice_agent.log"` | Debug log path |
| `CLAUDE_MODEL` | `"claude-3-haiku-20240307"` | Claude model for NLU |

---

## License

MIT
