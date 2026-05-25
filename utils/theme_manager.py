"""Lightweight theme manager — stores preference in config.json."""
from __future__ import annotations
import sys
import json
from pathlib import Path

_BASE = (
    Path(sys.executable).parent
    if getattr(sys, "frozen", False)
    else Path(__file__).parent.parent
)
CONFIG_PATH = _BASE / "config.json"
_current: str = "light"   # light by default

FONT_MIN = 8
FONT_MAX = 16
_font_size: int = 11      # 11pt default


def load() -> str:
    """Read theme from config file; return 'light' if missing."""
    global _current
    try:
        data = json.loads(CONFIG_PATH.read_text("utf-8"))
        _current = data.get("theme", "light")
    except Exception:
        _current = "light"
    return _current


def load_font_size() -> int:
    """Read font size from config file; return 11 if missing."""
    global _font_size
    try:
        data = json.loads(CONFIG_PATH.read_text("utf-8"))
        _font_size = int(data.get("font_size", 11))
        _font_size = max(FONT_MIN, min(FONT_MAX, _font_size))
    except Exception:
        _font_size = 11
    return _font_size


def current() -> str:
    return _current


def font_size() -> int:
    return _font_size


def apply(theme: str, app=None):
    """Apply stylesheet to running QApplication."""
    global _current
    _current = theme
    _save_config("theme", theme)

    from ui.styles import get_style
    from PyQt6.QtWidgets import QApplication
    target = app or QApplication.instance()
    if target:
        target.setStyleSheet(get_style(theme))


def set_font_size(size: int, app=None):
    """Set application font size and persist to config."""
    global _font_size
    _font_size = max(FONT_MIN, min(FONT_MAX, size))
    _save_config("font_size", _font_size)

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    target = app or QApplication.instance()
    if target:
        f = QFont("Segoe UI", _font_size)
        f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        target.setFont(f)


def toggle(app=None) -> str:
    new = "dark" if _current == "light" else "light"
    apply(new, app)
    return new


def _save_config(key: str, value):
    try:
        existing: dict = {}
        try:
            existing = json.loads(CONFIG_PATH.read_text("utf-8"))
        except Exception:
            pass
        existing[key] = value
        CONFIG_PATH.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2), "utf-8"
        )
    except Exception:
        pass
