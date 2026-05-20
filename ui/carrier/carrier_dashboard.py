from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QScrollArea, QFrame, QFileDialog,
    QLineEdit, QTextEdit, QMessageBox, QFormLayout, QComboBox,
    QDoubleSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath

from database.models import (
    OrderModel, UserModel, CompanyModel, NotificationModel,
    MessageModel, ResponseModel, ReviewModel, TruckModel
)
from ui.styles import (
    C_SIDEBAR_BG, C_CONTENT_BG, C_CARD_BG, C_BORDER, C_TEXT,
    C_TEXT_MUTED, C_PRIMARY, NAV_BTN_STYLE, C_SUCCESS
)
from ui.carrier.company_profile_dialog import CompanyProfileDialog
from ui.carrier.available_orders_window import AvailableOrdersWindow
from ui.chat.chat_window import ChatWindow
from utils.helpers import save_avatar, stars_text, fmt_money, fmt_date


class _ClickableFrame(QFrame):
    """QFrame that emits clicked() on left mouse press."""
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CarrierOrdersWindow(QWidget):
    """Carrier's own active/completed orders."""

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

        self._orders: list[dict] = []

    def _build_list_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        root = QVBoxLayout(page)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Мои перевозки")
        hdr.setProperty("heading", "true")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        btn_r = QPushButton("Обновить")
        btn_r.setProperty("cls", "secondary")
        btn_r.setFixedSize(110, 36)
        btn_r.clicked.connect(self._load)
        hdr_row.addWidget(btn_r)
        root.addLayout(hdr_row)

        self.cmb = QComboBox()
        self.cmb.addItems(["Все", "В работе", "Завершённые"])
        self.cmb.setFixedSize(150, 36)
        self.cmb.currentIndexChanged.connect(self._filter)
        root.addWidget(self.cmb, alignment=Qt.AlignmentFlag.AlignRight)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.cl = QVBoxLayout(self.container)
        self.cl.setContentsMargins(0, 0, 0, 0)
        self.cl.setSpacing(12)
        self.cl.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

        return page

    # ── Data ──────────────────────────────────────────────────────

    def _load(self):
        self._orders = OrderModel.get_by_carrier(self.current_user["id"])
        self._filter()

    def _filter(self):
        idx    = self.cmb.currentIndex()
        status = [None, "in_progress", "completed"][idx]
        orders = self._orders if not status else [
            o for o in self._orders if o["status"] == status
        ]
        self._render(orders)

    def _render(self, orders: list[dict]):
        from ui.widgets.order_card import OrderCard
        while self.cl.count() > 1:
            item = self.cl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for o in orders:
            card = OrderCard(o, mode="carrier")
            card.clicked.connect(self._show_detail)
            self.cl.insertWidget(self.cl.count() - 1, card)

        if not orders:
            lbl = QLabel("Перевозок нет")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 40px;")
            self.cl.insertWidget(0, lbl)

    # ── Detail page ───────────────────────────────────────────────

    def _show_detail(self, order: dict):
        page = self._build_detail_page(order)
        old = self.sub_stack.widget(1)
        self.sub_stack.removeWidget(old)
        old.deleteLater()
        self.sub_stack.insertWidget(1, page)
        self.sub_stack.setCurrentIndex(1)

    def _build_detail_page(self, order: dict) -> QWidget:
        from ui.styles import STATUS_LABELS
        from ui.widgets.progress_tracker import ProgressTracker

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

        btn_back = QPushButton("← Мои перевозки")
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
        carrier_id = self.current_user["id"]

        # Progress tracker
        if o.get("status") == "in_progress":
            prog_frame = QFrame()
            prog_frame.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
            )
            pfl = QVBoxLayout(prog_frame)
            pfl.setContentsMargins(16, 14, 16, 14)
            pfl.setSpacing(8)
            pfl.addWidget(_cow_mlbl("Прогресс выполнения"))
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
            cf = _cow_card()
            cgl = QVBoxLayout(cf)
            cgl.setContentsMargins(16, 12, 16, 12)
            cgl.addWidget(_cow_mlbl("Комментарий заказчика"))
            cl = QLabel(o.get("comment", ""))
            cl.setWordWrap(True)
            cgl.addWidget(cl)
            wl.addWidget(cf)

        if o.get("special_requirements"):
            sf = QFrame()
            sf.setStyleSheet("QFrame { background: #2D2006; border: 1.5px solid #78350F; border-radius: 10px; } QLabel { border: none; background: transparent; }")
            srl = QVBoxLayout(sf)
            srl.setContentsMargins(16, 12, 16, 12)
            srl.addWidget(_cow_mlbl("⚠ Специальные требования"))
            sl = QLabel(o.get("special_requirements", ""))
            sl.setStyleSheet("color: #FCD34D;")
            sl.setWordWrap(True)
            srl.addWidget(sl)
            wl.addWidget(sf)

        # ── Carrier actions (in_progress orders) ──────────────────
        if o.get("status") == "in_progress" and o.get("carrier_id") == carrier_id:
            progress = o.get("progress_status", "waiting")

            if progress == "waiting":
                veh_grp = QFrame()
                veh_grp.setStyleSheet(
                    f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
                )
                vgl = QVBoxLayout(veh_grp)
                vgl.setContentsMargins(20, 16, 20, 16)
                vgl.setSpacing(12)
                vgl.addWidget(_cow_mlbl("🚛 Назначить транспорт"))

                fleet_trucks = TruckModel.get_by_carrier(carrier_id)
                if fleet_trucks:
                    fleet_lbl = QLabel("Выбрать из автопарка:")
                    fleet_lbl.setStyleSheet(
                        f"color: {C_TEXT_MUTED}; font-size: 9pt; font-weight: 600;"
                    )
                    vgl.addWidget(fleet_lbl)

                    self.cmb_fleet = QComboBox()
                    self.cmb_fleet.setFixedHeight(40)
                    self.cmb_fleet.setStyleSheet(
                        "QComboBox { background: #1A2540; border: 2px solid #3B82F6; border-radius: 8px; "
                        "color: #F1F5F9; padding: 4px 10px; font-size: 10pt; }"
                        "QComboBox:focus { border-color: #60A5FA; }"
                        "QComboBox::drop-down { border: none; width: 20px; }"
                        "QComboBox QAbstractItemView { background: #1E293B; color: #F1F5F9; border: 1px solid #3B82F6; }"
                    )
                    self.cmb_fleet.addItem("— Выбрать ТС из автопарка —", None)
                    for t in fleet_trucks:
                        label = (
                            f"{t['brand']} {t['model']}  ·  "
                            f"{t['plate_number']}  ·  {t['capacity_tons']}т"
                        )
                        self.cmb_fleet.addItem(label, t)
                    self.cmb_fleet.currentIndexChanged.connect(self._on_fleet_select)
                    vgl.addWidget(self.cmb_fleet)

                _inp_sty = (
                    "QLineEdit { background: #1A2540; border: 2px solid #3B82F6; border-radius: 8px; "
                    "color: #F1F5F9; padding: 4px 10px; font-size: 10pt; }"
                    "QLineEdit:focus { border-color: #60A5FA; background: #1E3050; }"
                )

                fl = QFormLayout()
                fl.setSpacing(10)

                self.inp_driver = QLineEdit()
                self.inp_driver.setPlaceholderText("Иванов Иван Иванович")
                self.inp_driver.setFixedHeight(40)
                self.inp_driver.setStyleSheet(_inp_sty)
                fl.addRow("Водитель *", self.inp_driver)

                self.inp_truck_num = QLineEdit()
                self.inp_truck_num.setPlaceholderText("А123ВС77")
                self.inp_truck_num.setFixedHeight(40)
                self.inp_truck_num.setStyleSheet(_inp_sty)
                fl.addRow("Номер ТС *", self.inp_truck_num)

                self.inp_truck_model = QLineEdit()
                self.inp_truck_model.setPlaceholderText("МАЗ-4371, КАМАЗ-5490...")
                self.inp_truck_model.setFixedHeight(40)
                self.inp_truck_model.setStyleSheet(_inp_sty)
                fl.addRow("Модель ТС", self.inp_truck_model)
                vgl.addLayout(fl)

                btn_row = QHBoxLayout()
                btn_row.addStretch()
                btn_assign = QPushButton("Назначить транспорт")
                btn_assign.setProperty("cls", "success")
                btn_assign.setFixedHeight(40)
                btn_assign.clicked.connect(lambda: self._assign_vehicle(order))
                btn_row.addWidget(btn_assign)
                vgl.addLayout(btn_row)
                wl.addWidget(veh_grp)

            else:
                # Show assigned vehicle info
                if o.get("driver_name") or o.get("truck_number"):
                    veh_info = _cow_card()
                    vil = QVBoxLayout(veh_info)
                    vil.setContentsMargins(18, 14, 18, 14)
                    vil.setSpacing(6)
                    vil.addWidget(_cow_mlbl("🚛 Назначенный транспорт"))
                    if o.get("driver_name"):
                        vil.addWidget(_cow_info_row("Водитель", o["driver_name"]))
                    if o.get("truck_number"):
                        vil.addWidget(_cow_info_row("Номер ТС", o["truck_number"]))
                    if o.get("truck_model"):
                        vil.addWidget(_cow_info_row("Модель ТС", o["truck_model"]))
                    wl.addWidget(veh_info)

                if progress == "vehicle_assigned":
                    box = QFrame()
                    box.setStyleSheet(
                        "background: #1E3A5F; border: 1.5px solid #2563EB; border-radius: 12px;"
                    )
                    bl = QVBoxLayout(box)
                    bl.setContentsMargins(18, 14, 18, 14)
                    bl.setSpacing(10)
                    info = QLabel(
                        "🚛 Транспорт назначен. После погрузки нажмите «Груз отправлен», "
                        "затем заказчик подтвердит отправку."
                    )
                    info.setStyleSheet("color: #93C5FD; font-size: 10pt;")
                    info.setWordWrap(True)
                    bl.addWidget(info)
                    btn = QPushButton("📦 Отметить: груз отправлен")
                    btn.setProperty("cls", "secondary")
                    btn.setFixedHeight(40)
                    btn.clicked.connect(lambda: self._mark_dispatched(order))
                    bl.addWidget(btn)
                    wl.addWidget(box)

                elif progress in ("dispatched", "in_transit"):
                    box = QFrame()
                    box.setStyleSheet(
                        "background: #0C2340; border: 1.5px solid #1D4ED8; border-radius: 12px;"
                    )
                    bl = QVBoxLayout(box)
                    bl.setContentsMargins(18, 14, 18, 14)
                    bl.setSpacing(10)
                    info = QLabel(
                        "🚚 Груз в пути. По прибытии к месту назначения нажмите «Прибыл»."
                    )
                    info.setStyleSheet("color: #93C5FD; font-size: 10pt;")
                    info.setWordWrap(True)
                    bl.addWidget(info)
                    btn = QPushButton("📍 Отметить: прибыл к месту назначения")
                    btn.setProperty("cls", "secondary")
                    btn.setFixedHeight(40)
                    btn.clicked.connect(lambda: self._mark_arrived(order))
                    bl.addWidget(btn)
                    wl.addWidget(box)

                elif progress == "arrived":
                    info = QLabel(
                        "📍 Вы отметили прибытие. Ожидайте подтверждения заказчика."
                    )
                    info.setStyleSheet(
                        "QFrame { background: #14532D; border: 1.5px solid #16A34A; border-radius: 10px; } QLabel { border: none; background: transparent; }"
                        "color: #86EFAC; font-size: 10pt; padding: 12px 16px;"
                    )
                    info.setWordWrap(True)
                    wl.addWidget(info)

        wl.addStretch()
        scroll.setWidget(w)
        outer.addWidget(scroll)
        return page

    # ── Fleet selector ────────────────────────────────────────────

    def _on_fleet_select(self, idx: int):
        truck = self.cmb_fleet.itemData(idx)
        if truck:
            self.inp_truck_num.setText(truck.get("plate_number", ""))
            self.inp_truck_model.setText(
                f"{truck['brand']} {truck['model']} ({truck.get('year','')})"
            )

    # ── Carrier actions ───────────────────────────────────────────

    def _assign_vehicle(self, order: dict):
        driver = self.inp_driver.text().strip()
        truck_num = self.inp_truck_num.text().strip()
        truck_model = self.inp_truck_model.text().strip()

        if not driver or not truck_num:
            QMessageBox.warning(self, "Ошибка", "Введите имя водителя и номер ТС")
            return

        OrderModel.assign_vehicle(order["id"], driver, truck_num, truck_model)
        NotificationModel.create(
            order["customer_id"], "vehicle_assigned",
            "Транспорт назначен",
            f"Перевозчик назначил транспорт на заявку «{order.get('title','')}»: "
            f"водитель {driver}, ТС {truck_num}."
        )
        QMessageBox.information(
            self, "Готово",
            "Транспорт назначен. Заказчик получил уведомление.\n"
            "После погрузки отметьте отправку груза."
        )
        self._go_back()

    def _mark_dispatched(self, order: dict):
        OrderModel.mark_dispatched_by_carrier(order["id"])
        NotificationModel.create(
            order["customer_id"], "cargo_dispatched",
            "Груз отправлен",
            f"Перевозчик отметил отправку груза по заявке «{order.get('title','')}». "
            "Пожалуйста, подтвердите отправку в системе."
        )
        QMessageBox.information(
            self, "Готово",
            "Отправка груза отмечена. Заказчик получил уведомление."
        )
        self._go_back()

    def _mark_arrived(self, order: dict):
        OrderModel.mark_arrived_by_carrier(order["id"])
        NotificationModel.create(
            order["customer_id"], "cargo_arrived",
            "Груз прибыл к месту назначения",
            f"Перевозчик отметил прибытие груза по заявке «{order.get('title','')}». "
            "Пожалуйста, подтвердите получение в системе."
        )
        QMessageBox.information(
            self, "Готово",
            "Прибытие отмечено. Заказчик должен подтвердить получение груза."
        )
        self._go_back()

    def _go_back(self):
        self.sub_stack.setCurrentIndex(0)
        self._load()

    def refresh(self):
        self._load()


# ── CarrierOrdersWindow helpers ────────────────────────────────────

def _cow_mlbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #64748B; font-size: 9pt; font-weight: 700; text-transform: uppercase; "
        "background: transparent; border: none;"
    )
    return lbl


def _cow_card() -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
    )
    return f


def _cow_info_row(label: str, value: str) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent; border: none;")
    hl = QHBoxLayout(w)
    hl.setContentsMargins(0, 0, 0, 0)
    lb = QLabel(label + ":")
    lb.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt; font-weight: 600;")
    lb.setFixedWidth(100)
    vl = QLabel(value)
    vl.setStyleSheet(f"color: {C_TEXT}; font-size: 10pt;")
    hl.addWidget(lb)
    hl.addWidget(vl)
    hl.addStretch()
    return w


class CarrierDashboard(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"FreightExchange — {user.get('full_name') or user['username']}")
        self.setMinimumSize(1100, 700)
        self._build()
        self._start_timers()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setStyleSheet(f"background-color: {C_SIDEBAR_BG};")
        sidebar.setFixedWidth(240)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(12, 0, 12, 16)
        sb.setSpacing(4)

        logo_area = QWidget()
        logo_area.setFixedHeight(64)
        logo_area.setStyleSheet(f"background: {C_SIDEBAR_BG};")
        la = QHBoxLayout(logo_area)
        la.setContentsMargins(8, 0, 8, 0)
        logo_lbl = QLabel("🚛 FreightExchange")
        logo_lbl.setStyleSheet("color: white; font-size: 13pt; font-weight: 800;")
        la.addWidget(logo_lbl)
        sb.addWidget(logo_area)

        user_card = QFrame()
        user_card.setStyleSheet(
            "background: rgba(255,255,255,0.06); border-radius: 10px; border: none;"
        )
        ucl = QVBoxLayout(user_card)
        ucl.setContentsMargins(12, 12, 12, 10)
        ucl.setSpacing(4)

        self.avatar_lbl = QLabel("🏢")
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet(
            "font-size: 26pt; background: rgba(255,255,255,0.1); "
            "border-radius: 28px; min-width: 56px; min-height: 56px;"
        )
        self.avatar_lbl.setFixedSize(56, 56)
        ucl.addWidget(self.avatar_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        self._refresh_avatar()

        company = CompanyModel.get_by_user(self.user["id"])
        disp_name = company["company_name"] if company else (
            self.user.get("full_name") or self.user["username"]
        )
        self.name_lbl = QLabel(disp_name)
        self.name_lbl.setStyleSheet(
            "color: #F1F5F9; font-weight: 600; font-size: 10pt; "
            "background: transparent; border: none;"
        )
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_lbl.setWordWrap(True)
        ucl.addWidget(self.name_lbl)

        role_lbl = QLabel("Перевозчик")
        role_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 8pt; background: transparent; border: none;"
        )
        role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ucl.addWidget(role_lbl)

        # Balance
        self._bal_lbl = QLabel(fmt_money(self.user.get("balance", 0)))
        self._bal_lbl.setStyleSheet(
            "color: #4ADE80; font-size: 9pt; font-weight: 700; "
            "background: transparent; border: none;"
        )
        self._bal_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ucl.addWidget(self._bal_lbl)

        btn_topup = QPushButton("+ Пополнить")
        btn_topup.setStyleSheet(
            "background: rgba(74,222,128,0.15); color: #4ADE80; border: 1px solid #4ADE80; "
            "border-radius: 6px; padding: 4px 10px; font-size: 8pt; font-weight: 600;"
        )
        btn_topup.setFixedHeight(26)
        btn_topup.clicked.connect(self._topup_balance)
        ucl.addWidget(btn_topup)

        sb.addWidget(user_card)
        sb.addSpacing(8)

        nav_items = [
            ("🏠", "Главная",          0),
            ("🏢", "Профиль компании", 1),
            ("📦", "Доступные заявки", 2),
            ("🚚", "Мои перевозки",    3),
            ("💬", "Сообщения",        4),
            ("🔔", "Уведомления",      5),
            ("👤", "Профиль",          6),
        ]
        self._nav_btns: list[QPushButton] = []
        for icon, label, idx in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setStyleSheet(NAV_BTN_STYLE)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda _, i=idx: self._nav(i))
            self._nav_btns.append(btn)
            sb.addWidget(btn)

        sb.addStretch()

        btn_settings = QPushButton("  ⚙  Настройки")
        btn_settings.setStyleSheet(
            "background: transparent; color: #64748B; border: none; "
            "border-radius: 8px; padding: 10px 16px; text-align: left; font-size: 10pt;"
        )
        btn_settings.setFixedHeight(40)
        btn_settings.clicked.connect(self._open_settings)
        sb.addWidget(btn_settings)

        btn_logout = QPushButton("  ⬅  Выйти")
        btn_logout.setStyleSheet(
            "background: transparent; color: #EF4444; border: none; "
            "border-radius: 8px; padding: 10px 16px; text-align: left; font-size: 10pt;"
        )
        btn_logout.setFixedHeight(44)
        btn_logout.clicked.connect(self._logout)
        sb.addWidget(btn_logout)

        layout.addWidget(sidebar)

        # ── Content ───────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {C_CONTENT_BG};")
        layout.addWidget(self.stack)

        self.stack.addWidget(self._build_home())            # 0
        self.stack.addWidget(self._build_company_page())    # 1
        self.avail_page = AvailableOrdersWindow(self.user)
        self.stack.addWidget(self.avail_page)               # 2
        self.my_orders_page = CarrierOrdersWindow(self.user)
        self.stack.addWidget(self.my_orders_page)           # 3
        self.chat_page = ChatWindow(self.user)
        self.stack.addWidget(self.chat_page)                # 4
        self.stack.addWidget(self._build_notifications())   # 5
        self.stack.addWidget(self._build_profile())         # 6
        self.stack.addWidget(self._build_balance_page())    # 7
        self.stack.addWidget(self._build_settings_page())   # 8

        self._prev_page = 0
        self._nav(0)

    # ── Home ──────────────────────────────────────────────────────

    def _build_home(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        w.setFrameShape(QFrame.Shape.NoFrame)
        w.setStyleSheet("background: transparent; border: none;")

        self._home_inner = QWidget()
        self._home_inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(self._home_inner)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)

        company = CompanyModel.get_by_user(self.user["id"])
        name = company["company_name"] if company else (
            self.user.get("full_name") or self.user["username"]
        )

        greeting = QLabel(f"Добро пожаловать, {name}! 🚛")
        greeting.setStyleSheet(f"font-size: 22pt; font-weight: 800; color: {C_TEXT};")
        l.addWidget(greeting)

        sub = QLabel("Управляйте перевозками и находите новые заказы")
        sub.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt;")
        l.addWidget(sub)

        if not company:
            banner = QFrame()
            banner.setStyleSheet(
                "QFrame { background: #2D2006; border: 1.5px solid #78350F; border-radius: 12px; } QLabel { border: none; background: transparent; }"
            )
            bl = QHBoxLayout(banner)
            bl.setContentsMargins(20, 16, 20, 16)
            ico = QLabel("⚠")
            ico.setStyleSheet("font-size: 18pt;")
            bl.addWidget(ico)
            info = QVBoxLayout()
            info.addWidget(_lbl("Создайте профиль компании",
                                f"font-weight: 700; color: {C_TEXT};"))
            info.addWidget(_lbl("Без профиля заказчики не увидят вашу компанию",
                                f"color: {C_TEXT_MUTED}; font-size: 9pt;"))
            bl.addLayout(info)
            bl.addStretch()
            btn_c = QPushButton("Создать профиль")
            btn_c.setFixedSize(160, 36)
            btn_c.clicked.connect(lambda: self._nav(1))
            bl.addWidget(btn_c)
            l.addWidget(banner)

        # Stats
        self._home_stat_refs: list[QLabel] = []
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        for val, lbl_txt, color in [
            ("—", "Новых заявок",    C_PRIMARY),
            ("—", "Откликов ждут",   "#F59E0B"),
            ("—", "В работе",        "#0EA5E9"),
            ("—", "Выполнено",       C_SUCCESS),
        ]:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 2px solid {color}; border-radius: 12px; }} "
                f"QLabel {{ border: none; background: transparent; }}"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(20, 18, 20, 18)
            cl.setSpacing(4)
            vl = QLabel(val)
            vl.setStyleSheet(f"font-size: 30pt; font-weight: 800; color: {color};")
            ll = QLabel(lbl_txt)
            ll.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10pt; font-weight: 600;")
            cl.addWidget(vl)
            cl.addWidget(ll)
            self._home_stat_refs.append(vl)
            stats_row.addWidget(card)
        l.addLayout(stats_row)

        qa_lbl = QLabel("Быстрые действия")
        qa_lbl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {C_TEXT};")
        l.addWidget(qa_lbl)

        qa_row = QHBoxLayout()
        qa_row.setSpacing(12)
        for ico_t, title, desc, color, nav_i in [
            ("📦", "Найти заявки",    "Смотреть доступные заявки",    C_PRIMARY,  2),
            ("🚚", "Мои перевозки",   "Управлять текущими перевозками","#0EA5E9", 3),
            ("🏢", "Профиль компании","Редактировать данные",          "#7C3AED",  1),
        ]:
            btn = self._action_card(ico_t, title, desc, color)
            btn.clicked.connect(lambda _, i=nav_i: self._nav(i))
            qa_row.addWidget(btn)
        l.addLayout(qa_row)

        # Recent orders
        recent_lbl = QLabel("Последние перевозки")
        recent_lbl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {C_TEXT};")
        l.addWidget(recent_lbl)

        self._home_recent = QVBoxLayout()
        self._home_recent.setSpacing(10)
        l.addLayout(self._home_recent)

        l.addStretch()
        w.setWidget(self._home_inner)
        self._refresh_home_data()
        return w

    def _refresh_home_data(self):
        responses = ResponseModel.get_by_carrier(self.user["id"])
        my_orders = OrderModel.get_by_carrier(self.user["id"])
        active  = sum(1 for o in my_orders if o["status"] == "in_progress")
        done    = sum(1 for o in my_orders if o["status"] == "completed")
        pending = sum(1 for r in responses if r.get("status") == "pending")
        avail   = len(OrderModel.get_available())

        if hasattr(self, "_home_stat_refs"):
            for lbl, val in zip(self._home_stat_refs,
                                 [str(avail), str(pending), str(active), str(done)]):
                lbl.setText(val)

        if hasattr(self, "_home_recent"):
            while self._home_recent.count():
                item = self._home_recent.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if my_orders:
                from ui.widgets.order_card import OrderCard
                for o in my_orders[:3]:
                    card = OrderCard(o, mode="carrier")
                    card.clicked.connect(lambda _: self._nav(3))
                    self._home_recent.addWidget(card)
            else:
                lbl = QLabel("У вас пока нет активных перевозок")
                lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt;")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._home_recent.addWidget(lbl)

    def _action_card(self, icon: str, title: str, desc: str, color: str) -> QPushButton:
        btn = QPushButton()
        btn.setFixedHeight(110)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_CARD_BG};
                border: 1.5px solid {C_BORDER};
                border-radius: 12px;
                text-align: left;
            }}
            QPushButton:hover {{ border-color: {color}; }}
        """)
        inner = QVBoxLayout(btn)
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(6)
        inner.addWidget(_lbl(icon, f"font-size: 22pt; color: {color}; background: transparent;"))
        inner.addWidget(_lbl(title, f"font-weight: 700; font-size: 11pt; color: {C_TEXT}; background: transparent;"))
        inner.addWidget(_lbl(desc, f"color: {C_TEXT_MUTED}; font-size: 8pt; background: transparent;", wrap=True))
        return btn

    # ── Company page ──────────────────────────────────────────────

    def _build_company_page(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        w.setFrameShape(QFrame.Shape.NoFrame)
        w.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Профиль компании")
        hdr.setProperty("heading", "true")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        btn_edit = QPushButton("✏ Редактировать")
        btn_edit.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: 2px solid #3B82F6; "
            "border-radius: 8px; font-size: 10pt; font-weight: 700; padding: 0 16px; }"
            "QPushButton:hover { background: #1D4ED8; border-color: #60A5FA; }"
        )
        btn_edit.setFixedSize(180, 40)
        btn_edit.clicked.connect(self._edit_company)
        hdr_row.addWidget(btn_edit)
        l.addLayout(hdr_row)

        company = CompanyModel.get_by_user(self.user["id"])

        if not company:
            empty = QFrame()
            empty.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px dashed {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
            )
            el = QVBoxLayout(empty)
            el.setContentsMargins(40, 50, 40, 50)
            el.setSpacing(12)
            el.addWidget(_lbl("🏢", "font-size: 40pt;", align=True))
            el.addWidget(_lbl("Профиль компании не создан",
                              f"font-size: 14pt; font-weight: 700; color: {C_TEXT};", align=True))
            el.addWidget(_lbl("Создайте профиль, чтобы заказчики могли найти вас",
                              f"color: {C_TEXT_MUTED};", align=True))
            btn_create = QPushButton("Создать профиль компании")
            btn_create.setFixedSize(240, 44)
            btn_create.clicked.connect(self._edit_company)
            el.addWidget(btn_create, alignment=Qt.AlignmentFlag.AlignCenter)
            l.addWidget(empty)
        else:
            from ui.widgets.company_card import CompanyCard
            card = CompanyCard(company, show_chat=False)
            l.addWidget(card)

            reviews = ReviewModel.get_by_user(self.user["id"])
            if reviews:
                rev_lbl = QLabel(f"Отзывы ({len(reviews)})")
                rev_lbl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {C_TEXT};")
                l.addWidget(rev_lbl)
                for rev in reviews[:5]:
                    rc = QFrame()
                    rc.setStyleSheet(
                        f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; }}"
                    )
                    rcl = QVBoxLayout(rc)
                    rcl.setContentsMargins(16, 12, 16, 12)
                    rcl.setSpacing(4)
                    top = QHBoxLayout()
                    top.addWidget(_lbl(rev.get("reviewer_name", "Пользователь"),
                                       f"font-weight: 600; color: {C_TEXT};"))
                    top.addStretch()
                    stars = "★" * rev["rating"] + "☆" * (5 - rev["rating"])
                    top.addWidget(_lbl(stars, "color: #F59E0B; font-size: 12pt;"))
                    rcl.addLayout(top)
                    if rev.get("comment"):
                        rcl.addWidget(_lbl(rev["comment"], f"color: {C_TEXT_MUTED};"))
                    l.addWidget(rc)

        l.addStretch()
        w.setWidget(inner)
        return w

    # ── Notifications ─────────────────────────────────────────────

    def _build_notifications(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        w.setFrameShape(QFrame.Shape.NoFrame)
        w.setStyleSheet("background: transparent; border: none;")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(12)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Уведомления")
        hdr.setProperty("heading", "true")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        btn_mark = QPushButton("Прочитать все")
        btn_mark.setProperty("cls", "secondary")
        btn_mark.setFixedSize(150, 34)
        btn_mark.clicked.connect(lambda: (
            NotificationModel.mark_all_read(self.user["id"]),
            self._refresh_badges()
        ))
        hdr_row.addWidget(btn_mark)
        l.addLayout(hdr_row)

        notifs = NotificationModel.get_by_user(self.user["id"])
        type_icons = {
            "message":            "💬",
            "order_accepted":     "✅",
            "order_rejected":     "❌",
            "new_response":       "📩",
            "vehicle_assigned":   "🚛",
            "dispatch_confirmed": "📦",
            "cargo_dispatched":   "📦",
            "cargo_arrived":      "📍",
            "payment_released":   "💳",
            "direct_invitation":  "🎯",
        }

        # Pages: 0=Home, 1=Company, 2=Available orders, 3=My orders, 4=Chat, 5=Notifications, 6=Profile
        _dest = {
            "message":            4,   # → Chat
            "order_accepted":     3,   # → My orders
            "order_rejected":     3,
            "vehicle_assigned":   3,
            "dispatch_confirmed": 3,
            "cargo_dispatched":   3,
            "cargo_arrived":      3,
            "payment_released":   3,
            "new_response":       2,   # → Available orders
            "direct_invitation":  2,
        }

        from utils.helpers import fmt_datetime

        def _on_notif_click(notif_id: int, ntype: str):
            NotificationModel.mark_read(notif_id)
            self._refresh_badges()
            dest = _dest.get(ntype, 3)
            self._nav(dest)

        for n in notifs:
            is_read = bool(n["is_read"])
            bg     = C_CARD_BG if is_read else "#1E3A5F"
            border = C_BORDER  if is_read else "#2563EB"

            nf = _ClickableFrame()
            oid = f"nc_{n['id']}"
            nf.setObjectName(oid)
            nf.setStyleSheet(
                f"#{oid} {{ background: {bg}; border: 1.5px solid {border}; border-radius: 10px; }}"
                f"#{oid}:hover {{ background: #243447; border: 1.5px solid #3B82F6; }}"
            )
            nf.setCursor(Qt.CursorShape.PointingHandCursor)
            nf.clicked.connect(lambda _=None, nid=n["id"], nt=n["type"]: _on_notif_click(nid, nt))

            nl = QHBoxLayout(nf)
            nl.setContentsMargins(16, 12, 16, 12)
            nl.setSpacing(12)

            ico = QLabel(type_icons.get(n["type"], "🔔"))
            ico.setStyleSheet("font-size: 20pt; background: transparent;")
            ico.setFixedSize(36, 36)
            nl.addWidget(ico)

            col = QVBoxLayout()
            col.setSpacing(2)
            fw = "700" if not is_read else "600"
            col.addWidget(_lbl(n["title"], f"font-weight: {fw}; color: {C_TEXT}; background: transparent;"))
            if n.get("message"):
                col.addWidget(_lbl(n["message"],
                                   f"color: {C_TEXT_MUTED}; font-size: 9pt; background: transparent;",
                                   wrap=True))
            col.addWidget(_lbl(fmt_datetime(n.get("created_at", "")),
                               f"color: {C_TEXT_MUTED}; font-size: 8pt; background: transparent;"))
            nl.addLayout(col)
            nl.addStretch()

            if not is_read:
                dot = QLabel("●")
                dot.setStyleSheet(f"color: {C_PRIMARY}; font-size: 10pt; background: transparent;")
                nl.addWidget(dot)

            arrow = QLabel("›")
            arrow.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 14pt; background: transparent;")
            nl.addWidget(arrow)

            l.addWidget(nf)

        if not notifs:
            emp = QLabel("Уведомлений нет")
            emp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emp.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 40px;")
            l.addWidget(emp)

        l.addStretch()
        w.setWidget(inner)
        return w

    # ── Profile ───────────────────────────────────────────────────

    def _build_profile(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        w.setFrameShape(QFrame.Shape.NoFrame)
        w.setStyleSheet("background: transparent; border: none;")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)

        hdr = QLabel("Мой профиль")
        hdr.setProperty("heading", "true")
        l.addWidget(hdr)

        prof_card = QFrame()
        prof_card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
        )
        pcl = QVBoxLayout(prof_card)
        pcl.setContentsMargins(28, 24, 28, 24)
        pcl.setSpacing(16)

        av_row = QHBoxLayout()
        self.prof_avatar = QLabel("👤")
        self.prof_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prof_avatar.setFixedSize(90, 90)
        self.prof_avatar.setStyleSheet(
            f"font-size: 44pt; background: {C_CONTENT_BG}; border-radius: 45px; "
            f"border: 3px solid {C_PRIMARY};"
        )
        av_row.addWidget(self.prof_avatar)

        av_info = QVBoxLayout()
        av_info.setSpacing(6)
        av_info.addWidget(_lbl(self.user.get("full_name") or self.user["username"],
                               f"font-size: 16pt; font-weight: 700; color: {C_TEXT};"))
        bal = UserModel.get_balance(self.user["id"])
        av_info.addWidget(_lbl(f"💰 Баланс: {fmt_money(bal)}",
                               "color: #16A34A; font-size: 10pt; font-weight: 600;"))
        btn_av = QPushButton("✎ Изменить фото")
        btn_av.setFixedSize(150, 34)
        btn_av.setStyleSheet(
            "QPushButton { background: transparent; color: #3B82F6; border: 1.5px solid #3B82F6; "
            "border-radius: 8px; font-size: 9pt; font-weight: 600; }"
            "QPushButton:hover { background: rgba(59,130,246,0.12); }"
        )
        btn_av.clicked.connect(self._change_avatar)
        av_info.addWidget(btn_av)
        av_row.addLayout(av_info)
        av_row.addStretch()
        pcl.addLayout(av_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {C_BORDER}; max-height: 1px; border: none; border-radius: 0;")
        pcl.addWidget(sep)

        _inp = (
            "QLineEdit { background: #0F172A; border: 1.5px solid #4B6280; border-radius: 8px; "
            "color: #F1F5F9; padding: 4px 10px; font-size: 10pt; }"
            "QLineEdit:focus { border-color: #3B82F6; }"
        )
        _ta = (
            "QTextEdit { background: #0F172A; border: 1.5px solid #4B6280; border-radius: 8px; "
            "color: #F1F5F9; padding: 6px 10px; font-size: 10pt; }"
            "QTextEdit:focus { border-color: #3B82F6; }"
        )
        fl = QFormLayout()
        fl.setSpacing(12)
        self.pf_fullname = QLineEdit(self.user.get("full_name", ""))
        self.pf_fullname.setFixedHeight(38)
        self.pf_fullname.setStyleSheet(_inp)
        fl.addRow("Полное имя", self.pf_fullname)
        self.pf_phone = QLineEdit(self.user.get("phone", ""))
        self.pf_phone.setFixedHeight(38)
        self.pf_phone.setStyleSheet(_inp)
        fl.addRow("Телефон", self.pf_phone)
        self.pf_city = QLineEdit(self.user.get("city", ""))
        self.pf_city.setFixedHeight(38)
        self.pf_city.setStyleSheet(_inp)
        fl.addRow("Город", self.pf_city)
        self.pf_bio = QTextEdit(self.user.get("bio", ""))
        self.pf_bio.setFixedHeight(90)
        self.pf_bio.setPlaceholderText("Расскажите о своей компании...")
        self.pf_bio.setStyleSheet(_ta)
        fl.addRow("О себе", self.pf_bio)
        pcl.addLayout(fl)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background: {C_BORDER}; max-height: 1px; border: none; border-radius: 0;")
        pcl.addWidget(sep2)

        pcl.addWidget(_lbl("Изменение пароля",
                           f"font-weight: 600; font-size: 11pt; color: {C_TEXT};"))
        pw_fl = QFormLayout()
        pw_fl.setSpacing(10)
        self.pf_old_pw = QLineEdit()
        self.pf_old_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.pf_old_pw.setFixedHeight(38)
        self.pf_old_pw.setPlaceholderText("Введите текущий пароль")
        self.pf_old_pw.setStyleSheet(_inp)
        pw_fl.addRow("Текущий пароль", self.pf_old_pw)
        self.pf_new_pw = QLineEdit()
        self.pf_new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.pf_new_pw.setFixedHeight(38)
        self.pf_new_pw.setPlaceholderText("Новый пароль (мин. 6 символов)")
        self.pf_new_pw.setStyleSheet(_inp)
        pw_fl.addRow("Новый пароль", self.pf_new_pw)
        self.pf_new_pw2 = QLineEdit()
        self.pf_new_pw2.setEchoMode(QLineEdit.EchoMode.Password)
        self.pf_new_pw2.setFixedHeight(38)
        self.pf_new_pw2.setPlaceholderText("Повторите новый пароль")
        self.pf_new_pw2.setStyleSheet(_inp)
        pw_fl.addRow("Подтвердите", self.pf_new_pw2)
        pcl.addLayout(pw_fl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_pw = QPushButton("Сменить пароль")
        btn_pw.setFixedSize(160, 40)
        btn_pw.setStyleSheet(
            "QPushButton { background: transparent; color: #3B82F6; border: 2px solid #3B82F6; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; }"
            "QPushButton:hover { background: rgba(59,130,246,0.12); }"
        )
        btn_pw.clicked.connect(self._change_password)
        btn_row.addWidget(btn_pw)
        btn_save = QPushButton("Сохранить профиль")
        btn_save.setFixedSize(180, 40)
        btn_save.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; font-size: 10pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_save.clicked.connect(self._save_profile)
        btn_row.addWidget(btn_save)
        pcl.addLayout(btn_row)

        l.addWidget(prof_card)
        l.addStretch()
        w.setWidget(inner)
        return w

    # ── Navigation ────────────────────────────────────────────────

    def _nav(self, index: int):
        if index < len(self._nav_btns):
            for i, btn in enumerate(self._nav_btns):
                btn.setProperty("active", "true" if i == index else "false")
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        if index == 5:
            self.stack.removeWidget(self.stack.widget(5))
            self.stack.insertWidget(5, self._build_notifications())
            self.stack.setCurrentIndex(5)
            NotificationModel.mark_all_read(self.user["id"])
            self._refresh_badges()
        else:
            self.stack.setCurrentIndex(index)

    # ── Balance page (fullscreen) ─────────────────────────────────

    def _build_balance_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top_bar = QWidget()
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet(
            f"background: {C_CARD_BG}; border-bottom: 1px solid {C_BORDER};"
        )
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(16, 0, 16, 0)
        btn_back = QPushButton("← Назад")
        btn_back.setProperty("cls", "secondary")
        btn_back.setFixedHeight(36)
        btn_back.clicked.connect(lambda: self._nav(self._prev_page))
        tb.addWidget(btn_back)
        tb.addStretch()
        title = QLabel("💳 Пополнение баланса")
        title.setStyleSheet(f"font-size: 12pt; font-weight: 700; color: {C_TEXT};")
        tb.addWidget(title)
        tb.addSpacing(16)
        outer.addWidget(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 40, 32, 40)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 16px; }} QLabel {{ border: none; background: transparent; }}"
        )
        card.setMaximumWidth(580)
        card.setMinimumWidth(400)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 36, 40, 36)
        cl.setSpacing(20)

        bal_bg = QFrame()
        bal_bg.setStyleSheet(
            f"QFrame {{ background: {C_CONTENT_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; }}"
        )
        bfl = QVBoxLayout(bal_bg)
        bfl.setContentsMargins(24, 18, 24, 18)
        bfl.setSpacing(4)
        ml = QLabel("ТЕКУЩИЙ БАЛАНС")
        ml.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 8pt; font-weight: 700;")
        bfl.addWidget(ml)
        current = UserModel.get_balance(self.user["id"])
        self._bal_page_lbl = QLabel(fmt_money(current))
        self._bal_page_lbl.setStyleSheet(
            f"font-size: 30pt; font-weight: 800; color: {C_PRIMARY};"
        )
        bfl.addWidget(self._bal_page_lbl)
        cl.addWidget(bal_bg)

        qa_lbl = QLabel("Быстрое пополнение")
        qa_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt; font-weight: 700;")
        cl.addWidget(qa_lbl)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(10)
        for amount in [5000, 10000, 25000, 50000]:
            btn = QPushButton(fmt_money(amount))
            btn.setStyleSheet(
                "QPushButton { background: #1E3A5F; color: #60A5FA; border: 2px solid #3B82F6; "
                "border-radius: 10px; font-size: 10pt; font-weight: 700; }"
                "QPushButton:hover { background: #2563EB; color: white; }"
            )
            btn.setFixedHeight(48)
            btn.clicked.connect(lambda _, a=amount: self._bal_spn.setValue(a))
            quick_row.addWidget(btn)
        cl.addLayout(quick_row)

        ca_lbl = QLabel("✏ Или введите сумму:")
        ca_lbl.setStyleSheet("color: #94A3B8; font-size: 10pt; font-weight: 700;")
        cl.addWidget(ca_lbl)

        self._bal_spn = QDoubleSpinBox()
        self._bal_spn.setRange(100, 10_000_000)
        self._bal_spn.setSuffix(" ₽")
        self._bal_spn.setDecimals(0)
        self._bal_spn.setSingleStep(1000)
        self._bal_spn.setValue(10000)
        self._bal_spn.setFixedHeight(56)
        self._bal_spn.setStyleSheet(
            "QDoubleSpinBox { background: #1A2540; border: 2px solid #3B82F6; border-radius: 10px; "
            "color: #F1F5F9; padding: 4px 14px; font-size: 15pt; font-weight: 700; }"
            "QDoubleSpinBox:focus { border-color: #60A5FA; background: #1E3050; }"
            "QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 24px; }"
        )
        cl.addWidget(self._bal_spn)

        info = QLabel(
            "ℹ️  Средства зачисляются мгновенно и доступны для оплаты заказов."
        )
        info.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
        info.setWordWrap(True)
        cl.addWidget(info)

        btn_ok = QPushButton("💳  Пополнить")
        btn_ok.setFixedHeight(52)
        btn_ok.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; background: {C_PRIMARY}; "
            "color: white; border-radius: 10px;"
        )
        btn_ok.clicked.connect(lambda: self._do_topup(self._bal_spn.value()))
        cl.addWidget(btn_ok)

        # ── Withdrawal section ────────────────────────────────────
        sep_w = QFrame()
        sep_w.setFrameShape(QFrame.Shape.HLine)
        sep_w.setStyleSheet(f"background: {C_BORDER}; max-height: 1px; border: none; border-radius: 0;")
        cl.addWidget(sep_w)

        wd_lbl = QLabel("💸 Вывод средств")
        wd_lbl.setStyleSheet("color: #94A3B8; font-size: 10pt; font-weight: 700;")
        cl.addWidget(wd_lbl)

        self._withdraw_spn = QDoubleSpinBox()
        self._withdraw_spn.setRange(100, 10_000_000)
        self._withdraw_spn.setSuffix(" ₽")
        self._withdraw_spn.setDecimals(0)
        self._withdraw_spn.setSingleStep(1000)
        self._withdraw_spn.setValue(5000)
        self._withdraw_spn.setFixedHeight(52)
        self._withdraw_spn.setStyleSheet(
            "QDoubleSpinBox { background: #1A2540; border: 2px solid #22C55E; border-radius: 10px; "
            "color: #F1F5F9; padding: 4px 14px; font-size: 14pt; font-weight: 700; }"
            "QDoubleSpinBox:focus { border-color: #86EFAC; background: #1E3050; }"
            "QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 24px; }"
        )
        cl.addWidget(self._withdraw_spn)

        wd_info = QLabel(
            "⚠️  Средства будут списаны с баланса. "
            "Убедитесь, что сумма не превышает текущий баланс."
        )
        wd_info.setStyleSheet("color: #F59E0B; font-size: 9pt;")
        wd_info.setWordWrap(True)
        cl.addWidget(wd_info)

        btn_wd = QPushButton("💸  Вывести средства")
        btn_wd.setFixedHeight(50)
        btn_wd.setStyleSheet(
            "QPushButton { font-size: 11pt; font-weight: 700; background: #16A34A; "
            "color: white; border: 2px solid #22C55E; border-radius: 10px; }"
            "QPushButton:hover { background: #15803D; }"
        )
        btn_wd.clicked.connect(lambda: self._do_withdraw(self._withdraw_spn.value()))
        cl.addWidget(btn_wd)

        center = QHBoxLayout()
        center.addStretch()
        center.addWidget(card)
        center.addStretch()
        root.addLayout(center)

        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    def _do_topup(self, amount: float):
        new_bal = UserModel.add_balance(self.user["id"], amount)
        self.user["balance"] = new_bal
        self._bal_lbl.setText(fmt_money(new_bal))
        if hasattr(self, "_bal_page_lbl"):
            self._bal_page_lbl.setText(fmt_money(new_bal))
        QMessageBox.information(
            self, "Баланс пополнен",
            f"На ваш счёт зачислено {fmt_money(amount)}.\n"
            f"Текущий баланс: {fmt_money(new_bal)}"
        )
        self._nav(self._prev_page)

    def _do_withdraw(self, amount: float):
        current = UserModel.get_balance(self.user["id"])
        if amount <= 0:
            QMessageBox.warning(self, "Ошибка", "Введите сумму больше нуля")
            return
        if amount > current:
            QMessageBox.warning(
                self, "Недостаточно средств",
                f"На балансе {fmt_money(current)}, а запрошено {fmt_money(amount)}.\n"
                "Уменьшите сумму вывода."
            )
            return
        reply = QMessageBox.question(
            self, "Подтверждение вывода",
            f"Вывести {fmt_money(amount)} с баланса?\n"
            f"Остаток после вывода: {fmt_money(current - amount)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        new_bal = UserModel.add_balance(self.user["id"], -amount)
        self.user["balance"] = new_bal
        self._bal_lbl.setText(fmt_money(new_bal))
        if hasattr(self, "_bal_page_lbl"):
            self._bal_page_lbl.setText(fmt_money(new_bal))
        QMessageBox.information(
            self, "Вывод выполнен",
            f"Выведено {fmt_money(amount)}.\n"
            f"Текущий баланс: {fmt_money(new_bal)}"
        )
        self._nav(self._prev_page)

    # ── Settings page (fullscreen) ────────────────────────────────

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top_bar = QWidget()
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet(
            f"background: {C_CARD_BG}; border-bottom: 1px solid {C_BORDER};"
        )
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(16, 0, 16, 0)
        btn_back = QPushButton("← Назад")
        btn_back.setProperty("cls", "secondary")
        btn_back.setFixedHeight(36)
        btn_back.clicked.connect(lambda: self._nav(self._prev_page))
        tb.addWidget(btn_back)
        tb.addStretch()
        title = QLabel("⚙  Настройки")
        title.setStyleSheet(f"font-size: 12pt; font-weight: 700; color: {C_TEXT};")
        tb.addWidget(title)
        tb.addSpacing(16)
        outer.addWidget(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)

        pg_hdr = QLabel("Настройки")
        pg_hdr.setStyleSheet(f"font-size: 20pt; font-weight: 800; color: {C_TEXT};")
        l.addWidget(pg_hdr)

        notif_card = QFrame()
        notif_card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 14px; }} QLabel {{ border: none; background: transparent; }}"
        )
        ncl = QVBoxLayout(notif_card)
        ncl.setContentsMargins(28, 24, 28, 24)
        ncl.setSpacing(14)
        nc_hdr = QLabel("🔔 Уведомления")
        nc_hdr.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {C_TEXT};")
        ncl.addWidget(nc_hdr)
        for text in [
            "Принятые/отклонённые отклики",
            "Сообщения в чате",
            "Изменение статуса заказа",
            "Поступление оплаты",
        ]:
            cb = QCheckBox(text)
            cb.setChecked(True)
            ncl.addWidget(cb)
        btn_sv = QPushButton("💾 Сохранить")
        btn_sv.setFixedSize(160, 42)
        btn_sv.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: 2px solid #3B82F6; "
            "border-radius: 10px; font-size: 10pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; border-color: #60A5FA; }"
            "QPushButton:pressed { background: #1E40AF; }"
        )
        ncl.addWidget(btn_sv, alignment=Qt.AlignmentFlag.AlignRight)
        l.addWidget(notif_card)

        about_card = QFrame()
        about_card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 14px; }} QLabel {{ border: none; background: transparent; }}"
        )
        acl = QVBoxLayout(about_card)
        acl.setContentsMargins(28, 28, 28, 28)
        acl.setSpacing(12)
        logo = QLabel("🚛")
        logo.setStyleSheet("font-size: 48pt;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        acl.addWidget(logo)
        app_name = QLabel("FreightExchange")
        app_name.setStyleSheet("font-size: 20pt; font-weight: 800; color: #3B82F6;")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        acl.addWidget(app_name)
        for line in [
            "Биржа фрахта для малого логистического бизнеса",
            "Версия 1.0 — Дипломный проект 2026",
            "Реализовано на Python + PyQt6 + SQLite",
        ]:
            lbl = QLabel(line)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
            acl.addWidget(lbl)
        l.addWidget(about_card)
        l.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    # ── Navigation / actions ──────────────────────────────────────

    def _edit_company(self):
        dlg = CompanyProfileDialog(self.user["id"], self)
        if dlg.exec():
            self.stack.removeWidget(self.stack.widget(1))
            self.stack.insertWidget(1, self._build_company_page())
            company = CompanyModel.get_by_user(self.user["id"])
            if company:
                self.name_lbl.setText(company["company_name"])

    def _topup_balance(self):
        self._prev_page = self.stack.currentIndex()
        old = self.stack.widget(7)
        self.stack.removeWidget(old)
        old.deleteLater()
        self.stack.insertWidget(7, self._build_balance_page())
        self._nav(7)

    def _on_balance_updated(self, new_bal: float):
        self.user["balance"] = new_bal
        self._bal_lbl.setText(fmt_money(new_bal))

    def _open_settings(self):
        self._prev_page = self.stack.currentIndex()
        self._nav(8)

    def _change_avatar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "", "Изображения (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            dest = save_avatar(path, self.user["id"])
            UserModel.update_avatar(self.user["id"], dest)
            self.user["avatar_path"] = dest
            self._refresh_avatar()

    @staticmethod
    def _circular_pixmap(path: str, size: int) -> QPixmap:
        source = QPixmap(path)
        if source.isNull():
            return source
        scaled = source.scaled(size, size,
                               Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
        x = (scaled.width()  - size) // 2
        y = (scaled.height() - size) // 2
        scaled = scaled.copy(x, y, size, size)
        result = QPixmap(size, size)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        clip = QPainterPath()
        clip.addEllipse(0, 0, float(size), float(size))
        painter.setClipPath(clip)
        painter.drawPixmap(0, 0, scaled)
        painter.end()
        return result

    def _refresh_avatar(self):
        path = self.user.get("avatar_path", "")
        if path:
            try:
                pix = self._circular_pixmap(path, 54)
                self.avatar_lbl.setPixmap(pix)
                self.avatar_lbl.setText("")
            except Exception:
                pass

    def _save_profile(self):
        UserModel.update_profile(
            self.user["id"],
            self.pf_fullname.text().strip(),
            self.pf_phone.text().strip(),
            self.pf_city.text().strip(),
            self.pf_bio.toPlainText().strip()
        )
        self.user["full_name"] = self.pf_fullname.text().strip()
        QMessageBox.information(self, "Готово", "Профиль сохранён")

    def _change_password(self):
        old_pw  = self.pf_old_pw.text()
        new_pw  = self.pf_new_pw.text()
        new_pw2 = self.pf_new_pw2.text()
        if not all([old_pw, new_pw, new_pw2]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        if new_pw != new_pw2:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
        ok, msg = UserModel.change_password(self.user["id"], old_pw, new_pw)
        if ok:
            QMessageBox.information(self, "Готово", msg)
        else:
            QMessageBox.warning(self, "Ошибка", msg)

    def _logout(self):
        from ui.auth.login_window import LoginWindow
        self._login = LoginWindow()
        self._login.show()
        self.close()

    # ── Timers ────────────────────────────────────────────────────

    def _start_timers(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(4000)

    def _tick(self):
        self._refresh_badges()
        idx = self.stack.currentIndex()
        if idx == 0:
            self._refresh_home_data()
        elif idx == 2:
            self.avail_page.refresh() if hasattr(self.avail_page, "refresh") else None
        elif idx == 3:
            self.my_orders_page.refresh()

    def _refresh_badges(self):
        notif_count = NotificationModel.get_unread_count(self.user["id"])
        msg_count   = MessageModel.get_unread_count(self.user["id"])
        self._nav_btns[4].setText(
            f"  💬  Сообщения{f'  ({msg_count})' if msg_count else ''}"
        )
        self._nav_btns[5].setText(
            f"  🔔  Уведомления{f'  ({notif_count})' if notif_count else ''}"
        )
        bal = UserModel.get_balance(self.user["id"])
        self._bal_lbl.setText(fmt_money(bal))
        self.user["balance"] = bal


def _lbl(text: str, style: str = "", align: bool = False, wrap: bool = False) -> QLabel:
    lbl = QLabel(text)
    if style:
        lbl.setStyleSheet(style)
    if align:
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if wrap:
        lbl.setWordWrap(True)
    return lbl
