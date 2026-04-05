"""
AI Voice-Controlled PC Agent for Windows
=========================================
A production-ready voice assistant that accepts spoken commands and performs
system actions such as opening websites, searching the web, and controlling
common Windows applications.

Dependencies:
    pip install SpeechRecognition pyttsx3 pyaudio
"""

import datetime
import logging
import os
import subprocess
import sys
import webbrowser

import pyttsx3
import speech_recognition as sr

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SHUTDOWN_DELAY_SECONDS = 10

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# TTS engine
# ---------------------------------------------------------------------------


def _build_tts_engine() -> pyttsx3.Engine:
    """Initialise and configure the text-to-speech engine."""
    engine = pyttsx3.init()
    # Slightly slower rate is easier to understand
    engine.setProperty("rate", 170)
    engine.setProperty("volume", 1.0)
    # Prefer a female voice when available (optional, falls back gracefully)
    voices = engine.getProperty("voices")
    for voice in voices:
        if "zira" in voice.name.lower() or "female" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break
    return engine


_tts_engine = _build_tts_engine()


def speak(text: str) -> None:
    """Convert *text* to speech and log it."""
    logger.info("Agent: %s", text)
    _tts_engine.say(text)
    _tts_engine.runAndWait()


# ---------------------------------------------------------------------------
# Speech recognition
# ---------------------------------------------------------------------------


def listen(recognizer: sr.Recognizer, source: sr.Microphone) -> str | None:
    """
    Listen for a single utterance from *source* and return the recognised text
    in lower-case, or *None* on failure.
    """
    speak("Listening…")
    try:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
    except sr.WaitTimeoutError:
        speak("I didn't hear anything. Please try again.")
        return None

    try:
        text = recognizer.recognize_google(audio)
        logger.info("Heard: %s", text)
        return text.lower()
    except sr.UnknownValueError:
        speak("Sorry, I could not understand that.")
        return None
    except sr.RequestError as exc:
        speak("Speech recognition service is unavailable.")
        logger.error("RequestError: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def open_youtube() -> None:
    speak("Opening YouTube.")
    webbrowser.open("https://www.youtube.com")


def search_youtube(query: str) -> None:
    if not query:
        speak("What would you like to search on YouTube?")
        return
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    speak(f"Searching YouTube for {query}.")
    webbrowser.open(url)


def open_google() -> None:
    speak("Opening Google.")
    webbrowser.open("https://www.google.com")


def search_google(query: str) -> None:
    if not query:
        speak("What would you like to search on Google?")
        return
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    speak(f"Searching Google for {query}.")
    webbrowser.open(url)


def open_wikipedia(query: str) -> None:
    if not query:
        speak("What would you like to look up on Wikipedia?")
        return
    url = f"https://en.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '+')}"
    speak(f"Opening Wikipedia for {query}.")
    webbrowser.open(url)


def tell_time() -> None:
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    speak(f"The current time is {time_str}.")


def tell_date() -> None:
    today = datetime.date.today()
    date_str = today.strftime("%A, %B %d, %Y")
    speak(f"Today is {date_str}.")


def open_notepad() -> None:
    speak("Opening Notepad.")
    try:
        subprocess.Popen(["notepad.exe"])
    except FileNotFoundError:
        speak("Notepad is not available on this system.")


def open_calculator() -> None:
    speak("Opening Calculator.")
    try:
        subprocess.Popen(["calc.exe"])
    except FileNotFoundError:
        speak("Calculator is not available on this system.")


def open_file_explorer() -> None:
    speak("Opening File Explorer.")
    try:
        subprocess.Popen(["explorer.exe"])
    except FileNotFoundError:
        speak("File Explorer is not available on this system.")


def take_screenshot() -> None:
    screenshot_dir = os.path.expanduser("~/Pictures")
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(screenshot_dir, f"screenshot_{timestamp}.png")
    try:
        # Use Windows Snipping Tool silently (available on Win 10/11)
        subprocess.Popen(
            ["snippingtool.exe", "/clip"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        speak("Screenshot tool opened. Select an area to capture.")
    except FileNotFoundError:
        speak("Screenshot tool is not available on this system.")


def increase_volume() -> None:
    speak("Increasing volume.")
    # Send the VK_VOLUME_UP key via PowerShell
    _send_key_via_powershell("VolumeUp", 3)


def decrease_volume() -> None:
    speak("Decreasing volume.")
    _send_key_via_powershell("VolumeDown", 3)


def mute_volume() -> None:
    speak("Toggling mute.")
    _send_key_via_powershell("VolumeMute", 1)


def _send_key_via_powershell(key: str, times: int = 1) -> None:
    # Build a proper volume key script
    vk_map = {
        "VolumeUp": 0xAF,
        "VolumeDown": 0xAE,
        "VolumeMute": 0xAD,
    }
    vk = vk_map.get(key, 0xAF)
    ps_script = (
        f"$code = @'\n"
        f"using System;\n"
        f"using System.Runtime.InteropServices;\n"
        f"public class KeyPress {{\n"
        f"    [DllImport(\"user32.dll\")]\n"
        f"    public static extern void keybd_event(byte bVk, byte bScan, int dwFlags, int dwExtraInfo);\n"
        f"}}\n"
        f"'@\n"
        f"Add-Type -TypeDefinition $code;\n"
        + "\n".join(
            [
                f"[KeyPress]::keybd_event({vk}, 0, 0, 0); [KeyPress]::keybd_event({vk}, 0, 2, 0);"
                for _ in range(times)
            ]
        )
    )
    try:
        subprocess.Popen(
            ["powershell", "-NonInteractive", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        logger.warning("PowerShell not found; cannot adjust volume.")


def lock_computer() -> None:
    speak("Locking the computer.")
    try:
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
    except FileNotFoundError:
        speak("Unable to lock the computer on this system.")


def shutdown_computer() -> None:
    speak(f"Shutting down the computer in {SHUTDOWN_DELAY_SECONDS} seconds. Say 'cancel shutdown' to abort.")
    try:
        subprocess.Popen(["shutdown", "/s", "/t", str(SHUTDOWN_DELAY_SECONDS)])
    except FileNotFoundError:
        speak("Shutdown command is not available on this system.")


def cancel_shutdown() -> None:
    speak("Cancelling shutdown.")
    try:
        subprocess.Popen(["shutdown", "/a"])
    except FileNotFoundError:
        speak("Shutdown command is not available on this system.")


def restart_computer() -> None:
    speak(f"Restarting the computer in {SHUTDOWN_DELAY_SECONDS} seconds.")
    try:
        subprocess.Popen(["shutdown", "/r", "/t", str(SHUTDOWN_DELAY_SECONDS)])
    except FileNotFoundError:
        speak("Restart command is not available on this system.")


def open_settings() -> None:
    speak("Opening Windows Settings.")
    try:
        os.startfile("ms-settings:")
    except (AttributeError, OSError):
        speak("Unable to open Settings on this system.")


# ---------------------------------------------------------------------------
# Command dispatcher
# ---------------------------------------------------------------------------

HELP_TEXT = (
    "Here are the commands I understand: "
    "open YouTube, search YouTube, open Google, search Google, "
    "open Wikipedia, what time is it, what is today's date, "
    "open Notepad, open Calculator, open File Explorer, "
    "take a screenshot, increase volume, decrease volume, mute, "
    "lock computer, shutdown, restart, open settings, help, and exit."
)


def process_command(command: str) -> bool:
    """
    Dispatch *command* to the appropriate handler.

    Returns *False* when the agent should stop, *True* to continue.
    """
    # Exit / stop
    if any(word in command for word in ("exit", "quit", "goodbye", "bye", "stop")):
        speak("Goodbye! Have a great day.")
        return False

    # Help
    elif "help" in command:
        speak(HELP_TEXT)

    # YouTube
    elif command.startswith("search youtube"):
        query = command.replace("search youtube", "").strip()
        search_youtube(query)
    elif "open youtube" in command or "youtube" in command:
        open_youtube()

    # Google
    elif command.startswith("search google") or command.startswith("google search"):
        query = (
            command.replace("search google", "").replace("google search", "").strip()
        )
        search_google(query)
    elif "open google" in command or "google" in command:
        open_google()

    # Wikipedia
    elif "wikipedia" in command:
        query = command.replace("wikipedia", "").replace("open", "").strip()
        open_wikipedia(query)

    # Time & date
    elif any(p in command for p in ("what time", "current time", "tell me the time")):
        tell_time()
    elif any(
        p in command for p in ("what date", "today's date", "tell me the date", "what day")
    ):
        tell_date()

    # Applications
    elif "notepad" in command:
        open_notepad()
    elif "calculator" in command or "calc" in command:
        open_calculator()
    elif "file explorer" in command or "explorer" in command:
        open_file_explorer()
    elif "screenshot" in command or "screen shot" in command:
        take_screenshot()
    elif "settings" in command:
        open_settings()

    # Volume
    elif "increase volume" in command or "volume up" in command:
        increase_volume()
    elif "decrease volume" in command or "volume down" in command:
        decrease_volume()
    elif "mute" in command:
        mute_volume()

    # Power management
    elif "lock" in command:
        lock_computer()
    elif "cancel shutdown" in command or "abort shutdown" in command:
        cancel_shutdown()
    elif "shutdown" in command or "shut down" in command:
        shutdown_computer()
    elif "restart" in command or "reboot" in command:
        restart_computer()

    else:
        speak(
            f"I'm not sure how to handle '{command}'. Say 'help' to hear available commands."
        )

    return True


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main() -> None:
    speak("Hello! I am your AI voice assistant. Say 'help' to hear what I can do, or 'exit' to quit.")

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    with sr.Microphone() as source:
        while True:
            command = listen(recognizer, source)
            if command is None:
                continue
            should_continue = process_command(command)
            if not should_continue:
                break


if __name__ == "__main__":
    main()
