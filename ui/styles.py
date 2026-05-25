# ─── Light palette (default / only theme) ─────────────────────────
L = {
    "primary":        "#2563EB",
    "primary_dark":   "#1D4ED8",
    "primary_light":  "#EFF6FF",
    "sidebar_bg":     "#FFFFFF",   # white sidebar
    "sidebar_hover":  "#F1F5F9",   # soft hover
    "sidebar_active": "#EFF6FF",   # light-blue active
    "content_bg":     "#F1F5F9",   # very light gray content
    "card_bg":        "#FFFFFF",
    "border":         "#E2E8F0",
    "text":           "#0F172A",
    "text_muted":     "#64748B",
    "success":        "#16A34A",
    "success_light":  "#F0FDF4",
    "warning":        "#D97706",
    "warning_light":  "#FFFBEB",
    "danger":         "#DC2626",
    "danger_light":   "#FEF2F2",
    "info":           "#0EA5E9",
    "input_bg":       "#FFFFFF",
    "input_border":   "#CBD5E1",
    "input_focus":    "#2563EB",
    "combo_drop":     "#FFFFFF",
    "combo_text":     "#0F172A",
    "combo_sel_bg":   "#EFF6FF",
    "combo_sel_text": "#2563EB",
    "tbl_alt":        "#F8FAFC",
    "progress_track": "#E2E8F0",
}

# ─── Dark palette (kept for compatibility) ────────────────────────
D = {
    "primary":        "#3B82F6",
    "primary_dark":   "#2563EB",
    "primary_light":  "#1E3A5F",
    "sidebar_bg":     "#020617",
    "sidebar_hover":  "#0F172A",
    "sidebar_active": "#2563EB",
    "content_bg":     "#0F172A",
    "card_bg":        "#1E293B",
    "border":         "#334155",
    "text":           "#F1F5F9",
    "text_muted":     "#94A3B8",
    "success":        "#22C55E",
    "success_light":  "#14532D",
    "warning":        "#F59E0B",
    "warning_light":  "#451A03",
    "danger":         "#EF4444",
    "danger_light":   "#450A0A",
    "info":           "#38BDF8",
    "input_bg":       "#1A2540",
    "input_border":   "#3B82F6",
    "input_focus":    "#60A5FA",
    "combo_drop":     "#1E293B",
    "combo_text":     "#F1F5F9",
    "combo_sel_bg":   "#1E3A5F",
    "combo_sel_text": "#93C5FD",
    "tbl_alt":        "#1A2535",
    "progress_track": "#334155",
}

STATUS_COLORS = {
    "new":         ("#DBEAFE", "#1D4ED8"),
    "in_progress": ("#FEF9C3", "#92400E"),
    "completed":   ("#DCFCE7", "#15803D"),
    "cancelled":   ("#FEE2E2", "#B91C1C"),
}
STATUS_LABELS = {
    "new":         "Новый",
    "in_progress": "В работе",
    "completed":   "Завершён",
    "cancelled":   "Отменён",
}
PAYMENT_STATUS_LABELS = {
    "pending":  "Ожидает",
    "held":     "Удержано",
    "released": "Выплачено",
    "refunded": "Возврат",
}
PROGRESS_LABELS = {
    "waiting":          "Ожидает назначения",
    "vehicle_assigned": "Машина назначена",
    "dispatched":       "Груз отправлен",
    "in_transit":       "В пути",
    "arrived":          "Прибыл",
    "completed":        "Завершено",
}


def _build(p: dict) -> str:
    focus_bg = p["primary_light"]
    return f"""
/* ══════════════════════════════════════════════════════════
   GLOBAL                                                    */
QWidget {{
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 11pt;
    color: {p["text"]};
    outline: 0;
}}
QMainWindow, QDialog, QWidget#central {{
    background-color: {p["content_bg"]};
}}

/* ── Scroll bars ────────────────────────────────────────── */
QScrollBar:vertical {{
    border: none; background: {p["content_bg"]}; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {p["border"]}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {p["text_muted"]}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    border: none; background: {p["content_bg"]}; height: 8px; border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {p["border"]}; border-radius: 4px; min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: {p["text_muted"]}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── QLineEdit / QTextEdit / QPlainTextEdit ─────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {p["input_bg"]};
    border: 1.5px solid {p["input_border"]};
    border-radius: 8px;
    padding: 8px 12px;
    color: {p["text"]};
    selection-background-color: {p["primary"]};
    selection-color: white;
    font-size: 11pt;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {p["input_focus"]};
    border-width: 2px;
    background: {focus_bg};
}}
QLineEdit:disabled, QTextEdit:disabled {{
    background: {p["content_bg"]}; color: {p["text_muted"]};
}}

/* ── QSpinBox / QDoubleSpinBox ──────────────────────────── */
QSpinBox, QDoubleSpinBox {{
    background: {p["input_bg"]};
    border: 1.5px solid {p["input_border"]};
    border-radius: 8px;
    padding: 7px 10px;
    color: {p["text"]};
    font-size: 11pt;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {p["input_focus"]}; border-width: 2px; background: {focus_bg}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: transparent; border: none; width: 18px;
}}

/* ── QComboBox ──────────────────────────────────────────── */
QComboBox {{
    background: {p["input_bg"]};
    border: 1.5px solid {p["input_border"]};
    border-radius: 8px;
    padding: 8px 36px 8px 12px;
    color: {p["text"]};
    min-width: 100px;
    font-size: 11pt;
}}
QComboBox:focus {{ border-color: {p["input_focus"]}; border-width: 2px; background: {focus_bg}; }}
QComboBox:hover {{ border-color: {p["primary"]}; }}
QComboBox::drop-down {{
    border: none; width: 30px; background: transparent;
}}
QComboBox::down-arrow {{
    border-left:  5px solid transparent;
    border-right: 5px solid transparent;
    border-top:   6px solid {p["text_muted"]};
    width: 0; height: 0;
}}
/* ─ Dropdown popup ─ */
QComboBox QAbstractItemView {{
    background: {p["combo_drop"]};
    border: 1.5px solid {p["input_border"]};
    border-radius: 8px;
    color: {p["combo_text"]};
    selection-background-color: {p["combo_sel_bg"]};
    selection-color: {p["combo_sel_text"]};
    outline: none;
    padding: 4px;
}}
QComboBox QAbstractItemView::item {{
    color: {p["combo_text"]};
    background: transparent;
    padding: 9px 12px;
    min-height: 30px;
    border-radius: 6px;
}}
QComboBox QAbstractItemView::item:selected,
QComboBox QAbstractItemView::item:hover {{
    background: {p["combo_sel_bg"]};
    color: {p["combo_sel_text"]};
}}

/* ── QDateEdit ──────────────────────────────────────────── */
QDateEdit {{
    background: {p["input_bg"]};
    border: 1.5px solid {p["input_border"]};
    border-radius: 8px;
    padding: 8px 12px;
    color: {p["text"]};
    font-size: 11pt;
}}
QDateEdit:focus {{ border-color: {p["input_focus"]}; border-width: 2px; }}
QDateEdit::drop-down {{ border: none; width: 26px; background: transparent; }}

/* ── QCalendarWidget ────────────────────────────────────── */
QCalendarWidget QToolButton {{ background: {p["primary"]}; color: white; border-radius: 6px; }}
QCalendarWidget QMenu {{ background: {p["card_bg"]}; color: {p["text"]}; }}
QCalendarWidget QAbstractItemView:enabled {{
    background: {p["card_bg"]}; color: {p["text"]};
    selection-background-color: {p["primary"]}; selection-color: white;
}}

/* ══════════════════════════════════════════════════════════
   BUTTONS                                                   */
QPushButton {{
    background-color: {p["primary"]};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 11pt;
    min-height: 36px;
}}
QPushButton:hover    {{ background-color: {p["primary_dark"]}; }}
QPushButton:pressed  {{ background-color: {p["primary_dark"]}; }}
QPushButton:disabled {{ background-color: {p["border"]}; color: {p["text_muted"]}; }}
QPushButton:focus    {{ outline: none; border: none; }}

/* Secondary — outline style */
QPushButton[cls="secondary"] {{
    background-color: transparent;
    color: {p["primary"]};
    border: 1.5px solid {p["primary"]};
}}
QPushButton[cls="secondary"]:hover  {{ background-color: {p["primary_light"]}; }}
QPushButton[cls="secondary"]:focus  {{ outline: none; border: 1.5px solid {p["primary"]}; }}

/* Danger */
QPushButton[cls="danger"] {{ background-color: {p["danger"]}; color: white; }}
QPushButton[cls="danger"]:hover {{ background-color: #B91C1C; }}

/* Success */
QPushButton[cls="success"] {{ background-color: {p["success"]}; color: white; }}
QPushButton[cls="success"]:hover {{ background-color: #15803D; }}

/* Warning */
QPushButton[cls="warning"] {{ background-color: {p["warning"]}; color: white; }}
QPushButton[cls="warning"]:hover {{ background-color: #B45309; }}

/* Flat / ghost */
QPushButton[cls="flat"] {{
    background-color: transparent; color: {p["text_muted"]};
    border: none; padding: 6px 12px; font-weight: 400; min-height: 28px;
}}
QPushButton[cls="flat"]:hover {{ background-color: {p["border"]}; color: {p["text"]}; }}

/* Icon-only small */
QPushButton[cls="icon"] {{
    background: transparent; border: none; padding: 4px;
    min-width: 30px; min-height: 30px; border-radius: 6px;
}}
QPushButton[cls="icon"]:hover {{ background: {p["border"]}; }}

/* ── QLabel ─────────────────────────────────────────────── */
QLabel {{ background: transparent; color: {p["text"]}; border: none; outline: none; }}
QLabel[cls="heading"]    {{ font-size: 24pt; font-weight: 800; color: {p["text"]}; }}
QLabel[cls="subheading"] {{ font-size: 14pt; font-weight: 700; color: {p["text"]}; }}
QLabel[cls="muted"]      {{ color: {p["text_muted"]}; font-size: 10pt; }}
QLabel[heading="true"]   {{ font-size: 24pt; font-weight: 800; color: {p["text"]}; }}
QLabel[cls="badge-new"]  {{
    background: {p["primary_light"]}; color: {p["primary"]};
    border-radius: 10px; padding: 3px 10px;
    font-size: 9pt; font-weight: 700;
}}
QLabel[cls="badge-done"] {{
    background: {p["success_light"]}; color: {p["success"]};
    border-radius: 10px; padding: 3px 10px;
    font-size: 9pt; font-weight: 700;
}}

/* ── QTabWidget ─────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1.5px solid {p["border"]};
    border-radius: 10px;
    background: {p["card_bg"]};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent; color: {p["text_muted"]};
    padding: 11px 22px; border: none; font-weight: 500; font-size: 11pt;
}}
QTabBar::tab:selected {{ color: {p["primary"]}; border-bottom: 2px solid {p["primary"]}; font-weight: 700; }}
QTabBar::tab:hover {{ color: {p["text"]}; }}

/* ── QTableWidget ───────────────────────────────────────── */
QTableWidget {{
    background: {p["card_bg"]};
    border: 1.5px solid {p["border"]};
    border-radius: 10px;
    gridline-color: {p["border"]};
    color: {p["text"]};
    alternate-background-color: {p["tbl_alt"]};
}}
QTableWidget::item {{ padding: 10px; border: none; color: {p["text"]}; font-size: 11pt; }}
QTableWidget::item:selected {{
    background: {p["primary_light"]}; color: {p["text"]};
}}
QHeaderView::section {{
    background: {p["content_bg"]}; color: {p["text_muted"]};
    padding: 11px 12px; border: none;
    border-bottom: 1.5px solid {p["border"]};
    font-weight: 700; font-size: 10pt;
}}

/* ── QGroupBox ──────────────────────────────────────────── */
QGroupBox {{
    background: {p["card_bg"]};
    border: 1.5px solid {p["border"]};
    border-radius: 10px;
    margin-top: 16px;
    padding-top: 12px;
    font-weight: 600; color: {p["text"]};
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 14px; top: -2px; padding: 0 6px;
    color: {p["text_muted"]}; font-size: 10pt; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.5px;
    background: {p["card_bg"]};
}}

/* ── QCheckBox / QRadioButton ───────────────────────────── */
QCheckBox, QRadioButton {{ spacing: 8px; color: {p["text"]}; background: transparent; font-size: 11pt; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px; height: 18px;
    border: 1.5px solid {p["input_border"]};
    border-radius: 4px;
    background: {p["input_bg"]};
}}
QCheckBox::indicator:checked {{
    background: {p["primary"]}; border-color: {p["primary"]};
}}
QRadioButton::indicator {{ border-radius: 9px; }}
QRadioButton::indicator:checked {{ background: {p["primary"]}; border-color: {p["primary"]}; }}

/* ── QScrollArea ────────────────────────────────────────── */
QScrollArea {{ border: none; background: transparent; }}

/* ── QListWidget ────────────────────────────────────────── */
QListWidget {{
    background: {p["card_bg"]}; border: 1.5px solid {p["border"]}; border-radius: 8px; outline: none;
}}
QListWidget::item {{ padding: 11px 14px; border-bottom: 1px solid {p["border"]}; color: {p["text"]}; font-size: 11pt; }}
QListWidget::item:selected {{ background: {p["primary_light"]}; color: {p["primary"]}; }}
QListWidget::item:hover {{ background: {p["tbl_alt"]}; }}

/* ── QSplitter ──────────────────────────────────────────── */
QSplitter::handle {{ background: {p["border"]}; }}
QSplitter::handle:horizontal {{ width: 1px; }}

/* ── QToolTip ───────────────────────────────────────────── */
QToolTip {{
    background: {p["text"]}; color: {p["card_bg"]};
    border: none; border-radius: 6px; padding: 7px 12px; font-size: 10pt;
}}

/* ── QMessageBox ────────────────────────────────────────── */
QMessageBox {{
    background: {p["card_bg"]};
}}
QMessageBox QLabel {{
    color: {p["text"]};
    font-size: 11pt;
    background: transparent;
    border: none;
}}
QMessageBox QPushButton {{
    background: {p["primary"]};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 11pt;
    font-weight: 600;
    min-width: 80px;
    min-height: 34px;
}}
QMessageBox QPushButton:hover {{ background: {p["primary_dark"]}; }}
QMessageBox QPushButton:default {{
    background: {p["primary_dark"]};
}}
QMessageBox QPushButton[text="Cancel"],
QMessageBox QPushButton[text="Отмена"] {{
    background: transparent;
    color: {p["primary"]};
    border: 1.5px solid {p["primary"]};
}}
QMessageBox QPushButton[text="Cancel"]:hover,
QMessageBox QPushButton[text="Отмена"]:hover {{
    background: {p["primary_light"]};
}}

/* ── QProgressBar ───────────────────────────────────────── */
QProgressBar {{
    background: {p["progress_track"]}; border-radius: 4px;
    height: 8px; text-align: center;
}}
QProgressBar::chunk {{ background: {p["primary"]}; border-radius: 4px; }}

/* ── QFrame ── */
QFrame {{ border: none; }}
QFrame[cls="card"] {{
    background: {p["card_bg"]}; border: 1.5px solid {p["border"]}; border-radius: 12px;
}}
QFrame[cls="card-hover"]:hover {{ border-color: {p["primary"]}; }}

/* ── Sidebar (light version) ────────────────────────────── */
QWidget[cls="sidebar"] {{
    background-color: {p["sidebar_bg"]};
    border-right: 1px solid {p["border"]};
}}
QWidget[cls="sidebar_card"] {{
    background: {p["tbl_alt"]}; border-radius: 10px; border: 1px solid {p["border"]};
}}
QLabel[cls="sidebar_name"] {{
    color: {p["text"]}; font-weight: 700; font-size: 11pt;
    background: transparent; border: none;
}}
QLabel[cls="sidebar_role"] {{
    color: {p["text_muted"]}; font-size: 9pt;
    background: transparent; border: none;
}}

QPushButton[cls="nav"] {{
    background-color: transparent;
    color: {p["text_muted"]};
    border: none; border-radius: 8px;
    padding: 12px 16px;
    text-align: left; font-size: 11pt; font-weight: 500; min-height: 44px;
}}
QPushButton[cls="nav"]:hover {{
    background-color: {p["sidebar_hover"]}; color: {p["text"]};
}}
QPushButton[cls="nav_active"] {{
    background-color: {p["sidebar_active"]};
    color: {p["primary"]};
    border: none; border-radius: 8px;
    padding: 12px 16px;
    text-align: left; font-size: 11pt; font-weight: 700; min-height: 44px;
}}
QPushButton[cls="logout"] {{
    background: transparent; color: {p["danger"]}; border: none;
    border-radius: 8px; padding: 11px 16px; text-align: left;
    font-size: 11pt; min-height: 44px;
}}
QPushButton[cls="logout"]:hover {{ background: {p["danger_light"]}; }}
"""


_LIGHT_STYLE: str | None = None
_DARK_STYLE:  str | None = None

# Force re-build on import (clears cached style after any edit)
_LIGHT_STYLE = None
_DARK_STYLE  = None


def get_style(theme: str = "light") -> str:
    global _LIGHT_STYLE, _DARK_STYLE
    if theme == "dark":
        if _DARK_STYLE is None:
            _DARK_STYLE = _build(D)
        return _DARK_STYLE
    if _LIGHT_STYLE is None:
        _LIGHT_STYLE = _build(L)
    return _LIGHT_STYLE


def palette(theme: str = "light") -> dict:
    return D if theme == "dark" else L


# ── Module-level aliases (always light) ───────────────────────────
_p = L
GLOBAL_STYLE     = get_style("light")

C_PRIMARY        = _p["primary"]
C_PRIMARY_DARK   = _p["primary_dark"]
C_PRIMARY_LIGHT  = _p["primary_light"]
C_SIDEBAR_BG     = _p["sidebar_bg"]
C_SIDEBAR_HOVER  = _p["sidebar_hover"]
C_SIDEBAR_ACTIVE = _p["sidebar_active"]
C_CONTENT_BG     = _p["content_bg"]
C_CARD_BG        = _p["card_bg"]
C_BORDER         = _p["border"]
C_TEXT           = _p["text"]
C_TEXT_MUTED     = _p["text_muted"]
C_SUCCESS        = _p["success"]
C_WARNING        = _p["warning"]
C_DANGER         = _p["danger"]
C_INFO           = _p["info"]

# ── QMessageBox white-theme helpers ──────────────────────────────────
_MB_STYLE = """
QMessageBox {
    background: #FFFFFF;
    font-family: "Segoe UI", "Arial", sans-serif;
}
QMessageBox QLabel {
    color: #0F172A;
    font-size: 11pt;
    background: transparent;
    border: none;
    min-width: 280px;
}
QMessageBox QPushButton {
    background: #2563EB;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 22px;
    font-size: 11pt;
    font-weight: 600;
    min-width: 88px;
    min-height: 36px;
}
QMessageBox QPushButton:hover { background: #1D4ED8; }
QMessageBox QPushButton:default { background: #1D4ED8; }
"""


def show_info(parent, title: str, text: str) -> None:
    """Show a white-themed information dialog."""
    from PyQt6.QtWidgets import QMessageBox as _MB
    mb = _MB(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(_MB.Icon.Information)
    mb.setStyleSheet(_MB_STYLE)
    mb.exec()


def show_warning(parent, title: str, text: str) -> None:
    """Show a white-themed warning dialog."""
    from PyQt6.QtWidgets import QMessageBox as _MB
    mb = _MB(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(_MB.Icon.Warning)
    mb.setStyleSheet(_MB_STYLE)
    mb.exec()


def show_question(parent, title: str, text: str) -> bool:
    """Show a white-themed Yes/No question dialog. Returns True if Yes."""
    from PyQt6.QtWidgets import QMessageBox as _MB
    mb = _MB(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(_MB.Icon.Question)
    mb.setStandardButtons(_MB.StandardButton.Yes | _MB.StandardButton.No)
    mb.setDefaultButton(_MB.StandardButton.Yes)
    mb.setStyleSheet(_MB_STYLE + """
QMessageBox QPushButton[text="No"],
QMessageBox QPushButton[text="Нет"] {
    background: transparent;
    color: #2563EB;
    border: 1.5px solid #2563EB;
}
QMessageBox QPushButton[text="No"]:hover,
QMessageBox QPushButton[text="Нет"]:hover {
    background: #EFF6FF;
}
""")
    return mb.exec() == _MB.StandardButton.Yes


# Light-compatible sidebar nav button style
NAV_BTN_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {_p["text_muted"]};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 11pt;
    font-weight: 500;
    min-height: 44px;
}}
QPushButton:hover {{
    background-color: {_p["sidebar_hover"]};
    color: {_p["text"]};
}}
QPushButton[active="true"] {{
    background-color: {_p["sidebar_active"]};
    color: {_p["primary"]};
    font-weight: 700;
}}
"""
