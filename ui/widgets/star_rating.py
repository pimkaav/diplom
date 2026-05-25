from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import pyqtSignal


class StarRatingWidget(QWidget):
    rating_changed = pyqtSignal(int)

    def __init__(self, rating: int = 0, editable: bool = True, parent=None):
        super().__init__(parent)
        self._rating = rating
        self._editable = editable
        self._stars: list[QPushButton] = []
        self.setStyleSheet("background: transparent;")
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)
        for i in range(1, 6):
            btn = QPushButton("★")
            btn.setFixedSize(40, 40)
            btn.setFlat(True)
            btn.setStyleSheet(
                "QPushButton { font-size: 24pt; border: none; background: transparent; "
                "padding: 0; margin: 0; }"
            )
            if self._editable:
                btn.setCursor(self.cursor().shape())
                btn.clicked.connect(lambda _, v=i: self._on_click(v))
                btn.enterEvent = lambda e, v=i: self._hover(v)
                btn.leaveEvent = lambda e: self._refresh()
            self._stars.append(btn)
            layout.addWidget(btn)
        layout.addStretch()
        self._refresh()

    def _on_click(self, value: int):
        self._rating = value
        self._refresh()
        self.rating_changed.emit(value)

    def _hover(self, value: int):
        for i, btn in enumerate(self._stars):
            color = "#F59E0B" if i < value else "#CBD5E1"
            btn.setStyleSheet(
                f"QPushButton {{ font-size: 24pt; border: none; background: transparent; "
                f"color: {color}; padding: 0; margin: 0; }}"
            )

    def _refresh(self):
        for i, btn in enumerate(self._stars):
            color = "#F59E0B" if i < self._rating else "#94A3B8"
            btn.setStyleSheet(
                f"QPushButton {{ font-size: 24pt; border: none; background: transparent; "
                f"color: {color}; padding: 0; margin: 0; }}"
            )

    def value(self) -> int:
        return self._rating

    def set_value(self, v: int):
        self._rating = v
        self._refresh()
