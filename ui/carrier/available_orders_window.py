from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QComboBox, QStackedWidget,
    QTextEdit, QDoubleSpinBox, QSpinBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import OrderModel, ResponseModel, NotificationModel
from ui.widgets.order_card import OrderCard
from ui.styles import (
    C_CONTENT_BG, C_TEXT_MUTED, C_TEXT, C_CARD_BG, C_BORDER, C_PRIMARY,
    STATUS_LABELS
)
from ui.widgets.progress_tracker import ProgressTracker
from utils.helpers import fmt_money, fmt_date


class AvailableOrdersWindow(QWidget):
    response_sent = pyqtSignal()

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

        # Page 0 — list
        self.sub_stack.addWidget(self._build_list_page())

        # Page 1 — detail placeholder
        self.sub_stack.addWidget(QWidget())

        self._all_orders: list[dict] = []

    def _build_list_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        root = QVBoxLayout(page)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Доступные заявки")
        hdr.setProperty("heading", "true")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()

        btn_refresh = QPushButton("Обновить")
        btn_refresh.setProperty("cls", "secondary")
        btn_refresh.setFixedSize(110, 36)
        btn_refresh.clicked.connect(self._load)
        hdr_row.addWidget(btn_refresh)
        root.addLayout(hdr_row)

        # Filters
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        _inp = (
            "QLineEdit { background: #1A2540; border: 2px solid #3B82F6; border-radius: 8px; "
            "color: #F1F5F9; padding: 4px 12px; font-size: 10pt; }"
            "QLineEdit:focus { border-color: #60A5FA; background: #1E3050; }"
        )
        _cmb = (
            "QComboBox { background: #1A2540; border: 2px solid #3B82F6; border-radius: 8px; "
            "color: #F1F5F9; padding: 4px 10px; font-size: 10pt; }"
            "QComboBox:focus { border-color: #60A5FA; }"
            "QComboBox::drop-down { border: none; width: 20px; }"
            "QComboBox QAbstractItemView { background: #1E293B; color: #F1F5F9; border: 1px solid #3B82F6; }"
        )

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 Поиск по городам, типу груза...")
        self.inp_search.setFixedHeight(42)
        self.inp_search.setStyleSheet(_inp)
        self.inp_search.textChanged.connect(self._filter)
        filter_row.addWidget(self.inp_search, 3)

        self.cmb_cargo = QComboBox()
        self.cmb_cargo.addItem("Все типы груза", None)
        from ui.customer.create_order_dialog import CARGO_TYPES
        for ct in CARGO_TYPES:
            self.cmb_cargo.addItem(ct, ct)
        self.cmb_cargo.setFixedHeight(42)
        self.cmb_cargo.setStyleSheet(_cmb)
        self.cmb_cargo.currentIndexChanged.connect(self._filter)
        filter_row.addWidget(self.cmb_cargo, 2)

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
        self._all_orders = OrderModel.get_available()
        self._filter()

    def _filter(self):
        query = self.inp_search.text().strip().lower()
        cargo = self.cmb_cargo.currentData()

        orders = self._all_orders
        if query:
            orders = [
                o for o in orders
                if query in o.get("from_city", "").lower()
                or query in o.get("to_city", "").lower()
                or query in o.get("cargo_type", "").lower()
                or query in o.get("title", "").lower()
            ]
        if cargo:
            orders = [o for o in orders if o.get("cargo_type") == cargo]

        self._render(orders)

    def _render(self, orders: list[dict]):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.count_lbl.setText(f"Найдено заявок: {len(orders)}")

        for order in orders:
            card = OrderCard(order, mode="public")
            card.clicked.connect(self._show_detail)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        if not orders:
            lbl = QLabel("Доступных заявок нет")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 40px;")
            self.cards_layout.insertWidget(0, lbl)

    # ── Detail page ───────────────────────────────────────────────

    def _show_detail(self, order: dict):
        page = self._build_detail_page(order)
        old = self.sub_stack.widget(1)
        self.sub_stack.removeWidget(old)
        old.deleteLater()
        self.sub_stack.insertWidget(1, page)
        self.sub_stack.setCurrentIndex(1)

    def _build_detail_page(self, order: dict) -> QWidget:
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

        btn_back = QPushButton("← Доступные заявки")
        btn_back.setProperty("cls", "secondary")
        btn_back.setFixedHeight(36)
        btn_back.clicked.connect(self._go_back)
        tb.addWidget(btn_back)
        tb.addStretch()

        outer.addWidget(top_bar)

        # ── Scrollable content ────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        wl = QVBoxLayout(w)
        wl.setContentsMargins(24, 24, 24, 24)
        wl.setSpacing(16)

        o = order

        # Progress tracker (active orders)
        if o.get("status") == "in_progress":
            prog_frame = QFrame()
            prog_frame.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
            )
            pfl = QVBoxLayout(prog_frame)
            pfl.setContentsMargins(16, 14, 16, 14)
            pfl.setSpacing(8)
            pfl.addWidget(_mlbl("Прогресс выполнения"))
            pfl.addWidget(ProgressTracker(o.get("progress_status", "waiting")))
            wl.addWidget(prog_frame)

        # Title
        title_lbl = QLabel(o.get("title", ""))
        title_lbl.setStyleSheet(f"font-size: 15pt; font-weight: 800; color: {C_TEXT};")
        title_lbl.setWordWrap(True)
        wl.addWidget(title_lbl)

        # Details card
        detail_card = QFrame()
        detail_card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
        )
        dcl = QVBoxLayout(detail_card)
        dcl.setContentsMargins(20, 16, 20, 16)
        dcl.setSpacing(10)

        def row(label: str, value: str):
            r = QHBoxLayout()
            lb = QLabel(label + ":")
            lb.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt; font-weight: 600;")
            lb.setFixedWidth(160)
            vl = QLabel(value or "—")
            vl.setStyleSheet(f"color: {C_TEXT}; font-size: 10pt;")
            vl.setWordWrap(True)
            r.addWidget(lb)
            r.addWidget(vl)
            r.addStretch()
            dcl.addLayout(r)

        row("Маршрут",          f"{o.get('from_city','?')} → {o.get('to_city','?')}")
        if o.get("from_address"):
            row("Адрес отправки",   o.get("from_address", ""))
        if o.get("to_address"):
            row("Адрес назначения", o.get("to_address", ""))
        row("Тип груза",        o.get("cargo_type", ""))
        row("Вес / Объём",      f"{o.get('cargo_weight',0)} т / {o.get('cargo_volume',0)} м³")
        if o.get("distance"):
            row("Расстояние",   f"{o.get('distance',0):.0f} км")
        row("Дата погрузки",    fmt_date(o.get("pickup_date", "")))
        row("Доставка",         fmt_date(o.get("delivery_date", "")))
        row("Бюджет заказчика", fmt_money(o.get("budget", 0)))
        row("Статус",           STATUS_LABELS.get(o.get("status", ""), ""))

        if o.get("customer_name"):
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"background: {C_BORDER}; border: none; border-radius: 0;")
            dcl.addWidget(sep)
            row("Заказчик", o.get("customer_name", ""))
            if o.get("customer_phone"):
                row("Телефон",  o.get("customer_phone", ""))
            if o.get("customer_email"):
                row("Email",    o.get("customer_email", ""))

        wl.addWidget(detail_card)

        if o.get("comment"):
            cf = _card()
            cgl = QVBoxLayout(cf)
            cgl.setContentsMargins(16, 12, 16, 12)
            cgl.addWidget(_mlbl("Комментарий заказчика"))
            cl = QLabel(o.get("comment", ""))
            cl.setWordWrap(True)
            cgl.addWidget(cl)
            wl.addWidget(cf)

        if o.get("special_requirements"):
            sf = QFrame()
            sf.setStyleSheet("QFrame { background: #2D2006; border: 1.5px solid #78350F; border-radius: 10px; } QLabel { border: none; background: transparent; }")
            srl = QVBoxLayout(sf)
            srl.setContentsMargins(16, 12, 16, 12)
            srl.addWidget(_mlbl("⚠ Специальные требования"))
            sl = QLabel(o.get("special_requirements", ""))
            sl.setStyleSheet("color: #FCD34D;")
            sl.setWordWrap(True)
            srl.addWidget(sl)
            wl.addWidget(sf)

        # ── Response form (for new orders) ────────────────────────
        carrier_id = self.current_user["id"]
        already = ResponseModel.already_responded(o["id"], carrier_id)

        if o.get("status") == "new" and not already:
            self._build_response_form(wl, order)
        elif already and o.get("status") == "new":
            done_lbl = QFrame()
            done_lbl.setStyleSheet(
                "QFrame { background: #14532D; border: 1.5px solid #16A34A; border-radius: 10px; } QLabel { border: none; background: transparent; }"
            )
            dl = QHBoxLayout(done_lbl)
            dl.setContentsMargins(16, 12, 16, 12)
            done_txt = QLabel("✅ Вы уже откликнулись на эту заявку")
            done_txt.setStyleSheet("color: #86EFAC; font-weight: 600;")
            dl.addWidget(done_txt)
            wl.addWidget(done_lbl)

        wl.addStretch()
        scroll.setWidget(w)
        outer.addWidget(scroll)
        return page

    def _build_response_form(self, parent: QVBoxLayout, order: dict):
        o = order
        resp_grp = QFrame()
        resp_grp.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
        )
        rgl = QVBoxLayout(resp_grp)
        rgl.setContentsMargins(20, 18, 20, 18)
        rgl.setSpacing(12)
        rgl.addWidget(_mlbl("Подать отклик"))

        fl = QFormLayout()
        fl.setSpacing(10)

        _spn_sty = (
            "QSpinBox, QDoubleSpinBox { background: #1A2540; border: 2px solid #3B82F6; "
            "border-radius: 8px; color: #F1F5F9; padding: 4px 10px; font-size: 10pt; }"
            "QSpinBox:focus, QDoubleSpinBox:focus { border-color: #60A5FA; background: #1E3050; }"
            "QSpinBox::up-button, QDoubleSpinBox::up-button, "
            "QSpinBox::down-button, QDoubleSpinBox::down-button { width: 20px; }"
        )

        self.spn_cost = QDoubleSpinBox()
        self.spn_cost.setRange(1000, 99_999_999)
        self.spn_cost.setSuffix(" ₽")
        self.spn_cost.setDecimals(0)
        self.spn_cost.setSingleStep(1000)
        self.spn_cost.setValue(o.get("budget", 50000) or 50000)
        self.spn_cost.setFixedHeight(42)
        self.spn_cost.setStyleSheet(_spn_sty)
        fl.addRow("Ваша цена *", self.spn_cost)

        self.spn_days = QSpinBox()
        self.spn_days.setRange(1, 365)
        self.spn_days.setSuffix(" дней")
        self.spn_days.setValue(3)
        self.spn_days.setFixedHeight(42)
        self.spn_days.setStyleSheet(_spn_sty)
        fl.addRow("Срок доставки *", self.spn_days)
        rgl.addLayout(fl)

        rgl.addWidget(_mlbl("Сообщение заказчику"))
        self.inp_msg = QTextEdit()
        self.inp_msg.setPlaceholderText(
            "Здравствуйте! Готовы выполнить вашу перевозку. "
            "Имеем опыт в данном направлении..."
        )
        self.inp_msg.setFixedHeight(90)
        self.inp_msg.setStyleSheet(
            "QTextEdit { background: #1A2540; border: 2px solid #3B82F6; border-radius: 8px; "
            "color: #F1F5F9; padding: 6px 10px; font-size: 10pt; }"
            "QTextEdit:focus { border-color: #60A5FA; background: #1E3050; }"
        )
        rgl.addWidget(self.inp_msg)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_send = QPushButton("✉  Отправить отклик")
        btn_send.setFixedSize(200, 44)
        btn_send.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; font-size: 11pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_send.clicked.connect(lambda: self._send_response(order))
        btn_row.addWidget(btn_send)
        rgl.addLayout(btn_row)
        parent.addWidget(resp_grp)

    # ── Actions ────────────────────────────────────────────────────

    def _go_back(self):
        self.sub_stack.setCurrentIndex(0)
        self._load()

    def _send_response(self, order: dict):
        cost = self.spn_cost.value()
        days = self.spn_days.value()
        msg  = self.inp_msg.toPlainText().strip()
        carrier_id = self.current_user["id"]

        if cost <= 0:
            QMessageBox.warning(self, "Ошибка", "Укажите стоимость")
            return

        ResponseModel.create(order["id"], carrier_id, msg, cost, days)
        NotificationModel.create(
            order["customer_id"], "new_response",
            "Новый отклик на вашу заявку",
            f"Перевозчик откликнулся на заявку «{order.get('title','')}» "
            f"с ценой {fmt_money(cost)}",
            order["id"]
        )
        QMessageBox.information(self, "Отклик отправлен", "Ваш отклик успешно отправлен заказчику.")
        self.response_sent.emit()
        self._go_back()

    def refresh(self):
        self._load()


# ── Helpers ────────────────────────────────────────────────────────

def _mlbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #64748B; font-size: 9pt; font-weight: 700; text-transform: uppercase; "
        "background: transparent; border: none;"
    )
    return lbl


def _card() -> QFrame:
    from ui.styles import C_CARD_BG, C_BORDER
    f = QFrame()
    f.setStyleSheet(
        f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
    )
    return f
