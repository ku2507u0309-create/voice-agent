"""
config.py – Central configuration for the AI Voice Agent.

All tuneable constants live here so that no other module needs to be edited
for basic customisation.
"""

import os

# ---------------------------------------------------------------------------
# Wake word
# ---------------------------------------------------------------------------
WAKE_WORD: str = "kitty"          # Lower-case; detection is case-insensitive
ACTIVATION_TIMEOUT: int = 10      # Seconds to stay active after wake word

# ---------------------------------------------------------------------------
# Speech recognition
# ---------------------------------------------------------------------------
ENERGY_THRESHOLD: int = 300       # Microphone sensitivity (higher = less sensitive)
PAUSE_THRESHOLD: float = 0.8      # Seconds of silence that mark end-of-speech
LISTEN_TIMEOUT: int = 10          # Max seconds to wait for speech to start
PHRASE_TIME_LIMIT: int = 10       # Max seconds for a single phrase

# ---------------------------------------------------------------------------
# Text-to-speech
# ---------------------------------------------------------------------------
TTS_RATE: int = 170               # Words per minute
TTS_VOLUME: float = 1.0           # 0.0 – 1.0

# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------
SHUTDOWN_DELAY_SECONDS: int = 10  # Grace period before shutdown/restart

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
NOTES_FILE: str = "notes.json"    # Persistent notes store

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE: str = "voice_agent.log" # Debug log file

# ---------------------------------------------------------------------------
# Claude / Anthropic (optional NLU backend)
# ---------------------------------------------------------------------------
# Set the CLAUDE_API_KEY environment variable to enable Claude-powered intent
# detection.  If the variable is absent or the 'anthropic' package is not
# installed the assistant falls back to the built-in rule-based system.
CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL: str = "claude-3-haiku-20240307"  # Fast, cheap model for NLU
