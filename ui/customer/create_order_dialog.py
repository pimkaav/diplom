from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QDoubleSpinBox,
    QDateEdit, QGroupBox, QFormLayout, QMessageBox, QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from database.models import OrderModel
from ui.styles import C_CARD_BG, C_BORDER, C_CONTENT_BG, C_TEXT, C_TEXT_MUTED


CARGO_TYPES = [
    "Генеральные грузы",
    "Сборные грузы",
    "Рефрижераторные",
    "Опасные грузы",
    "Негабаритные",
    "Навалочные",
    "Наливные",
    "Автомобили",
    "Строительные материалы",
    "Продукты питания",
    "Промышленное оборудование",
    "Другое",
]

RUSSIAN_CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Омск", "Самара", "Уфа", "Ростов-на-Дону",
    "Красноярск", "Воронеж", "Пермь", "Волгоград", "Краснодар", "Тюмень",
    "Саратов", "Тольятти", "Ижевск", "Барнаул", "Ульяновск", "Иркутск",
    "Хабаровск", "Ярославль", "Владивосток", "Махачкала", "Томск", "Оренбург",
]


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
        scroll.setStyleSheet("background: transparent;")

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        wl = QVBoxLayout(w)
        wl.setContentsMargins(32, 28, 32, 28)
        wl.setSpacing(18)

        title_lbl = QLabel("Создать заявку на перевозку")
        title_lbl.setStyleSheet(
            f"font-size: 18pt; font-weight: 800; color: {C_TEXT};"
        )
        wl.addWidget(title_lbl)

        # ── Основная информация ───────────────────────────────────
        grp1 = QGroupBox("Основная информация")
        fl1  = QFormLayout(grp1)
        fl1.setSpacing(12)
        fl1.setContentsMargins(16, 20, 16, 16)

        self.inp_title = QLineEdit()
        self.inp_title.setPlaceholderText("Например: Перевозка оборудования Москва-СПб")
        self.inp_title.setFixedHeight(40)
        fl1.addRow("Название заявки *", self.inp_title)

        self.cmb_cargo = QComboBox()
        self.cmb_cargo.addItems(CARGO_TYPES)
        self.cmb_cargo.setFixedHeight(40)
        fl1.addRow("Тип груза *", self.cmb_cargo)

        row_wt = QHBoxLayout()
        self.spn_weight = QDoubleSpinBox()
        self.spn_weight.setRange(0.01, 99999)
        self.spn_weight.setSuffix(" т")
        self.spn_weight.setDecimals(2)
        self.spn_weight.setFixedHeight(40)
        row_wt.addWidget(self.spn_weight)
        vol_lbl = QLabel("Объём:")
        vol_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; background: transparent;")
        row_wt.addWidget(vol_lbl)
        self.spn_volume = QDoubleSpinBox()
        self.spn_volume.setRange(0, 120)
        self.spn_volume.setSuffix(" м³")
        self.spn_volume.setDecimals(1)
        self.spn_volume.setFixedHeight(40)
        row_wt.addWidget(self.spn_volume)
        fl1.addRow("Вес *", row_wt)

        wl.addWidget(grp1)

        # ── Маршрут ───────────────────────────────────────────────
        grp2 = QGroupBox("Маршрут")
        g2l  = QVBoxLayout(grp2)
        g2l.setContentsMargins(16, 20, 16, 16)
        g2l.setSpacing(10)

        fl2 = QFormLayout()
        fl2.setSpacing(10)

        self.cmb_from = QComboBox()
        self.cmb_from.setEditable(True)
        self.cmb_from.addItems(RUSSIAN_CITIES)
        self.cmb_from.setFixedHeight(40)
        fl2.addRow("Откуда *", self.cmb_from)

        self.cmb_to = QComboBox()
        self.cmb_to.setEditable(True)
        self.cmb_to.addItems(RUSSIAN_CITIES)
        self.cmb_to.setCurrentIndex(1)
        self.cmb_to.setFixedHeight(40)
        fl2.addRow("Куда *", self.cmb_to)

        self.spn_dist = QDoubleSpinBox()
        self.spn_dist.setRange(0, 99999)
        self.spn_dist.setSuffix(" км")
        self.spn_dist.setDecimals(0)
        self.spn_dist.setFixedHeight(40)
        fl2.addRow("Расстояние (км)", self.spn_dist)

        g2l.addLayout(fl2)
        wl.addWidget(grp2)

        # ── Даты и бюджет ─────────────────────────────────────────
        grp3 = QGroupBox("Даты и бюджет")
        fl3  = QFormLayout(grp3)
        fl3.setSpacing(12)
        fl3.setContentsMargins(16, 20, 16, 16)

        self.dt_pickup = QDateEdit()
        self.dt_pickup.setDate(QDate.currentDate().addDays(1))
        self.dt_pickup.setCalendarPopup(True)
        self.dt_pickup.setFixedHeight(40)
        fl3.addRow("Дата погрузки *", self.dt_pickup)

        self.dt_delivery = QDateEdit()
        self.dt_delivery.setDate(QDate.currentDate().addDays(5))
        self.dt_delivery.setCalendarPopup(True)
        self.dt_delivery.setFixedHeight(40)
        fl3.addRow("Желаемая дата доставки", self.dt_delivery)

        self.spn_budget = QDoubleSpinBox()
        self.spn_budget.setRange(0, 99_999_999)
        self.spn_budget.setSuffix(" ₽")
        self.spn_budget.setDecimals(0)
        self.spn_budget.setSingleStep(1000)
        self.spn_budget.setFixedHeight(40)
        fl3.addRow("Бюджет (₽)", self.spn_budget)

        wl.addWidget(grp3)

        # ── Дополнительно ─────────────────────────────────────────
        grp4 = QGroupBox("Дополнительная информация")
        fl4  = QVBoxLayout(grp4)
        fl4.setContentsMargins(16, 20, 16, 16)
        fl4.setSpacing(8)

        _ta_style = (
            "QTextEdit { background: #0F172A; border: 2px solid #3B82F6; border-radius: 8px; "
            "color: #F1F5F9; padding: 6px 10px; font-size: 10pt; }"
            "QTextEdit:focus { border-color: #60A5FA; }"
        )

        fl4.addWidget(_lbl("Комментарий к заказу:"))
        self.inp_comment = QTextEdit()
        self.inp_comment.setPlaceholderText("Опишите особенности груза, условия погрузки/выгрузки...")
        self.inp_comment.setFixedHeight(90)
        self.inp_comment.setStyleSheet(_ta_style)
        fl4.addWidget(self.inp_comment)

        fl4.addWidget(_lbl("Специальные требования:"))
        self.inp_special = QTextEdit()
        self.inp_special.setPlaceholderText("Температурный режим, разрешения, страхование...")
        self.inp_special.setFixedHeight(70)
        self.inp_special.setStyleSheet(_ta_style)
        fl4.addWidget(self.inp_special)

        wl.addWidget(grp4)
        wl.addSpacing(8)

        # ── Кнопки ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setStyleSheet(
            "QPushButton { background: transparent; color: #94A3B8; border: 1.5px solid #4B6280; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; }"
            "QPushButton:hover { background: rgba(148,163,184,0.1); }"
        )
        btn_cancel.setFixedSize(130, 44)
        btn_cancel.clicked.connect(self.cancelled.emit)
        btn_row.addWidget(btn_cancel)

        btn_create = QPushButton("✚ Создать заявку")
        btn_create.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: 2px solid #3B82F6; "
            "border-radius: 10px; font-size: 11pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; border-color: #60A5FA; }"
        )
        btn_create.setFixedSize(200, 48)
        btn_create.clicked.connect(self._create)
        btn_row.addWidget(btn_create)

        wl.addLayout(btn_row)

        scroll.setWidget(w)
        outer.addWidget(scroll)

    def _create(self):
        title = self.inp_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите название заявки")
            return

        from_city = self.cmb_from.currentText().strip()
        to_city   = self.cmb_to.currentText().strip()
        if not from_city or not to_city:
            QMessageBox.warning(self, "Ошибка", "Укажите маршрут")
            return
        if from_city == to_city:
            QMessageBox.warning(self, "Ошибка", "Город отправления и назначения совпадают")
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
        """Clear all fields so the form is fresh on next visit."""
        self.inp_title.clear()
        self.inp_comment.clear()
        self.inp_special.clear()
        self.cmb_from.setCurrentIndex(0)
        self.cmb_to.setCurrentIndex(1)
        self.spn_dist.setValue(0)
        self.spn_weight.setValue(0.01)
        self.spn_volume.setValue(0)
        self.spn_budget.setValue(0)
        self.dt_pickup.setDate(QDate.currentDate().addDays(1))
        self.dt_delivery.setDate(QDate.currentDate().addDays(5))


class CreateOrderDialog(QDialog):
    """Dialog wrapper around CreateOrderPage (kept for backward compat)."""
    order_created = pyqtSignal(int)

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новый заказ на перевозку")
        self.setMinimumSize(600, 700)
        self.resize(640, 760)

        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        self._page = CreateOrderPage(customer_id, self)
        self._page.order_created.connect(self._on_created)
        self._page.cancelled.connect(self.reject)
        vl.addWidget(self._page)

    def _on_created(self, order_id: int):
        self.order_created.emit(order_id)
        QMessageBox.information(
            self, "Заявка создана",
            "Заявка успешно размещена!\nПеревозчики смогут подать отклики."
        )
        self.accept()


def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
    return lbl
