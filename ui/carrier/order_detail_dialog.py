from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QDoubleSpinBox, QSpinBox, QFrame, QWidget,
    QScrollArea, QLineEdit, QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import ResponseModel, NotificationModel, OrderModel, TruckModel
from ui.styles import (
    C_CONTENT_BG, C_CARD_BG, C_BORDER, C_TEXT, C_TEXT_MUTED, C_PRIMARY,
    STATUS_LABELS, show_info, show_warning
)
from ui.widgets.progress_tracker import ProgressTracker
from utils.helpers import fmt_money, fmt_date


class OrderDetailDialog(QDialog):
    response_sent = pyqtSignal()

    def __init__(self, order: dict, carrier_id: int, parent=None):
        super().__init__(parent)
        self.order      = order
        self.carrier_id = carrier_id
        self.setWindowTitle(f"Заявка: {order.get('title','')}")
        self.setMinimumSize(660, 580)
        self.resize(700, 640)
        self._build()

    def _build(self):
        self.setStyleSheet(f"background: {C_CONTENT_BG};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        w = QWidget()
        w.setStyleSheet(f"background: {C_CONTENT_BG};")
        wl = QVBoxLayout(w)
        wl.setContentsMargins(24, 24, 24, 24)
        wl.setSpacing(16)

        o = self.order

        # Progress tracker (active orders)
        if o.get("status") == "in_progress":
            prog_frame = QFrame()
            prog_frame.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
            )
            pfl = QVBoxLayout(prog_frame)
            pfl.setContentsMargins(16, 14, 16, 14)
            pfl.setSpacing(8)
            pfl.addWidget(_mlbl("Прогресс выполнения"))
            pfl.addWidget(ProgressTracker(o.get("progress_status", "waiting")))
            wl.addWidget(prog_frame)

        # Title
        title_lbl = QLabel(o.get("title", ""))
        title_lbl.setStyleSheet(f"font-size: 17pt; font-weight: 800; color: {C_TEXT};")
        title_lbl.setWordWrap(True)
        wl.addWidget(title_lbl)

        # Details card
        detail_card = QFrame()
        detail_card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )
        dcl = QVBoxLayout(detail_card)
        dcl.setContentsMargins(20, 16, 20, 16)
        dcl.setSpacing(10)

        def row(label: str, value: str):
            r = QHBoxLayout()
            lb = QLabel(label + ":")
            lb.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt; font-weight: 600;")
            lb.setFixedWidth(190)
            vl = QLabel(value or "—")
            vl.setStyleSheet(f"color: {C_TEXT}; font-size: 12pt;")
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
            cl.setStyleSheet(f"color: {C_TEXT}; font-size: 12pt; background: transparent;")
            cl.setWordWrap(True)
            cgl.addWidget(cl)
            wl.addWidget(cf)

        if o.get("special_requirements"):
            sf = QFrame()
            sf.setStyleSheet("QFrame { background: #FFFBEB; border: 1.5px solid #D97706; border-radius: 10px; } QLabel { border: none; background: transparent; }")
            srl = QVBoxLayout(sf)
            srl.setContentsMargins(16, 12, 16, 12)
            srl.addWidget(_mlbl("⚠ Специальные требования"))
            sl = QLabel(o.get("special_requirements", ""))
            sl.setStyleSheet("color: #92400E; font-size: 11pt; background: transparent;")
            sl.setWordWrap(True)
            srl.addWidget(sl)
            wl.addWidget(sf)

        # ── Carrier actions section ────────────────────────────────
        if o.get("status") == "in_progress" and o.get("carrier_id") == self.carrier_id:
            self._build_carrier_actions(wl)

        # ── Response form (for new orders) ────────────────────────
        already = ResponseModel.already_responded(o["id"], self.carrier_id)
        if o.get("status") == "new" and not already:
            self._build_response_form(wl)
        elif already and o.get("status") == "new":
            done_lbl = QFrame()
            done_lbl.setStyleSheet(
                "QFrame { background: #F0FDF4; border: 1.5px solid #16A34A; border-radius: 10px; } QLabel { border: none; background: transparent; }"
            )
            dl = QHBoxLayout(done_lbl)
            dl.setContentsMargins(16, 12, 16, 12)
            done_txt = QLabel("✅ Вы уже откликнулись на эту заявку")
            done_txt.setStyleSheet("color: #15803D; font-size: 12pt; font-weight: 600; background: transparent;")
            dl.addWidget(done_txt)
            wl.addWidget(done_lbl)

        wl.addStretch()
        scroll.setWidget(w)
        outer.addWidget(scroll)

    # ── Carrier actions ────────────────────────────────────────────

    def _build_carrier_actions(self, parent: QVBoxLayout):
        """Vehicle assignment + progress action buttons for the assigned carrier."""
        o = self.order
        progress = o.get("progress_status", "waiting")

        # Vehicle assignment form (when no vehicle yet)
        if progress == "waiting":
            veh_grp = QFrame()
            veh_grp.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
            )
            vgl = QVBoxLayout(veh_grp)
            vgl.setContentsMargins(20, 16, 20, 16)
            vgl.setSpacing(12)
            vgl.addWidget(_mlbl("🚛 Назначить транспорт"))

            # ── Fleet selector (trucks from company profile) ──────────
            self._fleet_trucks = TruckModel.get_by_carrier(self.carrier_id)
            if self._fleet_trucks:
                fleet_lbl = QLabel("Выбрать из автопарка:")
                fleet_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt; font-weight: 600;")
                vgl.addWidget(fleet_lbl)

                self.cmb_fleet = QComboBox()
                self.cmb_fleet.setFixedHeight(42)
                self.cmb_fleet.setStyleSheet(
                    "QComboBox { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
                    "color: #0F172A; padding: 6px 12px; font-size: 11pt; }"
                    "QComboBox:focus { border-color: #2563EB; background: #EFF6FF; }"
                    "QComboBox::drop-down { border: none; width: 26px; background: transparent; }"
                    "QComboBox QAbstractItemView { background: #FFFFFF; color: #0F172A; "
                    "border: 1.5px solid #CBD5E1; selection-background-color: #EFF6FF; "
                    "selection-color: #2563EB; font-size: 11pt; outline: none; }"
                    "QComboBox QAbstractItemView::item { color: #0F172A; padding: 8px 12px; min-height: 28px; }"
                    "QComboBox QAbstractItemView::item:selected { background: #EFF6FF; color: #2563EB; }"
                )
                self.cmb_fleet.addItem("— Выбрать ТС из автопарка —", None)
                for t in self._fleet_trucks:
                    label = f"{t['brand']} {t['model']}  ·  {t['plate_number']}  ·  {t['capacity_tons']}т"
                    self.cmb_fleet.addItem(label, t)
                self.cmb_fleet.currentIndexChanged.connect(self._on_fleet_select)
                vgl.addWidget(self.cmb_fleet)

            fl = QFormLayout()
            fl.setSpacing(10)

            _inp_sty = (
                "QLineEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
                "color: #0F172A; padding: 4px 12px; font-size: 11pt; }"
                "QLineEdit:focus { border-color: #2563EB; background: #EFF6FF; }"
            )

            self.inp_driver = QLineEdit()
            self.inp_driver.setPlaceholderText("Иванов Иван Иванович")
            self.inp_driver.setFixedHeight(42)
            self.inp_driver.setStyleSheet(_inp_sty)
            fl.addRow("Водитель *", self.inp_driver)

            self.inp_truck_num = QLineEdit()
            self.inp_truck_num.setPlaceholderText("А123ВС77")
            self.inp_truck_num.setFixedHeight(42)
            self.inp_truck_num.setStyleSheet(_inp_sty)
            fl.addRow("Номер ТС *", self.inp_truck_num)

            self.inp_truck_model = QLineEdit()
            self.inp_truck_model.setPlaceholderText("МАЗ-4371, КАМАЗ-5490...")
            self.inp_truck_model.setFixedHeight(42)
            self.inp_truck_model.setStyleSheet(_inp_sty)
            fl.addRow("Модель ТС", self.inp_truck_model)
            vgl.addLayout(fl)

            btn_row = QHBoxLayout()
            btn_row.addStretch()
            btn_assign = QPushButton("✅ Назначить транспорт")
            btn_assign.setFixedSize(220, 44)
            btn_assign.setStyleSheet(
                "QPushButton { background: #16A34A; color: white; border: none; "
                "border-radius: 8px; font-size: 11pt; font-weight: 700; }"
                "QPushButton:hover { background: #15803D; }"
            )
            btn_assign.clicked.connect(self._assign_vehicle)
            btn_row.addWidget(btn_assign)
            vgl.addLayout(btn_row)
            parent.addWidget(veh_grp)

        else:
            # Show assigned vehicle info
            if o.get("driver_name") or o.get("truck_number"):
                veh_info = _card()
                vil = QVBoxLayout(veh_info)
                vil.setContentsMargins(18, 14, 18, 14)
                vil.setSpacing(6)
                vil.addWidget(_mlbl("🚛 Назначенный транспорт"))
                if o.get("driver_name"):
                    vil.addWidget(_info_row("Водитель", o["driver_name"]))
                if o.get("truck_number"):
                    vil.addWidget(_info_row("Номер ТС", o["truck_number"]))
                if o.get("truck_model"):
                    vil.addWidget(_info_row("Модель ТС", o["truck_model"]))
                parent.addWidget(veh_info)

            # Action buttons based on progress
            if progress == "vehicle_assigned":
                box = QFrame()
                box.setStyleSheet(
                    "background: #EFF6FF; border: 1.5px solid #2563EB; border-radius: 12px;"
                )
                bl = QVBoxLayout(box)
                bl.setContentsMargins(18, 14, 18, 14)
                bl.setSpacing(10)
                info = QLabel(
                    "🚛 Транспорт назначен. После погрузки нажмите «Груз отправлен», "
                    "затем заказчик подтвердит отправку."
                )
                info.setStyleSheet("color: #1D4ED8; font-size: 11pt; background: transparent;")
                info.setWordWrap(True)
                bl.addWidget(info)
                btn = QPushButton("📦 Отметить: груз отправлен")
                btn.setFixedHeight(44)
                btn.setStyleSheet(
                    "QPushButton { background: transparent; color: #2563EB; border: 2px solid #2563EB; "
                    "border-radius: 8px; font-size: 11pt; font-weight: 600; padding: 0 16px; }"
                    "QPushButton:hover { background: #EFF6FF; }"
                )
                btn.clicked.connect(self._mark_dispatched)
                bl.addWidget(btn)
                parent.addWidget(box)

            elif progress in ("dispatched", "in_transit"):
                box = QFrame()
                box.setStyleSheet(
                    "background: #EFF6FF; border: 1.5px solid #1D4ED8; border-radius: 12px;"
                )
                bl = QVBoxLayout(box)
                bl.setContentsMargins(18, 14, 18, 14)
                bl.setSpacing(10)
                info = QLabel(
                    "🚚 Груз в пути. По прибытии к месту назначения нажмите «Прибыл»."
                )
                info.setStyleSheet("color: #1D4ED8; font-size: 11pt; background: transparent;")
                info.setWordWrap(True)
                bl.addWidget(info)
                btn = QPushButton("📍 Отметить: прибыл к месту назначения")
                btn.setFixedHeight(44)
                btn.setStyleSheet(
                    "QPushButton { background: transparent; color: #2563EB; border: 2px solid #2563EB; "
                    "border-radius: 8px; font-size: 11pt; font-weight: 600; padding: 0 16px; }"
                    "QPushButton:hover { background: #EFF6FF; }"
                )
                btn.clicked.connect(self._mark_arrived)
                bl.addWidget(btn)
                parent.addWidget(box)

            elif progress == "arrived":
                info = QLabel("📍 Вы отметили прибытие. Ожидайте подтверждения заказчика.")
                info.setStyleSheet(
                    "color: #15803D; font-size: 11pt; padding: 12px 16px; "
                    "background: #F0FDF4; border: 1.5px solid #16A34A; border-radius: 10px;"
                )
                info.setWordWrap(True)
                parent.addWidget(info)

    def _build_response_form(self, parent: QVBoxLayout):
        o = self.order
        resp_grp = QFrame()
        resp_grp.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )
        rgl = QVBoxLayout(resp_grp)
        rgl.setContentsMargins(20, 18, 20, 18)
        rgl.setSpacing(12)
        rgl.addWidget(_mlbl("Подать отклик"))

        fl = QFormLayout()
        fl.setSpacing(10)

        _spn_sty = (
            "QSpinBox, QDoubleSpinBox { background: #FFFFFF; border: 2px solid #CBD5E1; "
            "border-radius: 8px; color: #0F172A; padding: 4px 10px; font-size: 11pt; }"
            "QSpinBox:focus, QDoubleSpinBox:focus { border-color: #2563EB; background: #EFF6FF; }"
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
        self.inp_msg.setFixedHeight(100)
        self.inp_msg.setStyleSheet(
            "QTextEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
            "color: #0F172A; padding: 6px 10px; font-size: 11pt; }"
            "QTextEdit:focus { border-color: #2563EB; background: #EFF6FF; }"
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
        btn_send.clicked.connect(self._send_response)
        btn_row.addWidget(btn_send)
        rgl.addLayout(btn_row)
        parent.addWidget(resp_grp)

    # ── Actions ────────────────────────────────────────────────────

    def _on_fleet_select(self, idx: int):
        """Auto-fill truck fields when carrier picks from their fleet."""
        truck = self.cmb_fleet.itemData(idx)
        if truck:
            self.inp_truck_num.setText(truck.get("plate_number", ""))
            self.inp_truck_model.setText(
                f"{truck['brand']} {truck['model']} ({truck.get('year','')})"
            )

    def _assign_vehicle(self):
        driver = self.inp_driver.text().strip()
        truck_num = self.inp_truck_num.text().strip()
        truck_model = self.inp_truck_model.text().strip()

        if not driver or not truck_num:
            show_warning(self, "Ошибка", "Введите имя водителя и номер ТС")
            return

        OrderModel.assign_vehicle(self.order["id"], driver, truck_num, truck_model)
        NotificationModel.create(
            self.order["customer_id"], "vehicle_assigned",
            "Транспорт назначен",
            f"Перевозчик назначил транспорт на заявку «{self.order.get('title','')}»: "
            f"водитель {driver}, ТС {truck_num}."
        )
        show_info(
            self, "Готово",
            "Транспорт назначен. Заказчик получил уведомление.\n"
            "После погрузки отметьте отправку груза."
        )
        self.accept()

    def _mark_dispatched(self):
        OrderModel.mark_dispatched_by_carrier(self.order["id"])
        NotificationModel.create(
            self.order["customer_id"], "cargo_dispatched",
            "Груз отправлен",
            f"Перевозчик отметил отправку груза по заявке «{self.order.get('title','')}». "
            "Пожалуйста, подтвердите отправку в системе."
        )
        show_info(
            self, "Готово",
            "Отправка груза отмечена. Заказчик получил уведомление."
        )
        self.accept()

    def _mark_arrived(self):
        OrderModel.mark_arrived_by_carrier(self.order["id"])
        NotificationModel.create(
            self.order["customer_id"], "cargo_arrived",
            "Груз прибыл к месту назначения",
            f"Перевозчик отметил прибытие груза по заявке «{self.order.get('title','')}». "
            "Пожалуйста, подтвердите получение в системе."
        )
        show_info(
            self, "Готово",
            "Прибытие отмечено. Заказчик должен подтвердить получение груза."
        )
        self.accept()

    def _send_response(self):
        cost = self.spn_cost.value()
        days = self.spn_days.value()
        msg  = self.inp_msg.toPlainText().strip()

        if cost <= 0:
            show_warning(self, "Ошибка", "Укажите стоимость")
            return

        ResponseModel.create(self.order["id"], self.carrier_id, msg, cost, days)
        NotificationModel.create(
            self.order["customer_id"], "new_response",
            "Новый отклик на вашу заявку",
            f"Перевозчик откликнулся на заявку «{self.order.get('title','')}» "
            f"с ценой {fmt_money(cost)}",
            self.order["id"]
        )
        show_info(self, "Отклик отправлен", "Ваш отклик успешно отправлен заказчику.")
        self.response_sent.emit()
        self.accept()


def _mlbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #64748B; font-size: 10pt; font-weight: 700; text-transform: uppercase; "
        "background: transparent; border: none;"
    )
    return lbl


def _card() -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
    )
    return f


def _info_row(label: str, value: str) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent; border: none;")
    hl = QHBoxLayout(w)
    hl.setContentsMargins(0, 0, 0, 0)
    lb = QLabel(label + ":")
    lb.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt; font-weight: 600;")
    lb.setFixedWidth(130)
    vl = QLabel(value)
    vl.setStyleSheet(f"color: {C_TEXT}; font-size: 12pt;")
    hl.addWidget(lb)
    hl.addWidget(vl)
    hl.addStretch()
    return w
