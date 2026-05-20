from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from database.models import (
    UserModel, OrderModel, CompanyModel, PaymentModel, NotificationModel
)
from ui.styles import (
    C_SIDEBAR_BG, C_CONTENT_BG, C_CARD_BG, C_BORDER, C_TEXT,
    C_TEXT_MUTED, C_PRIMARY, NAV_BTN_STYLE, C_SUCCESS, C_DANGER,
    STATUS_LABELS, STATUS_COLORS, PAYMENT_STATUS_LABELS
)
from utils.helpers import fmt_money, fmt_date, fmt_datetime


class AdminDashboard(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle("FreightExchange — Панель администратора")
        self.setMinimumSize(1400, 800)
        self._build()
        self._start_timer()
        self.showMaximized()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setStyleSheet(f"background-color: {C_SIDEBAR_BG};")
        sidebar.setFixedWidth(240)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(12, 0, 12, 16)
        sb.setSpacing(4)

        logo_area = QWidget()
        logo_area.setFixedHeight(70)
        logo_area.setStyleSheet(f"background: {C_SIDEBAR_BG};")
        la = QHBoxLayout(logo_area)
        la.setContentsMargins(8, 0, 8, 0)
        ll = QLabel("🚛 FreightExchange")
        ll.setStyleSheet("color: white; font-size: 13pt; font-weight: 800;")
        la.addWidget(ll)
        sb.addWidget(logo_area)

        admin_badge = QFrame()
        admin_badge.setStyleSheet(
            "background: rgba(220,38,38,0.15); border-radius: 8px; border: 1px solid rgba(220,38,38,0.3);"
        )
        abl = QHBoxLayout(admin_badge)
        abl.setContentsMargins(12, 8, 12, 8)
        at = QLabel("🛡 Панель администратора")
        at.setStyleSheet("color: #FCA5A5; font-size: 9pt; font-weight: 600;")
        abl.addWidget(at)
        sb.addWidget(admin_badge)
        sb.addSpacing(8)

        name_lbl = QLabel(self.user.get("full_name") or "Администратор")
        name_lbl.setStyleSheet("color: #94A3B8; font-size: 9pt; padding: 0 8px;")
        sb.addWidget(name_lbl)
        sb.addSpacing(8)

        nav_items = [
            ("📊", "Обзор",          0),
            ("👥", "Пользователи",   1),
            ("📋", "Заявки",         2),
            ("🏢", "Компании",       3),
            ("💳", "Платежи",        4),
            ("💬", "Сообщения",      5),
        ]
        self._nav_btns: list[QPushButton] = []
        for icon, label, idx in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setStyleSheet(NAV_BTN_STYLE)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda _, i=idx: self._nav(i))
            self._nav_btns.append(btn)
            sb.addWidget(btn)

        sb.addStretch()

        btn_logout = QPushButton("  ⬅  Выйти")
        btn_logout.setStyleSheet(
            "background: transparent; color: #EF4444; border: none; "
            "border-radius: 8px; padding: 10px 16px; text-align: left; font-size: 10pt;"
        )
        btn_logout.setFixedHeight(44)
        btn_logout.clicked.connect(self._logout)
        sb.addWidget(btn_logout)

        layout.addWidget(sidebar)

        # ── Content ───────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {C_CONTENT_BG};")
        layout.addWidget(self.stack)

        self.stack.addWidget(self._build_overview())   # 0
        self.stack.addWidget(self._build_users())      # 1
        self.stack.addWidget(self._build_orders())     # 2
        self.stack.addWidget(self._build_companies())  # 3
        self.stack.addWidget(self._build_payments())   # 4
        self.stack.addWidget(self._build_messages())   # 5

        self._nav(0)

    def _start_timer(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(5000)

    def _tick(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            self._refresh_overview()
        elif idx == 1:
            self._reload_users()
        elif idx == 2:
            self._reload_orders()
        elif idx == 3:
            self._reload_companies()
        elif idx == 4:
            self._reload_payments()

    # ── Overview ──────────────────────────────────────────────────

    def _build_overview(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        w.setFrameShape(QFrame.Shape.NoFrame)
        w.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)

        hdr = QLabel("Обзор системы")
        hdr.setStyleSheet(f"font-size: 22pt; font-weight: 800; color: {C_TEXT};")
        l.addWidget(hdr)

        # Stats rows — store label refs for live update
        self._overview_stat_labels: list[QLabel] = []

        row1 = QHBoxLayout()
        row1.setSpacing(14)
        for lbl, color in [
            ("Всего пользователей", C_PRIMARY),
            ("Грузоотправителей",   "#0EA5E9"),
            ("Перевозчиков",        "#7C3AED"),
            ("Компаний",            "#F59E0B"),
        ]:
            card, val_lbl = self._stat_card_live("—", lbl, color)
            self._overview_stat_labels.append(val_lbl)
            row1.addWidget(card)
        l.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(14)
        for lbl, color in [
            ("Всего заявок",  C_TEXT),
            ("Новых заявок",  "#F59E0B"),
            ("В работе",      "#0EA5E9"),
            ("Оборот (₽)",    C_SUCCESS),
        ]:
            card, val_lbl = self._stat_card_live("—", lbl, color)
            self._overview_stat_labels.append(val_lbl)
            row2.addWidget(card)
        l.addLayout(row2)

        hdr2 = QLabel("Последние регистрации")
        hdr2.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {C_TEXT};")
        l.addWidget(hdr2)

        self._overview_users_tbl = self._make_table(
            ["ID", "Логин", "Имя", "Роль", "Баланс", "Дата", "Статус"], []
        )
        l.addWidget(self._overview_users_tbl)
        l.addStretch()
        w.setWidget(inner)

        self._refresh_overview()
        return w

    def _refresh_overview(self):
        users       = UserModel.get_all()
        customers   = [u for u in users if u["role"] == "customer"]
        carriers    = [u for u in users if u["role"] == "carrier"]
        order_stats = OrderModel.stats()
        companies   = CompanyModel.get_all()
        payments    = PaymentModel.get_all()
        total_pay   = sum(p.get("amount", 0) for p in payments if p["status"] == "released")

        vals = [
            str(len(users)),
            str(len(customers)),
            str(len(carriers)),
            str(len(companies)),
            str(order_stats["total"]),
            str(order_stats["new"]),
            str(order_stats["in_progress"]),
            fmt_money(total_pay),
        ]
        for lbl, val in zip(self._overview_stat_labels, vals):
            lbl.setText(val)

        tbl = self._overview_users_tbl
        tbl.setRowCount(0)
        recent = sorted(users, key=lambda x: x.get("created_at", ""), reverse=True)[:10]
        for u in recent:
            row = tbl.rowCount()
            tbl.insertRow(row)
            tbl.setItem(row, 0, QTableWidgetItem(str(u["id"])))
            tbl.setItem(row, 1, QTableWidgetItem(u["username"]))
            tbl.setItem(row, 2, QTableWidgetItem(u.get("full_name", "")))
            tbl.setItem(row, 3, QTableWidgetItem(u["role"]))
            bal = UserModel.get_balance(u["id"])
            tbl.setItem(row, 4, QTableWidgetItem(fmt_money(bal)))
            tbl.setItem(row, 5, QTableWidgetItem(fmt_date(u.get("created_at", ""))))
            si = QTableWidgetItem("Активен" if u.get("is_active") else "Заблокирован")
            si.setForeground(QColor(C_SUCCESS if u.get("is_active") else C_DANGER))
            tbl.setItem(row, 6, si)

    # ── Users ─────────────────────────────────────────────────────

    def _build_users(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {C_CONTENT_BG};")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(16)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Управление пользователями")
        hdr.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT};")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()

        self.users_role_filter = QComboBox()
        self.users_role_filter.addItems(["Все", "Заказчики", "Перевозчики", "Администраторы"])
        self.users_role_filter.setFixedSize(170, 36)
        self.users_role_filter.currentIndexChanged.connect(self._reload_users)
        hdr_row.addWidget(self.users_role_filter)
        l.addLayout(hdr_row)

        self.users_table = self._make_table(
            ["ID", "Логин", "Email", "Имя", "Роль", "Город", "Баланс", "Рейтинг", "Дата", "Статус", "Действия"],
            []
        )
        self.users_table.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
        self.users_table.setColumnWidth(0, 40)
        self.users_table.setColumnWidth(10, 170)
        l.addWidget(self.users_table)
        self._reload_users()
        return w

    def _reload_users(self):
        idx   = self.users_role_filter.currentIndex()
        role  = [None, "customer", "carrier", "admin"][idx]
        users = UserModel.get_all(role)

        self.users_table.setRowCount(0)
        for u in users:
            row = self.users_table.rowCount()
            self.users_table.insertRow(row)
            self.users_table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
            self.users_table.setItem(row, 1, QTableWidgetItem(u["username"]))
            self.users_table.setItem(row, 2, QTableWidgetItem(u.get("email", "")))
            self.users_table.setItem(row, 3, QTableWidgetItem(u.get("full_name", "")))
            self.users_table.setItem(row, 4, QTableWidgetItem(u["role"]))
            self.users_table.setItem(row, 5, QTableWidgetItem(u.get("city", "")))
            bal = UserModel.get_balance(u["id"])
            bal_item = QTableWidgetItem(fmt_money(bal))
            bal_item.setForeground(QColor(C_SUCCESS if bal > 0 else C_TEXT_MUTED))
            self.users_table.setItem(row, 6, bal_item)
            self.users_table.setItem(row, 7, QTableWidgetItem(
                f"{u.get('rating', 0):.1f} ({u.get('rating_count', 0)})"
            ))
            self.users_table.setItem(row, 8, QTableWidgetItem(fmt_date(u.get("created_at", ""))))
            si = QTableWidgetItem("Активен" if u.get("is_active") else "Заблокирован")
            si.setForeground(QColor(C_SUCCESS if u.get("is_active") else C_DANGER))
            self.users_table.setItem(row, 9, si)

            if u["role"] != "admin":
                if u.get("is_active"):
                    btn = QPushButton("Заблокировать")
                    btn.setStyleSheet(self._btn_style("#EF4444", "#DC2626"))
                    btn.clicked.connect(lambda _, uid=u["id"]: self._toggle_user(uid, 0))
                else:
                    btn = QPushButton("Разблокировать")
                    btn.setStyleSheet(self._btn_style("#22C55E", "#16A34A"))
                    btn.clicked.connect(lambda _, uid=u["id"]: self._toggle_user(uid, 1))
                self.users_table.setCellWidget(row, 10, self._wrap_btn(btn))

    def _toggle_user(self, user_id: int, is_active: int):
        action = "разблокировать" if is_active else "заблокировать"
        if QMessageBox.question(
            self, "Подтверждение", f"Вы хотите {action} пользователя?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            UserModel.set_active(user_id, is_active)
            self._reload_users()

    # ── Orders ────────────────────────────────────────────────────

    def _build_orders(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {C_CONTENT_BG};")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(16)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Управление заявками")
        hdr.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT};")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()

        self.orders_filter = QComboBox()
        self.orders_filter.addItems(["Все", "Новые", "В работе", "Завершённые", "Отменённые"])
        self.orders_filter.setFixedSize(160, 36)
        self.orders_filter.currentIndexChanged.connect(self._reload_orders)
        hdr_row.addWidget(self.orders_filter)
        l.addLayout(hdr_row)

        self.orders_table = self._make_table(
            ["ID", "Название", "Откуда", "Куда", "Заказчик", "Перевозчик",
             "Бюджет", "Дата", "Статус"],
            []
        )
        l.addWidget(self.orders_table)
        self._reload_orders()
        return w

    def _reload_orders(self):
        idx    = self.orders_filter.currentIndex()
        status = [None, "new", "in_progress", "completed", "cancelled"][idx]
        orders = OrderModel.get_all()
        if status:
            orders = [o for o in orders if o["status"] == status]

        self.orders_table.setRowCount(0)
        for o in orders:
            row = self.orders_table.rowCount()
            self.orders_table.insertRow(row)
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(o["id"])))
            self.orders_table.setItem(row, 1, QTableWidgetItem(o.get("title", "")))
            self.orders_table.setItem(row, 2, QTableWidgetItem(o.get("from_city", "")))
            self.orders_table.setItem(row, 3, QTableWidgetItem(o.get("to_city", "")))
            self.orders_table.setItem(row, 4, QTableWidgetItem(o.get("customer_name", "")))
            self.orders_table.setItem(row, 5, QTableWidgetItem(o.get("carrier_name", "—")))
            self.orders_table.setItem(row, 6, QTableWidgetItem(fmt_money(o.get("budget", 0))))
            self.orders_table.setItem(row, 7, QTableWidgetItem(fmt_date(o.get("pickup_date", ""))))

            status_val = o.get("status", "")
            si = QTableWidgetItem(STATUS_LABELS.get(status_val, status_val))
            _, fg = STATUS_COLORS.get(status_val, ("#1E293B", C_TEXT_MUTED))
            si.setForeground(QColor(fg))
            self.orders_table.setItem(row, 8, si)

    # ── Companies ─────────────────────────────────────────────────

    def _build_companies(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {C_CONTENT_BG};")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(16)

        hdr = QLabel("Компании перевозчиков")
        hdr.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT};")
        l.addWidget(hdr)

        self.companies_table = self._make_table(
            ["ID", "Название", "Владелец", "Авт.", "₽/км", "Рейтинг", "Заказов", "Проверен", "Действия"],
            []
        )
        self.companies_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.companies_table.setColumnWidth(8, 200)
        l.addWidget(self.companies_table)
        self._reload_companies()
        return w

    def _reload_companies(self):
        companies = CompanyModel.get_all()
        self.companies_table.setRowCount(0)
        for c in companies:
            row = self.companies_table.rowCount()
            self.companies_table.insertRow(row)
            self.companies_table.setItem(row, 0, QTableWidgetItem(str(c["id"])))
            self.companies_table.setItem(row, 1, QTableWidgetItem(c.get("company_name", "")))
            self.companies_table.setItem(row, 2, QTableWidgetItem(c.get("username", "")))
            self.companies_table.setItem(row, 3, QTableWidgetItem(str(c.get("truck_count", 0))))
            self.companies_table.setItem(row, 4, QTableWidgetItem(f"{c.get('price_per_km', 0)} ₽"))
            self.companies_table.setItem(row, 5, QTableWidgetItem(
                f"{c.get('rating', 0):.1f} ({c.get('rating_count', 0)})"
            ))
            self.companies_table.setItem(row, 6, QTableWidgetItem(str(c.get("completed_orders", 0))))
            ver = "✅ Да" if c.get("is_verified") else "❌ Нет"
            vi = QTableWidgetItem(ver)
            vi.setForeground(QColor(C_SUCCESS if c.get("is_verified") else C_DANGER))
            self.companies_table.setItem(row, 7, vi)

            if c.get("is_verified"):
                btn = QPushButton("Снять верификацию")
                btn.setStyleSheet(self._btn_style("#EF4444", "#DC2626"))
                btn.clicked.connect(lambda _, cid=c["id"]: self._toggle_verify(cid, 0))
            else:
                btn = QPushButton("Верифицировать")
                btn.setStyleSheet(self._btn_style("#22C55E", "#16A34A"))
                btn.clicked.connect(lambda _, cid=c["id"]: self._toggle_verify(cid, 1))
            self.companies_table.setCellWidget(row, 8, self._wrap_btn(btn))

    def _toggle_verify(self, company_id: int, is_verified: int):
        CompanyModel.set_verified(company_id, is_verified)
        self._reload_companies()

    # ── Payments ──────────────────────────────────────────────────

    def _build_payments(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {C_CONTENT_BG};")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(16)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Безопасные расчёты")
        hdr.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT};")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        l.addLayout(hdr_row)

        # Live payment stat labels
        self._pay_stat_labels: list[QLabel] = []
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        for lbl, color in [
            ("Общий оборот",  C_PRIMARY),
            ("Удержано",      "#F59E0B"),
            ("Выплачено",     C_SUCCESS),
            ("Транзакций",    C_TEXT),
        ]:
            card, val_lbl = self._stat_card_live("—", lbl, color)
            self._pay_stat_labels.append(val_lbl)
            stats_row.addWidget(card)
        l.addLayout(stats_row)

        desc = QFrame()
        # Type selectors prevent border from cascading to child QLabels
        desc.setStyleSheet(
            "QFrame { background: #1E3A5F; border: 1.5px solid #2563EB; border-radius: 10px; }"
            "QLabel { background: transparent; border: none; }"
        )
        dl = QVBoxLayout(desc)
        dl.setContentsMargins(16, 12, 16, 12)
        dl.setSpacing(4)
        title_lbl = QLabel("ℹ️  Схема безопасных расчётов (Escrow)")
        title_lbl.setStyleSheet("font-weight: 700; color: #93C5FD; font-size: 11pt; border: none;")
        dl.addWidget(title_lbl)
        for txt in [
            "1. Заказчик принимает отклик → средства удерживаются системой (Held)",
            "2. Перевозчик выполняет доставку → заказчик подтверждает прибытие",
            "3. Средства автоматически выплачиваются перевозчику (Released)",
            "4. При спорах — ручное рассмотрение и возврат средств администратором",
        ]:
            lbl = QLabel(txt)
            lbl.setStyleSheet("color: #CBD5E1; font-size: 9pt; border: none;")
            dl.addWidget(lbl)
        l.addWidget(desc)

        self._pay_table = self._make_table(
            ["ID", "Заявка", "Сумма", "Статус", "Плательщик", "Получатель", "Транзакция", "Дата", "Действия"],
            []
        )
        self._pay_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self._pay_table.setColumnWidth(8, 270)
        l.addWidget(self._pay_table)
        self._reload_payments()
        return w

    def _reload_payments(self):
        payments = PaymentModel.get_all()

        total    = sum(p.get("amount", 0) for p in payments)
        held     = sum(p.get("amount", 0) for p in payments if p["status"] == "held")
        released = sum(p.get("amount", 0) for p in payments if p["status"] == "released")

        stat_vals = [fmt_money(total), fmt_money(held), fmt_money(released), str(len(payments))]
        for lbl, val in zip(self._pay_stat_labels, stat_vals):
            lbl.setText(val)

        self._pay_table.setRowCount(0)
        for p in payments:
            row = self._pay_table.rowCount()
            self._pay_table.insertRow(row)
            self._pay_table.setItem(row, 0, QTableWidgetItem(str(p["id"])))
            self._pay_table.setItem(row, 1, QTableWidgetItem(p.get("order_title", "")))
            self._pay_table.setItem(row, 2, QTableWidgetItem(fmt_money(p.get("amount", 0))))

            status_val = p["status"]
            status_lbl = PAYMENT_STATUS_LABELS.get(status_val, status_val)
            si = QTableWidgetItem(status_lbl)
            color_map = {
                "pending":  "#F59E0B",
                "held":     "#3B82F6",
                "released": C_SUCCESS,
                "refunded": C_DANGER,
            }
            si.setForeground(QColor(color_map.get(status_val, C_TEXT_MUTED)))
            self._pay_table.setItem(row, 3, si)

            self._pay_table.setItem(row, 4, QTableWidgetItem(p.get("payer_name", "")))
            self._pay_table.setItem(row, 5, QTableWidgetItem(p.get("receiver_name", "")))
            self._pay_table.setItem(row, 6, QTableWidgetItem(p.get("transaction_id", "")))
            self._pay_table.setItem(row, 7, QTableWidgetItem(fmt_datetime(p.get("created_at", ""))))

            if status_val == "pending":
                b = QPushButton("Удержать")
                b.setStyleSheet(self._btn_style("#3B82F6", "#2563EB"))
                b.clicked.connect(lambda _, pid=p["id"]: self._hold_payment(pid))
                self._pay_table.setCellWidget(row, 8, self._wrap_btn(b))
            elif status_val == "held":
                b1 = QPushButton("✅ Выплатить")
                b1.setStyleSheet(self._btn_style("#16A34A", "#15803D"))
                b1.clicked.connect(lambda _, pid=p["id"]: self._release_payment(pid))
                b2 = QPushButton("↩ Возврат")
                b2.setStyleSheet(self._btn_style(
                    "transparent", "rgba(239,68,68,0.12)",
                    text_color="#EF4444", border="1px solid #EF4444"
                ))
                b2.clicked.connect(lambda _, pid=p["id"]: self._refund_payment(pid))
                w = QWidget(); w.setStyleSheet("background: transparent;")
                wl = QHBoxLayout(w)
                wl.setContentsMargins(4, 4, 4, 4)
                wl.setSpacing(5)
                wl.addWidget(b1)
                wl.addWidget(b2)
                self._pay_table.setCellWidget(row, 8, w)
            else:
                self._pay_table.setCellWidget(row, 8, QWidget())

    def _hold_payment(self, pid: int):
        PaymentModel.hold(pid)
        self._reload_payments()

    def _release_payment(self, pid: int):
        if QMessageBox.question(
            self, "Подтверждение", "Выплатить средства перевозчику?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            PaymentModel.release(pid)
            self._reload_payments()

    def _refund_payment(self, pid: int):
        if QMessageBox.question(
            self, "Подтверждение", "Вернуть средства заказчику?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            PaymentModel.refund(pid)
            self._reload_payments()

    # ── Messages ──────────────────────────────────────────────────

    def _build_messages(self) -> QWidget:
        from ui.chat.chat_window import ChatWindow
        w = QWidget()
        w.setStyleSheet(f"background: {C_CONTENT_BG};")
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(16)

        hdr = QLabel("Сообщения (Администратор)")
        hdr.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT};")
        l.addWidget(hdr)

        chat = ChatWindow(self.user)
        l.addWidget(chat)
        return w

    # ── Helpers ───────────────────────────────────────────────────

    def _stat_card_live(self, value: str, label: str, color: str) -> tuple:
        card = QFrame()
        # Use type selectors so labels inside DON'T inherit card border
        card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border-radius: 12px; }}"
            f"QLabel {{ background: transparent; border: none; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 18, 20, 18)
        cl.setSpacing(4)
        vl = QLabel(value)
        vl.setStyleSheet(f"font-size: 20pt; font-weight: 800; color: {color};")
        cl.addWidget(vl)
        ll = QLabel(label)
        ll.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
        cl.addWidget(ll)
        return card, vl

    # ── Button-cell helpers ───────────────────────────────────────

    @staticmethod
    def _btn_style(bg: str, hover: str, text_color: str = "white",
                   border: str = "none") -> str:
        return (
            f"QPushButton {{ background: {bg}; color: {text_color}; "
            f"border: {border}; border-radius: 5px; "
            f"font-size: 9pt; font-weight: 700; "
            f"padding: 0 10px; min-height: 0; }}"
            f"QPushButton:hover {{ background: {hover}; }}"
        )

    @staticmethod
    def _wrap_btn(btn: "QPushButton", spacing: int = 0) -> "QWidget":
        """Wrap a button in a transparent cell widget with 4 px margin."""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QHBoxLayout(w)
        l.setContentsMargins(4, 4, 4, 4)
        l.setSpacing(spacing)
        l.addWidget(btn)
        return w

    def _make_table(self, headers: list, rows: list) -> QTableWidget:
        tbl = QTableWidget()
        tbl.setColumnCount(len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.verticalHeader().setDefaultSectionSize(42)
        tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tbl.setRowCount(len(rows))
        for r, row_data in enumerate(rows):
            for c, val in enumerate(row_data):
                tbl.setItem(r, c, QTableWidgetItem(str(val)))
        return tbl

    def _nav(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_btns):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _logout(self):
        from ui.auth.login_window import LoginWindow
        self._login = LoginWindow()
        self._login.show()
        self.close()
