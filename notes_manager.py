"""
notes_manager.py – Persistent note storage backed by a local JSON file.

Notes are stored as a list of objects with ``content`` and ``timestamp`` keys.
"""

import datetime
import json
import os
from typing import List

from config import NOTES_FILE
from logger import setup_logger

logger = setup_logger("notes_manager")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load() -> List[dict]:
    """Load all notes from the JSON file, returning an empty list on failure."""
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Could not load notes from '%s': %s", NOTES_FILE, exc)
        return []


def _save(notes: List[dict]) -> None:
    """Persist *notes* to the JSON file."""
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as fh:
            json.dump(notes, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        logger.error("Could not save notes to '%s': %s", NOTES_FILE, exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def add_note(content: str) -> dict:
    """Append a timestamped note and persist it.  Returns the new note dict."""
    content = content.strip()
    note = {
        "content": content,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    notes = _load()
    notes.append(note)
    _save(notes)
    logger.info("Note saved: %s", content)
    return note


def get_notes() -> List[dict]:
    """Return all stored notes as a list of dicts."""
    return _load()


def get_notes_as_text() -> str:
    """Return a human-readable string of all notes, or a placeholder message."""
    notes = _load()
    if not notes:
        return "You have no saved notes."
    lines: List[str] = []
    for i, note in enumerate(notes, start=1):
        try:
            dt = datetime.datetime.fromisoformat(note["timestamp"])
            # Convert to local time for a friendlier display
            local_dt = dt.astimezone()
            time_str = local_dt.strftime("%B %d at %I:%M %p")
        except (KeyError, ValueError):
            time_str = "unknown time"
        lines.append(f"Note {i}, saved on {time_str}: {note['content']}")
    return ". ".join(lines)
