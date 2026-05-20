"""Settings dialog — notifications and about."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки — FreightExchange")
        self.setMinimumSize(480, 380)
        self.resize(500, 400)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        outer.addWidget(tabs)

        tabs.addTab(self._build_notifications_tab(), "🔔 Уведомления")
        tabs.addTab(self._build_about(), "ℹ️ О программе")

    # ── Notifications ─────────────────────────────────────────────

    def _build_notifications_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(28, 24, 28, 24)
        l.setSpacing(14)

        l.addWidget(_h("Настройки уведомлений"))

        for text in [
            "Новые отклики на мои заявки",
            "Сообщения в чате",
            "Изменение статуса заказа",
            "Подтверждение платежа",
        ]:
            cb = QCheckBox(text)
            cb.setChecked(True)
            l.addWidget(cb)

        l.addStretch()
        btn = QPushButton("💾 Сохранить")
        btn.setFixedSize(160, 42)
        btn.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: 2px solid #3B82F6; "
            "border-radius: 10px; font-size: 10pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; border-color: #60A5FA; }"
            "QPushButton:pressed { background: #1E40AF; }"
        )
        l.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
        return w

    # ── About ─────────────────────────────────────────────────────

    def _build_about(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(28, 28, 28, 28)
        l.setSpacing(12)
        l.setAlignment(Qt.AlignmentFlag.AlignTop)

        logo = QLabel("🚛")
        logo.setStyleSheet("font-size: 48pt;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(logo)

        name = QLabel("FreightExchange")
        name.setStyleSheet("font-size: 20pt; font-weight: 800; color: #3B82F6;")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(name)

        for line in [
            "Биржа фрахта для малого логистического бизнеса",
            "Версия 1.0 — Дипломный проект 2026",
            "Реализовано на Python + PyQt6 + SQLite",
        ]:
            lbl = QLabel(line)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #64748B; font-size: 9pt;")
            l.addWidget(lbl)

        l.addStretch()
        return w


def _h(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("font-size: 13pt; font-weight: 700;")
    return lbl
