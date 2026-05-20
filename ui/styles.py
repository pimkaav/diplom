# ─── Light palette ────────────────────────────────────────────────
L = {
    "primary":        "#2563EB",
    "primary_dark":   "#1D4ED8",
    "primary_light":  "#EFF6FF",
    "sidebar_bg":     "#0F172A",
    "sidebar_hover":  "#1E293B",
    "sidebar_active": "#2563EB",
    "content_bg":     "#F1F5F9",
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
    "input_border":   "#E2E8F0",
    "input_focus":    "#2563EB",
    "combo_drop":     "#FFFFFF",
    "combo_text":     "#0F172A",
    "combo_sel_bg":   "#EFF6FF",
    "combo_sel_text": "#2563EB",
    "tbl_alt":        "#F8FAFC",
    "progress_track": "#E2E8F0",
}

# ─── Dark palette ─────────────────────────────────────────────────
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
    "new":         ("#1E3A5F", "#93C5FD"),
    "in_progress": ("#2D2006", "#FCD34D"),
    "completed":   ("#14532D", "#86EFAC"),
    "cancelled":   ("#450A0A", "#FCA5A5"),
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

# Expose convenience aliases — always use the dark palette (app uses dark theme only)
C_PRIMARY        = D["primary"]
C_PRIMARY_DARK   = D["primary_dark"]
C_PRIMARY_LIGHT  = D["primary_light"]
C_SIDEBAR_BG     = D["sidebar_bg"]
C_SIDEBAR_HOVER  = D["sidebar_hover"]
C_SIDEBAR_ACTIVE = D["sidebar_active"]
C_CONTENT_BG     = D["content_bg"]
C_CARD_BG        = D["card_bg"]
C_BORDER         = D["border"]
C_TEXT           = D["text"]
C_TEXT_MUTED     = D["text_muted"]
C_SUCCESS        = D["success"]
C_WARNING        = D["warning"]
C_DANGER         = D["danger"]
C_INFO           = D["info"]
NAV_BTN_STYLE    = ""   # filled in below


def _build(p: dict) -> str:
    return f"""
/* ══════════════════════════════════════════════════════════
   GLOBAL                                                    */
QWidget {{
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 10pt;
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
    border: 2px solid {p["input_border"]};
    border-radius: 8px;
    padding: 8px 12px;
    color: {p["text"]};
    selection-background-color: {p["primary"]};
    selection-color: white;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {p["input_focus"]};
    background: #1E3050;
}}
QLineEdit:disabled, QTextEdit:disabled {{
    background: {p["content_bg"]}; color: {p["text_muted"]};
}}

/* ── QSpinBox / QDoubleSpinBox ──────────────────────────── */
QSpinBox, QDoubleSpinBox {{
    background: {p["input_bg"]};
    border: 2px solid {p["input_border"]};
    border-radius: 8px;
    padding: 6px 10px;
    color: {p["text"]};
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {p["input_focus"]}; background: #1E3050; }}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: transparent; border: none; width: 18px;
}}

/* ── QComboBox ──────────────────────────────────────────── */
QComboBox {{
    background: {p["input_bg"]};
    border: 2px solid {p["input_border"]};
    border-radius: 8px;
    padding: 7px 36px 7px 12px;
    color: {p["text"]};
    min-width: 100px;
}}
QComboBox:focus {{ border-color: {p["input_focus"]}; background: #1E3050; }}
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
    padding: 8px 12px;
    min-height: 28px;
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
    padding: 7px 12px;
    color: {p["text"]};
}}
QDateEdit:focus {{ border-color: {p["input_focus"]}; }}
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
    padding: 9px 22px;
    font-weight: 600;
    font-size: 10pt;
    min-height: 34px;
}}
QPushButton:hover    {{ background-color: {p["primary_dark"]}; }}
QPushButton:pressed  {{ background-color: {p["primary_dark"]}; opacity: 0.85; }}
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
    min-width: 28px; min-height: 28px;
    border-radius: 6px;
}}
QPushButton[cls="icon"]:hover {{ background: {p["border"]}; }}

/* ── QLabel ─────────────────────────────────────────────── */
QLabel {{ background: transparent; color: {p["text"]}; border: none; outline: none; }}
QLabel[cls="heading"]    {{ font-size: 22pt; font-weight: 800; color: {p["text"]}; }}
QLabel[cls="subheading"] {{ font-size: 13pt; font-weight: 700; color: {p["text"]}; }}
QLabel[cls="muted"]      {{ color: {p["text_muted"]}; font-size: 9pt; }}
/* heading property used by dashboards */
QLabel[heading="true"]   {{ font-size: 22pt; font-weight: 800; color: {p["text"]}; }}
QLabel[cls="badge-new"]  {{
    background: {p["primary_light"]}; color: {p["primary"]};
    border-radius: 10px; padding: 2px 10px;
    font-size: 8pt; font-weight: 700;
}}
QLabel[cls="badge-done"] {{
    background: {p["success_light"]}; color: {p["success"]};
    border-radius: 10px; padding: 2px 10px;
    font-size: 8pt; font-weight: 700;
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
    padding: 10px 20px; border: none; font-weight: 500;
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
QTableWidget::item {{ padding: 8px; border: none; color: {p["text"]}; }}
QTableWidget::item:selected {{
    background: {p["primary_light"]}; color: {p["text"]};
}}
QHeaderView::section {{
    background: {p["content_bg"]}; color: {p["text_muted"]};
    padding: 10px 12px; border: none;
    border-bottom: 1.5px solid {p["border"]};
    font-weight: 700; font-size: 9pt;
}}

/* ── QGroupBox ──────────────────────────────────────────── */
QGroupBox {{
    background: {p["card_bg"]};
    border: 1.5px solid {p["border"]};
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600; color: {p["text"]};
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 14px; top: -2px; padding: 0 6px;
    color: {p["text_muted"]}; font-size: 9pt; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.5px;
}}

/* ── QCheckBox / QRadioButton ───────────────────────────── */
QCheckBox, QRadioButton {{ spacing: 8px; color: {p["text"]}; background: transparent; }}
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
QListWidget::item {{ padding: 10px 14px; border-bottom: 1px solid {p["border"]}; color: {p["text"]}; }}
QListWidget::item:selected {{ background: {p["primary_light"]}; color: {p["primary"]}; }}
QListWidget::item:hover {{ background: {p["tbl_alt"]}; }}

/* ── QSplitter ──────────────────────────────────────────── */
QSplitter::handle {{ background: {p["border"]}; }}
QSplitter::handle:horizontal {{ width: 1px; }}

/* ── QToolTip ───────────────────────────────────────────── */
QToolTip {{
    background: {p["text"]}; color: {p["card_bg"]};
    border: none; border-radius: 6px; padding: 6px 10px; font-size: 9pt;
}}

/* ── QMessageBox ────────────────────────────────────────── */
QMessageBox {{ background: {p["card_bg"]}; }}
QMessageBox QLabel {{ color: {p["text"]}; }}

/* ── QProgressBar ───────────────────────────────────────── */
QProgressBar {{
    background: {p["progress_track"]}; border-radius: 4px;
    height: 8px; text-align: center;
}}
QProgressBar::chunk {{ background: {p["primary"]}; border-radius: 4px; }}

/* ── QFrame — reset default box border, explicit borders via setStyleSheet ── */
QFrame {{ border: none; }}

/* ── QFrame (cards) ─────────────────────────────────────── */
QFrame[cls="card"] {{
    background: {p["card_bg"]}; border: 1.5px solid {p["border"]}; border-radius: 12px;
}}
QFrame[cls="card-hover"]:hover {{ border-color: #93C5FD; }}

/* ── Sidebar ────────────────────────────────────────────── */
QWidget[cls="sidebar"] {{ background-color: {p["sidebar_bg"]}; }}
QWidget[cls="sidebar_card"] {{
    background: rgba(255,255,255,0.06); border-radius: 10px; border: none;
}}
QLabel[cls="sidebar_name"] {{ color: #F1F5F9; font-weight: 600; font-size: 10pt; background: transparent; border: none; }}
QLabel[cls="sidebar_role"] {{ color: #94A3B8; font-size: 8pt; background: transparent; border: none; }}

QPushButton[cls="nav"] {{
    background-color: transparent; color: #94A3B8;
    border: none; border-radius: 8px; padding: 12px 16px;
    text-align: left; font-size: 10pt; font-weight: 500; min-height: 40px;
}}
QPushButton[cls="nav"]:hover {{ background-color: {p["sidebar_hover"]}; color: #F1F5F9; }}
QPushButton[cls="nav_active"] {{
    background-color: {p["sidebar_active"]}; color: white;
    border: none; border-radius: 8px; padding: 12px 16px;
    text-align: left; font-size: 10pt; font-weight: 700; min-height: 40px;
}}
QPushButton[cls="logout"] {{
    background: transparent; color: #EF4444; border: none;
    border-radius: 8px; padding: 10px 16px; text-align: left;
    font-size: 10pt; min-height: 40px;
}}
QPushButton[cls="logout"]:hover {{ background: rgba(239,68,68,0.1); }}
"""


_LIGHT_STYLE: str | None = None
_DARK_STYLE:  str | None = None


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


# Legacy aliases so existing code doesn't break
GLOBAL_STYLE = get_style("light")

# Actual nav button stylesheet — used by dashboards that call btn.setStyleSheet(NAV_BTN_STYLE)
NAV_BTN_STYLE = """
QPushButton {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 10pt;
    font-weight: 500;
    min-height: 40px;
}
QPushButton:hover {
    background-color: #1E293B;
    color: #F1F5F9;
}
QPushButton[active="true"] {
    background-color: #2563EB;
    color: white;
    font-weight: 700;
}
"""
