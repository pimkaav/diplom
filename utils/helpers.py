from __future__ import annotations
import sys
import os
import math
import json
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


# ── City coordinates (lat, lon) ───────────────────────────────────
CITY_COORDS: dict[str, tuple[float, float]] = {
    "Москва":             (55.7558,  37.6173),
    "Санкт-Петербург":    (59.9311,  30.3609),
    "Новосибирск":        (54.9833,  82.8964),
    "Екатеринбург":       (56.8389,  60.6057),
    "Казань":             (55.8304,  49.0661),
    "Нижний Новгород":    (56.3269,  44.0059),
    "Челябинск":          (55.1644,  61.4368),
    "Омск":               (54.9885,  73.3242),
    "Самара":             (53.2001,  50.1500),
    "Уфа":                (54.7388,  55.9721),
    "Ростов-на-Дону":     (47.2357,  39.7015),
    "Красноярск":         (56.0184,  92.8672),
    "Воронеж":            (51.6720,  39.1843),
    "Пермь":              (58.0105,  56.2502),
    "Волгоград":          (48.7194,  44.5018),
    "Краснодар":          (45.0448,  38.9760),
    "Тюмень":             (57.1522,  65.5272),
    "Саратов":            (51.5336,  46.0343),
    "Тольятти":           (53.5303,  49.3461),
    "Ижевск":             (56.8527,  53.2114),
    "Барнаул":            (53.3547,  83.7697),
    "Ульяновск":          (54.3142,  48.4032),
    "Иркутск":            (52.2978, 104.2964),
    "Хабаровск":          (48.4827, 135.0840),
    "Ярославль":          (57.6261,  39.8845),
    "Владивосток":        (43.1332, 131.9113),
    "Махачкала":          (42.9849,  47.5047),
    "Томск":              (56.4977,  84.9744),
    "Оренбург":           (51.7727,  55.0988),
    "Новокузнецк":        (53.7596,  87.1216),
    "Кемерово":           (55.3549,  86.0882),
    "Рязань":             (54.6296,  39.7418),
    "Астрахань":          (46.3497,  48.0408),
    "Набережные Челны":   (55.7434,  52.4057),
    "Пенза":              (53.1950,  45.0183),
    "Липецк":             (52.6088,  39.5990),
    "Калининград":        (54.7104,  20.4522),
    "Тула":               (54.1935,  37.6166),
    "Киров":              (58.5969,  49.6578),
    "Чебоксары":          (56.1439,  47.2489),
    "Брянск":             (53.2435,  34.3640),
    "Курск":              (51.7304,  36.1938),
    "Иваново":            (57.0005,  40.9739),
    "Магнитогорск":       (53.4145,  59.0621),
    "Белгород":           (50.5997,  36.5985),
    "Владимир":           (56.1291,  40.4066),
    "Сочи":               (43.5855,  39.7231),
    "Тверь":              (56.8587,  35.9176),
    "Калуга":             (54.5293,  36.2754),
    "Смоленск":           (54.7826,  32.0453),
}

_BASE_CFG = (
    Path(sys.executable).parent
    if getattr(sys, "frozen", False)
    else Path(__file__).parent.parent
)
_CONFIG_PATH = _BASE_CFG / "config.json"


def _read_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text("utf-8"))
    except Exception:
        return {}


def _write_config(data: dict):
    try:
        _CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass


def load_custom_cities() -> dict[str, tuple[float, float]]:
    """Return {name: (lat, lon)} of user-added cities."""
    return _read_config().get("custom_cities", {})


def save_custom_city(name: str, lat: float, lon: float):
    cfg = _read_config()
    cities = cfg.get("custom_cities", {})
    cities[name] = [lat, lon]
    cfg["custom_cities"] = cities
    _write_config(cfg)


def all_cities() -> dict[str, tuple[float, float]]:
    """Merged built-in + custom cities."""
    result = dict(CITY_COORDS)
    for name, coords in load_custom_cities().items():
        result[name] = tuple(coords)
    return result


def haversine_km(city1: str, city2: str) -> float:
    """Return road-approximate distance between two cities (km).
    Uses straight-line Haversine × 1.25 road correction factor."""
    coords = all_cities()
    if city1 not in coords or city2 not in coords:
        return 0.0
    lat1, lon1 = coords[city1]
    lat2, lon2 = coords[city2]
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return round(R * c * 1.25)
