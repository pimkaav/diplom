from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.styles import (
    C_CARD_BG, C_BORDER, C_TEXT, C_TEXT_MUTED,
    STATUS_COLORS, STATUS_LABELS, C_PRIMARY
)
from utils.helpers import fmt_money, fmt_date, truncate


class OrderCard(QFrame):
    clicked        = pyqtSignal(dict)
    status_changed = pyqtSignal(int, str)

    def __init__(self, order: dict, mode: str = "customer", parent=None):
        """
        mode: 'customer' | 'carrier' | 'public'
        """
        super().__init__(parent)
        self.order = order
        self.mode  = mode
        self._build()

    def _build(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background: {C_CARD_BG};
                border: 1.5px solid {C_BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: #93C5FD;
            }}
            QLabel {{
                border: none;
                background: transparent;
                color: {C_TEXT};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        # ── Header row ──────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel(self.order.get("title", "Без названия"))
        title.setStyleSheet(f"font-weight: 700; font-size: 13pt; color: {C_TEXT};")
        hdr.addWidget(title)

        hdr.addStretch()
        status = self.order.get("status", "new")
        bg, fg = STATUS_COLORS.get(status, ("#F8FAFC", C_TEXT_MUTED))
        badge = QLabel(STATUS_LABELS.get(status, status))
        badge.setStyleSheet(
            f"background: {bg}; color: {fg}; border: 2px solid {fg}; border-radius: 12px; "
            f"padding: 4px 14px; font-weight: 700; font-size: 10pt;"
        )
        hdr.addWidget(badge)
        root.addLayout(hdr)

        # ── Route ────────────────────────────────────────────────
        route = QLabel(f"📍 {self.order.get('from_city','?')}  →  {self.order.get('to_city','?')}")
        route.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt;")
        root.addWidget(route)

        # ── Details row ──────────────────────────────────────────
        details = QHBoxLayout()
        details.setSpacing(20)

        def info_lbl(icon: str, text: str) -> QLabel:
            lbl = QLabel(f"{icon} {text}")
            lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10pt;")
            return lbl

        details.addWidget(info_lbl("📦", self.order.get("cargo_type") or "Груз"))
        if self.order.get("cargo_weight"):
            details.addWidget(info_lbl("⚖", f"{self.order['cargo_weight']} т"))
        details.addWidget(info_lbl("📅", fmt_date(self.order.get("pickup_date", ""))))
        if self.order.get("budget"):
            details.addWidget(info_lbl("💰", fmt_money(self.order["budget"])))
        details.addStretch()
        root.addLayout(details)

        # ── Comment ──────────────────────────────────────────────
        comment = self.order.get("comment", "")
        if comment:
            lbl = QLabel(truncate(comment, 120))
            lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 11pt; font-style: italic;")
            lbl.setWordWrap(True)
            root.addWidget(lbl)

        # ── Action buttons ────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {C_BORDER}; max-height: 1px; border: none; border-radius: 0;")
        root.addWidget(sep)

        btns = QHBoxLayout()
        btns.setSpacing(8)

        # "Подробнее" button — always visible
        btn_detail = QPushButton("Подробнее →")
        btn_detail.setStyleSheet(
            "QPushButton { background: transparent; color: #3B82F6; border: 2px solid #3B82F6; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; padding: 0 14px; }"
            "QPushButton:hover { background: rgba(59,130,246,0.14); }"
        )
        btn_detail.setFixedHeight(36)
        btn_detail.clicked.connect(lambda: self.clicked.emit(self.order))
        btns.addWidget(btn_detail)

        btns.addStretch()

        _sty_green = (
            "QPushButton { background: transparent; color: #22C55E; border: 2px solid #22C55E; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; padding: 0 14px; }"
            "QPushButton:hover { background: rgba(34,197,94,0.14); }"
        )
        _sty_red = (
            "QPushButton { background: transparent; color: #EF4444; border: 2px solid #EF4444; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; padding: 0 14px; }"
            "QPushButton:hover { background: rgba(239,68,68,0.14); }"
        )

        if self.mode == "customer":
            cur_status = self.order.get("status", "new")
            if cur_status == "new":
                btn_prog = QPushButton("В работу")
                btn_prog.setStyleSheet(_sty_green)
                btn_prog.setFixedHeight(36)
                btn_prog.clicked.connect(
                    lambda: self.status_changed.emit(self.order["id"], "in_progress")
                )
                btns.addWidget(btn_prog)

                btn_cancel = QPushButton("Отменить")
                btn_cancel.setStyleSheet(_sty_red)
                btn_cancel.setFixedHeight(36)
                btn_cancel.clicked.connect(
                    lambda: self.status_changed.emit(self.order["id"], "cancelled")
                )
                btns.addWidget(btn_cancel)

            elif cur_status == "in_progress":
                btn_done = QPushButton("Завершить")
                btn_done.setStyleSheet(_sty_green)
                btn_done.setFixedHeight(36)
                btn_done.clicked.connect(
                    lambda: self.status_changed.emit(self.order["id"], "completed")
                )
                btns.addWidget(btn_done)

        root.addLayout(btns)

    def mousePressEvent(self, event):
        try:
            self.clicked.emit(self.order)
            super().mousePressEvent(event)
        except RuntimeError:
            pass  # widget already deleted — ignore stale event
