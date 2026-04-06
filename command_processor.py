"""
command_processor.py – Natural-language intent detection and command dispatch.

Intent detection strategy
--------------------------
1. **Claude API** (optional): If the ``anthropic`` package is installed and
   ``CLAUDE_API_KEY`` is set in the environment, a lightweight Claude prompt
   is used to classify the user's utterance into a structured intent.
2. **Rule-based fallback**: A list of keyword/regex rules is applied when the
   Claude backend is unavailable or returns an error.

All action execution is delegated to ``actions`` and ``notes_manager``.
"""

import os
import re
from typing import Callable, Optional, Tuple

import actions
import notes_manager
from config import CLAUDE_API_KEY, CLAUDE_MODEL
from logger import setup_logger

logger = setup_logger("command_processor")

SpeakFn = Callable[[str], None]

# ---------------------------------------------------------------------------
# Claude / Anthropic integration (optional)
# ---------------------------------------------------------------------------

try:
    import anthropic as _anthropic_lib  # type: ignore[import]
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

_CLAUDE_CLIENT = None
if _ANTHROPIC_AVAILABLE and CLAUDE_API_KEY:
    _CLAUDE_CLIENT = _anthropic_lib.Anthropic(api_key=CLAUDE_API_KEY)


_CLAUDE_SYSTEM_PROMPT = """
You are an intent classifier for a voice assistant.
Given a user utterance, reply with EXACTLY one line in this format:
INTENT: <intent_name> | DATA: <extracted_data_or_empty>

Valid intents and example data:
- exit | (no data)
- help | (no data)
- add_note | the note content
- show_notes | (no data)
- search_youtube | search query
- open_youtube | (no data)
- search_google | search query
- open_google | (no data)
- open_wikipedia | topic
- tell_time | (no data)
- tell_date | (no data)
- open_notepad | (no data)
- open_calculator | (no data)
- open_file_explorer | (no data)
- open_vscode | (no data)
- take_screenshot | (no data)
- open_settings | (no data)
- increase_volume | (no data)
- decrease_volume | (no data)
- mute_volume | (no data)
- lock_computer | (no data)
- shutdown | (no data)
- restart | (no data)
- cancel_shutdown | (no data)
- unknown | (no data)

Examples:
"Let's watch some videos" → INTENT: open_youtube | DATA:
"I want to code today" → INTENT: open_vscode | DATA:
"note this buy milk" → INTENT: add_note | DATA: buy milk
"what is 2 + 2 on google" → INTENT: search_google | DATA: 2 + 2
""".strip()


def _detect_intent_claude(command: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Use Claude to classify *command* into an (intent, data) tuple.
    Returns *None* if the call fails so the caller can fall back.
    """
    if _CLAUDE_CLIENT is None:
        return None
    try:
        message = _CLAUDE_CLIENT.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=64,
            system=_CLAUDE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": command}],
        )
        reply = message.content[0].text.strip()
        logger.debug("Claude reply: %s", reply)
        # Parse "INTENT: foo | DATA: bar"
        # Use [^|]* for data to avoid consuming extra pipes; limit to 512 chars.
        match = re.match(r"INTENT:\s*(\w+)\s*\|\s*DATA:\s*([^|]*)", reply)
        if match:
            intent = match.group(1).strip()
            raw_data = match.group(2).strip()
            # Sanitise: cap length and strip control characters
            raw_data = raw_data[:512].strip()
            data: Optional[str] = raw_data or None
            return intent, data
    except Exception as exc:  # noqa: BLE001
        logger.warning("Claude intent detection failed: %s", exc)
    return None


# ---------------------------------------------------------------------------
# Rule-based intent detection
# ---------------------------------------------------------------------------

# Each rule is a dict with either:
#   "patterns": list[str]  – regex patterns; first capture group becomes data
#   "keywords": list[str]  – plain substring checks
# and always "intent": str.
_INTENT_RULES = [
    # Exit / stop
    {
        "keywords": ["exit", "quit", "goodbye", "bye", "stop"],
        "intent": "exit",
    },
    # Help
    {"keywords": ["help"], "intent": "help"},
    # Notes
    {
        "patterns": [
            r"note this (.+)",
            r"remember this (.+)",
            r"save note (.+)",
            r"note that (.+)",
            r"note (.+)",
        ],
        "intent": "add_note",
    },
    {
        "keywords": [
            "show my notes",
            "read my notes",
            "my notes",
            "show notes",
            "list notes",
        ],
        "intent": "show_notes",
    },
    # YouTube
    {
        "patterns": [
            r"search youtube (?:for )?(.+)",
            r"youtube search (.+)",
            r"find (.+) on youtube",
        ],
        "intent": "search_youtube",
    },
    {
        "keywords": [
            "youtube",
            "watch something",
            "watch a video",
            "watch videos",
        ],
        "intent": "open_youtube",
    },
    # Google
    {
        "patterns": [
            r"search google (?:for )?(.+)",
            r"google search (.+)",
            r"search for (.+)",
            r"google (.+)",
        ],
        "intent": "search_google",
    },
    {"keywords": ["open google", "go to google"], "intent": "open_google"},
    # Wikipedia
    {
        "patterns": [
            r"wikipedia (.+)",
            r"look up (.+) on wikipedia",
            r"search wikipedia for (.+)",
        ],
        "intent": "open_wikipedia",
    },
    # Time & date
    {
        "keywords": ["what time", "current time", "tell me the time", "what's the time"],
        "intent": "tell_time",
    },
    {
        "keywords": [
            "what date",
            "today's date",
            "tell me the date",
            "what day",
            "what is today",
        ],
        "intent": "tell_date",
    },
    # Applications
    {"keywords": ["notepad"], "intent": "open_notepad"},
    {"keywords": ["calculator", "calc"], "intent": "open_calculator"},
    {"keywords": ["file explorer", "open explorer"], "intent": "open_file_explorer"},
    {
        "keywords": [
            "vs code",
            "vscode",
            "visual studio code",
            "let's code",
            "lets code",
            "start coding",
            "open code",
        ],
        "intent": "open_vscode",
    },
    {"keywords": ["screenshot", "screen shot"], "intent": "take_screenshot"},
    {"keywords": ["settings"], "intent": "open_settings"},
    # Volume
    {"keywords": ["increase volume", "volume up", "louder"], "intent": "increase_volume"},
    {"keywords": ["decrease volume", "volume down", "quieter", "lower volume"], "intent": "decrease_volume"},
    {"keywords": ["mute"], "intent": "mute_volume"},
    # Power management
    {"keywords": ["cancel shutdown", "abort shutdown"], "intent": "cancel_shutdown"},
    {"keywords": ["lock computer", "lock screen", "lock my computer"], "intent": "lock_computer"},
    {"keywords": ["shutdown", "shut down", "power off", "turn off"], "intent": "shutdown"},
    {"keywords": ["restart", "reboot"], "intent": "restart"},
]


def _detect_intent_rules(command: str) -> Tuple[str, Optional[str]]:
    """
    Apply the rule table to *command* and return ``(intent, data)``.
    Returns ``("unknown", None)`` when no rule matches.
    """
    for rule in _INTENT_RULES:
        if "patterns" in rule:
            for pattern in rule["patterns"]:
                match = re.search(pattern, command)
                if match:
                    groups = match.groups()
                    data = groups[0].strip() if groups else None
                    return rule["intent"], data
        elif "keywords" in rule:
            for kw in rule["keywords"]:
                if kw in command:
                    return rule["intent"], None
    return "unknown", None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

HELP_TEXT = (
    "Here are the commands I understand: "
    "open YouTube, search YouTube, open Google, search Google, "
    "open Wikipedia, what time is it, what is today's date, "
    "open Notepad, open Calculator, open File Explorer, open VS Code, "
    "take a screenshot, open Settings, "
    "increase volume, decrease volume, mute, "
    "note this, show my notes, "
    "lock computer, shutdown, cancel shutdown, restart, "
    "help, and exit."
)


def detect_intent(command: str) -> Tuple[str, Optional[str]]:
    """
    Return ``(intent, data)`` for *command*.

    Tries Claude first (if configured), then falls back to the rule-based
    system.
    """
    result = _detect_intent_claude(command)
    if result is not None:
        logger.info("Intent (Claude): %s | data: %s", result[0], result[1])
        return result

    intent, data = _detect_intent_rules(command)
    logger.info("Intent (rules): %s | data: %s", intent, data)
    return intent, data


def process_command(command: str, speak: SpeakFn) -> bool:
    """
    Detect the intent of *command*, execute the appropriate action, and use
    *speak* to give voice feedback.

    Returns *True* to continue the main loop, *False* to exit.
    """
    logger.info("Processing command: '%s'", command)
    intent, data = detect_intent(command)

    # --- Exit ---
    if intent == "exit":
        speak("Goodbye! Have a great day.")
        return False

    # --- Help ---
    elif intent == "help":
        speak(HELP_TEXT)

    # --- Notes ---
    elif intent == "add_note":
        if data:
            notes_manager.add_note(data)
            speak(f"Got it, I've saved your note: {data}.")
        else:
            speak("What would you like me to note?")

    elif intent == "show_notes":
        speak(notes_manager.get_notes_as_text())

    # --- YouTube ---
    elif intent == "search_youtube":
        actions.search_youtube(data or "", speak)
    elif intent == "open_youtube":
        actions.open_youtube(speak)

    # --- Google ---
    elif intent == "search_google":
        actions.search_google(data or "", speak)
    elif intent == "open_google":
        actions.open_google(speak)

    # --- Wikipedia ---
    elif intent == "open_wikipedia":
        actions.open_wikipedia(data or "", speak)

    # --- Time & date ---
    elif intent == "tell_time":
        actions.tell_time(speak)
    elif intent == "tell_date":
        actions.tell_date(speak)

    # --- Applications ---
    elif intent == "open_notepad":
        actions.open_notepad(speak)
    elif intent == "open_calculator":
        actions.open_calculator(speak)
    elif intent == "open_file_explorer":
        actions.open_file_explorer(speak)
    elif intent == "open_vscode":
        actions.open_vscode(speak)
    elif intent == "take_screenshot":
        actions.take_screenshot(speak)
    elif intent == "open_settings":
        actions.open_settings(speak)

    # --- Volume ---
    elif intent == "increase_volume":
        actions.increase_volume(speak)
    elif intent == "decrease_volume":
        actions.decrease_volume(speak)
    elif intent == "mute_volume":
        actions.mute_volume(speak)

    # --- Power ---
    elif intent == "lock_computer":
        actions.lock_computer(speak)
    elif intent == "cancel_shutdown":
        actions.cancel_shutdown(speak)
    elif intent == "shutdown":
        actions.shutdown_computer(speak)
    elif intent == "restart":
        actions.restart_computer(speak)

    # --- Unknown ---
    else:
        speak(
            "I'm not sure how to handle that. Say 'help' to hear available commands."
        )

    return True
