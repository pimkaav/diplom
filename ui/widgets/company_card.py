from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.styles import C_CARD_BG, C_BORDER, C_TEXT, C_TEXT_MUTED, C_PRIMARY, C_CONTENT_BG
from utils.helpers import fmt_money, stars_text, truncate


class CompanyCard(QFrame):
    clicked      = pyqtSignal(dict)
    chat_clicked = pyqtSignal(dict)

    def __init__(self, company: dict, show_chat: bool = True, parent=None):
        super().__init__(parent)
        self.company   = company
        self.show_chat = show_chat
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
            QFrame:hover {{ border-color: #93C5FD; }}
            QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        # ── Header ───────────────────────────────────────────────
        hdr = QHBoxLayout()
        avatar = QLabel("🏢")
        avatar.setStyleSheet("font-size: 28pt;")
        avatar.setFixedSize(52, 52)
        hdr.addWidget(avatar)

        info = QVBoxLayout()
        info.setSpacing(3)
        name_lbl = QLabel(self.company.get("company_name", "Компания"))
        name_lbl.setStyleSheet(f"font-weight: 700; font-size: 13pt; color: {C_TEXT};")
        info.addWidget(name_lbl)

        verified = self.company.get("is_verified", 0)
        rating   = self.company.get("rating", 0.0)
        r_count  = self.company.get("rating_count", 0)
        star_lbl = QLabel(stars_text(rating, r_count))
        star_lbl.setStyleSheet(f"color: #F59E0B; font-size: 11pt;")
        info.addWidget(star_lbl)
        hdr.addLayout(info)
        hdr.addStretch()

        if verified:
            vbadge = QLabel("✓ Проверен")
            vbadge.setStyleSheet(
                "background: #F0FDF4; color: #15803D; border: 2px solid #16A34A; "
                "border-radius: 10px; padding: 4px 12px; font-size: 9pt; font-weight: 700;"
            )
            hdr.addWidget(vbadge, alignment=Qt.AlignmentFlag.AlignTop)

        root.addLayout(hdr)

        # ── Stats ────────────────────────────────────────────────
        stats = QHBoxLayout()
        stats.setSpacing(16)

        def stat(icon: str, value: str, label: str) -> QFrame:
            box = QFrame()
            box.setStyleSheet(
                f"QFrame {{ background: {C_CONTENT_BG}; border: 1px solid {C_BORDER}; border-radius: 8px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
            )
            lay = QVBoxLayout(box)
            lay.setContentsMargins(12, 8, 12, 8)
            lay.setSpacing(0)
            v = QLabel(f"{icon} {value}")
            v.setStyleSheet(f"font-weight: 700; font-size: 11pt; color: {C_TEXT}; background: transparent;")
            lay.addWidget(v)
            l = QLabel(label)
            l.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 8pt; background: transparent;")
            lay.addWidget(l)
            return box

        stats.addWidget(stat("🚚", str(self.company.get("truck_count", 0)), "Автомобилей"))
        pkm = self.company.get("price_per_km", 0)
        stats.addWidget(stat("💰", f"{pkm} ₽/км", "Тариф"))
        done = self.company.get("completed_orders", 0)
        stats.addWidget(stat("✅", str(done), "Выполнено"))
        stats.addStretch()
        root.addLayout(stats)

        # ── Description ──────────────────────────────────────────
        desc = self.company.get("description", "")
        if desc:
            lbl = QLabel(truncate(desc, 120))
            lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10pt;")
            lbl.setWordWrap(True)
            root.addWidget(lbl)

        cats = self.company.get("truck_categories", "")
        if cats:
            clbl = QLabel(f"🏷 {cats}")
            clbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
            root.addWidget(clbl)

        # ── Cities ───────────────────────────────────────────────
        cities = self.company.get("operating_cities", "")
        if cities:
            clbl = QLabel(f"📍 {cities}")
            clbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
            clbl.setWordWrap(True)
            root.addWidget(clbl)

        # ── Buttons ──────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C_BORDER};")
        root.addWidget(sep)

        btns = QHBoxLayout()
        btns.setSpacing(8)

        btn_detail = QPushButton("Подробнее →")
        btn_detail.setStyleSheet(
            "QPushButton { background: transparent; color: #3B82F6; border: 2px solid #3B82F6; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; padding: 0 14px; }"
            "QPushButton:hover { background: rgba(59,130,246,0.14); }"
        )
        btn_detail.setFixedHeight(36)
        btn_detail.clicked.connect(lambda: self.clicked.emit(self.company))
        btns.addWidget(btn_detail)

        if self.show_chat:
            btn_chat = QPushButton("💬 Написать")
            btn_chat.setStyleSheet(
                "QPushButton { background: #2563EB; color: white; border: none; "
                "border-radius: 8px; font-size: 10pt; font-weight: 600; padding: 0 14px; }"
                "QPushButton:hover { background: #1D4ED8; }"
            )
            btn_chat.setFixedHeight(36)
            btn_chat.clicked.connect(lambda: self.chat_clicked.emit(self.company))
            btns.addWidget(btn_chat)

        btns.addStretch()
        root.addLayout(btns)

    def mousePressEvent(self, event):
        try:
            super().mousePressEvent(event)
        except RuntimeError:
            pass
