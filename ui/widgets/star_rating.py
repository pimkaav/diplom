from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal


class StarRatingWidget(QWidget):
    rating_changed = pyqtSignal(int)

    def __init__(self, rating: int = 0, editable: bool = True, parent=None):
        super().__init__(parent)
        self._rating = rating
        self._editable = editable
        self._stars: list[QPushButton] = []
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        for i in range(1, 6):
            btn = QPushButton("★")
            btn.setFixedSize(28, 28)
            btn.setFlat(True)
            btn.setStyleSheet("font-size: 18pt; border: none; background: transparent;")
            if self._editable:
                btn.setCursor(self.cursor().shape())
                btn.clicked.connect(lambda _, v=i: self._on_click(v))
                btn.enterEvent = lambda e, v=i: self._hover(v)
                btn.leaveEvent = lambda e: self._refresh()
            self._stars.append(btn)
            layout.addWidget(btn)
        self._refresh()

    def _on_click(self, value: int):
        self._rating = value
        self._refresh()
        self.rating_changed.emit(value)

    def _hover(self, value: int):
        for i, btn in enumerate(self._stars):
            btn.setStyleSheet(
                f"font-size: 18pt; border: none; background: transparent; "
                f"color: {'#F59E0B' if i < value else '#475569'};"
            )

    def _refresh(self):
        for i, btn in enumerate(self._stars):
            btn.setStyleSheet(
                f"font-size: 18pt; border: none; background: transparent; "
                f"color: {'#F59E0B' if i < self._rating else '#475569'};"
            )

    def value(self) -> int:
        return self._rating

    def set_value(self, v: int):
        self._rating = v
        self._refresh()
