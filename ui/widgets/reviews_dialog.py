"""Reviews dialog — view and write reviews for a carrier."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from database.models import ReviewModel
from utils.helpers import fmt_date
from ui.styles import show_info, show_warning


class StarRatingWidget(QWidget):
    """Interactive 1–5 star selector."""
    rating_changed = pyqtSignal(int)

    def __init__(self, initial: int = 5, parent=None):
        super().__init__(parent)
        self._rating = initial
        self.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(self)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(4)
        self._btns: list[QPushButton] = []
        for i in range(1, 6):
            btn = QPushButton("★")
            btn.setFixedSize(34, 34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("font-size: 20pt; background: transparent; border: none; padding: 0;")
            btn.clicked.connect(lambda _, v=i: self._set(v))
            self._btns.append(btn)
            hl.addWidget(btn)
        hl.addStretch()
        self._refresh()

    def _set(self, val: int):
        self._rating = val
        self._refresh()
        self.rating_changed.emit(val)

    def _refresh(self):
        for i, btn in enumerate(self._btns):
            color = "#F59E0B" if i < self._rating else "#CBD5E1"
            btn.setStyleSheet(
                f"font-size: 20pt; color: {color}; "
                "background: transparent; border: none; padding: 0;"
            )

    def value(self) -> int:
        return self._rating


class ReviewCard(QFrame):
    def __init__(self, review: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; }"
        )
        vl = QVBoxLayout(self)
        vl.setContentsMargins(18, 14, 18, 14)
        vl.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        name_lbl = QLabel(review.get("reviewer_name") or "Пользователь")
        name_lbl.setStyleSheet("font-weight: 700; font-size: 11pt; color: #0F172A;")
        hdr.addWidget(name_lbl)
        hdr.addStretch()
        date_lbl = QLabel(fmt_date(review.get("created_at", "")))
        date_lbl.setStyleSheet("color: #64748B; font-size: 9pt;")
        hdr.addWidget(date_lbl)
        vl.addLayout(hdr)

        # Stars row
        rating = review.get("rating", 5)
        stars_row = QHBoxLayout()
        stars_row.setSpacing(2)
        for i in range(1, 6):
            s = QLabel("★" if i <= rating else "☆")
            s.setStyleSheet(
                f"font-size: 14pt; color: {'#F59E0B' if i <= rating else '#CBD5E1'}; "
                "background: transparent;"
            )
            stars_row.addWidget(s)
        stars_row.addSpacing(8)
        rating_txt = QLabel(f"{rating}/5")
        rating_txt.setStyleSheet("color: #F59E0B; font-weight: 700; font-size: 10pt;")
        stars_row.addWidget(rating_txt)
        stars_row.addStretch()
        vl.addLayout(stars_row)

        # Comment text
        comment = review.get("comment", "")
        if comment:
            txt = QLabel(comment)
            txt.setStyleSheet("color: #0F172A; font-size: 10pt;")
            txt.setWordWrap(True)
            vl.addWidget(txt)


class ReviewsDialog(QDialog):
    """View all reviews for a carrier + optional write-review form."""

    def __init__(self, carrier_user_id: int, carrier_name: str,
                 current_user: dict,
                 completed_order_id: int | None = None,
                 parent=None):
        super().__init__(parent)
        self.carrier_uid        = carrier_user_id
        self.carrier_name       = carrier_name
        self.current_user       = current_user
        self.completed_order_id = completed_order_id
        self._rating            = 5

        self.setWindowTitle(f"Отзывы — {carrier_name}")
        self.setMinimumSize(600, 680)
        self.resize(640, 720)
        self._build()

    def _build(self):
        self.setStyleSheet("background: #F1F5F9;")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────
        hdr_w = QWidget()
        hdr_w.setStyleSheet("background: #FFFFFF; border-bottom: 2px solid #E2E8F0;")
        hdr_w.setFixedHeight(68)
        hl = QHBoxLayout(hdr_w)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.setSpacing(12)

        ico = QLabel("⭐")
        ico.setStyleSheet("font-size: 22pt; background: transparent;")
        hl.addWidget(ico)

        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        title_lbl = QLabel(f"Отзывы о «{self.carrier_name}»")
        title_lbl.setStyleSheet("color: #0F172A; font-size: 13pt; font-weight: 700;")
        info_col.addWidget(title_lbl)

        reviews = ReviewModel.get_by_user(self.carrier_uid)
        if reviews:
            avg = sum(r["rating"] for r in reviews) / len(reviews)
            sub_lbl = QLabel(f"Средняя оценка: {avg:.1f} ★  ·  {len(reviews)} отзывов")
        else:
            sub_lbl = QLabel("Отзывов пока нет — будьте первым!")
        sub_lbl.setStyleSheet("color: #64748B; font-size: 9pt;")
        info_col.addWidget(sub_lbl)
        hl.addLayout(info_col)
        hl.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(34, 34)
        btn_close.setStyleSheet(
            "color: #94A3B8; background: transparent; border: none; font-size: 16pt;"
        )
        btn_close.clicked.connect(self.reject)
        hl.addWidget(btn_close)
        root.addWidget(hdr_w)

        # ── Scroll body ───────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(inner)
        vl.setContentsMargins(24, 24, 24, 24)
        vl.setSpacing(16)

        # ── Write-review card ─────────────────────────────────────
        can_review = (
            self.current_user.get("role") == "customer"
            and self.completed_order_id is not None
            and not ReviewModel.already_reviewed(
                self.current_user["id"],
                self.carrier_uid,
                self.completed_order_id,
            )
        )

        if can_review:
            write_card = QFrame()
            write_card.setStyleSheet(
                "QFrame { background: #EFF6FF; border: 1.5px solid #2563EB; border-radius: 14px; }"
            )
            wl = QVBoxLayout(write_card)
            wl.setContentsMargins(20, 18, 20, 18)
            wl.setSpacing(12)

            w_title = QLabel("✍  Написать отзыв")
            w_title.setStyleSheet("font-size: 13pt; font-weight: 700; color: #1D4ED8;")
            wl.addWidget(w_title)

            # Star selector
            rating_row = QHBoxLayout()
            rating_lbl = QLabel("Оценка:")
            rating_lbl.setStyleSheet("color: #94A3B8; font-size: 10pt;")
            rating_row.addWidget(rating_lbl)
            self._star_widget = StarRatingWidget(5)
            self._star_widget.rating_changed.connect(lambda v: setattr(self, "_rating", v))
            rating_row.addWidget(self._star_widget)
            rating_row.addStretch()
            wl.addLayout(rating_row)

            # Text input
            self._inp_review = QTextEdit()
            self._inp_review.setPlaceholderText(
                "Напишите ваш отзыв о перевозчике...\n"
                "Расскажите о качестве перевозки, пунктуальности, "
                "бережном обращении с грузом, общении с водителем."
            )
            self._inp_review.setFixedHeight(110)
            self._inp_review.setStyleSheet(
                "background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 8px; "
                "color: #0F172A; padding: 10px; font-size: 10pt;"
            )
            wl.addWidget(self._inp_review)

            btn_submit = QPushButton("Опубликовать отзыв")
            btn_submit.setFixedHeight(42)
            btn_submit.setStyleSheet(
                "background: #2563EB; color: white; border: none; border-radius: 8px; "
                "font-size: 11pt; font-weight: 700;"
            )
            btn_submit.clicked.connect(self._submit)
            wl.addWidget(btn_submit)
            vl.addWidget(write_card)

        elif (self.current_user.get("role") == "customer"
              and self.completed_order_id is not None):
            done_lbl = QLabel("✅  Вы уже оставили отзыв об этой перевозке")
            done_lbl.setStyleSheet(
                "color: #15803D; font-size: 10pt; font-weight: 600; "
                "background: #F0FDF4; border: 1px solid #16A34A; border-radius: 8px; padding: 10px 16px;"
            )
            vl.addWidget(done_lbl)

        # ── Reviews list ──────────────────────────────────────────
        if reviews:
            sec = QLabel(f"Все отзывы ({len(reviews)})")
            sec.setStyleSheet("color: #64748B; font-size: 9pt; font-weight: 700; text-transform: uppercase;")
            vl.addWidget(sec)
            for rv in reviews:
                vl.addWidget(ReviewCard(rv))
        else:
            empty = QFrame()
            empty.setStyleSheet(
                "background: #F8FAFC; border: 1.5px dashed #CBD5E1; border-radius: 12px;"
            )
            el = QVBoxLayout(empty)
            el.setContentsMargins(24, 32, 24, 32)
            e1 = QLabel("😶  Отзывов пока нет")
            e1.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e1.setStyleSheet("color: #64748B; font-size: 14pt;")
            el.addWidget(e1)
            vl.addWidget(empty)

        vl.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll)

    def _submit(self):
        comment = self._inp_review.toPlainText().strip()
        if not comment:
            show_warning(self, "Ошибка", "Пожалуйста, напишите текст отзыва")
            return
        if len(comment) < 10:
            show_warning(self, "Ошибка", "Отзыв слишком короткий — напишите хотя бы 10 символов")
            return
        ReviewModel.create(
            self.current_user["id"],
            self.carrier_uid,
            self.completed_order_id,
            self._rating,
            comment,
        )
        show_info(
            self, "Спасибо за отзыв!",
            f"Ваш отзыв опубликован.\nОценка: {'★' * self._rating}{'☆' * (5 - self._rating)}"
        )
        self.accept()
