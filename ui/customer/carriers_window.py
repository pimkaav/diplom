from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QComboBox, QStackedWidget,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import CompanyModel, ReviewModel, UserModel, OrderModel, NotificationModel
from ui.widgets.company_card import CompanyCard
from ui.styles import C_CONTENT_BG, C_TEXT, C_TEXT_MUTED, C_CARD_BG, C_BORDER, C_PRIMARY
from utils.helpers import stars_text, fmt_datetime


class CarriersWindow(QWidget):
    chat_with = pyqtSignal(dict)

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._build()
        self._load()

    # ── Build ─────────────────────────────────────────────────────

    def _build(self):
        self.setStyleSheet(f"background: {C_CONTENT_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sub_stack = QStackedWidget()
        root.addWidget(self.sub_stack)

        # Page 0 — list view
        self.sub_stack.addWidget(self._build_list_page())

        # Page 1 — detail placeholder (replaced on each click)
        self.sub_stack.addWidget(QWidget())

        self._companies: list[dict] = []

    def _build_list_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        root = QVBoxLayout(page)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr = QLabel("Перевозчики")
        hdr.setProperty("heading", "true")
        root.addWidget(hdr)

        # Filters
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 Поиск по названию, городу...")
        self.inp_search.setFixedHeight(38)
        self.inp_search.textChanged.connect(self._filter)
        filter_row.addWidget(self.inp_search, 3)

        self.cmb_sort = QComboBox()
        self.cmb_sort.addItems(["По рейтингу", "По цене (возр.)", "По заказам"])
        self.cmb_sort.setFixedHeight(38)
        self.cmb_sort.currentIndexChanged.connect(self._filter)
        filter_row.addWidget(self.cmb_sort, 1)

        btn_refresh = QPushButton("Обновить")
        btn_refresh.setProperty("cls", "secondary")
        btn_refresh.setFixedSize(110, 38)
        btn_refresh.clicked.connect(self._load)
        filter_row.addWidget(btn_refresh)

        root.addLayout(filter_row)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
        root.addWidget(self.count_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

        return page

    # ── Data ──────────────────────────────────────────────────────

    def _load(self):
        self._companies = CompanyModel.get_all()
        self._filter()

    def _filter(self):
        query = self.inp_search.text().strip().lower()
        sort  = self.cmb_sort.currentIndex()

        filtered = self._companies
        if query:
            filtered = [
                c for c in filtered
                if query in c.get("company_name", "").lower()
                or query in c.get("operating_cities", "").lower()
                or query in c.get("truck_categories", "").lower()
            ]

        if sort == 0:
            filtered = sorted(filtered, key=lambda c: c.get("rating", 0), reverse=True)
        elif sort == 1:
            filtered = sorted(filtered, key=lambda c: c.get("price_per_km", 0))
        elif sort == 2:
            filtered = sorted(filtered, key=lambda c: c.get("completed_orders", 0), reverse=True)

        self._render(filtered)

    def _render(self, companies: list[dict]):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.count_lbl.setText(f"Найдено: {len(companies)} компаний")

        for company in companies:
            card = CompanyCard(company, show_chat=True)
            card.clicked.connect(self._show_detail)
            card.chat_clicked.connect(self._open_chat)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        if not companies:
            lbl = QLabel("Перевозчики не найдены")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 40px;")
            self.cards_layout.insertWidget(0, lbl)

    # ── Detail page ───────────────────────────────────────────────

    def _show_detail(self, company: dict):
        page = self._build_detail_page(company)
        # Replace page 1
        old = self.sub_stack.widget(1)
        self.sub_stack.removeWidget(old)
        old.deleteLater()
        self.sub_stack.insertWidget(1, page)
        self.sub_stack.setCurrentIndex(1)

    def _build_detail_page(self, company: dict) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────────
        top_bar = QWidget()
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet(
            f"background: {C_CARD_BG}; border-bottom: 1px solid {C_BORDER};"
        )
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(16, 0, 16, 0)
        tb.setSpacing(12)

        btn_back = QPushButton("← Перевозчики")
        btn_back.setProperty("cls", "secondary")
        btn_back.setFixedHeight(36)
        btn_back.clicked.connect(self._go_back)
        tb.addWidget(btn_back)

        tb.addStretch()

        carrier_user = UserModel.get_by_id(company.get("user_id"))
        btn_chat = QPushButton("💬 Написать")
        btn_chat.setFixedSize(140, 36)
        btn_chat.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; }"
            "QPushButton:hover { background: #1D4ED8; }"
            "QPushButton:disabled { background: #1E293B; color: #475569; border: 1px solid #334155; }"
        )
        if carrier_user:
            btn_chat.clicked.connect(lambda: self.chat_with.emit(carrier_user))
        else:
            btn_chat.setEnabled(False)
        tb.addWidget(btn_chat)

        outer.addWidget(top_bar)

        # ── Scrollable content ────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

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
        nm = QLabel(company.get("company_name", ""))
        nm.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT};")
        hinfo.addWidget(nm)

        rating = company.get("rating", 0.0)
        r_cnt  = company.get("rating_count", 0)
        rl = QLabel(stars_text(rating, r_cnt))
        rl.setStyleSheet("color: #F59E0B; font-size: 11pt;")
        hinfo.addWidget(rl)

        if company.get("is_verified"):
            vl = QLabel("✓ Верифицированная компания")
            vl.setStyleSheet("color: #86EFAC; font-size: 9pt; font-weight: 600;")
            hinfo.addWidget(vl)

        hl.addLayout(hinfo)
        hl.addStretch()
        l.addWidget(hdr)

        # Stats row
        stats = QHBoxLayout()
        stats.setSpacing(10)
        for icon, val, lbl_txt in [
            ("🚚", str(company.get("truck_count", 0)),       "Автомобилей"),
            ("💰", f"{company.get('price_per_km', 0)} ₽",   "За км"),
            ("✅", str(company.get("completed_orders", 0)),  "Выполнено"),
            ("⭐", f"{company.get('rating', 0):.1f}",        "Рейтинг"),
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
            lb = QLabel(lbl_txt)
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
            val = company.get(key, "")
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
        has_contact = False
        for icon, key in [("📞", "phone"), ("✉️", "email"), ("🌐", "website"), ("🏛", "inn")]:
            val = company.get(key, "")
            if val:
                cl.addWidget(QLabel(f"{icon}  {val}"))
                has_contact = True
        if has_contact:
            l.addWidget(contacts)

        # ── Reviews section ───────────────────────────────────────
        reviews_hdr = QLabel("⭐ Отзывы")
        reviews_hdr.setStyleSheet(f"font-size: 13pt; font-weight: 700; color: {C_TEXT};")
        l.addWidget(reviews_hdr)

        reviews = ReviewModel.get_by_user(company.get("user_id", 0))

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
                stars_r = "★" * rev["rating"] + "☆" * (5 - rev["rating"])
                top.addWidget(_label(stars_r, "color: #F59E0B; font-size: 13pt;"))
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
        else:
            emp = QLabel("Отзывов пока нет")
            emp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emp.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 30px;")
            l.addWidget(emp)

        # ── Invite section ────────────────────────────────────────
        invite_hdr = QLabel("📦 Предложить заказ")
        invite_hdr.setStyleSheet(f"font-size: 13pt; font-weight: 700; color: {C_TEXT};")
        l.addWidget(invite_hdr)

        l.addWidget(_label(
            f"Отправьте приглашение компании «{company.get('company_name','')}».\n"
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
        else:
            l.addWidget(_muted("Выберите заявку:"))
            self._invite_order_cmb = QComboBox()
            self._invite_order_cmb.setFixedHeight(40)
            for o in open_orders:
                self._invite_order_cmb.addItem(
                    f"#{o['id']} — {o['title']} ({o['from_city']} → {o['to_city']})",
                    o["id"]
                )
            l.addWidget(self._invite_order_cmb)

            l.addWidget(_muted("Сопроводительное сообщение (необязательно):"))
            self._invite_msg_inp = QTextEdit()
            self._invite_msg_inp.setPlaceholderText(
                "Здравствуйте! Хочу предложить вам перевозку груза. Пожалуйста, ознакомьтесь с заявкой..."
            )
            self._invite_msg_inp.setFixedHeight(90)
            l.addWidget(self._invite_msg_inp)

            btn_row = QHBoxLayout()
            btn_row.addStretch()
            btn_send = QPushButton("📨 Отправить приглашение")
            btn_send.setStyleSheet(
                "QPushButton { background: #2563EB; color: white; border: 2px solid #3B82F6; "
                "border-radius: 10px; font-size: 11pt; font-weight: 700; padding: 0 20px; }"
                "QPushButton:hover { background: #1D4ED8; border-color: #60A5FA; }"
            )
            btn_send.setFixedSize(260, 48)
            btn_send.clicked.connect(lambda: self._send_invite(company))
            btn_row.addWidget(btn_send)
            l.addLayout(btn_row)

        l.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    def _go_back(self):
        self.sub_stack.setCurrentIndex(0)
        self._load()

    # ── Actions ────────────────────────────────────────────────────

    def _send_invite(self, company: dict):
        order_id   = self._invite_order_cmb.currentData()
        carrier_id = company.get("user_id")
        msg        = self._invite_msg_inp.toPlainText().strip()

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
        self._go_back()

    def _open_chat(self, company: dict):
        user = UserModel.get_by_id(company.get("user_id"))
        if user:
            self.chat_with.emit(user)

    def _emit_chat(self, user: dict):
        self.chat_with.emit(user)


# ── Helpers ────────────────────────────────────────────────────────

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
