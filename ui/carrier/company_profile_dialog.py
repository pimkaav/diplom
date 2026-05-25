from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QScrollArea,
    QFrame, QWidget, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox
)
from ui.styles import show_info, show_warning, show_question
from PyQt6.QtCore import Qt

from database.models import CompanyModel, TruckModel
from ui.styles import C_CONTENT_BG, C_CARD_BG, C_BORDER, C_TEXT, C_TEXT_MUTED, C_SUCCESS, C_DANGER

TRUCK_CATEGORIES = [
    "Тентованные (Шторные)",
    "Рефрижераторы",
    "Бортовые",
    "Фургоны",
    "Самосвалы",
    "Цистерны",
    "Контейнеровозы",
    "Автовозы",
    "Зерновозы",
    "Манипулятор",
    "Платформа",
    "Негабаритные перевозки",
    "Тяжеловесные",
    "Изотермы",
]

TRUCK_BRANDS = [
    "Mercedes-Benz", "Volvo", "Scania", "MAN", "DAF",
    "Iveco", "Renault Trucks", "КАМАЗ", "МАЗ", "ГАЗ",
    "Газель", "Liebherr", "Schmitz Cargobull", "Krone",
    "Freightliner", "Kenworth", "Peterbilt", "Другое",
]

CARGO_TYPES_TRUCK = [
    "Тентованные", "Рефрижераторы", "Бортовые", "Фургоны",
    "Самосвалы", "Зерновозы", "Цистерны", "Платформа",
    "Манипулятор", "Изотермы", "Контейнер", "Другое",
]


class CompanyProfileDialog(QDialog):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id  = user_id
        self.existing = CompanyModel.get_by_user(user_id)
        title = "Редактировать профиль компании" if self.existing else "Создать профиль компании"
        self.setWindowTitle(title)
        self.setMinimumSize(680, 800)
        self._build()
        self.showMaximized()

    # ── Reusable input styles ──────────────────────────────────────
    _sty_inp = (
        "QLineEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
        "color: #0F172A; padding: 4px 12px; font-size: 11pt; }"
        "QLineEdit:focus { border-color: #2563EB; background: #EFF6FF; }"
    )
    _sty_ta = (
        "QTextEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
        "color: #0F172A; padding: 6px 12px; font-size: 11pt; }"
        "QTextEdit:focus { border-color: #2563EB; background: #EFF6FF; }"
    )
    _sty_cmb = (
        "QComboBox { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
        "color: #0F172A; padding: 4px 12px; font-size: 11pt; }"
        "QComboBox:focus { border-color: #2563EB; }"
        "QComboBox::drop-down { border: none; width: 22px; background: transparent; }"
        "QComboBox QAbstractItemView { background: #FFFFFF; color: #0F172A; "
        "border: 1.5px solid #CBD5E1; selection-background-color: #EFF6FF; "
        "selection-color: #2563EB; font-size: 11pt; outline: none; }"
        "QComboBox QAbstractItemView::item { color: #0F172A; padding: 8px 12px; min-height: 28px; }"
        "QComboBox QAbstractItemView::item:selected { background: #EFF6FF; color: #2563EB; }"
    )
    _sty_spn = (
        "QSpinBox, QDoubleSpinBox { background: #FFFFFF; border: 2px solid #CBD5E1; "
        "border-radius: 8px; color: #0F172A; padding: 4px 12px; font-size: 11pt; }"
        "QSpinBox:focus, QDoubleSpinBox:focus { border-color: #2563EB; background: #EFF6FF; }"
    )

    # ── GroupBox title style (explicit, always visible) ───────────
    _sty_grp = (
        "QGroupBox { background: #F1F5F9; border: 1.5px solid #E2E8F0; border-radius: 10px; "
        "margin-top: 18px; padding-top: 14px; }"
        "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; "
        "left: 14px; top: -2px; padding: 0 6px; "
        "color: #334155; font-size: 11pt; font-weight: 700; background: #F1F5F9; }"
        "QLabel { background: transparent; border: none; color: #0F172A; }"
    )
    _sty_chk = (
        "QCheckBox { color: #0F172A; font-size: 11pt; background: transparent; "
        "border: none; spacing: 8px; }"
        "QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #CBD5E1; "
        "border-radius: 4px; background: #FFFFFF; }"
        "QCheckBox::indicator:checked { background: #2563EB; border-color: #2563EB; }"
        "QCheckBox::indicator:hover { border-color: #2563EB; }"
    )

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
        wl.setContentsMargins(24, 24, 24, 24)
        wl.setSpacing(16)

        hdr = QLabel("Профиль компании-перевозчика")
        hdr.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT}; background: transparent;")
        wl.addWidget(hdr)

        e = self.existing or {}

        # ── Основные данные ───────────────────────────────────────
        grp1 = QGroupBox("Основные данные")
        grp1.setStyleSheet(self._sty_grp)
        fl1  = QFormLayout(grp1)
        fl1.setSpacing(12)
        fl1.setContentsMargins(16, 20, 16, 16)

        self.inp_name = QLineEdit(e.get("company_name", ""))
        self.inp_name.setPlaceholderText("ООО ТрансГрупп")
        self.inp_name.setFixedHeight(42)
        self.inp_name.setStyleSheet(self._sty_inp)
        fl1.addRow("Название компании *", self.inp_name)

        self.inp_desc = QTextEdit(e.get("description", ""))
        self.inp_desc.setPlaceholderText("Опишите вашу компанию, опыт работы, преимущества...")
        self.inp_desc.setFixedHeight(90)
        self.inp_desc.setStyleSheet(self._sty_ta)
        fl1.addRow("Описание", self.inp_desc)

        row_inn = QHBoxLayout()
        self.inp_inn = QLineEdit(e.get("inn", ""))
        self.inp_inn.setPlaceholderText("1234567890")
        self.inp_inn.setFixedHeight(42)
        self.inp_inn.setStyleSheet(self._sty_inp)
        row_inn.addWidget(self.inp_inn)
        row_inn.addWidget(QLabel(" Лицензия:"))
        self.inp_license = QLineEdit(e.get("license_number", ""))
        self.inp_license.setFixedHeight(42)
        self.inp_license.setStyleSheet(self._sty_inp)
        row_inn.addWidget(self.inp_license)
        fl1.addRow("ИНН", row_inn)

        wl.addWidget(grp1)

        # ── Ценообразование ───────────────────────────────────────
        grp2 = QGroupBox("Ценообразование и автопарк")
        grp2.setStyleSheet(self._sty_grp)
        fl2  = QFormLayout(grp2)
        fl2.setSpacing(12)
        fl2.setContentsMargins(16, 20, 16, 16)

        pricing_row = QHBoxLayout()
        pricing_row.setSpacing(12)

        self.spn_pkm = QDoubleSpinBox()
        self.spn_pkm.setRange(1, 9999)
        self.spn_pkm.setSuffix(" ₽/км")
        self.spn_pkm.setDecimals(0)
        self.spn_pkm.setValue(e.get("price_per_km", 40))
        self.spn_pkm.setFixedSize(140, 42)
        self.spn_pkm.setStyleSheet(self._sty_spn)
        pricing_row.addWidget(self.spn_pkm)

        sep_lbl = QLabel("|")
        sep_lbl.setStyleSheet("color: #94A3B8; font-size: 14pt; background: transparent;")
        pricing_row.addWidget(sep_lbl)

        trucks_lbl = QLabel("Автомобилей:")
        trucks_lbl.setStyleSheet("color: #64748B; font-size: 10pt; background: transparent;")
        pricing_row.addWidget(trucks_lbl)

        self.spn_trucks = QSpinBox()
        self.spn_trucks.setRange(0, 9999)
        self.spn_trucks.setValue(e.get("truck_count", 0))
        self.spn_trucks.setFixedSize(100, 42)
        self.spn_trucks.setStyleSheet(self._sty_spn)
        pricing_row.addWidget(self.spn_trucks)
        pricing_row.addStretch()

        fl2.addRow("Цена/км  ·  Парк", pricing_row)

        wl.addWidget(grp2)

        # ── Типы транспорта ───────────────────────────────────────
        grp3 = QGroupBox("Типы транспорта")
        grp3.setStyleSheet(self._sty_grp)
        gl3  = QVBoxLayout(grp3)
        gl3.setContentsMargins(16, 20, 16, 16)
        gl3.setSpacing(6)

        existing_cats = e.get("truck_categories", "").split(", ") if e.get("truck_categories") else []
        self._cat_checks: list[QCheckBox] = []

        # 2-column layout for checkboxes
        row_l = None
        for i, cat in enumerate(TRUCK_CATEGORIES):
            if i % 2 == 0:
                row_l = QHBoxLayout()
                gl3.addLayout(row_l)
            cb = QCheckBox(cat)
            cb.setChecked(cat in existing_cats)
            cb.setStyleSheet(self._sty_chk)
            self._cat_checks.append(cb)
            row_l.addWidget(cb)
        if len(TRUCK_CATEGORIES) % 2 == 1 and row_l:
            row_l.addStretch()

        wl.addWidget(grp3)

        # ── Автопарк ─────────────────────────────────────────────
        fleet_grp = QGroupBox("Автопарк (конкретные машины)")
        fleet_grp.setStyleSheet(self._sty_grp)
        fleet_vl  = QVBoxLayout(fleet_grp)
        fleet_vl.setContentsMargins(16, 16, 16, 16)
        fleet_vl.setSpacing(12)

        # Table of trucks
        self._truck_table = QTableWidget()
        self._truck_table.setColumnCount(7)
        self._truck_table.setHorizontalHeaderLabels(
            ["Марка", "Модель", "Год", "Гос. номер", "Тип груза", "Тоннаж", ""]
        )
        self._truck_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._truck_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._truck_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._truck_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._truck_table.verticalHeader().setVisible(False)
        self._truck_table.setAlternatingRowColors(True)
        self._truck_table.setFixedHeight(200)
        self._truck_table.setStyleSheet("""
            QTableWidget { background: #FFFFFF; alternate-background-color: #F8FAFC;
                border: 1px solid #E2E8F0; border-radius: 8px;
                gridline-color: #E2E8F0; color: #0F172A; font-size: 11pt; outline: none; }
            QTableWidget::item { padding: 6px 10px; border: none; color: #0F172A; }
            QTableWidget::item:selected { background: #EFF6FF; color: #1D4ED8; }
            QHeaderView::section { background: #F1F5F9; color: #334155; font-weight: 700;
                font-size: 10pt; padding: 7px 10px; border: none;
                border-bottom: 2px solid #E2E8F0; border-right: 1px solid #E2E8F0; }
        """)
        fleet_vl.addWidget(self._truck_table)

        # Add truck form
        add_frame = QFrame()
        add_frame.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )
        add_fl = QVBoxLayout(add_frame)
        add_fl.setContentsMargins(14, 12, 14, 12)
        add_fl.setSpacing(8)

        add_lbl = QLabel("Добавить автомобиль:")
        add_lbl.setStyleSheet(f"font-weight: 700; color: {C_TEXT}; font-size: 10pt;")
        add_fl.addWidget(add_lbl)

        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self._inp_brand = QComboBox()
        self._inp_brand.setEditable(True)
        self._inp_brand.addItems(TRUCK_BRANDS)
        self._inp_brand.setFixedHeight(40)
        self._inp_brand.setPlaceholderText("Марка")
        self._inp_brand.setStyleSheet(self._sty_cmb)
        row1.addWidget(self._inp_brand)

        self._inp_model = QLineEdit()
        self._inp_model.setPlaceholderText("Модель (напр. Actros 1845)")
        self._inp_model.setFixedHeight(40)
        self._inp_model.setStyleSheet(self._sty_inp)
        row1.addWidget(self._inp_model)

        self._inp_year = QSpinBox()
        self._inp_year.setRange(2000, 2026)
        self._inp_year.setValue(2022)
        self._inp_year.setFixedWidth(100)
        self._inp_year.setFixedHeight(40)
        self._inp_year.setStyleSheet(self._sty_spn)
        row1.addWidget(self._inp_year)
        add_fl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self._inp_plate = QLineEdit()
        self._inp_plate.setPlaceholderText("Гос. номер (А 123 МК 77)")
        self._inp_plate.setFixedHeight(40)
        self._inp_plate.setStyleSheet(self._sty_inp)
        row2.addWidget(self._inp_plate)

        self._inp_cargo_type = QComboBox()
        self._inp_cargo_type.addItems(CARGO_TYPES_TRUCK)
        self._inp_cargo_type.setFixedHeight(40)
        self._inp_cargo_type.setStyleSheet(self._sty_cmb)
        row2.addWidget(self._inp_cargo_type)

        self._inp_capacity = QDoubleSpinBox()
        self._inp_capacity.setRange(0.5, 60.0)
        self._inp_capacity.setValue(20.0)
        self._inp_capacity.setSuffix(" т")
        self._inp_capacity.setDecimals(1)
        self._inp_capacity.setFixedWidth(110)
        self._inp_capacity.setFixedHeight(40)
        self._inp_capacity.setStyleSheet(self._sty_spn)
        row2.addWidget(self._inp_capacity)

        btn_add_truck = QPushButton("+ Добавить")
        btn_add_truck.setFixedSize(120, 36)
        btn_add_truck.setStyleSheet(
            "QPushButton { background: #16A34A; color: white; border: none; "
            "border-radius: 8px; font-size: 10pt; font-weight: 700; }"
            "QPushButton:hover { background: #15803D; }"
        )
        btn_add_truck.clicked.connect(self._add_truck)
        row2.addWidget(btn_add_truck)
        add_fl.addLayout(row2)

        fleet_vl.addWidget(add_frame)
        wl.addWidget(fleet_grp)

        # ── Регионы ───────────────────────────────────────────────
        grp4 = QGroupBox("Регионы работы")
        grp4.setStyleSheet(self._sty_grp)
        fl4  = QFormLayout(grp4)
        fl4.setSpacing(12)
        fl4.setContentsMargins(16, 20, 16, 16)

        self.inp_cities = QLineEdit(e.get("operating_cities", ""))
        self.inp_cities.setPlaceholderText("Москва, Санкт-Петербург, Екатеринбург...")
        self.inp_cities.setFixedHeight(42)
        self.inp_cities.setStyleSheet(self._sty_inp)
        fl4.addRow("Города / Регионы работы", self.inp_cities)

        wl.addWidget(grp4)

        # ── Контакты ──────────────────────────────────────────────
        grp5 = QGroupBox("Контактная информация")
        grp5.setStyleSheet(self._sty_grp)
        fl5  = QFormLayout(grp5)
        fl5.setSpacing(12)
        fl5.setContentsMargins(16, 20, 16, 16)

        self.inp_phone = QLineEdit(e.get("phone", ""))
        self.inp_phone.setPlaceholderText("+7 (___) ___-__-__")
        self.inp_phone.setFixedHeight(42)
        self.inp_phone.setStyleSheet(self._sty_inp)
        fl5.addRow("Телефон", self.inp_phone)

        self.inp_email = QLineEdit(e.get("email", ""))
        self.inp_email.setPlaceholderText("info@company.ru")
        self.inp_email.setFixedHeight(42)
        self.inp_email.setStyleSheet(self._sty_inp)
        fl5.addRow("Email", self.inp_email)

        self.inp_website = QLineEdit(e.get("website", ""))
        self.inp_website.setPlaceholderText("https://company.ru")
        self.inp_website.setFixedHeight(42)
        self.inp_website.setStyleSheet(self._sty_inp)
        fl5.addRow("Сайт", self.inp_website)

        wl.addWidget(grp5)
        wl.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setStyleSheet(
            "QPushButton { background: transparent; color: #64748B; border: 1.5px solid #CBD5E1; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; }"
            "QPushButton:hover { background: #F1F5F9; }"
        )
        btn_cancel.setFixedSize(120, 42)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Сохранить профиль")
        btn_save.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: 2px solid #3B82F6; "
            "border-radius: 8px; font-size: 11pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_save.setFixedSize(220, 46)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        wl.addLayout(btn_row)

        scroll.setWidget(w)
        outer.addWidget(scroll)

        self._load_trucks()

    def _load_trucks(self):
        trucks = TruckModel.get_by_carrier(self.user_id)
        self._truck_table.setRowCount(0)
        for t in trucks:
            row = self._truck_table.rowCount()
            self._truck_table.insertRow(row)
            self._truck_table.setItem(row, 0, QTableWidgetItem(t.get("brand", "")))
            self._truck_table.setItem(row, 1, QTableWidgetItem(t.get("model", "")))
            self._truck_table.setItem(row, 2, QTableWidgetItem(str(t.get("year", ""))))
            self._truck_table.setItem(row, 3, QTableWidgetItem(t.get("plate_number", "")))
            self._truck_table.setItem(row, 4, QTableWidgetItem(t.get("cargo_type", "")))
            self._truck_table.setItem(row, 5, QTableWidgetItem(f"{t.get('capacity_tons',0)} т"))

            cell = QWidget()
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(4, 2, 4, 2)
            btn_del = QPushButton("✕")
            btn_del.setProperty("cls", "danger")
            btn_del.setFixedSize(30, 26)
            btn_del.clicked.connect(lambda _, tid=t["id"]: self._del_truck(tid))
            cl.addWidget(btn_del)
            self._truck_table.setCellWidget(row, 6, cell)

    def _add_truck(self):
        brand = self._inp_brand.currentText().strip()
        model = self._inp_model.text().strip()
        if not brand or not model:
            show_warning(self, "Ошибка", "Введите марку и модель автомобиля")
            return
        TruckModel.add(
            self.user_id, brand, model,
            self._inp_year.value(),
            self._inp_plate.text().strip(),
            self._inp_cargo_type.currentText(),
            self._inp_capacity.value(),
            82.0,
        )
        self._inp_model.clear()
        self._inp_plate.clear()
        self._load_trucks()

    def _del_truck(self, truck_id: int):
        if show_question(self, "Удалить?", "Удалить автомобиль из автопарка?"):
            TruckModel.delete(truck_id)
            self._load_trucks()

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            show_warning(self, "Ошибка", "Введите название компании")
            return

        selected_cats = [cb.text() for cb in self._cat_checks if cb.isChecked()]
        truck_count   = TruckModel.count(self.user_id) or self.spn_trucks.value()

        data = {
            "company_name":     name,
            "description":      self.inp_desc.toPlainText().strip(),
            "truck_count":      truck_count,
            "truck_categories": ", ".join(selected_cats),
            "price_per_km":     self.spn_pkm.value(),
            "operating_cities": self.inp_cities.text().strip(),
            "phone":            self.inp_phone.text().strip(),
            "email":            self.inp_email.text().strip(),
            "website":          self.inp_website.text().strip(),
            "inn":              self.inp_inn.text().strip(),
            "license_number":   self.inp_license.text().strip(),
        }

        CompanyModel.upsert(self.user_id, data)
        show_info(self, "Готово", "Профиль компании сохранён успешно!")
        self.accept()
