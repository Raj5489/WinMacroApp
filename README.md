# WinMacroApp — Mouse & Keyboard Simulator

A Windows desktop app to simulate mouse clicks, mouse movement, keyboard input, and Chrome tab switching — built with Python + PyAutoGUI + Tkinter.

---

## Features

| Tab                  | What it does                                                      |
| -------------------- | ----------------------------------------------------------------- |
| 🖱 Mouse             | Move mouse, left/right/middle click, double-click, drag, scroll   |
| ⌨ Keyboard           | Type text, press single keys, send hotkeys (Ctrl+C, etc.)         |
| 🌐 Chrome Tabs       | Next/prev tab, go to tab #, new tab, close tab, open URL, refresh |
| 📍 Position Recorder | Live X/Y tracker — capture coordinates & click them back          |

---

## Setup

```bash
cd WinMacroApp

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

---

## How to Use

### Mouse Tab

- Enter X, Y coordinates and click **Move** — the mouse glides there smoothly
- Enter X, Y, choose button type (left/right/middle), set click count → **Click**
- Drag from one point to another
- Scroll up (positive) or down (negative) at any position

### Keyboard Tab

- **Type Text** — types a string character by character with natural speed
- **Press Key** — press any single key (enter, esc, tab, f5, etc.)
- **Hotkey** — comma-separated keys fired simultaneously (e.g. `ctrl,shift,t`)

### Chrome Tabs Tab

- Switch to next/previous tab with one button
- Jump directly to tab #1–8
- Open any URL in the focused Chrome window
- New tab, close tab, refresh

### Position Recorder Tab

- Shows live X/Y as you move your mouse
- Click **Capture** to save a coordinate to the list
- Select a saved coordinate and click **Click Selected** to replay it

---

## Emergency Stop

Move your mouse to the **top-left corner** of the screen (0, 0) — PyAutoGUI will throw a `FailSafeException` and stop all actions immediately.

---

## Notes

- All actions fire with a **1.5 second delay** after you click a button — giving you time to switch focus to Chrome or another window
- Works on Windows 10/11
- Chrome must already be open and focused for tab shortcuts to work
