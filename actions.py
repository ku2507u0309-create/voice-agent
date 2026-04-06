"""
actions.py – System action handlers for the AI Voice Agent.

Every public function in this module accepts a *speak* callable as its first
argument so that the handler can give voice feedback without importing
``listener`` directly (avoiding circular imports and making unit testing
straightforward).

New handler: open_vscode()
"""

import datetime
import os
import subprocess
import webbrowser
from typing import Callable

from config import SHUTDOWN_DELAY_SECONDS
from logger import setup_logger

logger = setup_logger("actions")

SpeakFn = Callable[[str], None]


# ---------------------------------------------------------------------------
# Web actions
# ---------------------------------------------------------------------------


def open_youtube(speak: SpeakFn) -> None:
    speak("Opening YouTube.")
    webbrowser.open("https://www.youtube.com")


def search_youtube(query: str, speak: SpeakFn) -> None:
    if not query:
        speak("What would you like to search on YouTube?")
        return
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    speak(f"Searching YouTube for {query}.")
    webbrowser.open(url)


def open_google(speak: SpeakFn) -> None:
    speak("Opening Google.")
    webbrowser.open("https://www.google.com")


def search_google(query: str, speak: SpeakFn) -> None:
    if not query:
        speak("What would you like to search on Google?")
        return
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    speak(f"Searching Google for {query}.")
    webbrowser.open(url)


def open_wikipedia(query: str, speak: SpeakFn) -> None:
    if not query:
        speak("What would you like to look up on Wikipedia?")
        return
    url = (
        f"https://en.wikipedia.org/wiki/Special:Search"
        f"?search={query.replace(' ', '+')}"
    )
    speak(f"Opening Wikipedia for {query}.")
    webbrowser.open(url)


# ---------------------------------------------------------------------------
# Time & date
# ---------------------------------------------------------------------------


def tell_time(speak: SpeakFn) -> None:
    time_str = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {time_str}.")


def tell_date(speak: SpeakFn) -> None:
    date_str = datetime.date.today().strftime("%A, %B %d, %Y")
    speak(f"Today is {date_str}.")


# ---------------------------------------------------------------------------
# Application launchers
# ---------------------------------------------------------------------------


def _launch(executable: str, label: str, speak: SpeakFn) -> None:
    """Generic launcher with error handling."""
    speak(f"Opening {label}.")
    try:
        subprocess.Popen([executable])  # noqa: S603
    except FileNotFoundError:
        speak(f"{label} is not available on this system.")


def open_notepad(speak: SpeakFn) -> None:
    _launch("notepad.exe", "Notepad", speak)


def open_calculator(speak: SpeakFn) -> None:
    _launch("calc.exe", "Calculator", speak)


def open_file_explorer(speak: SpeakFn) -> None:
    _launch("explorer.exe", "File Explorer", speak)


def open_vscode(speak: SpeakFn) -> None:
    """Open VS Code, trying the PATH first then common install locations."""
    speak("Opening VS Code.")

    # Try 'code' on PATH (works when VS Code shell integration is installed)
    try:
        subprocess.Popen(["code"])  # noqa: S603
        return
    except FileNotFoundError:
        pass

    # Fallback: try the Windows registry to locate the executable
    try:
        import winreg  # type: ignore[import]

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Code.exe",
        )
        exe_path, _ = winreg.QueryValueEx(key, "")
        winreg.CloseKey(key)
        subprocess.Popen([exe_path])  # noqa: S603
        return
    except (ImportError, OSError):
        pass

    speak("VS Code does not appear to be installed on this system.")


# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------


def take_screenshot(speak: SpeakFn) -> None:
    try:
        subprocess.Popen(  # noqa: S603
            ["snippingtool.exe", "/clip"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        speak("Screenshot tool opened. Select an area to capture.")
    except FileNotFoundError:
        speak("Screenshot tool is not available on this system.")


# ---------------------------------------------------------------------------
# Volume control
# ---------------------------------------------------------------------------


def _send_key_via_powershell(key: str, times: int = 1) -> None:
    """Send a media/volume key via a PowerShell script."""
    vk_map = {"VolumeUp": 0xAF, "VolumeDown": 0xAE, "VolumeMute": 0xAD}
    vk = vk_map.get(key, 0xAF)
    key_calls = "\n".join(
        f"[KeyPress]::keybd_event({vk}, 0, 0, 0); "
        f"[KeyPress]::keybd_event({vk}, 0, 2, 0);"
        for _ in range(times)
    )
    ps_script = (
        "$code = @'\n"
        "using System;\n"
        "using System.Runtime.InteropServices;\n"
        "public class KeyPress {\n"
        '    [DllImport("user32.dll")]\n'
        "    public static extern void keybd_event("
        "byte bVk, byte bScan, int dwFlags, int dwExtraInfo);\n"
        "}\n"
        "'@\n"
        "Add-Type -TypeDefinition $code;\n"
        + key_calls
    )
    try:
        subprocess.Popen(  # noqa: S603
            ["powershell", "-NonInteractive", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        logger.warning("PowerShell not found; cannot adjust volume.")


def increase_volume(speak: SpeakFn) -> None:
    speak("Increasing volume.")
    _send_key_via_powershell("VolumeUp", 3)


def decrease_volume(speak: SpeakFn) -> None:
    speak("Decreasing volume.")
    _send_key_via_powershell("VolumeDown", 3)


def mute_volume(speak: SpeakFn) -> None:
    speak("Toggling mute.")
    _send_key_via_powershell("VolumeMute", 1)


# ---------------------------------------------------------------------------
# Power management
# ---------------------------------------------------------------------------


def lock_computer(speak: SpeakFn) -> None:
    speak("Locking the computer.")
    try:
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])  # noqa: S603
    except FileNotFoundError:
        speak("Unable to lock the computer on this system.")


def shutdown_computer(speak: SpeakFn) -> None:
    speak(
        f"Shutting down the computer in {SHUTDOWN_DELAY_SECONDS} seconds. "
        "Say 'cancel shutdown' to abort."
    )
    try:
        subprocess.Popen(["shutdown", "/s", "/t", str(SHUTDOWN_DELAY_SECONDS)])  # noqa: S603
    except FileNotFoundError:
        speak("Shutdown command is not available on this system.")


def cancel_shutdown(speak: SpeakFn) -> None:
    speak("Cancelling shutdown.")
    try:
        subprocess.Popen(["shutdown", "/a"])  # noqa: S603
    except FileNotFoundError:
        speak("Shutdown command is not available on this system.")


def restart_computer(speak: SpeakFn) -> None:
    speak(
        f"Restarting the computer in {SHUTDOWN_DELAY_SECONDS} seconds. "
        "Say 'cancel shutdown' to abort."
    )
    try:
        subprocess.Popen(["shutdown", "/r", "/t", str(SHUTDOWN_DELAY_SECONDS)])  # noqa: S603
    except FileNotFoundError:
        speak("Restart command is not available on this system.")

def open_settings(speak: SpeakFn) -> None:
    speak("Opening Windows Settings.")
    try:
        os.startfile("ms-settings:")  # noqa: S606
    except (AttributeError, OSError):
        speak("Unable to open Settings on this system.")
