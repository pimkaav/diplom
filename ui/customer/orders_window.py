from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QTabWidget,
    QComboBox, QTextEdit, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import (
    OrderModel, ResponseModel, ReviewModel, NotificationModel,
    CompanyModel, PaymentModel, UserModel
)
from ui.widgets.order_card import OrderCard
from ui.widgets.progress_tracker import ProgressTracker
from ui.styles import (
    C_CONTENT_BG, C_TEXT_MUTED, C_CARD_BG, C_BORDER, C_TEXT,
    C_PRIMARY, STATUS_LABELS, show_info, show_warning, show_question
)
from utils.helpers import fmt_money, fmt_date, stars_text


class OrderDetailDialog(QDialog):
    def __init__(self, order: dict, current_user: dict, parent=None):
        super().__init__(parent)
        self.order        = order
        self.current_user = current_user
        self.setWindowTitle(f"Заявка: {order.get('title','')}")
        self.setMinimumSize(740, 620)
        self.resize(760, 660)
        self._build()

    def _build(self):
        self.setStyleSheet(f"background: {C_CONTENT_BG};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        outer.addWidget(tabs)

        tabs.addTab(self._build_detail_tab(), "📋 Детали заказа")

        responses = ResponseModel.get_by_order(self.order["id"])
        tabs.addTab(self._build_responses_tab(responses), f"📩 Отклики ({len(responses)})")

        if self.order.get("status") == "completed" and self.order.get("carrier_id"):
            tabs.addTab(self._build_review_tab(), "⭐ Оставить отзыв")

    # ── Detail tab ─────────────────────────────────────────────────

    def _build_detail_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(14)

        # Progress tracker (shown when order is in_progress or later)
        if self.order.get("status") in ("in_progress", "completed"):
            prog_frame = QFrame()
            prog_frame.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
            )
            pfl = QVBoxLayout(prog_frame)
            pfl.setContentsMargins(16, 14, 16, 14)
            pfl.setSpacing(8)
            pfl.addWidget(_muted("Прогресс выполнения"))
            pfl.addWidget(ProgressTracker(self.order.get("progress_status", "waiting")))
            l.addWidget(prog_frame)

        # Main info card
        title_lbl = QLabel(self.order.get("title", ""))
        title_lbl.setStyleSheet(f"font-size: 15pt; font-weight: 800; color: {C_TEXT};")
        title_lbl.setWordWrap(True)
        l.addWidget(title_lbl)

        grid = QFrame()
        grid.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )
        gl = QVBoxLayout(grid)
        gl.setContentsMargins(20, 16, 20, 16)
        gl.setSpacing(8)

        o = self.order

        def row(label: str, value: str):
            r = QHBoxLayout()
            lb = QLabel(label + ":")
            lb.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt; font-weight: 600;")
            lb.setFixedWidth(190)
            vl = QLabel(value or "—")
            vl.setStyleSheet(f"color: {C_TEXT}; font-size: 12pt;")
            vl.setWordWrap(True)
            r.addWidget(lb)
            r.addWidget(vl)
            r.addStretch()
            gl.addLayout(r)

        row("Маршрут",          f"{o.get('from_city','?')} → {o.get('to_city','?')}")
        if o.get("from_address"):
            row("Адрес отправки",  o.get("from_address", ""))
        if o.get("to_address"):
            row("Адрес назначения", o.get("to_address", ""))
        row("Тип груза",        o.get("cargo_type", ""))
        row("Вес / Объём",      f"{o.get('cargo_weight',0)} т / {o.get('cargo_volume',0)} м³")
        if o.get("distance"):
            row("Расстояние",   f"{o.get('distance',0):.0f} км")
        row("Дата погрузки",    fmt_date(o.get("pickup_date", "")))
        row("Желаемая доставка", fmt_date(o.get("delivery_date", "")))
        row("Бюджет",           fmt_money(o.get("budget", 0)))
        row("Статус",           STATUS_LABELS.get(o.get("status",""), o.get("status","")))
        if o.get("carrier_name"):
            row("Перевозчик",   o.get("carrier_name", ""))
        l.addWidget(grid)

        # Vehicle info (shown when assigned)
        if o.get("driver_name") or o.get("truck_number"):
            veh = QFrame()
            veh.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
            )
            vl2 = QVBoxLayout(veh)
            vl2.setContentsMargins(20, 14, 20, 14)
            vl2.setSpacing(8)
            vl2.addWidget(_muted("🚛 Назначенный транспорт"))
            if o.get("driver_name"):
                vl2.addWidget(_row_lbl("Водитель", o["driver_name"]))
            if o.get("truck_number"):
                vl2.addWidget(_row_lbl("Номер ТС", o["truck_number"]))
            if o.get("truck_model"):
                vl2.addWidget(_row_lbl("Модель ТС", o["truck_model"]))
            l.addWidget(veh)

        # Confirmation actions
        progress = o.get("progress_status", "waiting")
        if o.get("status") == "in_progress":
            self._build_confirm_actions(l, progress)

        # Payment block
        if o.get("status") in ("in_progress", "completed"):
            payment = PaymentModel.get_by_order(o["id"])
            if payment:
                self._build_payment_block(l, payment)

        # Comment / requirements
        if o.get("comment"):
            cf = _section_frame()
            cfl = QVBoxLayout(cf)
            cfl.setContentsMargins(16, 12, 16, 12)
            cfl.addWidget(_muted("Комментарий"))
            cm = QLabel(o["comment"])
            cm.setWordWrap(True)
            cfl.addWidget(cm)
            l.addWidget(cf)

        if o.get("special_requirements"):
            sf = QFrame()
            sf.setStyleSheet("QFrame { background: #FFFBEB; border: 1.5px solid #D97706; border-radius: 10px; } QLabel { border: none; background: transparent; }")
            sfl = QVBoxLayout(sf)
            sfl.setContentsMargins(16, 12, 16, 12)
            sfl.addWidget(_muted("⚠ Специальные требования"))
            sl = QLabel(o["special_requirements"])
            sl.setStyleSheet("color: #92400E;")
            sl.setWordWrap(True)
            sfl.addWidget(sl)
            l.addWidget(sf)

        l.addStretch()
        scroll.setWidget(w)
        return scroll

    def _build_confirm_actions(self, parent_layout: QVBoxLayout, progress: str):
        """Customer action buttons based on current progress state."""
        o = self.order

        if progress == "vehicle_assigned":
            box = QFrame()
            box.setStyleSheet(
                "background: #EFF6FF; border: 1.5px solid #2563EB; border-radius: 12px;"
            )
            bl = QVBoxLayout(box)
            bl.setContentsMargins(18, 14, 18, 14)
            bl.setSpacing(10)
            info = QLabel(
                "🚛 Перевозчик назначил транспорт.\n"
                "Когда груз будет забран, подтвердите отправку — оплата будет заблокирована."
            )
            info.setStyleSheet("color: #1D4ED8; font-size: 11pt;")
            info.setWordWrap(True)
            bl.addWidget(info)

            btn = QPushButton("✅ Подтвердить отправку груза")
            btn.setProperty("cls", "success")
            btn.setFixedHeight(42)
            btn.clicked.connect(self._confirm_dispatch)
            bl.addWidget(btn)
            parent_layout.addWidget(box)

        elif progress == "arrived":
            box = QFrame()
            box.setStyleSheet(
                "QFrame { background: #F0FDF4; border: 1.5px solid #16A34A; border-radius: 12px; } QLabel { border: none; background: transparent; }"
            )
            bl = QVBoxLayout(box)
            bl.setContentsMargins(18, 14, 18, 14)
            bl.setSpacing(10)
            info = QLabel(
                "📍 Перевозчик отметил прибытие.\n"
                "Подтвердите получение груза — оплата будет переведена перевозчику."
            )
            info.setStyleSheet("color: #15803D; font-size: 11pt;")
            info.setWordWrap(True)
            bl.addWidget(info)

            btn = QPushButton("🏁 Подтвердить получение груза")
            btn.setProperty("cls", "success")
            btn.setFixedHeight(42)
            btn.clicked.connect(self._confirm_arrival)
            bl.addWidget(btn)
            parent_layout.addWidget(box)

        elif progress == "dispatched":
            info = QLabel("📦 Груз отправлен, ожидается прибытие к месту назначения.")
            info.setStyleSheet(
                "background: #EFF6FF; border: 1.5px solid #3B82F6; border-radius: 10px; "
                "color: #1D4ED8; font-size: 11pt; padding: 12px 16px;"
            )
            info.setWordWrap(True)
            parent_layout.addWidget(info)

        elif progress == "in_transit":
            info = QLabel("🚚 Груз в пути. Ожидайте прибытия к месту назначения.")
            info.setStyleSheet(
                "background: #EFF6FF; border: 1.5px solid #3B82F6; border-radius: 10px; "
                "color: #1D4ED8; font-size: 11pt; padding: 12px 16px;"
            )
            info.setWordWrap(True)
            parent_layout.addWidget(info)

    def _build_payment_block(self, parent_layout: QVBoxLayout, payment: dict):
        pf = _section_frame()
        pl = QVBoxLayout(pf)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(6)
        pl.addWidget(_muted("💳 Оплата"))

        status_map = {
            "pending":  ("⏳ Ожидает холдирования", "#D97706"),
            "held":     ("🔒 Средства заблокированы (холд)", "#1D4ED8"),
            "released": ("✅ Оплата переведена перевозчику", "#15803D"),
            "refunded": ("↩ Возврат средств", "#DC2626"),
        }
        st = payment.get("status", "pending")
        label_text, color = status_map.get(st, (st, C_TEXT_MUTED))

        pl.addWidget(_row_lbl("Сумма",  fmt_money(payment.get("amount", 0))))
        pl.addWidget(_row_lbl("Статус", label_text, color))
        if payment.get("transaction_id"):
            pl.addWidget(_row_lbl("ID транзакции", payment["transaction_id"]))
        parent_layout.addWidget(pf)

    # ── Responses tab ──────────────────────────────────────────────

    def _build_responses_tab(self, responses: list) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        rl = QVBoxLayout(w)
        rl.setContentsMargins(24, 24, 24, 24)
        rl.setSpacing(12)

        if responses:
            for resp in responses:
                rc = QFrame()
                rc.setStyleSheet(
                    f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
                )
                rcl = QVBoxLayout(rc)
                rcl.setContentsMargins(16, 14, 16, 14)
                rcl.setSpacing(8)

                top = QHBoxLayout()
                nm = QLabel(resp.get("company_name") or resp.get("carrier_name") or "Перевозчик")
                nm.setStyleSheet(f"font-weight: 700; font-size: 11pt; color: {C_TEXT};")
                top.addWidget(nm)
                top.addStretch()

                cost_lbl = QLabel(fmt_money(resp.get("proposed_cost", 0)))
                cost_lbl.setStyleSheet(
                    "background: #EFF6FF; color: #1D4ED8; border: 2px solid #2563EB; "
                    "border-radius: 8px; padding: 4px 14px; font-weight: 800; font-size: 14pt;"
                )
                top.addWidget(cost_lbl)
                rcl.addLayout(top)

                rating = resp.get("company_rating", 0)
                if rating:
                    rl2 = QLabel(stars_text(rating))
                    rl2.setStyleSheet("color: #F59E0B; font-size: 11pt;")
                    rcl.addWidget(rl2)

                if resp.get("message"):
                    ml = QLabel(resp["message"])
                    ml.setWordWrap(True)
                    ml.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt;")
                    rcl.addWidget(ml)

                if resp.get("estimated_days"):
                    dl2 = QLabel(f"⏱ Срок доставки: {resp['estimated_days']} дней")
                    dl2.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10pt;")
                    rcl.addWidget(dl2)

                if resp.get("status") == "pending" and self.order.get("status") == "new":
                    btn_row = QHBoxLayout()
                    btn_row.addStretch()
                    btn_accept = QPushButton("✅ Принять")
                    btn_accept.setStyleSheet(
                        "QPushButton { background: #16A34A; color: white; border: 2px solid #22C55E; "
                        "border-radius: 8px; font-size: 11pt; font-weight: 700; padding: 0 16px; }"
                        "QPushButton:hover { background: #15803D; }"
                    )
                    btn_accept.setFixedSize(140, 40)
                    btn_accept.clicked.connect(lambda _, r=resp: self._accept_response(r))
                    btn_row.addWidget(btn_accept)
                    btn_reject = QPushButton("❌ Отклонить")
                    btn_reject.setStyleSheet(
                        "QPushButton { background: transparent; color: #EF4444; border: 2px solid #EF4444; "
                        "border-radius: 8px; font-size: 11pt; font-weight: 700; padding: 0 16px; }"
                        "QPushButton:hover { background: rgba(239,68,68,0.14); }"
                    )
                    btn_reject.setFixedSize(150, 40)
                    btn_reject.clicked.connect(lambda _, r=resp: self._reject_response(r))
                    btn_row.addWidget(btn_reject)
                    rcl.addLayout(btn_row)
                else:
                    bg_map = {
                        "pending":  ("#EFF6FF", "#1D4ED8"),
                        "accepted": ("#F0FDF4", "#15803D"),
                        "rejected": ("#FEF2F2", "#B91C1C"),
                    }
                    bg, fg = bg_map.get(resp.get("status","pending"), ("#F8FAFC", C_TEXT))
                    status_lbl = QLabel(
                        {"pending": "⏳ Ожидает", "accepted": "✅ Принят", "rejected": "❌ Отклонён"}
                        .get(resp.get("status", ""), resp.get("status", ""))
                    )
                    status_lbl.setStyleSheet(
                        f"background: {bg}; color: {fg}; border-radius: 8px; "
                        "padding: 2px 10px; font-size: 9pt; font-weight: 600;"
                    )
                    status_lbl.setFixedHeight(26)
                    rcl.addWidget(status_lbl, alignment=Qt.AlignmentFlag.AlignRight)

                rl.addWidget(rc)
        else:
            emp = QLabel("Откликов пока нет")
            emp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emp.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 40px;")
            rl.addWidget(emp)

        rl.addStretch()
        scroll.setWidget(w)
        return scroll

    # ── Review tab ─────────────────────────────────────────────────

    def _build_review_tab(self) -> QWidget:
        from ui.widgets.star_rating import StarRatingWidget
        w = QWidget()
        w.setStyleSheet(f"background: {C_CONTENT_BG};")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(16)

        already = ReviewModel.already_reviewed(
            self.current_user["id"], self.order["carrier_id"], self.order["id"]
        )
        if already:
            lbl = QLabel("✅ Вы уже оставили отзыв на этот заказ")
            lbl.setStyleSheet("color: #15803D; font-size: 12pt; margin: 40px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
            return w

        l.addWidget(_muted("Оцените перевозчика"))
        self._rev_stars = StarRatingWidget(0, editable=True)
        l.addWidget(self._rev_stars)

        l.addWidget(_muted("Комментарий"))
        self._rev_text = QTextEdit()
        self._rev_text.setPlaceholderText("Расскажите о вашем опыте работы с перевозчиком...")
        self._rev_text.setFixedHeight(100)
        l.addWidget(self._rev_text)

        btn = QPushButton("Отправить отзыв")
        btn.setFixedSize(180, 42)
        btn.clicked.connect(self._submit_review)
        l.addWidget(btn)
        l.addStretch()
        return w

    # ── Actions ────────────────────────────────────────────────────

    def _accept_response(self, response: dict):
        cost = response.get("proposed_cost", 0)

        # Check balance
        balance = UserModel.get_balance(self.current_user["id"])
        if cost > 0 and balance < cost:
            show_warning(
                self, "Недостаточно средств",
                f"На вашем балансе {fmt_money(balance)}, "
                f"а стоимость перевозки составляет {fmt_money(cost)}.\n\n"
                "Пополните баланс в профиле или через кнопку «+ Пополнить» в боковом меню."
            )
            return

        if not show_question(
            self, "Подтверждение",
            f"Принять отклик перевозчика на сумму {fmt_money(cost)}?\n"
            f"С вашего баланса будет списано {fmt_money(cost)} (эскроу)."
        ):
            return

        ResponseModel.update_status(response["id"], "accepted")
        OrderModel.update_status(self.order["id"], "in_progress", response["carrier_id"])

        # Deduct from customer balance and hold payment immediately
        if cost > 0:
            UserModel.subtract_balance(self.current_user["id"], cost)
            payment_id = PaymentModel.create(
                self.order["id"], cost,
                payer_id=self.current_user["id"],
                receiver_id=response["carrier_id"],
            )
            PaymentModel.hold(payment_id)

        NotificationModel.create(
            response["carrier_id"], "order_accepted",
            "Ваш отклик принят!",
            f"Заказчик принял ваш отклик на заявку #{self.order['id']}. "
            "Назначьте транспорт и приступайте к работе."
        )
        show_info(
            self, "Готово",
            f"Отклик принят! {fmt_money(cost)} заблокированы на эскроу.\n"
            "Заказ переведён в статус «В работе»."
        )
        self.accept()

    def _reject_response(self, response: dict):
        ResponseModel.update_status(response["id"], "rejected")
        NotificationModel.create(
            response["carrier_id"], "order_rejected",
            "Отклик отклонён",
            f"Заказчик отклонил ваш отклик на заявку #{self.order['id']}"
        )
        show_info(self, "Готово", "Отклик отклонён.")
        self.accept()

    def _confirm_dispatch(self):
        """Customer confirms cargo was picked up → move to in_transit."""
        if not show_question(
            self, "Подтверждение отправки",
            "Подтвердите, что груз забран перевозчиком."
        ):
            return

        OrderModel.confirm_dispatch(self.order["id"])

        NotificationModel.create(
            self.order["carrier_id"], "dispatch_confirmed",
            "Заказчик подтвердил отправку",
            f"Заказчик подтвердил, что груз по заявке #{self.order['id']} забран. "
            "Средства находятся в эскроу до подтверждения получения."
        )
        show_info(
            self, "Готово",
            "Отправка подтверждена. Средства в эскроу.\n"
            "После доставки подтвердите получение груза."
        )
        self.accept()

    def _confirm_arrival(self):
        """Customer confirms receipt → release payment to carrier's balance, complete order."""
        if not show_question(
            self, "Подтверждение получения",
            "Подтвердите получение груза.\n"
            "Оплата будет переведена перевозчику, заказ завершится."
        ):
            return

        OrderModel.confirm_arrival(self.order["id"])

        # Release payment — add amount to carrier's balance
        payment = PaymentModel.get_by_order(self.order["id"])
        if payment:
            PaymentModel.release(payment["id"])
            # Credit carrier's balance
            carrier_id = self.order.get("carrier_id")
            if carrier_id and payment.get("amount"):
                UserModel.add_balance(carrier_id, payment["amount"])

        carrier_id = self.order.get("carrier_id")
        if carrier_id:
            CompanyModel.increment_completed(carrier_id)
            NotificationModel.create(
                carrier_id, "payment_released",
                "Оплата переведена",
                f"Заказчик подтвердил получение груза по заявке #{self.order['id']}. "
                "Оплата переведена на ваш счёт."
            )
        show_info(
            self, "Заказ завершён",
            "Получение подтверждено. Оплата переведена перевозчику.\n"
            "Вы можете оставить отзыв о перевозчике."
        )
        self.accept()

    def _submit_review(self):
        rating = self._rev_stars.value()
        if rating == 0:
            show_warning(self, "Ошибка", "Выберите оценку")
            return
        ReviewModel.create(
            self.current_user["id"],
            self.order["carrier_id"],
            self.order["id"],
            rating,
            self._rev_text.toPlainText().strip()
        )
        show_info(self, "Спасибо!", "Ваш отзыв опубликован.")
        self.accept()


# ── List window ────────────────────────────────────────────────────

class CustomerOrdersWindow(QWidget):
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._build()
        self._load()

    # ── Build ─────────────────────────────────────────────────────

    def _build(self):
        self.setStyleSheet(f"background: {C_CONTENT_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sub_stack = QStackedWidget()
        root.addWidget(self.sub_stack)

        self.sub_stack.addWidget(self._build_list_page())  # page 0 — list
        self.sub_stack.addWidget(QWidget())                # page 1 — detail placeholder

        self._all_orders: list[dict] = []

    def _build_list_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        root = QVBoxLayout(page)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Мои заявки")
        hdr.setProperty("heading", "true")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()

        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Все", "Новые", "В работе", "Завершённые", "Отменённые"])
        self.cmb_filter.setFixedSize(170, 40)
        self.cmb_filter.setStyleSheet(
            "QComboBox { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
            "color: #0F172A; padding: 6px 12px; font-size: 11pt; }"
            "QComboBox:focus { border-color: #2563EB; background: #EFF6FF; }"
            "QComboBox::drop-down { border: none; width: 26px; }"
            "QComboBox QAbstractItemView { background: #FFFFFF; color: #0F172A; "
            "border: 1.5px solid #CBD5E1; selection-background-color: #EFF6FF; "
            "selection-color: #2563EB; font-size: 11pt; outline: none; }"
            "QComboBox QAbstractItemView::item { color: #0F172A; padding: 8px 12px; min-height: 28px; }"
            "QComboBox QAbstractItemView::item:selected { background: #EFF6FF; color: #2563EB; }"
        )
        self.cmb_filter.currentIndexChanged.connect(self._filter)
        hdr_row.addWidget(self.cmb_filter)

        root.addLayout(hdr_row)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
        root.addWidget(self.count_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

        return page

    # ── Data ──────────────────────────────────────────────────────

    def _load(self):
        self._all_orders = OrderModel.get_by_customer(self.current_user["id"])
        self._filter()

    def _filter(self):
        idx    = self.cmb_filter.currentIndex()
        status = [None, "new", "in_progress", "completed", "cancelled"][idx]
        orders = self._all_orders if not status else [
            o for o in self._all_orders if o["status"] == status
        ]
        self._render(orders)

    def _render(self, orders: list[dict]):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.count_lbl.setText(f"Всего заявок: {len(orders)}")

        for order in orders:
            card = OrderCard(order, mode="customer")
            card.clicked.connect(self._show_detail)
            card.status_changed.connect(self._change_status)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        if not orders:
            lbl = QLabel("Заявок нет")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 40px;")
            self.cards_layout.insertWidget(0, lbl)

    # ── Navigation ────────────────────────────────────────────────

    def _show_detail(self, order: dict):
        page = self._build_detail_page(order)
        old = self.sub_stack.widget(1)
        self.sub_stack.removeWidget(old)
        old.deleteLater()
        self.sub_stack.insertWidget(1, page)
        self.sub_stack.setCurrentIndex(1)

    def _go_back(self):
        self.sub_stack.setCurrentIndex(0)
        self._load()

    # ── Detail page ───────────────────────────────────────────────

    def _build_detail_page(self, order: dict) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet(
            f"background: {C_CARD_BG}; border-bottom: 1px solid {C_BORDER};"
        )
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(16, 0, 16, 0)
        tb.setSpacing(12)

        btn_back = QPushButton("← Мои заявки")
        btn_back.setProperty("cls", "secondary")
        btn_back.setFixedHeight(36)
        btn_back.clicked.connect(self._go_back)
        tb.addWidget(btn_back)
        tb.addStretch()

        title_hdr = QLabel(order.get("title", ""))
        title_hdr.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {C_TEXT};")
        tb.addWidget(title_hdr)

        outer.addWidget(top_bar)

        # Tabs
        tabs = QTabWidget()
        outer.addWidget(tabs)

        tabs.addTab(self._build_detail_tab(order), "📋 Детали заказа")

        responses = ResponseModel.get_by_order(order["id"])
        tabs.addTab(self._build_responses_tab(order, responses),
                    f"📩 Отклики ({len(responses)})")

        if order.get("status") == "completed" and order.get("carrier_id"):
            tabs.addTab(self._build_review_tab(order), "⭐ Оставить отзыв")

        return page

    def _build_detail_tab(self, order: dict) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(14)

        o = order

        # Progress tracker
        if o.get("status") in ("in_progress", "completed"):
            prog_frame = QFrame()
            prog_frame.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
            )
            pfl = QVBoxLayout(prog_frame)
            pfl.setContentsMargins(16, 14, 16, 14)
            pfl.setSpacing(8)
            pfl.addWidget(_muted("Прогресс выполнения"))
            pfl.addWidget(ProgressTracker(o.get("progress_status", "waiting")))
            l.addWidget(prog_frame)

        title_lbl = QLabel(o.get("title", ""))
        title_lbl.setStyleSheet(f"font-size: 15pt; font-weight: 800; color: {C_TEXT};")
        title_lbl.setWordWrap(True)
        l.addWidget(title_lbl)

        # Info card
        grid = QFrame()
        grid.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )
        gl = QVBoxLayout(grid)
        gl.setContentsMargins(20, 16, 20, 16)
        gl.setSpacing(8)

        def row(label: str, value: str):
            r = QHBoxLayout()
            lb = QLabel(label + ":")
            lb.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt; font-weight: 600;")
            lb.setFixedWidth(190)
            vl = QLabel(value or "—")
            vl.setStyleSheet(f"color: {C_TEXT}; font-size: 12pt;")
            vl.setWordWrap(True)
            r.addWidget(lb)
            r.addWidget(vl)
            r.addStretch()
            gl.addLayout(r)

        row("Маршрут",           f"{o.get('from_city','?')} → {o.get('to_city','?')}")
        if o.get("from_address"):
            row("Адрес отправки",  o.get("from_address", ""))
        if o.get("to_address"):
            row("Адрес назначения", o.get("to_address", ""))
        row("Тип груза",         o.get("cargo_type", ""))
        row("Вес / Объём",       f"{o.get('cargo_weight',0)} т / {o.get('cargo_volume',0)} м³")
        if o.get("distance"):
            row("Расстояние",    f"{o.get('distance',0):.0f} км")
        row("Дата погрузки",     fmt_date(o.get("pickup_date", "")))
        row("Желаемая доставка", fmt_date(o.get("delivery_date", "")))
        row("Бюджет",            fmt_money(o.get("budget", 0)))
        row("Статус",            STATUS_LABELS.get(o.get("status",""), o.get("status","")))
        if o.get("carrier_name"):
            row("Перевозчик",    o.get("carrier_name", ""))
        l.addWidget(grid)

        # Vehicle info
        if o.get("driver_name") or o.get("truck_number"):
            veh = QFrame()
            veh.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
            )
            vl2 = QVBoxLayout(veh)
            vl2.setContentsMargins(20, 14, 20, 14)
            vl2.setSpacing(8)
            vl2.addWidget(_muted("🚛 Назначенный транспорт"))
            if o.get("driver_name"):
                vl2.addWidget(_row_lbl("Водитель", o["driver_name"]))
            if o.get("truck_number"):
                vl2.addWidget(_row_lbl("Номер ТС", o["truck_number"]))
            if o.get("truck_model"):
                vl2.addWidget(_row_lbl("Модель ТС", o["truck_model"]))
            l.addWidget(veh)

        # Confirmation actions
        progress = o.get("progress_status", "waiting")
        if o.get("status") == "in_progress":
            self._build_confirm_actions(l, order, progress)

        # Payment block
        if o.get("status") in ("in_progress", "completed"):
            payment = PaymentModel.get_by_order(o["id"])
            if payment:
                self._build_payment_block(l, payment)

        if o.get("comment"):
            cf = _section_frame()
            cfl = QVBoxLayout(cf)
            cfl.setContentsMargins(16, 14, 16, 14)
            cfl.addWidget(_muted("Комментарий"))
            cm = QLabel(o["comment"])
            cm.setStyleSheet(f"color: {C_TEXT}; font-size: 12pt;")
            cm.setWordWrap(True)
            cfl.addWidget(cm)
            l.addWidget(cf)

        if o.get("special_requirements"):
            sf = QFrame()
            sf.setStyleSheet(
                "QFrame { background: #FFFBEB; border: 1.5px solid #D97706; border-radius: 10px; } QLabel { border: none; background: transparent; }"
            )
            sfl = QVBoxLayout(sf)
            sfl.setContentsMargins(16, 14, 16, 14)
            sfl.addWidget(_muted("⚠ Специальные требования"))
            sl = QLabel(o["special_requirements"])
            sl.setStyleSheet("color: #92400E; font-size: 12pt;")
            sl.setWordWrap(True)
            sfl.addWidget(sl)
            l.addWidget(sf)

        l.addStretch()
        scroll.setWidget(w)
        return scroll

    def _build_confirm_actions(self, parent_layout: QVBoxLayout, order: dict, progress: str):
        if progress == "vehicle_assigned":
            box = QFrame()
            box.setStyleSheet(
                "background: #EFF6FF; border: 1.5px solid #2563EB; border-radius: 12px;"
            )
            bl = QVBoxLayout(box)
            bl.setContentsMargins(18, 14, 18, 14)
            bl.setSpacing(10)
            info = QLabel(
                "🚛 Перевозчик назначил транспорт.\n"
                "Когда груз будет забран, подтвердите отправку — оплата будет заблокирована."
            )
            info.setStyleSheet("color: #1D4ED8; font-size: 10pt;")
            info.setWordWrap(True)
            bl.addWidget(info)
            btn = QPushButton("✅ Подтвердить отправку груза")
            btn.setProperty("cls", "success")
            btn.setFixedHeight(42)
            btn.clicked.connect(lambda: self._confirm_dispatch(order))
            bl.addWidget(btn)
            parent_layout.addWidget(box)

        elif progress == "arrived":
            box = QFrame()
            box.setStyleSheet(
                "QFrame { background: #F0FDF4; border: 1.5px solid #16A34A; border-radius: 12px; } QLabel { border: none; background: transparent; }"
            )
            bl = QVBoxLayout(box)
            bl.setContentsMargins(18, 14, 18, 14)
            bl.setSpacing(10)
            info = QLabel(
                "📍 Перевозчик отметил прибытие.\n"
                "Подтвердите получение груза — оплата будет переведена перевозчику."
            )
            info.setStyleSheet("color: #15803D; font-size: 10pt;")
            info.setWordWrap(True)
            bl.addWidget(info)
            btn = QPushButton("🏁 Подтвердить получение груза")
            btn.setProperty("cls", "success")
            btn.setFixedHeight(42)
            btn.clicked.connect(lambda: self._confirm_arrival(order))
            bl.addWidget(btn)
            parent_layout.addWidget(box)

        elif progress == "dispatched":
            info = QLabel("📦 Груз отправлен, ожидается прибытие к месту назначения.")
            info.setStyleSheet(
                "background: #EFF6FF; border: 1.5px solid #3B82F6; border-radius: 10px; "
                "color: #1D4ED8; font-size: 11pt; padding: 12px 16px;"
            )
            info.setWordWrap(True)
            parent_layout.addWidget(info)

        elif progress == "in_transit":
            info = QLabel("🚚 Груз в пути. Ожидайте прибытия к месту назначения.")
            info.setStyleSheet(
                "background: #EFF6FF; border: 1.5px solid #3B82F6; border-radius: 10px; "
                "color: #1D4ED8; font-size: 11pt; padding: 12px 16px;"
            )
            info.setWordWrap(True)
            parent_layout.addWidget(info)

    def _build_payment_block(self, parent_layout: QVBoxLayout, payment: dict):
        pf = _section_frame()
        pl = QVBoxLayout(pf)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(6)
        pl.addWidget(_muted("💳 Оплата"))
        status_map = {
            "pending":  ("⏳ Ожидает холдирования", "#D97706"),
            "held":     ("🔒 Средства заблокированы (холд)", "#1D4ED8"),
            "released": ("✅ Оплата переведена перевозчику", "#15803D"),
            "refunded": ("↩ Возврат средств", "#DC2626"),
        }
        st = payment.get("status", "pending")
        label_text, color = status_map.get(st, (st, C_TEXT_MUTED))
        pl.addWidget(_row_lbl("Сумма",  fmt_money(payment.get("amount", 0))))
        pl.addWidget(_row_lbl("Статус", label_text, color))
        if payment.get("transaction_id"):
            pl.addWidget(_row_lbl("ID транзакции", payment["transaction_id"]))
        parent_layout.addWidget(pf)

    def _build_responses_tab(self, order: dict, responses: list) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        rl = QVBoxLayout(w)
        rl.setContentsMargins(24, 24, 24, 24)
        rl.setSpacing(12)

        if responses:
            for resp in responses:
                rc = QFrame()
                rc.setStyleSheet(
                    f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
                )
                rcl = QVBoxLayout(rc)
                rcl.setContentsMargins(16, 14, 16, 14)
                rcl.setSpacing(8)

                top = QHBoxLayout()
                nm = QLabel(
                    resp.get("company_name") or resp.get("carrier_name") or "Перевозчик"
                )
                nm.setStyleSheet(f"font-weight: 700; font-size: 13pt; color: {C_TEXT};")
                top.addWidget(nm)
                top.addStretch()
                cost_lbl = QLabel(fmt_money(resp.get("proposed_cost", 0)))
                cost_lbl.setStyleSheet(
                    "background: #EFF6FF; color: #1D4ED8; border: 2px solid #2563EB; "
                    "border-radius: 8px; padding: 4px 16px; font-weight: 800; font-size: 15pt;"
                )
                top.addWidget(cost_lbl)
                rcl.addLayout(top)

                rating = resp.get("company_rating", 0)
                if rating:
                    rl2 = QLabel(stars_text(rating))
                    rl2.setStyleSheet("color: #F59E0B; font-size: 12pt;")
                    rcl.addWidget(rl2)

                if resp.get("message"):
                    ml = QLabel(resp["message"])
                    ml.setWordWrap(True)
                    ml.setStyleSheet(f"color: {C_TEXT}; font-size: 11pt;")
                    rcl.addWidget(ml)

                if resp.get("estimated_days"):
                    dl2 = QLabel(f"⏱ Срок доставки: {resp['estimated_days']} дней")
                    dl2.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt;")
                    rcl.addWidget(dl2)

                if resp.get("status") == "pending" and order.get("status") == "new":
                    btn_row = QHBoxLayout()
                    btn_row.addStretch()
                    btn_accept = QPushButton("✅ Принять")
                    btn_accept.setStyleSheet(
                        "QPushButton { background: #16A34A; color: white; border: 2px solid #22C55E; "
                        "border-radius: 8px; font-size: 11pt; font-weight: 700; padding: 0 16px; }"
                        "QPushButton:hover { background: #15803D; }"
                    )
                    btn_accept.setFixedSize(140, 40)
                    btn_accept.clicked.connect(
                        lambda _, r=resp: self._accept_response(order, r)
                    )
                    btn_row.addWidget(btn_accept)
                    btn_reject = QPushButton("❌ Отклонить")
                    btn_reject.setStyleSheet(
                        "QPushButton { background: transparent; color: #EF4444; border: 2px solid #EF4444; "
                        "border-radius: 8px; font-size: 11pt; font-weight: 700; padding: 0 16px; }"
                        "QPushButton:hover { background: rgba(239,68,68,0.14); }"
                    )
                    btn_reject.setFixedSize(150, 40)
                    btn_reject.clicked.connect(
                        lambda _, r=resp: self._reject_response(order, r)
                    )
                    btn_row.addWidget(btn_reject)
                    rcl.addLayout(btn_row)
                else:
                    bg_map = {
                        "pending":  ("#EFF6FF", "#1D4ED8"),
                        "accepted": ("#F0FDF4", "#15803D"),
                        "rejected": ("#FEF2F2", "#B91C1C"),
                    }
                    bg, fg = bg_map.get(resp.get("status", "pending"), ("#F8FAFC", C_TEXT_MUTED))
                    status_lbl = QLabel(
                        {"pending": "⏳ Ожидает",
                         "accepted": "✅ Принят",
                         "rejected": "❌ Отклонён"
                         }.get(resp.get("status", ""), resp.get("status", ""))
                    )
                    status_lbl.setStyleSheet(
                        f"background: {bg}; color: {fg}; border-radius: 8px; "
                        "padding: 2px 10px; font-size: 9pt; font-weight: 600;"
                    )
                    status_lbl.setFixedHeight(26)
                    rcl.addWidget(status_lbl, alignment=Qt.AlignmentFlag.AlignRight)

                rl.addWidget(rc)
        else:
            emp = QLabel("Откликов пока нет")
            emp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emp.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 40px;")
            rl.addWidget(emp)

        rl.addStretch()
        scroll.setWidget(w)
        return scroll

    def _build_review_tab(self, order: dict) -> QWidget:
        from ui.widgets.star_rating import StarRatingWidget
        w = QWidget()
        w.setStyleSheet(f"background: {C_CONTENT_BG};")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(16)

        already = ReviewModel.already_reviewed(
            self.current_user["id"], order["carrier_id"], order["id"]
        )
        if already:
            lbl = QLabel("✅ Вы уже оставили отзыв на этот заказ")
            lbl.setStyleSheet("color: #15803D; font-size: 12pt; margin: 40px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
            return w

        rate_lbl = QLabel("Оцените перевозчика:")
        rate_lbl.setStyleSheet(f"font-size: 13pt; font-weight: 600; color: {C_TEXT};")
        l.addWidget(rate_lbl)
        self._rev_stars = StarRatingWidget(0, editable=True)
        l.addWidget(self._rev_stars)

        comm_lbl = QLabel("Комментарий (необязательно):")
        comm_lbl.setStyleSheet(f"font-size: 12pt; font-weight: 600; color: {C_TEXT};")
        l.addWidget(comm_lbl)
        self._rev_text = QTextEdit()
        self._rev_text.setPlaceholderText(
            "Расскажите о вашем опыте работы с перевозчиком..."
        )
        self._rev_text.setFixedHeight(120)
        self._rev_text.setStyleSheet(
            "QTextEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
            "color: #0F172A; padding: 8px 12px; font-size: 12pt; }"
            "QTextEdit:focus { border-color: #2563EB; background: #EFF6FF; }"
        )
        l.addWidget(self._rev_text)

        btn = QPushButton("⭐ Отправить отзыв")
        btn.setFixedSize(220, 48)
        btn.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 10px; font-size: 12pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn.clicked.connect(lambda: self._submit_review(order))
        l.addWidget(btn)
        l.addStretch()
        return w

    # ── Actions ────────────────────────────────────────────────────

    def _accept_response(self, order: dict, response: dict):
        cost = response.get("proposed_cost", 0)
        balance = UserModel.get_balance(self.current_user["id"])
        if cost > 0 and balance < cost:
            show_warning(
                self, "Недостаточно средств",
                f"На вашем балансе {fmt_money(balance)}, "
                f"а стоимость перевозки составляет {fmt_money(cost)}.\n\n"
                "Пополните баланс в профиле или через кнопку «+ Пополнить» в боковом меню."
            )
            return

        if not show_question(
            self, "Подтверждение",
            f"Принять отклик перевозчика на сумму {fmt_money(cost)}?\n"
            f"С вашего баланса будет списано {fmt_money(cost)} (эскроу)."
        ):
            return

        ResponseModel.update_status(response["id"], "accepted")
        OrderModel.update_status(order["id"], "in_progress", response["carrier_id"])

        if cost > 0:
            UserModel.subtract_balance(self.current_user["id"], cost)
            payment_id = PaymentModel.create(
                order["id"], cost,
                payer_id=self.current_user["id"],
                receiver_id=response["carrier_id"],
            )
            PaymentModel.hold(payment_id)

        NotificationModel.create(
            response["carrier_id"], "order_accepted",
            "Ваш отклик принят!",
            f"Заказчик принял ваш отклик на заявку #{order['id']}. "
            "Назначьте транспорт и приступайте к работе."
        )
        show_info(
            self, "Готово",
            f"Отклик принят! {fmt_money(cost)} заблокированы на эскроу.\n"
            "Заказ переведён в статус «В работе»."
        )
        self._go_back()

    def _reject_response(self, order: dict, response: dict):
        ResponseModel.update_status(response["id"], "rejected")
        NotificationModel.create(
            response["carrier_id"], "order_rejected",
            "Отклик отклонён",
            f"Заказчик отклонил ваш отклик на заявку #{order['id']}"
        )
        show_info(self, "Готово", "Отклик отклонён.")
        self._go_back()

    def _confirm_dispatch(self, order: dict):
        if not show_question(
            self, "Подтверждение отправки",
            "Подтвердите, что груз забран перевозчиком."
        ):
            return

        OrderModel.confirm_dispatch(order["id"])
        NotificationModel.create(
            order["carrier_id"], "dispatch_confirmed",
            "Заказчик подтвердил отправку",
            f"Заказчик подтвердил, что груз по заявке #{order['id']} забран. "
            "Средства находятся в эскроу до подтверждения получения."
        )
        show_info(
            self, "Готово",
            "Отправка подтверждена. Средства в эскроу.\n"
            "После доставки подтвердите получение груза."
        )
        self._go_back()

    def _confirm_arrival(self, order: dict):
        if not show_question(
            self, "Подтверждение получения",
            "Подтвердите получение груза.\n"
            "Оплата будет переведена перевозчику, заказ завершится."
        ):
            return

        OrderModel.confirm_arrival(order["id"])
        payment = PaymentModel.get_by_order(order["id"])
        if payment:
            PaymentModel.release(payment["id"])
            carrier_id = order.get("carrier_id")
            if carrier_id and payment.get("amount"):
                UserModel.add_balance(carrier_id, payment["amount"])

        carrier_id = order.get("carrier_id")
        if carrier_id:
            CompanyModel.increment_completed(carrier_id)
            NotificationModel.create(
                carrier_id, "payment_released",
                "Оплата переведена",
                f"Заказчик подтвердил получение груза по заявке #{order['id']}. "
                "Оплата переведена на ваш счёт."
            )
        show_info(
            self, "Заказ завершён",
            "Получение подтверждено. Оплата переведена перевозчику.\n"
            "Вы можете оставить отзыв о перевозчике."
        )
        self._go_back()

    def _submit_review(self, order: dict):
        rating = self._rev_stars.value()
        if rating == 0:
            show_warning(self, "Ошибка", "Выберите оценку")
            return
        ReviewModel.create(
            self.current_user["id"],
            order["carrier_id"],
            order["id"],
            rating,
            self._rev_text.toPlainText().strip()
        )
        show_info(self, "Спасибо!", "Ваш отзыв опубликован.")
        self._go_back()

    def _change_status(self, order_id: int, status: str):
        labels = {
            "in_progress": "перевести в статус «В работе»",
            "completed":   "завершить заказ",
            "cancelled":   "отменить заказ",
        }
        if show_question(
            self, "Подтверждение",
            f"Вы хотите {labels.get(status, status)}?"
        ):
            OrderModel.update_status(order_id, status)
            self._load()

    def refresh(self):
        self._load()


# ── Helpers ────────────────────────────────────────────────────────

def _muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #64748B; font-size: 10pt; font-weight: 700; text-transform: uppercase;"
    )
    return lbl


def _section_frame() -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
    )
    return f


def _row_lbl(label: str, value: str, value_color: str = C_TEXT) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent; border: none;")
    hl = QHBoxLayout(w)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.setSpacing(8)
    lb = QLabel(label + ":")
    lb.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt; font-weight: 600;")
    lb.setFixedWidth(160)
    vl = QLabel(value)
    vl.setStyleSheet(f"color: {value_color}; font-size: 12pt;")
    vl.setWordWrap(True)
    hl.addWidget(lb)
    hl.addWidget(vl)
    hl.addStretch()
    return w
