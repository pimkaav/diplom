"""Route picker dialog — pure Qt, no WebEngine dependency."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QWidget, QFrame, QComboBox, QDoubleSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

# Extended city list with approximate distances between key hubs
CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Омск", "Самара", "Уфа",
    "Ростов-на-Дону", "Красноярск", "Воронеж", "Пермь", "Волгоград",
    "Краснодар", "Тюмень", "Саратов", "Тольятти", "Ижевск",
    "Барнаул", "Ульяновск", "Иркутск", "Хабаровск", "Ярославль",
    "Владивосток", "Махачкала", "Томск", "Оренбург", "Кемерово",
    "Рязань", "Астрахань", "Пенза", "Липецк", "Тула",
    "Киров", "Чебоксары", "Калининград", "Брянск", "Курск",
    "Иваново", "Магнитогорск", "Улан-Удэ", "Тверь", "Белгород",
    "Ставрополь", "Сочи", "Владимир", "Чита", "Нижний Тагил",
    # Московская область
    "Балашиха", "Химки", "Подольск", "Мытищи", "Люберцы",
    "Коломна", "Сергиев Посад", "Электросталь", "Щёлково", "Реутов",
]

# Approximate inter-city distances (km) — for popular routes
_DIST: dict[frozenset, int] = {
    frozenset(["Москва", "Санкт-Петербург"]): 710,
    frozenset(["Москва", "Нижний Новгород"]): 410,
    frozenset(["Москва", "Казань"]): 820,
    frozenset(["Москва", "Екатеринбург"]): 1800,
    frozenset(["Москва", "Самара"]): 1000,
    frozenset(["Москва", "Краснодар"]): 1350,
    frozenset(["Москва", "Ростов-на-Дону"]): 1070,
    frozenset(["Москва", "Воронеж"]): 520,
    frozenset(["Москва", "Ярославль"]): 270,
    frozenset(["Москва", "Рязань"]): 200,
    frozenset(["Москва", "Тула"]): 175,
    frozenset(["Москва", "Владимир"]): 190,
    frozenset(["Москва", "Тверь"]): 165,
    frozenset(["Москва", "Брянск"]): 380,
    frozenset(["Москва", "Курск"]): 540,
    frozenset(["Москва", "Липецк"]): 490,
    frozenset(["Москва", "Иваново"]): 300,
    frozenset(["Москва", "Пенза"]): 630,
    frozenset(["Москва", "Саратов"]): 855,
    frozenset(["Москва", "Волгоград"]): 1080,
    frozenset(["Москва", "Астрахань"]): 1410,
    frozenset(["Москва", "Уфа"]): 1340,
    frozenset(["Москва", "Пермь"]): 1390,
    frozenset(["Москва", "Челябинск"]): 1780,
    frozenset(["Москва", "Тюмень"]): 2100,
    frozenset(["Москва", "Омск"]): 2680,
    frozenset(["Москва", "Новосибирск"]): 3400,
    frozenset(["Москва", "Красноярск"]): 4120,
    frozenset(["Москва", "Иркутск"]): 5200,
    frozenset(["Москва", "Хабаровск"]): 8150,
    frozenset(["Москва", "Владивосток"]): 9100,
    frozenset(["Москва", "Балашиха"]): 28,
    frozenset(["Москва", "Химки"]): 22,
    frozenset(["Москва", "Подольск"]): 42,
    frozenset(["Москва", "Мытищи"]): 20,
    frozenset(["Москва", "Люберцы"]): 18,
    frozenset(["Москва", "Коломна"]): 112,
    frozenset(["Москва", "Сергиев Посад"]): 75,
    frozenset(["Москва", "Щёлково"]): 35,
    frozenset(["Москва", "Реутов"]): 14,
    frozenset(["Санкт-Петербург", "Казань"]): 1540,
    frozenset(["Санкт-Петербург", "Екатеринбург"]): 2240,
    frozenset(["Санкт-Петербург", "Нижний Новгород"]): 1100,
    frozenset(["Казань", "Нижний Новгород"]): 415,
    frozenset(["Казань", "Уфа"]): 540,
    frozenset(["Екатеринбург", "Тюмень"]): 330,
    frozenset(["Екатеринбург", "Челябинск"]): 210,
    frozenset(["Краснодар", "Ростов-на-Дону"]): 290,
    frozenset(["Краснодар", "Сочи"]): 150,
    frozenset(["Ростов-на-Дону", "Ставрополь"]): 430,
}


def estimate_distance(city_a: str, city_b: str) -> int:
    if city_a == city_b:
        return 0
    key = frozenset([city_a, city_b])
    if key in _DIST:
        return _DIST[key]
    # Rough fallback: ~40 km per "hop" in the list
    try:
        ia = CITIES.index(city_a)
        ib = CITIES.index(city_b)
        return abs(ia - ib) * 60 + 50
    except ValueError:
        return 500


class MapPickerDialog(QDialog):
    """Route picker dialog — no WebEngine, pure Qt city selector."""
    route_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор маршрута")
        self.setMinimumSize(520, 480)
        self.resize(560, 500)
        self._result: dict | None = None
        self._build()

    def _build(self):
        self.setStyleSheet("background: #F1F5F9;")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet("background: #FFFFFF; border-bottom: 2px solid #E2E8F0;")
        hdr.setFixedHeight(64)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 0, 24, 0)
        ico = QLabel("🗺")
        ico.setStyleSheet("font-size: 22pt; background: transparent;")
        hl.addWidget(ico)
        title = QLabel("Выбор маршрута перевозки")
        title.setStyleSheet("color: #0F172A; font-size: 14pt; font-weight: 700; background: transparent;")
        hl.addWidget(title)
        hl.addStretch()
        root.addWidget(hdr)

        # Content
        content = QScrollArea()
        content.setWidgetResizable(True)
        content.setFrameShape(QFrame.Shape.NoFrame)
        content.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(inner)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(20)

        # FROM
        from_card = self._make_card("📍 Откуда (город отправки)", "#22C55E")
        from_fl = QVBoxLayout(from_card)
        from_fl.setContentsMargins(16, 16, 16, 16)
        from_fl.setSpacing(8)
        from_fl.addWidget(_lbl("Город / населённый пункт:", "#64748B"))
        self.cmb_from = QComboBox()
        self.cmb_from.setEditable(True)
        self.cmb_from.addItems(CITIES)
        self.cmb_from.setFixedHeight(42)
        self.cmb_from.setStyleSheet(self._combo_style("#22C55E"))
        self.cmb_from.currentTextChanged.connect(self._update_dist)
        from_fl.addWidget(self.cmb_from)
        cl.addWidget(from_card)

        # Arrow
        arrow = QLabel("⬇")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setStyleSheet("font-size: 20pt; color: #475569; background: transparent;")
        cl.addWidget(arrow)

        # TO
        to_card = self._make_card("🏁 Куда (город назначения)", "#EF4444")
        to_fl = QVBoxLayout(to_card)
        to_fl.setContentsMargins(16, 16, 16, 16)
        to_fl.setSpacing(8)
        to_fl.addWidget(_lbl("Город / населённый пункт:", "#94A3B8"))
        self.cmb_to = QComboBox()
        self.cmb_to.setEditable(True)
        self.cmb_to.addItems(CITIES)
        self.cmb_to.setCurrentIndex(1)
        self.cmb_to.setFixedHeight(42)
        self.cmb_to.setStyleSheet(self._combo_style("#EF4444"))
        self.cmb_to.currentTextChanged.connect(self._update_dist)
        to_fl.addWidget(self.cmb_to)
        cl.addWidget(to_card)

        # Distance
        dist_card = self._make_card("📏 Расстояние", "#60A5FA")
        dist_fl = QHBoxLayout(dist_card)
        dist_fl.setContentsMargins(16, 14, 16, 14)
        dist_fl.setSpacing(12)
        self._dist_lbl = QLabel("Выберите города для расчёта")
        self._dist_lbl.setStyleSheet("color: #64748B; font-size: 10pt; background: transparent;")
        dist_fl.addWidget(self._dist_lbl)
        dist_fl.addStretch()
        self.spn_dist = QDoubleSpinBox()
        self.spn_dist.setRange(1, 20000)
        self.spn_dist.setSuffix(" км")
        self.spn_dist.setDecimals(0)
        self.spn_dist.setValue(710)
        self.spn_dist.setFixedHeight(38)
        self.spn_dist.setFixedWidth(120)
        self.spn_dist.setStyleSheet(
            "background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 8px; "
            "color: #0F172A; padding: 6px 10px;"
        )
        dist_fl.addWidget(self.spn_dist)
        cl.addWidget(dist_card)

        cl.addStretch()
        content.setWidget(inner)
        root.addWidget(content)

        # Bottom bar
        bar = QWidget()
        bar.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        bar.setFixedHeight(60)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(20, 0, 20, 0)
        bl.setSpacing(10)
        bl.addStretch()

        btn_cancel = QPushButton("Отмена")
        btn_cancel.setProperty("cls", "secondary")
        btn_cancel.setFixedSize(110, 38)
        btn_cancel.clicked.connect(self.reject)
        bl.addWidget(btn_cancel)

        btn_ok = QPushButton("✓ Применить маршрут")
        btn_ok.setFixedSize(180, 38)
        btn_ok.clicked.connect(self._confirm)
        bl.addWidget(btn_ok)

        root.addWidget(bar)
        self._update_dist()

    def _make_card(self, title: str, accent: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"background: #FFFFFF; border: 1.5px solid {accent}; border-radius: 12px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)
        hdr = QWidget()
        hdr.setStyleSheet(
            f"background: {accent}15; border-top-left-radius: 12px; border-top-right-radius: 12px;"
        )
        hdr.setFixedHeight(36)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {accent}; font-weight: 700; font-size: 10pt; background: transparent;")
        hl.addWidget(lbl)
        vl.addWidget(hdr)
        # Return the card; caller adds content widgets directly to it
        return card

    def _combo_style(self, accent: str) -> str:
        return f"""
            QComboBox {{
                background: #FFFFFF; border: 1.5px solid #CBD5E1;
                border-radius: 8px; padding: 8px 12px; color: #0F172A; font-size: 11pt;
            }}
            QComboBox:focus {{ border-color: {accent}; }}
            QComboBox QAbstractItemView {{
                background: #FFFFFF; border: 1px solid #CBD5E1;
                color: #0F172A; selection-background-color: {accent}33;
            }}
        """

    def _update_dist(self):
        a = self.cmb_from.currentText().strip()
        b = self.cmb_to.currentText().strip()
        if a and b and a != b:
            d = estimate_distance(a, b)
            self.spn_dist.setValue(d)
            self._dist_lbl.setText(f"~{d} км (приблизительно)")
            self._dist_lbl.setStyleSheet("color: #2563EB; font-size: 10pt; font-weight: 600; background: transparent;")
        else:
            self._dist_lbl.setText("Выберите города для расчёта")
            self._dist_lbl.setStyleSheet("color: #64748B; font-size: 10pt; background: transparent;")

    def _confirm(self):
        from_city = self.cmb_from.currentText().strip()
        to_city   = self.cmb_to.currentText().strip()
        if not from_city or not to_city:
            from ui.styles import show_warning
            show_warning(self, "Ошибка", "Выберите города отправки и назначения")
            return
        if from_city == to_city:
            from ui.styles import show_warning
            show_warning(self, "Ошибка", "Город отправки и назначения не могут совпадать")
            return

        data = {
            "from": {"address": from_city, "lat": 0, "lng": 0},
            "to":   {"address": to_city,   "lat": 0, "lng": 0},
            "distance": self.spn_dist.value(),
        }
        self._result = data
        self.route_selected.emit(data)
        self.accept()

    def result_data(self) -> dict | None:
        return self._result


def _lbl(text: str, color: str = "#64748B") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {color}; font-size: 9pt; background: transparent;")
    return lbl
