"""Simple balance top-up dialog."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDoubleSpinBox, QFrame, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import UserModel
from ui.styles import C_CARD_BG, C_BORDER, C_TEXT, C_TEXT_MUTED, C_PRIMARY, C_CONTENT_BG
from utils.helpers import fmt_money


class BalanceDialog(QDialog):
    balance_updated = pyqtSignal(float)   # emits new balance

    def __init__(self, user: dict, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Пополнение баланса")
        self.setFixedSize(420, 380)
        self._build()

    def _build(self):
        self.setStyleSheet(f"background: {C_CONTENT_BG};")
        l = QVBoxLayout(self)
        l.setContentsMargins(28, 28, 28, 28)
        l.setSpacing(16)

        # Header
        hdr = QLabel("💳 Пополнение баланса")
        hdr.setStyleSheet(f"font-size: 16pt; font-weight: 800; color: {C_TEXT};")
        l.addWidget(hdr)

        # Current balance card
        bal_card = QFrame()
        bal_card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )
        bcl = QVBoxLayout(bal_card)
        bcl.setContentsMargins(20, 16, 20, 16)
        bcl.setSpacing(4)
        bcl.addWidget(_muted("Текущий баланс"))
        current = UserModel.get_balance(self.user["id"])
        self._bal_lbl = QLabel(fmt_money(current))
        self._bal_lbl.setStyleSheet(f"font-size: 24pt; font-weight: 800; color: {C_PRIMARY};")
        bcl.addWidget(self._bal_lbl)
        l.addWidget(bal_card)

        # Quick amounts
        l.addWidget(_muted("Быстрое пополнение:"))
        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)
        for amount in [5000, 10000, 25000, 50000]:
            btn = QPushButton(fmt_money(amount))
            btn.setStyleSheet(
                "QPushButton { background: #EFF6FF; color: #2563EB; border: 2px solid #93C5FD; "
                "border-radius: 10px; font-size: 10pt; font-weight: 700; }"
                "QPushButton:hover { background: #2563EB; color: white; border-color: #2563EB; }"
            )
            btn.setFixedSize(96, 42)
            btn.clicked.connect(lambda _, a=amount: self._set_amount(a))
            quick_row.addWidget(btn)
        quick_row.addStretch()
        l.addLayout(quick_row)

        # Custom amount
        l.addWidget(_muted("Или введите сумму:"))
        self.spn_amount = QDoubleSpinBox()
        self.spn_amount.setRange(100, 10_000_000)
        self.spn_amount.setSuffix(" ₽")
        self.spn_amount.setDecimals(0)
        self.spn_amount.setSingleStep(1000)
        self.spn_amount.setValue(10000)
        self.spn_amount.setFixedHeight(48)
        self.spn_amount.setStyleSheet(
            "QDoubleSpinBox { background: #FFFFFF; border: 2px solid #2563EB; border-radius: 10px; "
            "color: #0F172A; padding: 4px 12px; font-size: 14pt; font-weight: 700; }"
            "QDoubleSpinBox:focus { border-color: #1D4ED8; background: #EFF6FF; }"
            "QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 22px; }"
        )
        l.addWidget(self.spn_amount)

        # Info
        info = QLabel(
            "ℹ️  Средства зачисляются мгновенно.\n"
            "Используйте баланс для оплаты заказов."
        )
        info.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
        info.setWordWrap(True)
        l.addWidget(info)

        l.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setStyleSheet(
            "QPushButton { background: transparent; color: #64748B; border: 1.5px solid #CBD5E1; "
            "border-radius: 8px; font-size: 10pt; font-weight: 600; }"
            "QPushButton:hover { background: #F1F5F9; }"
        )
        btn_cancel.setFixedSize(110, 42)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_ok = QPushButton("💳 Пополнить")
        btn_ok.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: 2px solid #3B82F6; "
            "border-radius: 8px; font-size: 11pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_ok.setFixedSize(160, 44)
        btn_ok.clicked.connect(self._topup)
        btn_row.addWidget(btn_ok)
        l.addLayout(btn_row)

    def _set_amount(self, amount: float):
        self.spn_amount.setValue(amount)

    def _topup(self):
        amount = self.spn_amount.value()
        new_bal = UserModel.add_balance(self.user["id"], amount)
        self.user["balance"] = new_bal
        self._bal_lbl.setText(fmt_money(new_bal))
        self.balance_updated.emit(new_bal)
        from ui.styles import show_info
        show_info(
            self, "Баланс пополнен",
            f"На ваш счёт зачислено {fmt_money(amount)}.\n"
            f"Текущий баланс: {fmt_money(new_bal)}"
        )
        self.accept()


def _muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #64748B; font-size: 9pt; font-weight: 700; text-transform: uppercase;"
    )
    return lbl
