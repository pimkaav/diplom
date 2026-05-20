"""Lightweight theme manager — stores preference in config.json."""
from __future__ import annotations
import sys
import json
from pathlib import Path

# When running as a PyInstaller .exe, resolve paths relative to the exe;
# otherwise use the project root (two levels up from utils/).
_BASE = (
    Path(sys.executable).parent
    if getattr(sys, "frozen", False)
    else Path(__file__).parent.parent
)
CONFIG_PATH = _BASE / "config.json"
_current: str = "dark"   # dark by default


def load() -> str:
    """Read theme from config file; return 'dark' if missing."""
    global _current
    try:
        data = json.loads(CONFIG_PATH.read_text("utf-8"))
        _current = data.get("theme", "dark")
    except Exception:
        _current = "dark"
    return _current


def current() -> str:
    return _current


def apply(theme: str, app=None):
    """Apply stylesheet to running QApplication."""
    global _current
    _current = theme
    _save(theme)

    from ui.styles import get_style
    from PyQt6.QtWidgets import QApplication
    target = app or QApplication.instance()
    if target:
        target.setStyleSheet(get_style(theme))


def toggle(app=None) -> str:
    new = "dark" if _current == "light" else "light"
    apply(new, app)
    return new


def _save(theme: str):
    try:
        existing: dict = {}
        try:
            existing = json.loads(CONFIG_PATH.read_text("utf-8"))
        except Exception:
            pass
        existing["theme"] = theme
        CONFIG_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass
