"""
voice_agent.py – Backward-compatible entry point for the AI Voice Agent.

This file preserves the original single-file interface. It delegates all work
to the new modular components so that existing users who run:

    python voice_agent.py

continue to get a fully working assistant (without wake-word detection, for
minimal-change compatibility).

For the full feature set including wake-word detection, background listening,
and NLU, run ``main.py`` instead:

    python main.py
"""

# Re-export public helpers from the new modules so that any code that imports
# from this file directly continues to work without modification.
# listen, speak, build_recognizer, and HELP_TEXT are intentionally exported.
from listener import build_recognizer, listen, speak  # noqa: F401
from command_processor import process_command as _process_command_new, HELP_TEXT  # noqa: F401
import speech_recognition as sr


def process_command(command: str) -> bool:
    """
    Backward-compatible wrapper: dispatch *command* using the new NLU engine.

    Returns *False* when the agent should stop, *True* to continue.
    """
    return _process_command_new(command, speak)


def main() -> None:
    """Original no-wake-word main loop – kept for backward compatibility."""
    speak(
        "Hello! I am your AI voice assistant. "
        "Say 'help' to hear what I can do, or 'exit' to quit. "
        "For wake-word support, run main.py instead."
    )

    recognizer = build_recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        while True:
            command = listen(recognizer, source)
            if command is None:
                continue
            should_continue = process_command(command)
            if not should_continue:
                break


if __name__ == "__main__":
    main()
