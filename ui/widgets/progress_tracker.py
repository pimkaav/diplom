"""Horizontal step-by-step order progress widget."""
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt

STEPS = [
    ("waiting",          "📋", "Создан"),
    ("vehicle_assigned", "🚛", "Машина\nназначена"),
    ("dispatched",       "📦", "Груз\nотправлен"),
    ("in_transit",       "🚚", "В пути"),
    ("arrived",          "📍", "Прибыл"),
    ("completed",        "✅", "Завершено"),
]

_STEP_INDEX = {s[0]: i for i, s in enumerate(STEPS)}


class ProgressTracker(QWidget):
    def __init__(self, current_status: str = "waiting", parent=None):
        super().__init__(parent)
        self.setMinimumHeight(90)
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().verticalPolicy(),
        )
        self._status = current_status
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        cur_idx = _STEP_INDEX.get(self._status, 0)

        for i, (key, icon, label) in enumerate(STEPS):
            is_done   = i < cur_idx
            is_active = i == cur_idx

            # Step circle
            step_col = QVBoxLayout()
            step_col.setSpacing(6)
            step_col.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            # Connector line before circle
            row = QHBoxLayout()
            row.setSpacing(0)
            row.setContentsMargins(0, 0, 0, 0)

            if i > 0:
                line = QFrame()
                line.setFixedHeight(3)
                line.setStyleSheet(
                    f"background: {'#16A34A' if is_done or is_active else '#E2E8F0'}; border-radius: 2px;"
                )
                row.addWidget(line, 1)

            circle = QLabel(icon if is_done or is_active else str(i + 1))
            circle.setFixedSize(40, 40)
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if is_active:
                bg, color, border = "#2563EB", "white", "3px solid #93C5FD"
            elif is_done:
                bg, color, border = "#16A34A", "white", "none"
            else:
                bg, color, border = "#F1F5F9", "#94A3B8", "2px solid #E2E8F0"

            circle.setStyleSheet(
                f"background: {bg}; color: {color}; border-radius: 20px; "
                f"border: {border}; font-size: 14pt;"
            )
            row.addWidget(circle)

            if i < len(STEPS) - 1:
                line2 = QFrame()
                line2.setFixedHeight(3)
                line2.setStyleSheet(
                    f"background: {'#16A34A' if is_done else '#E2E8F0'}; border-radius: 2px;"
                )
                row.addWidget(line2, 1)

            step_col.addLayout(row)

            # Label
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font_color = "#2563EB" if is_active else ("#16A34A" if is_done else "#64748B")
            lbl.setStyleSheet(
                f"color: {font_color}; font-size: 8pt; "
                f"font-weight: {'700' if is_active else '400'};"
            )
            lbl.setWordWrap(True)
            step_col.addWidget(lbl)

            container = QWidget()
            container.setLayout(step_col)
            layout.addWidget(container, 1)

    def set_status(self, status: str):
        if status != self._status:
            self._status = status
            # Rebuild widget
            old = self.layout()
            if old:
                while old.count():
                    item = old.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            self._build()
