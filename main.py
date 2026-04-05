"""
main.py – Entry point for the enhanced AI Voice Agent.

Architecture
------------
* A :class:`~wake_word.WakeWordDetector` runs in a background daemon thread
  and fires a threading.Event when "Nikol" (or the configured wake word) is
  heard.
* The main thread idles until that event fires, then switches into command
  mode: it listens for one utterance, processes it, and resets the activation
  timer.
* The assistant returns to idle after ACTIVATION_TIMEOUT seconds of silence.
* Speech output (TTS) is always blocking so the microphone is not opened
  simultaneously, avoiding audio-device conflicts.

Run
---
    python main.py
"""

import sys
import threading
import time

import speech_recognition as sr

from command_processor import process_command
from config import ACTIVATION_TIMEOUT, WAKE_WORD
from listener import build_recognizer, listen, speak
from logger import setup_logger
from wake_word import WakeWordDetector

logger = setup_logger("main")

# ---------------------------------------------------------------------------
# Shared state between main thread and wake-word callback
# ---------------------------------------------------------------------------

_activation_event = threading.Event()   # set when wake word heard
_active_until: float = 0.0              # epoch time when activation expires


def _on_wake_word() -> None:
    """Callback invoked by the WakeWordDetector background thread."""
    global _active_until
    logger.info("Wake word callback fired.")
    _active_until = time.time() + ACTIVATION_TIMEOUT
    _activation_event.set()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main() -> None:
    speak(
        f"Hello! I am Nikol, your AI voice assistant. "
        f"Say '{WAKE_WORD}' to activate me, or say 'help' after waking me "
        f"to hear what I can do."
    )

    recognizer = build_recognizer()

    # Start background wake-word detector
    detector = WakeWordDetector(wake_word=WAKE_WORD, on_detected=_on_wake_word)
    try:
        detector.start()
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not start wake-word detector: %s", exc)
        speak("Microphone initialisation failed. Exiting.")
        sys.exit(1)

    logger.info("Entering main loop. Waiting for wake word '%s'.", WAKE_WORD)

    with sr.Microphone() as source:
        # Initial noise calibration for the command microphone
        logger.info("Calibrating command microphone…")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        while True:
            # ---- Idle: wait for wake word --------------------------------
            if not _activation_event.is_set():
                _activation_event.wait(timeout=0.5)
                continue

            # ---- Check timeout -------------------------------------------
            if time.time() > _active_until:
                logger.info("Activation timed out – returning to idle.")
                _activation_event.clear()
                detector.resume()   # re-enable wake-word detection
                continue

            # ---- Active: listen for a command ----------------------------
            # Pause the background detector so its microphone thread does
            # not compete for the audio device.
            detector.pause()

            speak("Listening…")
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(
                    source, timeout=ACTIVATION_TIMEOUT, phrase_time_limit=10
                )
            except sr.WaitTimeoutError:
                speak("I didn't hear anything. Going back to sleep – say my name to wake me.")
                _activation_event.clear()
                detector.resume()
                continue

            # Transcribe
            try:
                text = recognizer.recognize_google(audio).lower()
                logger.info("Heard: %s", text)
            except sr.UnknownValueError:
                speak("Sorry, I could not understand that.")
                # Stay active – give user another chance within the window
                detector.resume()
                continue
            except sr.RequestError as exc:
                speak("Speech recognition service is unavailable.")
                logger.error("STT RequestError: %s", exc)
                _activation_event.clear()
                detector.resume()
                continue

            # ---- Process -------------------------------------------------
            should_continue = process_command(text, speak)
            if not should_continue:
                detector.stop()
                break

            # Reset the activation window after a successful command
            global _active_until
            _active_until = time.time() + ACTIVATION_TIMEOUT
            detector.resume()


if __name__ == "__main__":
    main()
