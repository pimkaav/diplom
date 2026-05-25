from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QDoubleSpinBox,
    QDateEdit, QGroupBox, QFormLayout,
    QScrollArea, QWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from database.models import OrderModel
from ui.styles import C_CARD_BG, C_BORDER, C_CONTENT_BG, C_TEXT, C_TEXT_MUTED, show_info, show_warning
from utils.helpers import haversine_km, all_cities, save_custom_city


CARGO_TYPES = [
    "Генеральные грузы", "Сборные грузы", "Рефрижераторные",
    "Опасные грузы", "Негабаритные", "Навалочные", "Наливные",
    "Автомобили", "Строительные материалы", "Продукты питания",
    "Промышленное оборудование", "Другое",
]

# ── Shared inline styles ───────────────────────────────────────────
_INP = (
    "QLineEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
    "color: #0F172A; padding: 6px 12px; font-size: 11pt; }"
    "QLineEdit:focus { border-color: #2563EB; border-width: 2px; background: #EFF6FF; }"
)
_CMB = (
    "QComboBox { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
    "color: #0F172A; padding: 6px 12px; font-size: 11pt; }"
    "QComboBox:focus { border-color: #2563EB; background: #EFF6FF; }"
    "QComboBox::drop-down { border: none; width: 26px; background: transparent; }"
    "QComboBox QAbstractItemView { background: #FFFFFF; color: #0F172A; "
    "border: 1.5px solid #CBD5E1; border-radius: 6px; selection-background-color: #EFF6FF; "
    "selection-color: #2563EB; font-size: 11pt; outline: none; }"
    "QComboBox QAbstractItemView::item { color: #0F172A; padding: 8px 12px; min-height: 28px; }"
    "QComboBox QAbstractItemView::item:selected { background: #EFF6FF; color: #2563EB; }"
    "QComboBox QAbstractItemView::item:hover { background: #F1F5F9; }"
)
_SPN = (
    "QSpinBox, QDoubleSpinBox { background: #FFFFFF; border: 2px solid #CBD5E1; "
    "border-radius: 8px; color: #0F172A; padding: 6px 10px; font-size: 11pt; }"
    "QSpinBox:focus, QDoubleSpinBox:focus { border-color: #2563EB; background: #EFF6FF; }"
    "QSpinBox::up-button, QDoubleSpinBox::up-button, "
    "QSpinBox::down-button, QDoubleSpinBox::down-button { background: transparent; border: none; width: 18px; }"
)
_DTE = (
    "QDateEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
    "color: #0F172A; padding: 6px 12px; font-size: 11pt; }"
    "QDateEdit:focus { border-color: #2563EB; background: #EFF6FF; }"
    "QDateEdit::drop-down { border: none; width: 26px; background: transparent; }"
)
_TA = (
    "QTextEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
    "color: #0F172A; padding: 6px 12px; font-size: 11pt; }"
    "QTextEdit:focus { border-color: #2563EB; background: #EFF6FF; }"
)
_GRP = (
    "QGroupBox { background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 10px; "
    "margin-top: 18px; padding-top: 14px; }"
    "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; "
    "left: 14px; top: -2px; padding: 0 6px; "
    "color: #334155; font-size: 11pt; font-weight: 700; "
    "background: #FFFFFF; }"
    "QLabel { background: transparent; border: none; color: #0F172A; }"
)


# sorted city list, refreshed each time
def _get_sorted_cities() -> list[str]:
    return sorted(all_cities().keys())


# ── Add City Dialog ────────────────────────────────────────────────
class AddCityDialog(QDialog):
    city_added = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить город")
        self.setFixedSize(400, 300)
        self.setStyleSheet(f"background: {C_CONTENT_BG};")
        self._build()

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setContentsMargins(24, 20, 24, 20)
        vl.setSpacing(12)

        vl.addWidget(_h("Новый город"))
        vl.addWidget(_muted("Введите название и координаты (можно найти на maps.google.com)"))

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название города")
        self.inp_name.setFixedHeight(40)
        self.inp_name.setStyleSheet(_INP)
        vl.addWidget(self.inp_name)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.inp_lat = QDoubleSpinBox()
        self.inp_lat.setRange(-90, 90)
        self.inp_lat.setDecimals(4)
        self.inp_lat.setValue(55.7558)
        self.inp_lat.setPrefix("Шир: ")
        self.inp_lat.setFixedHeight(40)
        self.inp_lat.setStyleSheet(_SPN)
        row.addWidget(self.inp_lat)
        self.inp_lon = QDoubleSpinBox()
        self.inp_lon.setRange(-180, 180)
        self.inp_lon.setDecimals(4)
        self.inp_lon.setValue(37.6173)
        self.inp_lon.setPrefix("Дол: ")
        self.inp_lon.setFixedHeight(40)
        self.inp_lon.setStyleSheet(_SPN)
        row.addWidget(self.inp_lon)
        vl.addLayout(row)

        vl.addWidget(_muted("Пример: Москва — 55.7558, 37.6173"))
        vl.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setProperty("cls", "secondary")
        btn_cancel.setFixedSize(110, 40)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_add = QPushButton("✚ Добавить")
        btn_add.setFixedSize(140, 40)
        btn_add.clicked.connect(self._do_add)
        btn_row.addWidget(btn_add)
        vl.addLayout(btn_row)

    def _do_add(self):
        name = self.inp_name.text().strip()
        if not name:
            show_warning(self, "Ошибка", "Введите название города")
            return
        save_custom_city(name, self.inp_lat.value(), self.inp_lon.value())
        self.city_added.emit(name)
        show_info(self, "Готово", f"Город «{name}» добавлен")
        self.accept()


# ── Main form ──────────────────────────────────────────────────────
class CreateOrderPage(QWidget):
    """Embeddable order-creation form (no dialog chrome)."""
    order_created = pyqtSignal(int)
    cancelled     = pyqtSignal()

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self._build()

    def _build(self):
        self.setStyleSheet(f"background: {C_CONTENT_BG};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background: {C_CONTENT_BG}; border: none;")

        w = QWidget()
        w.setStyleSheet(f"background: {C_CONTENT_BG};")
        wl = QVBoxLayout(w)
        wl.setContentsMargins(24, 20, 24, 20)
        wl.setSpacing(14)

        title_lbl = QLabel("Создать заявку на перевозку")
        title_lbl.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT}; background: transparent;")
        wl.addWidget(title_lbl)

        # ── Блок 1: Основная информация ───────────────────────────
        grp1 = QGroupBox("Основная информация")
        grp1.setStyleSheet(_GRP)
        fl1  = QFormLayout(grp1)
        fl1.setSpacing(10)
        fl1.setContentsMargins(16, 16, 16, 14)
        fl1.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.inp_title = QLineEdit()
        self.inp_title.setPlaceholderText("Например: Перевозка оборудования Москва→СПб")
        self.inp_title.setFixedHeight(42)
        self.inp_title.setStyleSheet(_INP)
        fl1.addRow(_flbl("Название *"), self.inp_title)

        # Тип груза + вес + объём — в одну строку
        cargo_row = QHBoxLayout()
        cargo_row.setSpacing(8)
        self.cmb_cargo = QComboBox()
        self.cmb_cargo.addItems(CARGO_TYPES)
        self.cmb_cargo.setFixedHeight(42)
        self.cmb_cargo.setMinimumWidth(200)
        self.cmb_cargo.setStyleSheet(_CMB)
        cargo_row.addWidget(self.cmb_cargo, 3)

        self.spn_weight = QDoubleSpinBox()
        self.spn_weight.setRange(0.01, 99999)
        self.spn_weight.setSuffix(" т")
        self.spn_weight.setDecimals(2)
        self.spn_weight.setFixedHeight(42)
        self.spn_weight.setToolTip("Масса груза в тоннах")
        self.spn_weight.setStyleSheet(_SPN)
        cargo_row.addWidget(self.spn_weight, 1)

        self.spn_volume = QDoubleSpinBox()
        self.spn_volume.setRange(0, 120)
        self.spn_volume.setSuffix(" м³")
        self.spn_volume.setDecimals(1)
        self.spn_volume.setFixedHeight(42)
        self.spn_volume.setToolTip("Объём груза")
        self.spn_volume.setStyleSheet(_SPN)
        cargo_row.addWidget(self.spn_volume, 1)
        fl1.addRow(_flbl("Груз / Вес / Объём *"), cargo_row)

        wl.addWidget(grp1)

        # ── Блок 2: Маршрут ───────────────────────────────────────
        grp2 = QGroupBox("Маршрут")
        grp2.setStyleSheet(_GRP)
        g2l  = QVBoxLayout(grp2)
        g2l.setContentsMargins(16, 16, 16, 14)
        g2l.setSpacing(10)

        # Откуда + Куда на одной строке
        cities = _get_sorted_cities()
        route_row = QHBoxLayout()
        route_row.setSpacing(10)

        from_col = QVBoxLayout()
        from_col.setSpacing(4)
        from_col.addWidget(_muted("Откуда *"))
        from_inner = QHBoxLayout()
        from_inner.setSpacing(6)
        self.cmb_from = QComboBox()
        self.cmb_from.setEditable(True)
        self.cmb_from.addItems(cities)
        self.cmb_from.setFixedHeight(42)
        self.cmb_from.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cmb_from.setStyleSheet(_CMB)
        from_inner.addWidget(self.cmb_from)
        btn_add_from = QPushButton("＋")
        btn_add_from.setFixedSize(34, 42)
        btn_add_from.setToolTip("Добавить новый город")
        btn_add_from.setStyleSheet(
            "QPushButton { background: transparent; color: #3B82F6; border: 2px solid #3B82F6; "
            "border-radius: 8px; font-size: 14pt; font-weight: 700; padding: 0; }"
            "QPushButton:hover { background: rgba(59,130,246,0.15); }"
        )
        btn_add_from.clicked.connect(self._add_city)
        from_inner.addWidget(btn_add_from)
        from_col.addLayout(from_inner)
        route_row.addLayout(from_col, 1)

        arrow_lbl = QLabel("→")
        arrow_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 18pt; background: transparent;")
        arrow_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_lbl.setFixedWidth(32)
        route_row.addWidget(arrow_lbl)

        to_col = QVBoxLayout()
        to_col.setSpacing(4)
        to_col.addWidget(_muted("Куда *"))
        to_inner = QHBoxLayout()
        to_inner.setSpacing(6)
        self.cmb_to = QComboBox()
        self.cmb_to.setEditable(True)
        self.cmb_to.addItems(cities)
        self.cmb_to.setCurrentIndex(min(1, len(cities) - 1))
        self.cmb_to.setFixedHeight(42)
        self.cmb_to.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cmb_to.setStyleSheet(_CMB)
        to_inner.addWidget(self.cmb_to)
        btn_add_to = QPushButton("＋")
        btn_add_to.setFixedSize(34, 42)
        btn_add_to.setToolTip("Добавить новый город")
        btn_add_to.setStyleSheet(
            "QPushButton { background: transparent; color: #3B82F6; border: 2px solid #3B82F6; "
            "border-radius: 8px; font-size: 14pt; font-weight: 700; padding: 0; }"
            "QPushButton:hover { background: rgba(59,130,246,0.15); }"
        )
        btn_add_to.clicked.connect(self._add_city)
        to_inner.addWidget(btn_add_to)
        to_col.addLayout(to_inner)
        route_row.addLayout(to_col, 1)

        g2l.addLayout(route_row)

        # Расстояние (авто-расчёт)
        dist_row = QHBoxLayout()
        dist_row.setSpacing(8)
        dist_lbl = QLabel("Расстояние:")
        dist_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt; background: transparent;")
        dist_row.addWidget(dist_lbl)
        self.spn_dist = QDoubleSpinBox()
        self.spn_dist.setRange(0, 99999)
        self.spn_dist.setSuffix(" км")
        self.spn_dist.setDecimals(0)
        self.spn_dist.setFixedHeight(40)
        self.spn_dist.setMinimumWidth(140)
        self.spn_dist.setStyleSheet(_SPN)
        dist_row.addWidget(self.spn_dist)
        btn_calc = QPushButton("⟳ Рассчитать км")
        btn_calc.setFixedSize(160, 40)
        btn_calc.setToolTip("Рассчитать расстояние по координатам")
        btn_calc.setStyleSheet(
            "QPushButton { background: #EFF6FF; color: #2563EB; border: 2px solid #2563EB; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; }"
            "QPushButton:hover { background: #2563EB; color: white; }"
        )
        btn_calc.clicked.connect(self._calc_distance)
        dist_row.addWidget(btn_calc)
        self._dist_hint = QLabel("")
        self._dist_hint.setStyleSheet(f"color: #2563EB; font-size: 10pt; background: transparent;")
        dist_row.addWidget(self._dist_hint)
        dist_row.addStretch()
        g2l.addLayout(dist_row)

        wl.addWidget(grp2)

        # Auto-calculate when cities change
        self.cmb_from.currentTextChanged.connect(self._auto_distance)
        self.cmb_to.currentTextChanged.connect(self._auto_distance)

        # ── Блок 3: Даты и бюджет ─────────────────────────────────
        grp3 = QGroupBox("Даты и бюджет")
        grp3.setStyleSheet(_GRP)
        fl3  = QFormLayout(grp3)
        fl3.setSpacing(10)
        fl3.setContentsMargins(16, 16, 16, 14)
        fl3.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Обе даты в одну строку
        dates_row = QHBoxLayout()
        dates_row.setSpacing(10)
        self.dt_pickup = QDateEdit()
        self.dt_pickup.setDate(QDate.currentDate().addDays(1))
        self.dt_pickup.setCalendarPopup(True)
        self.dt_pickup.setFixedHeight(42)
        self.dt_pickup.setMinimumWidth(150)
        self.dt_pickup.setStyleSheet(_DTE)
        dates_row.addWidget(self.dt_pickup)
        arr = QLabel("→")
        arr.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 16pt; background: transparent;")
        dates_row.addWidget(arr)
        self.dt_delivery = QDateEdit()
        self.dt_delivery.setDate(QDate.currentDate().addDays(5))
        self.dt_delivery.setCalendarPopup(True)
        self.dt_delivery.setFixedHeight(42)
        self.dt_delivery.setMinimumWidth(150)
        self.dt_delivery.setStyleSheet(_DTE)
        dates_row.addWidget(self.dt_delivery)
        dates_row.addStretch()
        fl3.addRow(_flbl("Погрузка → Доставка *"), dates_row)

        self.spn_budget = QDoubleSpinBox()
        self.spn_budget.setRange(0, 99_999_999)
        self.spn_budget.setSuffix(" ₽")
        self.spn_budget.setDecimals(0)
        self.spn_budget.setSingleStep(1000)
        self.spn_budget.setFixedHeight(42)
        self.spn_budget.setStyleSheet(_SPN)
        fl3.addRow(_flbl("Бюджет (₽)"), self.spn_budget)

        wl.addWidget(grp3)

        # ── Блок 4: Дополнительно ─────────────────────────────────
        grp4 = QGroupBox("Дополнительная информация")
        grp4.setStyleSheet(_GRP)
        fl4  = QVBoxLayout(grp4)
        fl4.setContentsMargins(16, 16, 16, 14)
        fl4.setSpacing(8)

        fl4.addWidget(_muted("Комментарий к заказу:"))
        self.inp_comment = QTextEdit()
        self.inp_comment.setPlaceholderText("Особенности груза, условия погрузки/выгрузки...")
        self.inp_comment.setFixedHeight(80)
        self.inp_comment.setStyleSheet(_TA)
        fl4.addWidget(self.inp_comment)

        fl4.addWidget(_muted("Специальные требования:"))
        self.inp_special = QTextEdit()
        self.inp_special.setPlaceholderText("Температурный режим, разрешения, страхование...")
        self.inp_special.setFixedHeight(64)
        self.inp_special.setStyleSheet(_TA)
        fl4.addWidget(self.inp_special)

        wl.addWidget(grp4)

        # ── Кнопки ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("← К моим заявкам")
        btn_cancel.setFixedSize(180, 46)
        btn_cancel.setStyleSheet(
            "QPushButton { background: transparent; color: #64748B; border: 2px solid #CBD5E1; "
            "border-radius: 8px; font-size: 11pt; font-weight: 600; }"
            "QPushButton:hover { background: #F1F5F9; border-color: #94A3B8; }"
        )
        btn_cancel.clicked.connect(self.cancelled.emit)
        btn_row.addWidget(btn_cancel)

        btn_create = QPushButton("✚ Создать заявку")
        btn_create.setFixedSize(200, 46)
        btn_create.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; font-size: 12pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; }"
            "QPushButton:pressed { background: #1E40AF; }"
        )
        btn_create.clicked.connect(self._create)
        btn_row.addWidget(btn_create)

        wl.addLayout(btn_row)
        wl.addSpacing(10)

        scroll.setWidget(w)
        outer.addWidget(scroll)

    # ── Distance helpers ──────────────────────────────────────────

    def _auto_distance(self):
        km = haversine_km(self.cmb_from.currentText(), self.cmb_to.currentText())
        if km > 0:
            self.spn_dist.setValue(km)
            self._dist_hint.setText(f"≈ {km:,.0f} км".replace(",", " "))
        else:
            self._dist_hint.setText("")

    def _calc_distance(self):
        self._auto_distance()

    def _add_city(self):
        dlg = AddCityDialog(self)
        dlg.city_added.connect(self._refresh_cities)
        dlg.exec()

    def _refresh_cities(self, new_city: str = ""):
        cities = _get_sorted_cities()
        cur_from = self.cmb_from.currentText()
        cur_to   = self.cmb_to.currentText()
        for cmb in (self.cmb_from, self.cmb_to):
            cmb.blockSignals(True)
            cmb.clear()
            cmb.addItems(cities)
            cmb.blockSignals(False)
        self.cmb_from.setCurrentText(cur_from)
        self.cmb_to.setCurrentText(cur_to)
        if new_city:
            self.cmb_from.setCurrentText(new_city)
        self._auto_distance()

    # ── Create order ──────────────────────────────────────────────

    def _create(self):
        title = self.inp_title.text().strip()
        if not title:
            show_warning(self, "Ошибка", "Введите название заявки")
            return
        from_city = self.cmb_from.currentText().strip()
        to_city   = self.cmb_to.currentText().strip()
        if not from_city or not to_city:
            show_warning(self, "Ошибка", "Укажите маршрут")
            return
        if from_city == to_city:
            show_warning(self, "Ошибка", "Город отправления и назначения совпадают")
            return
        data = {
            "customer_id":          self.customer_id,
            "title":                title,
            "cargo_type":           self.cmb_cargo.currentText(),
            "cargo_weight":         self.spn_weight.value(),
            "cargo_volume":         self.spn_volume.value(),
            "from_city":            from_city,
            "to_city":              to_city,
            "distance":             self.spn_dist.value(),
            "pickup_date":          self.dt_pickup.date().toString("yyyy-MM-dd"),
            "delivery_date":        self.dt_delivery.date().toString("yyyy-MM-dd"),
            "budget":               self.spn_budget.value(),
            "comment":              self.inp_comment.toPlainText().strip(),
            "special_requirements": self.inp_special.toPlainText().strip(),
        }
        order_id = OrderModel.create(data)
        self.order_created.emit(order_id)

    def reset(self):
        self.inp_title.clear()
        self.inp_comment.clear()
        self.inp_special.clear()
        cities = _get_sorted_cities()
        self.cmb_from.setCurrentIndex(0)
        self.cmb_to.setCurrentIndex(min(1, len(cities) - 1))
        self.spn_dist.setValue(0)
        self.spn_weight.setValue(0.01)
        self.spn_volume.setValue(0)
        self.spn_budget.setValue(0)
        self.dt_pickup.setDate(QDate.currentDate().addDays(1))
        self.dt_delivery.setDate(QDate.currentDate().addDays(5))
        self._dist_hint.setText("")


class CreateOrderDialog(QDialog):
    """Dialog wrapper around CreateOrderPage (kept for backward compat)."""
    order_created = pyqtSignal(int)

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новый заказ на перевозку")
        self.setMinimumSize(640, 700)
        self.resize(700, 780)
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        self._page = CreateOrderPage(customer_id, self)
        self._page.order_created.connect(self._on_created)
        self._page.cancelled.connect(self.reject)
        vl.addWidget(self._page)

    def _on_created(self, order_id: int):
        self.order_created.emit(order_id)
        show_info(self, "Заявка создана",
                  "Заявка успешно размещена!\nПеревозчики смогут подать отклики.")
        self.accept()


# ── Helpers ────────────────────────────────────────────────────────

def _muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10pt; background: transparent;")
    return lbl


def _flbl(text: str) -> QLabel:
    """Form row label — darker, slightly bigger."""
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #334155; font-size: 11pt; font-weight: 600; background: transparent;")
    return lbl


def _h(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {C_TEXT}; background: transparent;")
    return lbl
