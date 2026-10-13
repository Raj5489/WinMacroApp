"""
app.py
------
Main GUI for WinMacroApp — built with Python's built-in tkinter.
No extra GUI library needed.

Tabs:
  1. Mouse          — move, click, drag, scroll
  2. Keyboard       — type text, press keys, hotkeys
  3. Chrome Tabs    — tab switcher shortcuts
  4. Recorder       — record mouse position live (click-to-capture)
  5. Macro Sequence — chain multiple actions and run them all at once
"""

import json
import time
import traceback
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pyautogui
import macro_engine as engine

# ── Optional: global hotkey library ──────────────────────────────────────────
# The 'keyboard' package is used for the F8 emergency-stop hotkey.
# If it's not installed the app still works — the Stop button is the fallback.
try:
    import keyboard as _keyboard
    _KEYBOARD_AVAILABLE = True
except ImportError:
    _keyboard = None
    _KEYBOARD_AVAILABLE = False

# Module-level stop flag shared between the hotkey listener and macro runner
_GLOBAL_STOP = {"stop": False}
STOP_HOTKEY   = "f8"   # change here if you want a different key


# ══════════════════════════════════════════════
#  THEME / PALETTE
# ══════════════════════════════════════════════

COLORS = {
    "bg":           "#1e1e2e",   # main background
    "bg2":          "#27273a",   # slightly lighter panel bg
    "bg3":          "#313147",   # input / frame bg
    "border":       "#3d3d5c",   # subtle border
    "accent":       "#0ea5e9",   # sky blue — primary accent
    "accent_hover": "#38bdf8",
    "success":      "#22c55e",
    "warning":      "#f59e0b",
    "error":        "#ef4444",
    "text":         "#e2e8f0",   # main text
    "text_dim":     "#94a3b8",   # secondary / hint text
    "log_bg":       "#0d1117",   # log box background (terminal feel)
    "log_fg":       "#7ee787",   # log text (green terminal)
    "entry_bg":     "#2d2d44",
}


def apply_theme(root: tk.Tk):
    """Apply a custom dark theme to all ttk widgets."""
    root.configure(bg=COLORS["bg"])
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".",
        background=COLORS["bg"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["entry_bg"],
        troughcolor=COLORS["bg3"],
        bordercolor=COLORS["border"],
        darkcolor=COLORS["bg2"],
        lightcolor=COLORS["bg3"],
        selectbackground=COLORS["accent"],
        selectforeground="#ffffff",
        font=("Segoe UI", 9),
        relief="flat",
    )

    style.configure("TFrame", background=COLORS["bg"])

    style.configure("TLabelframe",
        background=COLORS["bg2"],
        bordercolor=COLORS["border"],
        relief="flat",
    )
    style.configure("TLabelframe.Label",
        background=COLORS["bg2"],
        foreground=COLORS["accent"],
        font=("Segoe UI", 9, "bold"),
    )

    style.configure("TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text"],
        font=("Segoe UI", 9),
    )
    style.configure("Dim.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text_dim"],
        font=("Segoe UI", 8),
    )
    style.configure("LogTitle.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text_dim"],
        font=("Segoe UI", 8, "bold"),
    )

    # Primary / accent button
    style.configure("Accent.TButton",
        background=COLORS["accent"],
        foreground="#ffffff",
        bordercolor=COLORS["accent"],
        font=("Segoe UI", 9, "bold"),
        padding=(10, 5),
        relief="flat",
    )
    style.map("Accent.TButton",
        background=[("active", COLORS["accent_hover"]), ("disabled", COLORS["bg3"])],
        foreground=[("disabled", COLORS["text_dim"])],
    )

    # Default / secondary button
    style.configure("TButton",
        background=COLORS["bg3"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        focusthickness=0,
        font=("Segoe UI", 9),
        padding=(8, 4),
        relief="flat",
    )
    style.map("TButton",
        background=[("active", COLORS["border"]), ("disabled", COLORS["bg2"])],
        foreground=[("disabled", COLORS["text_dim"])],
    )

    # Danger / destructive button
    style.configure("Danger.TButton",
        background="#450a0a",
        foreground=COLORS["error"],
        bordercolor="#7f1d1d",
        font=("Segoe UI", 9, "bold"),
        padding=(10, 5),
        relief="flat",
    )
    style.map("Danger.TButton",
        background=[("active", "#7f1d1d"), ("disabled", COLORS["bg2"])],
        foreground=[("disabled", COLORS["text_dim"])],
    )

    style.configure("TEntry",
        fieldbackground=COLORS["entry_bg"],
        foreground=COLORS["text"],
        insertcolor=COLORS["accent"],
        bordercolor=COLORS["border"],
        relief="flat",
        padding=4,
    )
    style.map("TEntry",
        bordercolor=[("focus", COLORS["accent"])],
    )

    style.configure("TCombobox",
        fieldbackground=COLORS["entry_bg"],
        background=COLORS["bg3"],
        foreground=COLORS["text"],
        arrowcolor=COLORS["accent"],
        bordercolor=COLORS["border"],
        selectbackground=COLORS["accent"],
        relief="flat",
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", COLORS["entry_bg"])],
        selectbackground=[("readonly", COLORS["entry_bg"])],
        selectforeground=[("readonly", COLORS["text"])],
    )

    style.configure("TSpinbox",
        fieldbackground=COLORS["entry_bg"],
        foreground=COLORS["text"],
        arrowcolor=COLORS["accent"],
        bordercolor=COLORS["border"],
        background=COLORS["bg3"],
        relief="flat",
    )

    style.configure("TScrollbar",
        background=COLORS["bg3"],
        troughcolor=COLORS["bg2"],
        arrowcolor=COLORS["text_dim"],
        bordercolor=COLORS["bg2"],
        relief="flat",
    )
    style.map("TScrollbar",
        background=[("active", COLORS["border"])],
    )

    style.configure("TNotebook",
        background=COLORS["bg"],
        bordercolor=COLORS["border"],
        tabmargins=[2, 4, 0, 0],
    )
    style.configure("TNotebook.Tab",
        background=COLORS["bg2"],
        foreground=COLORS["text_dim"],
        font=("Segoe UI", 10, "bold"),
        padding=(14, 7),
        bordercolor=COLORS["bg"],
    )
    style.map("TNotebook.Tab",
        background=[("selected", COLORS["bg3"])],
        foreground=[("selected", COLORS["accent"])],
        expand=[("selected", [0, 0, 0, 1])],
    )

    style.configure("TProgressbar",
        troughcolor=COLORS["bg3"],
        background=COLORS["accent"],
        bordercolor=COLORS["bg3"],
        lightcolor=COLORS["accent"],
        darkcolor=COLORS["accent"],
        thickness=6,
        relief="flat",
    )

    style.configure("TSeparator", background=COLORS["border"])


# ══════════════════════════════════════════════
#  WIDGET HELPERS
# ══════════════════════════════════════════════

def styled_log(parent, height=7) -> scrolledtext.ScrolledText:
    """Terminal-style log box — dark bg, green text."""
    return scrolledtext.ScrolledText(
        parent, height=height, state="disabled",
        font=("Consolas", 9),
        bg=COLORS["log_bg"], fg=COLORS["log_fg"],
        insertbackground=COLORS["log_fg"],
        selectbackground=COLORS["accent"],
        relief="flat", bd=0,
        padx=8, pady=6,
    )


def styled_listbox(parent, height=10) -> tk.Listbox:
    """Dark-styled listbox."""
    return tk.Listbox(
        parent, height=height,
        font=("Consolas", 9),
        bg=COLORS["entry_bg"], fg=COLORS["text"],
        selectbackground=COLORS["accent"],
        selectforeground="#ffffff",
        activestyle="none",
        relief="flat", bd=0,
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["accent"],
    )


# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

def run_in_thread(fn, *args, delay=1.5):
    """
    Run fn(*args) in a background thread after a short delay.
    Exceptions are swallowed — single actions are fire-and-forget.
    """
    def task():
        time.sleep(delay)
        try:
            fn(*args)
        except Exception:
            pass
    threading.Thread(target=task, daemon=True).start()


def safe_int(value, fallback=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return fallback


def safe_float(value, fallback=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return fallback


def log_msg(widget: scrolledtext.ScrolledText, message: str):
    """Append a timestamped message to a log widget (main-thread safe)."""
    ts = time.strftime("%H:%M:%S")
    widget.configure(state="normal")
    widget.insert(tk.END, f"[{ts}]  ▶  {message}\n")
    widget.see(tk.END)
    widget.configure(state="disabled")


def _hotkey_register(callback):
    """Register F8 stop hotkey. Safe to call even if already registered."""
    if not _KEYBOARD_AVAILABLE:
        return
    try:
        _keyboard.remove_hotkey(STOP_HOTKEY)
    except Exception:
        pass
    try:
        _keyboard.add_hotkey(STOP_HOTKEY, callback)
    except Exception:
        pass


def _hotkey_unregister():
    """Unregister F8 stop hotkey. Safe to call when not registered."""
    if not _KEYBOARD_AVAILABLE:
        return
    try:
        _keyboard.remove_hotkey(STOP_HOTKEY)
    except Exception:
        pass


# ══════════════════════════════════════════════
#  MOUSE TAB
# ══════════════════════════════════════════════

def build_mouse_tab(parent):
    frame = ttk.Frame(parent, padding=14)
    log_box = styled_log(frame, height=7)

    # ── Move Mouse ──────────────────────────────
    move_frame = ttk.LabelFrame(frame, text="  Move Mouse", padding=10)
    ttk.Label(move_frame, text="X:").grid(row=0, column=0, sticky="w")
    x_var = tk.StringVar(value="500")
    ttk.Entry(move_frame, textvariable=x_var, width=9).grid(row=0, column=1, padx=(4, 10))
    ttk.Label(move_frame, text="Y:").grid(row=0, column=2, sticky="w")
    y_var = tk.StringVar(value="400")
    ttk.Entry(move_frame, textvariable=y_var, width=9).grid(row=0, column=3, padx=(4, 10))
    ttk.Label(move_frame, text="Duration (s):").grid(row=0, column=4, sticky="w")
    dur_var = tk.StringVar(value="0.5")
    ttk.Entry(move_frame, textvariable=dur_var, width=7).grid(row=0, column=5, padx=(4, 10))

    def do_move():
        run_in_thread(
            engine.move_mouse,
            safe_int(x_var.get()), safe_int(y_var.get()),
            safe_float(dur_var.get(), 0.5),
        )
        log_msg(log_box, f"Move mouse → ({x_var.get()}, {y_var.get()}) in {dur_var.get()}s")

    ttk.Button(move_frame, text="Move", command=do_move,
               style="Accent.TButton").grid(row=0, column=6, padx=8)
    move_frame.pack(fill="x", pady=5)

    # ── Click ────────────────────────────────────
    click_frame = ttk.LabelFrame(frame, text="  Click", padding=10)
    ttk.Label(click_frame, text="X:").grid(row=0, column=0, sticky="w")
    cx_var = tk.StringVar(value="500")
    ttk.Entry(click_frame, textvariable=cx_var, width=9).grid(row=0, column=1, padx=(4, 10))
    ttk.Label(click_frame, text="Y:").grid(row=0, column=2, sticky="w")
    cy_var = tk.StringVar(value="400")
    ttk.Entry(click_frame, textvariable=cy_var, width=9).grid(row=0, column=3, padx=(4, 10))
    ttk.Label(click_frame, text="Button:").grid(row=0, column=4, sticky="w")
    btn_type = tk.StringVar(value="left")
    ttk.OptionMenu(click_frame, btn_type, "left", "left", "right", "middle").grid(row=0, column=5, padx=(4, 10))
    ttk.Label(click_frame, text="Clicks:").grid(row=0, column=6, sticky="w")
    clicks_var = tk.StringVar(value="1")
    ttk.Entry(click_frame, textvariable=clicks_var, width=5).grid(row=0, column=7, padx=(4, 10))

    def do_click():
        run_in_thread(
            engine.click,
            safe_int(cx_var.get()), safe_int(cy_var.get()),
            btn_type.get(), safe_int(clicks_var.get(), 1),
        )
        log_msg(log_box, f"{btn_type.get().capitalize()} click × {clicks_var.get()} at ({cx_var.get()}, {cy_var.get()})")

    ttk.Button(click_frame, text="Click", command=do_click,
               style="Accent.TButton").grid(row=0, column=8, padx=8)
    click_frame.pack(fill="x", pady=5)

    # ── Drag ─────────────────────────────────────
    drag_frame = ttk.LabelFrame(frame, text="  Drag", padding=10)
    drag_x1 = tk.StringVar(value="200"); drag_y1 = tk.StringVar(value="200")
    drag_x2 = tk.StringVar(value="600"); drag_y2 = tk.StringVar(value="400")
    ttk.Label(drag_frame, text="From X:").grid(row=0, column=0, sticky="w")
    ttk.Entry(drag_frame, textvariable=drag_x1, width=8).grid(row=0, column=1, padx=(4, 10))
    ttk.Label(drag_frame, text="From Y:").grid(row=0, column=2, sticky="w")
    ttk.Entry(drag_frame, textvariable=drag_y1, width=8).grid(row=0, column=3, padx=(4, 10))
    ttk.Label(drag_frame, text="To X:").grid(row=0, column=4, sticky="w")
    ttk.Entry(drag_frame, textvariable=drag_x2, width=8).grid(row=0, column=5, padx=(4, 10))
    ttk.Label(drag_frame, text="To Y:").grid(row=0, column=6, sticky="w")
    ttk.Entry(drag_frame, textvariable=drag_y2, width=8).grid(row=0, column=7, padx=(4, 10))

    def do_drag():
        run_in_thread(
            engine.drag,
            safe_int(drag_x1.get()), safe_int(drag_y1.get()),
            safe_int(drag_x2.get()), safe_int(drag_y2.get()),
        )
        log_msg(log_box, f"Drag ({drag_x1.get()},{drag_y1.get()}) → ({drag_x2.get()},{drag_y2.get()})")

    ttk.Button(drag_frame, text="Drag", command=do_drag,
               style="Accent.TButton").grid(row=0, column=8, padx=8)
    drag_frame.pack(fill="x", pady=5)

    # ── Scroll ───────────────────────────────────
    scroll_frame = ttk.LabelFrame(frame, text="  Scroll", padding=10)
    sc_x = tk.StringVar(value="500"); sc_y = tk.StringVar(value="400")
    ttk.Label(scroll_frame, text="At X:").grid(row=0, column=0, sticky="w")
    ttk.Entry(scroll_frame, textvariable=sc_x, width=8).grid(row=0, column=1, padx=(4, 10))
    ttk.Label(scroll_frame, text="At Y:").grid(row=0, column=2, sticky="w")
    ttk.Entry(scroll_frame, textvariable=sc_y, width=8).grid(row=0, column=3, padx=(4, 10))
    ttk.Label(scroll_frame, text="Amount  (+↑ / -↓):").grid(row=0, column=4, sticky="w")
    sc_amt = tk.StringVar(value="3")
    ttk.Entry(scroll_frame, textvariable=sc_amt, width=6).grid(row=0, column=5, padx=(4, 10))

    def do_scroll():
        run_in_thread(
            engine.scroll,
            safe_int(sc_x.get()), safe_int(sc_y.get()), safe_int(sc_amt.get(), 3),
        )
        log_msg(log_box, f"Scroll {sc_amt.get()} at ({sc_x.get()}, {sc_y.get()})")

    ttk.Button(scroll_frame, text="Scroll", command=do_scroll,
               style="Accent.TButton").grid(row=0, column=6, padx=8)
    scroll_frame.pack(fill="x", pady=5)

    # ── Live Cursor Position ──────────────────────
    pos_outer = ttk.LabelFrame(frame, text="  Live Cursor Position", padding=8)
    pos_label = ttk.Label(pos_outer, text="X: —    Y: —",
                          font=("Consolas", 11, "bold"),
                          foreground=COLORS["accent"],
                          background=COLORS["bg2"])
    pos_label.pack(anchor="w", padx=4)

    def _update_position():
        try:
            x, y = engine.get_mouse_position()
            pos_label.config(text=f"X: {x}    Y: {y}")
        except Exception:
            pass
        frame.after(250, _update_position)

    _update_position()
    pos_outer.pack(fill="x", pady=5)

    # ── Log ──────────────────────────────────────
    ttk.Label(frame, text="Action Log", style="LogTitle.TLabel").pack(anchor="w", pady=(6, 2))
    log_box.pack(fill="both", expand=True)

    return frame


# ══════════════════════════════════════════════
#  KEYBOARD TAB
# ══════════════════════════════════════════════

def build_keyboard_tab(parent):
    frame = ttk.Frame(parent, padding=14)
    log_box = styled_log(frame, height=7)

    # ── Type Text ────────────────────────────────
    type_frame = ttk.LabelFrame(frame, text="  Type Text", padding=10)
    ttk.Label(type_frame, text="Text:").grid(row=0, column=0, sticky="w")
    type_var = tk.StringVar(value="Hello, World!")
    ttk.Entry(type_frame, textvariable=type_var, width=40).grid(row=0, column=1, padx=(6, 10))
    ttk.Label(type_frame, text="Interval (s):").grid(row=0, column=2)
    interval_var = tk.StringVar(value="0.05")
    ttk.Entry(type_frame, textvariable=interval_var, width=7).grid(row=0, column=3, padx=(4, 10))

    def do_type():
        run_in_thread(engine.type_text, type_var.get(), safe_float(interval_var.get(), 0.05))
        log_msg(log_box, f"Type: \"{type_var.get()}\"")

    ttk.Button(type_frame, text="Type", command=do_type,
               style="Accent.TButton").grid(row=0, column=4, padx=8)
    type_frame.pack(fill="x", pady=5)

    # ── Press Key ────────────────────────────────
    key_frame = ttk.LabelFrame(frame, text="  Press Key", padding=10)
    ttk.Label(key_frame, text="Key:").grid(row=0, column=0, sticky="w")
    key_var = tk.StringVar(value="enter")
    ttk.Entry(key_frame, textvariable=key_var, width=14).grid(row=0, column=1, padx=(6, 10))

    def do_press():
        run_in_thread(engine.press_key, key_var.get())
        log_msg(log_box, f"Press: {key_var.get()}")

    ttk.Button(key_frame, text="Press", command=do_press,
               style="Accent.TButton").grid(row=0, column=2, padx=8)

    # Quick-pick row
    ttk.Label(key_frame, text="Quick pick:",
              foreground=COLORS["text_dim"],
              background=COLORS["bg2"]).grid(row=1, column=0, sticky="w", pady=(8, 2))
    quick_frame = ttk.Frame(key_frame)
    quick_frame.grid(row=2, column=0, columnspan=10, sticky="w", pady=2)
    for k in ["enter", "esc", "tab", "space", "backspace", "delete", "f5", "up", "down", "left", "right"]:
        ttk.Button(quick_frame, text=k, width=9,
                   command=lambda kk=k: (key_var.set(kk),
                                         run_in_thread(engine.press_key, kk),
                                         log_msg(log_box, f"Press: {kk}"))
                   ).pack(side="left", padx=2, pady=2)
    key_frame.pack(fill="x", pady=5)

    # ── Hotkey ───────────────────────────────────
    hotkey_frame = ttk.LabelFrame(frame, text="  Hotkey  (comma-separated keys)", padding=10)
    ttk.Label(hotkey_frame, text="Keys:").grid(row=0, column=0)
    hotkey_var = tk.StringVar(value="ctrl,c")
    ttk.Entry(hotkey_frame, textvariable=hotkey_var, width=22).grid(row=0, column=1, padx=(6, 10))

    def do_hotkey():
        keys = [k.strip() for k in hotkey_var.get().split(",") if k.strip()]
        if not keys:
            return
        run_in_thread(engine.hotkey, *keys)
        log_msg(log_box, f"Hotkey: {'+'.join(keys)}")

    ttk.Button(hotkey_frame, text="Send", command=do_hotkey,
               style="Accent.TButton").grid(row=0, column=2, padx=8)

    # Quick-pick grid
    quick_hotkeys = [
        ("Copy",       "ctrl,c"), ("Paste",      "ctrl,v"), ("Cut",        "ctrl,x"), ("Undo",     "ctrl,z"),
        ("Redo",       "ctrl,y"), ("Select All", "ctrl,a"), ("Save",       "ctrl,s"), ("New Tab",  "ctrl,t"),
        ("Find",       "ctrl,f"), ("Print",      "ctrl,p"), ("New Window", "ctrl,n"), ("Close",    "ctrl,w"),
    ]
    grid_frame = ttk.Frame(hotkey_frame)
    grid_frame.grid(row=2, column=0, columnspan=6, sticky="w", pady=(8, 2))
    for i, (label, combo) in enumerate(quick_hotkeys):
        ttk.Button(grid_frame, text=label, width=12,
                   command=lambda c=combo: (hotkey_var.set(c),
                                            run_in_thread(engine.hotkey, *c.split(",")),
                                            log_msg(log_box, f"Hotkey: {c}"))
                   ).grid(row=i // 6, column=i % 6, padx=3, pady=3)
    hotkey_frame.pack(fill="x", pady=5)

    ttk.Label(frame, text="Action Log", style="LogTitle.TLabel").pack(anchor="w", pady=(6, 2))
    log_box.pack(fill="both", expand=True)
    return frame


# ══════════════════════════════════════════════
#  CHROME TABS TAB
# ══════════════════════════════════════════════

def build_chrome_tab(parent):
    frame = ttk.Frame(parent, padding=14)
    log_box = styled_log(frame, height=7)

    # ── Tab Switcher ─────────────────────────────
    switch_frame = ttk.LabelFrame(frame, text="  Switch Tabs", padding=10)
    ttk.Button(switch_frame, text="◀  Previous Tab  (Ctrl+Shift+Tab)", width=30,
               command=lambda: (run_in_thread(engine.prev_tab),
                                log_msg(log_box, "Previous tab"))
               ).grid(row=0, column=0, padx=6, pady=4)
    ttk.Button(switch_frame, text="Next Tab  ▶  (Ctrl+Tab)", width=30,
               command=lambda: (run_in_thread(engine.next_tab),
                                log_msg(log_box, "Next tab"))
               ).grid(row=0, column=1, padx=6, pady=4)

    ttk.Label(switch_frame, text="Go to tab #:").grid(row=1, column=0, sticky="e", padx=4, pady=6)
    tab_num_var = tk.StringVar(value="1")
    ttk.Spinbox(switch_frame, from_=1, to=8, textvariable=tab_num_var, width=6).grid(row=1, column=1, sticky="w", padx=4)

    def do_go_to_tab():
        n = safe_int(tab_num_var.get(), 1)
        run_in_thread(engine.go_to_tab, n)
        log_msg(log_box, f"Go to tab #{n}")

    ttk.Button(switch_frame, text="Go", command=do_go_to_tab,
               style="Accent.TButton").grid(row=1, column=2, padx=6)
    switch_frame.pack(fill="x", pady=5)

    # ── Tab Actions ──────────────────────────────
    action_frame = ttk.LabelFrame(frame, text="  Tab Actions", padding=10)
    for i, (label, fn, sc) in enumerate([
        ("New Tab",      engine.new_tab,      "Ctrl+T"),
        ("Close Tab",    engine.close_tab,    "Ctrl+W"),
        ("Refresh Page", engine.refresh_page, "F5"),
    ]):
        ttk.Button(action_frame, text=f"{label}  ({sc})", width=24,
                   command=lambda f=fn, l=label: (run_in_thread(f), log_msg(log_box, l))
                   ).grid(row=0, column=i, padx=6, pady=4)
    action_frame.pack(fill="x", pady=5)

    # ── Find Tab by Name ─────────────────────────
    find_frame = ttk.LabelFrame(frame, text="  Switch to Tab by Name  (Ctrl+Shift+A)", padding=10)
    ttk.Label(find_frame,
              text="Type part of the tab title — Chrome Tab Search will jump to it.",
              style="Dim.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

    ttk.Label(find_frame, text="Keyword:").grid(row=1, column=0, sticky="w")
    find_var = tk.StringVar(value="Sales Page")
    ttk.Entry(find_frame, textvariable=find_var, width=32).grid(row=1, column=1, padx=(6, 10))

    def do_find_tab():
        kw = find_var.get().strip()
        if not kw:
            messagebox.showwarning("Empty", "Enter a tab name keyword first.")
            return
        run_in_thread(engine.switch_to_tab_by_name, kw)
        log_msg(log_box, f"Tab search: \"{kw}\"")

    ttk.Button(find_frame, text="Switch", command=do_find_tab,
               style="Accent.TButton").grid(row=1, column=2, padx=6)

    ttk.Label(find_frame, text="Saved tabs:", style="Dim.TLabel").grid(row=2, column=0, sticky="w", pady=(10, 2))
    saved_tabs_frame = ttk.Frame(find_frame)
    saved_tabs_frame.grid(row=3, column=0, columnspan=4, sticky="w")
    saved_tabs = []

    def refresh_saved_buttons():
        for w in saved_tabs_frame.winfo_children():
            w.destroy()
        for name in saved_tabs:
            ttk.Button(saved_tabs_frame, text=name, width=16,
                       command=lambda n=name: (find_var.set(n), do_find_tab())
                       ).pack(side="left", padx=3, pady=2)

    def save_tab_name():
        name = find_var.get().strip()
        if name and name not in saved_tabs:
            saved_tabs.append(name)
            refresh_saved_buttons()

    def clear_saved():
        saved_tabs.clear()
        refresh_saved_buttons()

    btn_row = ttk.Frame(find_frame)
    btn_row.grid(row=4, column=0, columnspan=4, sticky="w", pady=6)
    ttk.Button(btn_row, text="📌 Save this name", command=save_tab_name, width=16).pack(side="left", padx=3)
    ttk.Button(btn_row, text="🗑 Clear saved", command=clear_saved,
               style="Danger.TButton", width=14).pack(side="left", padx=3)
    find_frame.pack(fill="x", pady=5)

    # ── Open URL ─────────────────────────────────
    url_frame = ttk.LabelFrame(frame, text="  Open URL in Chrome", padding=10)
    ttk.Label(url_frame, text="URL:").grid(row=0, column=0)
    url_var = tk.StringVar(value="https://www.google.com")
    ttk.Entry(url_frame, textvariable=url_var, width=44).grid(row=0, column=1, padx=(6, 10))

    def do_open_url():
        url = url_var.get().strip()
        if not url:
            messagebox.showwarning("Empty", "Enter a URL first.")
            return
        run_in_thread(engine.open_url, url)
        log_msg(log_box, f"Open URL: {url}")

    ttk.Button(url_frame, text="Open", command=do_open_url,
               style="Accent.TButton").grid(row=0, column=2, padx=8)
    url_frame.pack(fill="x", pady=5)

    ttk.Label(frame, text="Action Log", style="LogTitle.TLabel").pack(anchor="w", pady=(6, 2))
    log_box.pack(fill="both", expand=True)
    return frame


# ══════════════════════════════════════════════
#  POSITION RECORDER TAB
# ══════════════════════════════════════════════

def build_recorder_tab(parent):
    frame = ttk.Frame(parent, padding=14)

    # ── Info banner ──────────────────────────────
    info = tk.Frame(frame, bg=COLORS["bg3"], padx=12, pady=8)
    info.pack(fill="x", pady=(0, 10))
    tk.Label(info,
             text="Move your mouse anywhere — coordinates update live below.",
             bg=COLORS["bg3"], fg=COLORS["text_dim"],
             font=("Segoe UI", 9)).pack(anchor="w")

    # ── Live coordinate badge ────────────────────
    badge = tk.Frame(frame, bg=COLORS["bg2"], padx=16, pady=14)
    badge.pack(fill="x", pady=(0, 10))
    tk.Label(badge, text="CURSOR POSITION",
             bg=COLORS["bg2"], fg=COLORS["text_dim"],
             font=("Segoe UI", 7, "bold")).pack(anchor="w")
    live_label = tk.Label(badge, text="X: 0    Y: 0",
                          bg=COLORS["bg2"], fg=COLORS["accent"],
                          font=("Consolas", 24, "bold"))
    live_label.pack(anchor="w", pady=(2, 0))

    # ── Captured list ────────────────────────────
    list_outer = ttk.LabelFrame(frame, text="  Captured Positions", padding=8)
    list_outer.pack(fill="both", expand=True, pady=4)
    captured = []
    listbox = styled_listbox(list_outer, height=10)
    sb = ttk.Scrollbar(list_outer, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=sb.set)
    listbox.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def _update_live():
        try:
            x, y = engine.get_mouse_position()
            live_label.config(text=f"X: {x}    Y: {y}")
        except Exception:
            pass
        frame.after(80, _update_live)

    def capture():
        try:
            x, y = engine.get_mouse_position()
            entry = f"({x}, {y})"
            captured.append(entry)
            listbox.insert(tk.END, f"  {len(captured):>3}.   {entry}")
            listbox.see(tk.END)
        except Exception:
            pass

    def clear_list():
        captured.clear()
        listbox.delete(0, tk.END)

    def click_captured():
        sel = listbox.curselection()
        if not sel:
            return
        try:
            val = captured[sel[0]]          # e.g. "(500, 300)"
            inner = val.strip("()")
            x_s, y_s = inner.split(",", 1)
            run_in_thread(engine.click, int(x_s.strip()), int(y_s.strip()))
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Could not parse the selected coordinate.")

    # ── Buttons ──────────────────────────────────
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=8)
    ttk.Button(btn_frame, text="📌  Capture Position", command=capture,
               style="Accent.TButton", width=20).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="🖱  Click Selected", command=click_captured,
               width=18).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="🗑  Clear All", command=clear_list,
               style="Danger.TButton", width=12).pack(side="left", padx=4)

    _update_live()
    return frame


# ══════════════════════════════════════════════
#  MACRO SEQUENCE TAB
# ══════════════════════════════════════════════

def build_macro_tab(parent):
    frame = ttk.Frame(parent, padding=14)

    sequence  = []
    is_running = False

    # ── Add Action panel ──────────────────────────
    input_frame = ttk.LabelFrame(frame, text="  Add Action", padding=10)
    input_frame.pack(fill="x", pady=4)

    action_type = tk.StringVar(value="move")
    param_frame = ttk.Frame(input_frame)
    param_widgets = {}

    ACTION_TYPES = [
        "move", "click", "right_click", "double_click",
        "type", "key", "hotkey",
        "scroll", "drag", "wait",
        "next_tab", "prev_tab", "new_tab", "close_tab", "refresh",
    ]

    def build_param_fields(event=None):
        for w in param_frame.winfo_children():
            w.destroy()
        param_widgets.clear()
        t = action_type.get()

        def lbl(text, col):
            ttk.Label(param_frame, text=text).grid(row=0, column=col, sticky="w", padx=(6, 2))

        def ent(var, col, width=8):
            ttk.Entry(param_frame, textvariable=var, width=width).grid(row=0, column=col, padx=2)

        if t in ("move", "click", "right_click", "double_click"):
            xv, yv = tk.StringVar(value="500"), tk.StringVar(value="400")
            lbl("X:", 0); ent(xv, 1); lbl("Y:", 2); ent(yv, 3)
            param_widgets.update(x=xv, y=yv)
            if t == "move":
                dv = tk.StringVar(value="0.4")
                lbl("Duration:", 4); ent(dv, 5, 6)
                param_widgets["duration"] = dv

        elif t == "scroll":
            xv, yv, av = tk.StringVar(value="500"), tk.StringVar(value="400"), tk.StringVar(value="3")
            lbl("X:", 0); ent(xv, 1); lbl("Y:", 2); ent(yv, 3)
            lbl("Amount:", 4); ent(av, 5, 5)
            param_widgets.update(x=xv, y=yv, amount=av)

        elif t == "drag":
            x1v, y1v = tk.StringVar(value="200"), tk.StringVar(value="200")
            x2v, y2v = tk.StringVar(value="600"), tk.StringVar(value="400")
            lbl("From X:", 0); ent(x1v, 1); lbl("Y:", 2); ent(y1v, 3)
            lbl("To X:",   4); ent(x2v, 5); lbl("Y:", 6); ent(y2v, 7)
            param_widgets.update(x1=x1v, y1=y1v, x2=x2v, y2=y2v)

        elif t == "type":
            tv = tk.StringVar(value="Hello!")
            lbl("Text:", 0)
            ttk.Entry(param_frame, textvariable=tv, width=30).grid(row=0, column=1, padx=4, columnspan=3)
            param_widgets["text"] = tv

        elif t == "key":
            kv = tk.StringVar(value="enter")
            lbl("Key:", 0); ent(kv, 1, 12)
            param_widgets["key"] = kv

        elif t == "hotkey":
            hv = tk.StringVar(value="ctrl,c")
            lbl("Keys (comma-sep):", 0)
            ttk.Entry(param_frame, textvariable=hv, width=20).grid(row=0, column=1, padx=4)
            param_widgets["keys"] = hv

        elif t == "wait":
            sv = tk.StringVar(value="1.0")
            lbl("Seconds:", 0); ent(sv, 1, 8)
            param_widgets["seconds"] = sv

        else:  # chrome no-param actions
            ttk.Label(param_frame, text="(no parameters needed)",
                      foreground=COLORS["text_dim"]).grid(row=0, column=0, padx=6)

    # Action type dropdown
    top_row = ttk.Frame(input_frame)
    top_row.pack(fill="x", pady=(0, 6))
    ttk.Label(top_row, text="Action:").pack(side="left")
    type_menu = ttk.Combobox(top_row, textvariable=action_type, values=ACTION_TYPES,
                              state="readonly", width=18)
    type_menu.pack(side="left", padx=(6, 10))
    type_menu.bind("<<ComboboxSelected>>", build_param_fields)
    param_frame.pack(fill="x", pady=4)
    build_param_fields()

    # ── Step builder / executor ───────────────────
    def make_step():
        t = action_type.get()
        p = {k: v.get() for k, v in param_widgets.items()}
        labels = {
            "move":         lambda: f"Move → ({p['x']}, {p['y']})  dur={p.get('duration','0.4')}s",
            "click":        lambda: f"Click at ({p['x']}, {p['y']})",
            "right_click":  lambda: f"Right Click at ({p['x']}, {p['y']})",
            "double_click": lambda: f"Double Click at ({p['x']}, {p['y']})",
            "scroll":       lambda: f"Scroll {p['amount']} at ({p['x']}, {p['y']})",
            "drag":         lambda: f"Drag ({p['x1']},{p['y1']}) → ({p['x2']},{p['y2']})",
            "type":         lambda: f"Type \"{p['text']}\"",
            "key":          lambda: f"Key [{p['key']}]",
            "hotkey":       lambda: f"Hotkey [{p['keys']}]",
            "wait":         lambda: f"Wait {p['seconds']}s",
        }
        label = labels[t]() if t in labels else t.replace("_", " ").title()
        return {"type": t, "params": p, "label": label}

    def execute_step(step):
        t = step["type"]
        p = step["params"]
        dispatch = {
            "move":         lambda: engine.move_mouse(int(p["x"]), int(p["y"]), float(p.get("duration", 0.4))),
            "click":        lambda: engine.click(int(p["x"]), int(p["y"])),
            "right_click":  lambda: engine.right_click(int(p["x"]), int(p["y"])),
            "double_click": lambda: engine.double_click(int(p["x"]), int(p["y"])),
            "scroll":       lambda: engine.scroll(int(p["x"]), int(p["y"]), int(p["amount"])),
            "drag":         lambda: engine.drag(int(p["x1"]), int(p["y1"]), int(p["x2"]), int(p["y2"])),
            "type":         lambda: engine.type_text(p["text"]),
            "key":          lambda: engine.press_key(p["key"]),
            "hotkey":       lambda: engine.hotkey(*[k.strip() for k in p["keys"].split(",") if k.strip()]),
            "wait":         lambda: engine.sleep(float(p["seconds"])),
            "next_tab":     engine.next_tab,
            "prev_tab":     engine.prev_tab,
            "new_tab":      engine.new_tab,
            "close_tab":    engine.close_tab,
            "refresh":      engine.refresh_page,
        }
        if t in dispatch:
            dispatch[t]()

    # ── Sequence listbox ──────────────────────────
    list_frame = ttk.LabelFrame(frame, text="  Sequence", padding=6)
    list_frame.pack(fill="both", expand=True, pady=4)
    seq_lb = styled_listbox(list_frame, height=9)
    seq_sb = ttk.Scrollbar(list_frame, orient="vertical", command=seq_lb.yview)
    seq_lb.configure(yscrollcommand=seq_sb.set)
    seq_lb.pack(side="left", fill="both", expand=True)
    seq_sb.pack(side="right", fill="y")

    def refresh_listbox():
        seq_lb.delete(0, tk.END)
        for i, step in enumerate(sequence):
            seq_lb.insert(tk.END, f"  {i+1:>2}.   {step['label']}")

    def add_step():
        sequence.append(make_step())
        refresh_listbox()
        seq_lb.see(tk.END)

    def remove_step():
        sel = seq_lb.curselection()
        if sel:
            sequence.pop(sel[0])
            refresh_listbox()

    def move_up():
        sel = seq_lb.curselection()
        if sel and sel[0] > 0:
            i = sel[0]
            sequence[i], sequence[i - 1] = sequence[i - 1], sequence[i]
            refresh_listbox()
            seq_lb.selection_set(i - 1)

    def move_down():
        sel = seq_lb.curselection()
        if sel and sel[0] < len(sequence) - 1:
            i = sel[0]
            sequence[i], sequence[i + 1] = sequence[i + 1], sequence[i]
            refresh_listbox()
            seq_lb.selection_set(i + 1)

    def clear_all():
        if messagebox.askyesno("Clear", "Clear entire sequence?"):
            sequence.clear()
            refresh_listbox()

    # ── Sequence buttons ──────────────────────────
    seq_btn_row = ttk.Frame(frame)
    seq_btn_row.pack(fill="x", pady=4)
    ttk.Button(seq_btn_row, text="➕  Add Step",  command=add_step,
               style="Accent.TButton", width=13).pack(side="left", padx=3)
    ttk.Button(seq_btn_row, text="🗑  Remove",    command=remove_step,
               width=10).pack(side="left", padx=3)
    ttk.Button(seq_btn_row, text="⬆  Up",         command=move_up,   width=8).pack(side="left", padx=3)
    ttk.Button(seq_btn_row, text="⬇  Down",       command=move_down, width=8).pack(side="left", padx=3)
    ttk.Button(seq_btn_row, text="🗂  Clear All", command=clear_all,
               style="Danger.TButton", width=12).pack(side="left", padx=3)

    # ── Save / Load ───────────────────────────────
    def save_sequence():
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Macro Sequence",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(sequence, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Saved", f"Sequence saved to:\n{path}")
        except OSError as e:
            messagebox.showerror("Save Failed", f"Could not save file:\n{e}")

    def load_sequence():
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Macro Sequence",
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, list):
                raise ValueError("File does not contain a sequence list.")
            sequence.clear()
            sequence.extend(loaded)
            refresh_listbox()
        except (OSError, json.JSONDecodeError, ValueError) as e:
            messagebox.showerror("Load Failed", f"Could not load file:\n{e}")

    io_row = ttk.Frame(frame)
    io_row.pack(fill="x", pady=2)
    ttk.Button(io_row, text="💾  Save Sequence", command=save_sequence, width=17).pack(side="left", padx=3)
    ttk.Button(io_row, text="📂  Load Sequence", command=load_sequence, width=17).pack(side="left", padx=3)

    # ── Run Controls ──────────────────────────────
    run_frame = ttk.LabelFrame(frame, text="  Run Controls", padding=10)
    run_frame.pack(fill="x", pady=6)

    cfg_row = ttk.Frame(run_frame)
    cfg_row.pack(fill="x", pady=(0, 6))
    ttk.Label(cfg_row, text="Start delay (s):").pack(side="left")
    delay_var = tk.StringVar(value="2.0")
    ttk.Entry(cfg_row, textvariable=delay_var, width=6).pack(side="left", padx=(4, 16))
    ttk.Label(cfg_row, text="Loops:").pack(side="left")
    loop_var = tk.StringVar(value="1")
    ttk.Spinbox(cfg_row, from_=1, to=999, textvariable=loop_var, width=7).pack(side="left", padx=(4, 16))
    ttk.Label(cfg_row, text="Step delay (s):").pack(side="left")
    step_delay_var = tk.StringVar(value="0.2")
    ttk.Entry(cfg_row, textvariable=step_delay_var, width=6).pack(side="left", padx=(4, 16))
    f8_hint = "  🔒 Press F8 to stop" if _KEYBOARD_AVAILABLE else "  🔒 Use Stop button to stop"
    ttk.Label(cfg_row, text=f8_hint, style="Dim.TLabel").pack(side="left", padx=(8, 0))

    ctrl_row = ttk.Frame(run_frame)
    ctrl_row.pack(fill="x", pady=2)
    run_btn  = ttk.Button(ctrl_row, text="▶  Run All",     style="Accent.TButton", width=14)
    stop_btn = ttk.Button(ctrl_row, text="⏹  Stop  (F8)", style="Danger.TButton", width=14, state="disabled")
    run_btn.pack(side="left", padx=(0, 6))
    stop_btn.pack(side="left", padx=6)
    progress_var = tk.DoubleVar()
    ttk.Progressbar(ctrl_row, variable=progress_var, maximum=100, length=260).pack(
        side="left", padx=(12, 6), fill="x", expand=True)

    status_label = ttk.Label(run_frame, text="Status: idle", style="Dim.TLabel")
    status_label.pack(anchor="w", pady=(4, 0))

    # ── Error log ─────────────────────────────────
    ttk.Label(frame, text="Error Log", style="LogTitle.TLabel").pack(anchor="w", pady=(6, 2))
    err_log = scrolledtext.ScrolledText(frame, height=4, state="disabled",
                                        font=("Consolas", 8),
                                        bg="#1a0a0a", fg=COLORS["error"],
                                        insertbackground=COLORS["error"],
                                        relief="flat", bd=0, padx=8, pady=6)
    err_log.pack(fill="x", pady=(0, 4))

    # ── Thread-safe UI updaters ───────────────────
    def _log_error(msg: str):
        def _w():
            err_log.configure(state="normal")
            err_log.insert(tk.END, msg + "\n")
            err_log.see(tk.END)
            err_log.configure(state="disabled")
        frame.after(0, _w)

    def _set_status(text: str, color: str):
        frame.after(0, lambda: status_label.config(text=text, foreground=color))

    def _set_progress(value: float):
        frame.after(0, lambda: progress_var.set(value))

    def _reset_ui():
        frame.after(0, lambda: (run_btn.config(state="normal"),
                                 stop_btn.config(state="disabled")))

    # ── Stop function (called from button OR hotkey thread) ──────────
    def stop_sequence():
        _GLOBAL_STOP["stop"] = True
        # .after(0) makes this safe when called from the keyboard hook thread
        frame.after(0, lambda: status_label.config(
            text="Status: stopping…", foreground=COLORS["warning"]))

    # ── Run function ──────────────────────────────
    def run_sequence():
        nonlocal is_running
        if not sequence:
            messagebox.showwarning("Empty", "Add at least one step before running.")
            return
        if is_running:
            return

        is_running = True
        _GLOBAL_STOP["stop"] = False
        run_btn.config(state="disabled")
        stop_btn.config(state="normal")

        # Register F8 — remove first so double-clicking Run never double-registers
        _hotkey_register(stop_sequence)

        loops       = safe_int(loop_var.get(), 1)
        start_delay = safe_float(delay_var.get(), 2.0)
        step_delay  = safe_float(step_delay_var.get(), 0.2)
        total_steps = max(len(sequence) * loops, 1)  # avoid /0

        def task():
            nonlocal is_running
            _set_status(f"Status: starting in {start_delay}s…", COLORS["warning"])
            time.sleep(start_delay)

            done = 0
            for loop_i in range(loops):
                if _GLOBAL_STOP["stop"]:
                    break
                for step_i, step in enumerate(sequence):
                    if _GLOBAL_STOP["stop"]:
                        break
                    _set_status(
                        f"Status: loop {loop_i+1}/{loops}  ·  "
                        f"step {step_i+1}/{len(sequence)}  —  {step['label']}",
                        COLORS["accent"],
                    )
                    try:
                        execute_step(step)
                    except Exception:
                        last_line = traceback.format_exc().strip().splitlines()[-1]
                        _log_error(f"[L{loop_i+1} S{step_i+1}] {step['label']}  →  {last_line}")
                    done += 1
                    _set_progress((done / total_steps) * 100)
                    time.sleep(step_delay)

            if _GLOBAL_STOP["stop"]:
                _set_status("Status: ⏹ stopped by user", COLORS["error"])
            else:
                _set_status("Status: ✅ completed", COLORS["success"])

            _set_progress(0)
            _reset_ui()
            _hotkey_unregister()
            is_running = False

        threading.Thread(target=task, daemon=True).start()

    run_btn.config(command=run_sequence)
    stop_btn.config(command=stop_sequence)

    return frame


# ══════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════

def main():
    root = tk.Tk()
    root.title("WinMacroApp")
    root.geometry("1020x720")
    root.minsize(820, 580)
    root.resizable(True, True)

    apply_theme(root)

    # ── Header bar ────────────────────────────────
    header_bar = tk.Frame(root, bg=COLORS["bg2"])
    header_bar.pack(fill="x")
    tk.Frame(header_bar, bg=COLORS["accent"], width=4).pack(side="left", fill="y")
    tk.Label(header_bar,
             text="⚡  WinMacroApp",
             bg=COLORS["bg2"], fg=COLORS["accent"],
             font=("Segoe UI", 14, "bold"),
             padx=16, pady=10).pack(side="left")
    tk.Label(header_bar,
             text="Mouse & Keyboard Automation for Windows",
             bg=COLORS["bg2"], fg=COLORS["text_dim"],
             font=("Segoe UI", 9)).pack(side="left")

    # ── Tabs ──────────────────────────────────────
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    notebook.add(build_mouse_tab(notebook),    text="  🖱  Mouse  ")
    notebook.add(build_keyboard_tab(notebook), text="  ⌨  Keyboard  ")
    notebook.add(build_chrome_tab(notebook),   text="  🌐  Chrome Tabs  ")
    notebook.add(build_recorder_tab(notebook), text="  📍  Recorder  ")
    notebook.add(build_macro_tab(notebook),    text="  ⚙  Macro Sequence  ")

    # ── Status bar ────────────────────────────────
    status_bar = tk.Frame(root, bg=COLORS["bg3"], pady=4)
    status_bar.pack(fill="x", side="bottom")
    tk.Frame(status_bar, bg=COLORS["warning"], width=4).pack(side="left", fill="y")
    tk.Label(status_bar,
             text="  ⚠  Move mouse to TOP-LEFT corner (0, 0) to emergency-stop  |  "
                  f"{'F8 = stop macro  |  ' if _KEYBOARD_AVAILABLE else ''}"
                  "All actions fire after a 1.5 s delay",
             bg=COLORS["bg3"], fg=COLORS["text_dim"],
             font=("Segoe UI", 8)).pack(side="left", padx=8)

    root.mainloop()


if __name__ == "__main__":
    main()
