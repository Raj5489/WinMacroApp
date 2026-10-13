"""
macro_engine.py
---------------
Core automation engine. All mouse + keyboard actions live here.
Uses pyautogui under the hood. Import this into the GUI or use standalone.
"""

import time
import pyautogui

# Failsafe DISABLED — sequences must never stop unless the user hits Stop
pyautogui.FAILSAFE = False
# Small pause between every pyautogui call
pyautogui.PAUSE = 0.05


def set_failsafe(enabled: bool):
    """Enable or disable the PyAutoGUI corner failsafe."""
    pyautogui.FAILSAFE = enabled


# ─────────────────────────────────────────────
#  MOUSE ACTIONS
# ─────────────────────────────────────────────

def move_mouse(x: int, y: int, duration: float = 0.5):
    """Smoothly move the mouse to (x, y) over `duration` seconds."""
    pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)


def click(x: int, y: int, button: str = "left", clicks: int = 1, duration: float = 0.3):
    """Move to (x, y) and click."""
    pyautogui.click(x, y, button=button, clicks=clicks, interval=0.1, duration=duration)


def double_click(x: int, y: int, duration: float = 0.3):
    """Double-click at (x, y)."""
    pyautogui.doubleClick(x, y, duration=duration)


def right_click(x: int, y: int, duration: float = 0.3):
    """Right-click at (x, y)."""
    pyautogui.rightClick(x, y, duration=duration)


def drag(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5):
    """Click and drag from (x1, y1) to (x2, y2)."""
    pyautogui.moveTo(x1, y1, duration=0.3)
    pyautogui.dragTo(x2, y2, duration=duration, button="left")


def scroll(x: int, y: int, amount: int = 3):
    """Scroll up (positive) or down (negative) at position (x, y)."""
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.scroll(amount)


def get_mouse_position() -> tuple:
    """Return the current (x, y) mouse position."""
    return pyautogui.position()


# ─────────────────────────────────────────────
#  KEYBOARD ACTIONS
# ─────────────────────────────────────────────

def type_text(text: str, interval: float = 0.05):
    """Type a string of text with a natural interval between keystrokes."""
    pyautogui.typewrite(text, interval=interval)


def press_key(key: str):
    """Press a single key (e.g. 'enter', 'esc', 'tab', 'f5')."""
    pyautogui.press(key)


def hotkey(*keys):
    """
    Press a key combination simultaneously.
    Examples:
        hotkey('ctrl', 'c')       → Copy
        hotkey('ctrl', 't')       → New tab in Chrome
        hotkey('ctrl', 'tab')     → Switch to next tab
        hotkey('ctrl', 'w')       → Close tab
        hotkey('alt', 'tab')      → Switch app window
        hotkey('ctrl', 'shift', 'tab') → Previous tab
    """
    pyautogui.hotkey(*keys)


def hold_key(key: str, duration: float = 1.0):
    """Hold a key down for `duration` seconds then release."""
    pyautogui.keyDown(key)
    time.sleep(duration)
    pyautogui.keyUp(key)


# ─────────────────────────────────────────────
#  CHROME TAB SHORTCUTS
# ─────────────────────────────────────────────

def next_tab():
    """Switch to the next tab in Chrome (Ctrl+Tab)."""
    hotkey("ctrl", "tab")


def prev_tab():
    """Switch to the previous tab in Chrome (Ctrl+Shift+Tab)."""
    hotkey("ctrl", "shift", "tab")


def new_tab():
    """Open a new tab in Chrome (Ctrl+T)."""
    hotkey("ctrl", "t")


def close_tab():
    """Close the current tab in Chrome (Ctrl+W)."""
    hotkey("ctrl", "w")


def go_to_tab(number: int):
    """
    Switch to a specific tab by number (1–8).
    Chrome shortcut: Ctrl+1 through Ctrl+8.
    """
    if 1 <= number <= 8:
        hotkey("ctrl", str(number))


def open_url(url: str):
    """Focus the address bar, type a URL and open it."""
    hotkey("ctrl", "l")           # Focus address bar
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a") # Select existing text
    pyautogui.typewrite(url, interval=0.03)
    pyautogui.press("enter")


def refresh_page():
    """Refresh the current Chrome tab (F5)."""
    press_key("f5")


def switch_to_tab_by_name(keyword: str):
    """
    Switch to a Chrome tab by searching its title/URL keyword.

    Uses Chrome's built-in Tab Search (Ctrl+Shift+A) — available in
    Chrome 87+. Opens the tab search popup, types the keyword,
    waits for results, then hits Enter to jump to the first match.

    Args:
        keyword: Part of the tab title or URL to search for.
                 e.g. "Sales Page", "Subscribers", "FlexiGenie"
    """
    hotkey("ctrl", "shift", "a")   # Open Chrome Tab Search popup
    time.sleep(0.4)                 # Wait for popup to appear
    # Tab search field is already focused — clear & type keyword
    hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.typewrite(keyword, interval=0.05)
    time.sleep(0.5)                 # Wait for search results to filter
    pyautogui.press("enter")        # Jump to first matching tab
    time.sleep(0.2)


# ─────────────────────────────────────────────
#  UTILITY
# ─────────────────────────────────────────────

def sleep(seconds: float):
    """Pause execution for a given number of seconds."""
    time.sleep(seconds)


def take_screenshot(path: str = "screenshot.png"):
    """Take a screenshot and save it to `path`."""
    pyautogui.screenshot(path)
    return path
