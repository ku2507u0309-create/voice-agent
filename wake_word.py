"""
wake_word.py – Background wake-word detection using a daemon thread.

The :class:`WakeWordDetector` opens the microphone in a background daemon
thread via ``listen_in_background`` so that the main thread remains free to
speak or process commands.  When the configured wake word is heard the
detector calls the user-supplied *on_detected* callback and suppresses further
detections until :meth:`reset` is called.

Usage::

    def handle_wake():
        print("Wake word heard!")

    detector = WakeWordDetector(on_detected=handle_wake)
    detector.start()
    # … do other things …
    detector.stop()
"""

import threading

import speech_recognition as sr

from config import ENERGY_THRESHOLD, PAUSE_THRESHOLD, WAKE_WORD
from logger import setup_logger

logger = setup_logger("wake_word")


class WakeWordDetector:
    """
    Listens for *wake_word* in a background daemon thread.

    Parameters
    ----------
    wake_word:
        The phrase to listen for (case-insensitive, default from config).
    on_detected:
        Zero-argument callable invoked on the background thread when the wake
        word is first detected.  Must be thread-safe.
    phrase_time_limit:
        Maximum seconds of audio to send to the recogniser per chunk.
    """

    def __init__(
        self,
        wake_word: str = WAKE_WORD,
        on_detected: callable = None,
        phrase_time_limit: int = 4,
    ) -> None:
        self.wake_word = wake_word.lower()
        self.on_detected = on_detected
        self.phrase_time_limit = phrase_time_limit

        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = ENERGY_THRESHOLD
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = PAUSE_THRESHOLD

        # Threading primitives
        self._detected = threading.Event()   # set while waiting for reset
        self._paused = threading.Event()     # set while main loop is active
        self._stop_fn = None                 # stopper returned by listen_in_background

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Open the microphone and begin background detection."""
        mic = sr.Microphone()
        with mic as source:
            logger.info("Calibrating wake-word microphone…")
            self._recognizer.adjust_for_ambient_noise(source, duration=1)

        self._stop_fn = self._recognizer.listen_in_background(
            mic, self._audio_callback, phrase_time_limit=self.phrase_time_limit
        )
        logger.info("Wake-word detector started – listening for '%s'.", self.wake_word)

    def stop(self) -> None:
        """Stop background listening."""
        if self._stop_fn is not None:
            self._stop_fn(wait_for_stop=False)
            self._stop_fn = None
        logger.info("Wake-word detector stopped.")

    def pause(self) -> None:
        """
        Temporarily suppress detection callbacks (e.g. while a command is
        being processed so that command audio is not mistaken for a new
        wake-word event).
        """
        self._paused.set()

    def resume(self) -> None:
        """Re-enable detection callbacks and clear the detected flag."""
        self._detected.clear()
        self._paused.clear()

    def reset(self) -> None:
        """Clear the detected flag so the detector can fire again."""
        self._detected.clear()

    @property
    def is_detected(self) -> bool:
        """True if the wake word was heard and has not yet been reset."""
        return self._detected.is_set()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _audio_callback(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        """
        Called by the background thread for every captured audio chunk.
        Checks whether the wake word is present and fires *on_detected*.
        """
        # Skip if paused or already pending acknowledgement
        if self._paused.is_set() or self._detected.is_set():
            return

        try:
            text = recognizer.recognize_google(audio).lower()
            logger.debug("Wake-word listener heard: '%s'", text)
            if self.wake_word in text:
                logger.info("Wake word '%s' detected!", self.wake_word)
                self._detected.set()
                if self.on_detected is not None:
                    self.on_detected()
        except sr.UnknownValueError:
            pass  # unintelligible audio – ignore silently
        except sr.RequestError as exc:
            logger.warning("Wake-word STT error: %s", exc)
