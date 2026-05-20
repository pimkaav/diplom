from __future__ import annotations
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

# When running as a PyInstaller .exe, store user data next to the executable;
# otherwise use the project root (two levels up from utils/).
_BASE = (
    Path(sys.executable).parent
    if getattr(sys, "frozen", False)
    else Path(__file__).parent.parent
)
AVATAR_DIR     = _BASE / "assets" / "avatars"
ATTACHMENT_DIR = _BASE / "assets" / "attachments"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)


# ── File helpers ──────────────────────────────────────────────────

def save_avatar(source_path: str, user_id: int) -> str:
    ext  = Path(source_path).suffix
    dest = AVATAR_DIR / f"user_{user_id}{ext}"
    shutil.copy2(source_path, dest)
    return str(dest)


def save_attachment(source_path: str) -> str:
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_{Path(source_path).name}"
    dest  = ATTACHMENT_DIR / fname
    shutil.copy2(source_path, dest)
    return str(dest)


# ── Round avatar pixmap ───────────────────────────────────────────

def make_round_pixmap(path: str, size: int):
    """Return a circular QPixmap from an image file. Returns None on failure."""
    try:
        from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QBrush
        from PyQt6.QtCore import Qt

        original = QPixmap(path)
        if original.isNull():
            return None

        scaled = original.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        result = QPixmap(size, size)
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        clip = QPainterPath()
        clip.addEllipse(0, 0, size, size)
        painter.setClipPath(clip)

        x = (scaled.width()  - size) // 2
        y = (scaled.height() - size) // 2
        painter.drawPixmap(0, 0, scaled, x, y, size, size)
        painter.end()
        return result
    except Exception:
        return None


def apply_round_avatar(label, path: str, size: int, fallback: str = "👤"):
    """Set a round pixmap on a QLabel, or fall back to emoji text."""
    pix = make_round_pixmap(path, size) if path else None
    if pix:
        label.setPixmap(pix)
        label.setText("")
    else:
        label.setText(fallback)
        label.setPixmap(label.pixmap() if False else __import__("PyQt6.QtGui", fromlist=["QPixmap"]).QPixmap())


# ── Formatting helpers ────────────────────────────────────────────

def fmt_money(amount) -> str:
    try:
        return f"{float(amount):,.0f} ₽".replace(",", " ")
    except (TypeError, ValueError):
        return "—"


def fmt_date(dt_str) -> str:
    """Format date to DD.MM.YYYY. Accepts datetime objects or strings."""
    if not dt_str:
        return "—"
    if isinstance(dt_str, datetime):
        return dt_str.strftime("%d.%m.%Y")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(str(dt_str), fmt).strftime("%d.%m.%Y")
        except ValueError:
            continue
    return str(dt_str)


def fmt_datetime(dt_str) -> str:
    """Format datetime to DD.MM.YYYY HH:MM. Accepts datetime objects or strings."""
    if not dt_str:
        return "—"
    if isinstance(dt_str, datetime):
        return dt_str.strftime("%d.%m.%Y %H:%M")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(dt_str), fmt).strftime("%d.%m.%Y %H:%M")
        except ValueError:
            continue
    return str(dt_str)


def stars_text(rating: float, count: int = 0) -> str:
    full = int(round(rating))
    s    = "★" * full + "☆" * (5 - full)
    return f"{s}  {rating:.1f}  ({count} отз.)" if count else f"{s}  {rating:.1f}"


def truncate(text: str, length: int = 80) -> str:
    if not text:
        return ""
    return text if len(text) <= length else text[:length] + "…"
