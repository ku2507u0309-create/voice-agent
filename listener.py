"""
listener.py – Microphone input and text-to-speech output helpers.

Exports:
    speak(text)                   – Convert text to speech (blocking).
    listen(recognizer, source)    – Capture one utterance and return its text.
    build_recognizer()            – Create a pre-configured Recognizer instance.
"""

import speech_recognition as sr
import pyttsx3

from config import (
    ENERGY_THRESHOLD,
    LISTEN_TIMEOUT,
    PAUSE_THRESHOLD,
    PHRASE_TIME_LIMIT,
    TTS_RATE,
    TTS_VOLUME,
)
from logger import setup_logger

logger = setup_logger("listener")

# ---------------------------------------------------------------------------
# Text-to-speech engine (module-level singleton)
# ---------------------------------------------------------------------------


def _build_tts_engine() -> pyttsx3.Engine:
    """Initialise and configure the text-to-speech engine."""
    engine = pyttsx3.init()
    engine.setProperty("rate", TTS_RATE)
    engine.setProperty("volume", TTS_VOLUME)
    # Prefer a female voice (Zira on Windows) when available
    voices = engine.getProperty("voices")
    for voice in voices:
        if "zira" in voice.name.lower() or "female" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break
    return engine


_tts_engine: pyttsx3.Engine = _build_tts_engine()


def speak(text: str) -> None:
    """Convert *text* to speech and log it."""
    logger.info("Agent: %s", text)
    _tts_engine.say(text)
    _tts_engine.runAndWait()


# ---------------------------------------------------------------------------
# Speech recognition
# ---------------------------------------------------------------------------


def build_recognizer() -> sr.Recognizer:
    """Return a pre-configured :class:`sr.Recognizer` instance."""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = ENERGY_THRESHOLD
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = PAUSE_THRESHOLD
    return recognizer


def listen(
    recognizer: sr.Recognizer,
    source: sr.Microphone,
    *,
    timeout: int = LISTEN_TIMEOUT,
    announce: bool = True,
) -> str | None:
    """
    Capture a single utterance from *source* and return recognised text
    (lower-case), or *None* on any failure.

    Parameters
    ----------
    recognizer:
        A configured :class:`sr.Recognizer`.
    source:
        An open :class:`sr.Microphone` context.
    timeout:
        Maximum seconds to wait for speech to begin.
    announce:
        When *True*, speaks "Listening…" before capturing audio.
    """
    if announce:
        speak("Listening…")
    try:
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        audio = recognizer.listen(
            source, timeout=timeout, phrase_time_limit=PHRASE_TIME_LIMIT
        )
    except sr.WaitTimeoutError:
        if announce:
            speak("I didn't hear anything. Please try again.")
        return None

    try:
        text = recognizer.recognize_google(audio)
        logger.info("Heard: %s", text)
        return text.lower()
    except sr.UnknownValueError:
        if announce:
            speak("Sorry, I could not understand that.")
        return None
    except sr.RequestError as exc:
        speak("Speech recognition service is unavailable.")
        logger.error("RequestError: %s", exc)
        return None
