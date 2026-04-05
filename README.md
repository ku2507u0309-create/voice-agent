# AI Voice Agent

A production-ready, voice-controlled AI PC agent for Windows built with Python.
Speak a command and the agent opens websites, searches the web, controls
Windows applications, manages system power, and more — all hands-free.

---

## Features

| Voice Command | Action |
|---|---|
| `open youtube` | Opens YouTube in the default browser |
| `search youtube <query>` | Searches YouTube for the given query |
| `open google` | Opens Google in the default browser |
| `search google <query>` | Searches Google for the given query |
| `wikipedia <topic>` | Opens a Wikipedia search for the topic |
| `what time is it` | Speaks the current time |
| `what is today's date` | Speaks the current date |
| `open notepad` | Launches Notepad |
| `open calculator` | Launches Calculator |
| `open file explorer` | Launches File Explorer |
| `take a screenshot` | Opens the Snipping Tool |
| `open settings` | Opens Windows Settings |
| `increase volume` / `volume up` | Increases system volume |
| `decrease volume` / `volume down` | Decreases system volume |
| `mute` | Toggles system mute |
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
> pip install PyAudio‑0.2.13‑cpXX‑cpXX‑win_amd64.whl
> ```

---

## Usage

```bash
python voice_agent.py
```

The agent will greet you and start listening.  Speak any command from the table
above clearly and wait for it to respond.

---

## Project Structure

```
voice-agent/
├── voice_agent.py   # Main agent – TTS engine, speech recognition, command dispatcher
├── requirements.txt # Python dependencies
└── README.md        # This file
```

---

## Architecture

```
Microphone ──► SpeechRecognition (Google STT) ──► process_command()
                                                        │
               ┌────────────────────────────────────────┤
               │                                        │
            pyttsx3 (TTS)                   webbrowser / os / subprocess
            (voice responses)               (system actions)
```

### Key modules

| Module | Role |
|---|---|
| `speech_recognition` | Captures audio from the microphone and converts it to text via the Google Web Speech API |
| `pyttsx3` | Converts agent responses to speech offline using the Windows SAPI5 engine |
| `webbrowser` | Opens URLs in the system default browser |
| `subprocess` | Launches native Windows executables (Notepad, Calculator, etc.) |
| `os` | File-system helpers (e.g. creating the screenshot output directory) |

---

## Configuration

You can tweak the following constants directly in `voice_agent.py`:

| Variable | Default | Description |
|---|---|---|
| `engine.setProperty("rate", 170)` | 170 wpm | Speech rate |
| `recognizer.energy_threshold` | 300 | Microphone sensitivity |
| `recognizer.pause_threshold` | 0.8 s | Silence before end-of-utterance |

---

## License

MIT
