"""Carrier company detail — reviews, invite to order, chat."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QWidget, QTabWidget, QComboBox,
    QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import ReviewModel, UserModel, OrderModel, NotificationModel
from ui.styles import C_CARD_BG, C_BORDER, C_TEXT, C_TEXT_MUTED, C_PRIMARY, C_CONTENT_BG
from ui.widgets.star_rating import StarRatingWidget
from utils.helpers import stars_text, fmt_datetime


class CarrierDetailDialog(QDialog):
    chat_requested = pyqtSignal(dict)

    def __init__(self, company: dict, current_user: dict, parent=None):
        super().__init__(parent)
        self.company      = company
        self.current_user = current_user
        self.setWindowTitle(f"Компания: {company.get('company_name','')}")
        self.setMinimumSize(720, 620)
        self.resize(760, 660)
        self._build()

    def _build(self):
        self.setStyleSheet(f"background: {C_CONTENT_BG};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        outer.addWidget(tabs)

        tabs.addTab(self._build_info_tab(), "🏢 О компании")
        tabs.addTab(self._build_reviews_tab(), "⭐ Отзывы")
        tabs.addTab(self._build_invite_tab(), "📦 Предложить заказ")

    # ── Info tab ─────────────────────────────────────────────────

    def _build_info_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(14)

        # Header card
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 14px; }} QLabel {{ border: none; background: transparent; }}"
        )
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(22, 20, 22, 20)
        hl.setSpacing(18)

        ico = QLabel("🏢")
        ico.setStyleSheet("font-size: 38pt;")
        ico.setFixedSize(64, 64)
        hl.addWidget(ico)

        hinfo = QVBoxLayout()
        hinfo.setSpacing(4)
        nm = QLabel(self.company.get("company_name", ""))
        nm.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT};")
        hinfo.addWidget(nm)

        rating  = self.company.get("rating", 0.0)
        r_cnt   = self.company.get("rating_count", 0)
        rl = QLabel(stars_text(rating, r_cnt))
        rl.setStyleSheet("color: #F59E0B; font-size: 11pt;")
        hinfo.addWidget(rl)

        if self.company.get("is_verified"):
            vl = QLabel("✓ Верифицированная компания")
            vl.setStyleSheet(f"color: #86EFAC; font-size: 9pt; font-weight: 600;")
            hinfo.addWidget(vl)

        hl.addLayout(hinfo)
        hl.addStretch()

        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)

        carrier_user = UserModel.get_by_id(self.company.get("user_id"))

        btn_chat = QPushButton("💬 Написать")
        btn_chat.setFixedSize(140, 38)
        btn_chat.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        if carrier_user:
            btn_chat.clicked.connect(lambda: (
                self.chat_requested.emit(carrier_user), self.accept()
            ))
        btn_col.addWidget(btn_chat)

        hl.addLayout(btn_col)
        l.addWidget(hdr)

        # Stats row
        stats = QHBoxLayout()
        stats.setSpacing(10)
        for icon, val, lbl in [
            ("🚚", str(self.company.get("truck_count", 0)),        "Автомобилей"),
            ("💰", f"{self.company.get('price_per_km', 0)} ₽",    "За км"),
            ("✅", str(self.company.get("completed_orders", 0)),   "Выполнено"),
            ("⭐", f"{self.company.get('rating', 0):.1f}",         "Рейтинг"),
        ]:
            f = QFrame()
            f.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; }}"
            )
            fl = QVBoxLayout(f)
            fl.setContentsMargins(14, 12, 14, 12)
            fl.setSpacing(2)
            v = QLabel(f"{icon} {val}")
            v.setStyleSheet(f"font-size: 16pt; font-weight: 800; color: {C_PRIMARY};")
            fl.addWidget(v)
            lb = QLabel(lbl)
            lb.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
            fl.addWidget(lb)
            stats.addWidget(f)
        l.addLayout(stats)

        # Text sections
        for label, key in [
            ("Описание", "description"),
            ("Типы транспорта", "truck_categories"),
            ("Регионы работы", "operating_cities"),
        ]:
            val = self.company.get(key, "")
            if not val:
                continue
            g = QFrame()
            g.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; }}"
            )
            gl = QVBoxLayout(g)
            gl.setContentsMargins(16, 12, 16, 12)
            gl.setSpacing(4)
            gl.addWidget(_muted(label))
            t = QLabel(val)
            t.setWordWrap(True)
            t.setStyleSheet(f"color: {C_TEXT}; font-size: 10pt;")
            gl.addWidget(t)
            l.addWidget(g)

        # Contacts
        contacts = QFrame()
        contacts.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; }}"
        )
        cl = QVBoxLayout(contacts)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(6)
        cl.addWidget(_muted("Контакты"))
        for icon, key in [("📞", "phone"), ("✉️", "email"), ("🌐", "website"), ("🏛", "inn")]:
            val = self.company.get(key, "")
            if val:
                cl.addWidget(QLabel(f"{icon}  {val}"))
        l.addWidget(contacts)

        l.addStretch()
        scroll.setWidget(inner)
        return scroll

    # ── Reviews tab ───────────────────────────────────────────────

    def _build_reviews_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(12)

        reviews = ReviewModel.get_by_user(self.company.get("user_id", 0))

        # Average block
        if reviews:
            avg_block = QFrame()
            avg_block.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
            )
            ab = QHBoxLayout(avg_block)
            ab.setContentsMargins(20, 16, 20, 16)
            ab.setSpacing(20)

            avg_val = sum(r["rating"] for r in reviews) / len(reviews)
            avg_lbl = QLabel(f"{avg_val:.1f}")
            avg_lbl.setStyleSheet("font-size: 40pt; font-weight: 800; color: #F59E0B;")
            ab.addWidget(avg_lbl)

            avg_right = QVBoxLayout()
            stars = "★" * int(round(avg_val)) + "☆" * (5 - int(round(avg_val)))
            avg_right.addWidget(_label(stars, "color: #F59E0B; font-size: 18pt;"))
            avg_right.addWidget(_label(f"{len(reviews)} отзывов",
                                       f"color: {C_TEXT_MUTED}; font-size: 10pt;"))
            ab.addLayout(avg_right)
            ab.addStretch()
            l.addWidget(avg_block)

        for rev in reviews:
            rc = QFrame()
            rc.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; }}"
            )
            rcl = QVBoxLayout(rc)
            rcl.setContentsMargins(16, 12, 16, 12)
            rcl.setSpacing(6)

            top = QHBoxLayout()
            reviewer = QLabel(rev.get("reviewer_name", "Пользователь"))
            reviewer.setStyleSheet(f"font-weight: 600; color: {C_TEXT};")
            top.addWidget(reviewer)
            top.addStretch()
            stars = "★" * rev["rating"] + "☆" * (5 - rev["rating"])
            top.addWidget(_label(stars, "color: #F59E0B; font-size: 13pt;"))
            rcl.addLayout(top)

            if rev.get("comment"):
                cm = QLabel(rev["comment"])
                cm.setWordWrap(True)
                cm.setStyleSheet(f"color: {C_TEXT}; font-size: 10pt;")
                rcl.addWidget(cm)

            dt = QLabel(fmt_datetime(rev.get("created_at", "")))
            dt.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 8pt;")
            rcl.addWidget(dt)
            l.addWidget(rc)

        if not reviews:
            emp = QLabel("Отзывов пока нет")
            emp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emp.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 50px;")
            l.addWidget(emp)

        l.addStretch()
        scroll.setWidget(inner)
        return scroll

    # ── Invite tab ────────────────────────────────────────────────

    def _build_invite_tab(self) -> QWidget:
        """Customer picks one of their open orders and invites this carrier."""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(16)

        l.addWidget(_label("Предложить заказ перевозчику",
                           "font-size: 14pt; font-weight: 700;"))
        l.addWidget(_label(
            f"Отправьте приглашение компании «{self.company.get('company_name','')}».\n"
            "Перевозчик получит уведомление и сможет сразу откликнуться на ваш заказ.",
            f"color: {C_TEXT_MUTED}; font-size: 10pt;",
            wrap=True,
        ))

        orders = OrderModel.get_by_customer(self.current_user["id"])
        open_orders = [o for o in orders if o["status"] == "new"]

        if not open_orders:
            info = QFrame()
            info.setStyleSheet("QFrame { background: #2D2006; border: 1.5px solid #78350F; border-radius: 10px; } QLabel { border: none; background: transparent; }")
            il = QVBoxLayout(info)
            il.setContentsMargins(16, 14, 16, 14)
            il.addWidget(_label(
                "⚠ У вас нет открытых заявок.\nСначала создайте заявку на перевозку.",
                "color: #FCD34D; font-size: 10pt;", wrap=True,
            ))
            l.addWidget(info)
            l.addStretch()
            return w

        l.addWidget(_muted("Выберите заявку:"))
        self._order_cmb = QComboBox()
        self._order_cmb.setFixedHeight(40)
        for o in open_orders:
            self._order_cmb.addItem(
                f"#{o['id']} — {o['title']} ({o['from_city']} → {o['to_city']})",
                o["id"]
            )
        l.addWidget(self._order_cmb)

        l.addWidget(_muted("Сопроводительное сообщение (необязательно):"))
        self._msg_inp = QTextEdit()
        self._msg_inp.setPlaceholderText(
            "Здравствуйте! Хочу предложить вам перевозку груза. Пожалуйста, ознакомьтесь с заявкой..."
        )
        self._msg_inp.setFixedHeight(90)
        l.addWidget(self._msg_inp)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_send = QPushButton("📨 Отправить приглашение")
        btn_send.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: 2px solid #3B82F6; "
            "border-radius: 10px; font-size: 11pt; font-weight: 700; padding: 0 20px; }"
            "QPushButton:hover { background: #1D4ED8; border-color: #60A5FA; }"
        )
        btn_send.setFixedSize(250, 46)
        btn_send.clicked.connect(self._send_invite)
        btn_row.addWidget(btn_send)
        l.addLayout(btn_row)

        l.addStretch()
        return w

    def _send_invite(self):
        order_id   = self._order_cmb.currentData()
        carrier_id = self.company.get("user_id")
        msg        = self._msg_inp.toPlainText().strip()

        if not order_id or not carrier_id:
            return

        OrderModel.invite_carrier(order_id, carrier_id)

        order = OrderModel.get_by_id(order_id)
        NotificationModel.create(
            carrier_id, "direct_invitation",
            "Прямое приглашение на заказ",
            f"Заказчик «{self.current_user.get('full_name') or self.current_user['username']}» "
            f"лично приглашает вас выполнить заявку «{order.get('title','')}» "
            f"({order.get('from_city','')} → {order.get('to_city','')}). "
            + (f"Сообщение: {msg}" if msg else ""),
            order_id,
        )

        # Also send a chat message if there's a note
        if msg:
            from database.models import MessageModel
            MessageModel.send(
                self.current_user["id"], carrier_id,
                f"🔔 Приглашение к заказу #{order_id}:\n{msg}",
                order_id=order_id,
            )

        QMessageBox.information(
            self, "Приглашение отправлено",
            "Перевозчик получил уведомление о вашем предложении.\n"
            "Он может откликнуться на заявку в обычном порядке."
        )
        self.accept()


def _label(text: str, style: str = "", wrap: bool = False) -> QLabel:
    lbl = QLabel(text)
    if style:
        lbl.setStyleSheet(style)
    if wrap:
        lbl.setWordWrap(True)
    return lbl


def _muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #64748B; font-size: 9pt; font-weight: 700; text-transform: uppercase;"
    )
    return lbl
