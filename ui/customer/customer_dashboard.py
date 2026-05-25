from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QScrollArea, QFrame, QFileDialog,
    QLineEdit, QTextEdit, QFormLayout,
    QDoubleSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath

from database.models import (
    OrderModel, UserModel, NotificationModel, MessageModel
)
from ui.styles import (
    C_SIDEBAR_BG, C_CONTENT_BG, C_CARD_BG, C_BORDER, C_TEXT,
    C_TEXT_MUTED, C_PRIMARY, NAV_BTN_STYLE, C_SUCCESS, C_WARNING,
    show_info, show_warning, show_question
)
from ui.customer.orders_window import CustomerOrdersWindow
from ui.customer.carriers_window import CarriersWindow
from ui.chat.chat_window import ChatWindow
from utils.helpers import save_avatar, fmt_date, stars_text, fmt_money


class _ClickableFrame(QFrame):
    """QFrame that emits clicked() on left mouse press."""
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CustomerDashboard(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"FreightExchange — {user.get('full_name') or user['username']}")
        self.setMinimumSize(1100, 700)
        self._build()
        self._start_timers()

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
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 0, 12, 16)
        sb_layout.setSpacing(4)

        # Logo
        logo_area = QWidget()
        logo_area.setStyleSheet(f"background: {C_SIDEBAR_BG};")
        logo_area.setFixedHeight(64)
        la = QHBoxLayout(logo_area)
        la.setContentsMargins(8, 0, 8, 0)
        logo_lbl = QLabel("🚛 FreightExchange")
        logo_lbl.setStyleSheet(
            "color: #0F172A; font-size: 13pt; font-weight: 800; letter-spacing: 0.5px;"
        )
        la.addWidget(logo_lbl)
        sb_layout.addWidget(logo_area)

        # User card
        user_card = QFrame()
        user_card.setStyleSheet(
            "background: #F8FAFC; border-radius: 10px; border: 1px solid #E2E8F0;"
        )
        ucl = QVBoxLayout(user_card)
        ucl.setContentsMargins(12, 12, 12, 10)
        ucl.setSpacing(4)

        self.avatar_lbl = QLabel("👤")
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet(
            "font-size: 26pt; background: #E2E8F0; "
            "border-radius: 28px; min-width: 56px; min-height: 56px;"
        )
        self.avatar_lbl.setFixedSize(56, 56)
        ucl.addWidget(self.avatar_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        self._refresh_avatar()

        self.name_lbl = QLabel(self.user.get("full_name") or self.user["username"])
        self.name_lbl.setStyleSheet(
            "color: #0F172A; font-weight: 600; font-size: 10pt; "
            "background: transparent; border: none;"
        )
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_lbl.setWordWrap(True)
        ucl.addWidget(self.name_lbl)

        role_lbl = QLabel("Грузоотправитель")
        role_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 8pt; background: transparent; border: none;"
        )
        role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ucl.addWidget(role_lbl)

        # Balance
        self._bal_lbl = QLabel(fmt_money(self.user.get("balance", 0)))
        self._bal_lbl.setStyleSheet(
            "color: #16A34A; font-size: 9pt; font-weight: 700; "
            "background: transparent; border: none;"
        )
        self._bal_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ucl.addWidget(self._bal_lbl)

        btn_topup = QPushButton("+ Пополнить")
        btn_topup.setStyleSheet(
            "background: #F0FDF4; color: #16A34A; border: 1px solid #16A34A; "
            "border-radius: 6px; padding: 4px 10px; font-size: 8pt; font-weight: 600;"
        )
        btn_topup.setFixedHeight(26)
        btn_topup.clicked.connect(self._topup_balance)
        ucl.addWidget(btn_topup)

        sb_layout.addWidget(user_card)
        sb_layout.addSpacing(8)

        # Navigation
        nav_items = [
            ("🏠", "Главная",     0),
            ("📋", "Мои заявки", 1),
            ("🚚", "Перевозчики", 2),
            ("💬", "Сообщения",   3),
            ("🔔", "Уведомления", 4),
            ("👤", "Профиль",     5),
        ]
        self._nav_btns: list[QPushButton] = []
        for icon, label, idx in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setStyleSheet(NAV_BTN_STYLE)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda _, i=idx: self._nav(i))
            self._nav_btns.append(btn)
            sb_layout.addWidget(btn)

        sb_layout.addStretch()

        # Settings
        btn_settings = QPushButton("  ⚙  Настройки")
        btn_settings.setStyleSheet(
            "background: transparent; color: #64748B; border: none; "
            "border-radius: 8px; padding: 10px 16px; text-align: left; font-size: 10pt;"
        )
        btn_settings.setFixedHeight(40)
        btn_settings.clicked.connect(self._open_settings)
        sb_layout.addWidget(btn_settings)

        btn_logout = QPushButton("  ⬅  Выйти")
        btn_logout.setStyleSheet(
            "background: transparent; color: #EF4444; border: none; "
            "border-radius: 8px; padding: 10px 16px; text-align: left; font-size: 10pt;"
        )
        btn_logout.setFixedHeight(44)
        btn_logout.clicked.connect(self._logout)
        sb_layout.addWidget(btn_logout)

        layout.addWidget(sidebar)

        # ── Content ───────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {C_CONTENT_BG};")
        layout.addWidget(self.stack)

        self.home_page = self._build_home()
        self.stack.addWidget(self.home_page)                     # 0

        self.orders_page = CustomerOrdersWindow(self.user)
        self.stack.addWidget(self.orders_page)                   # 1

        self.carriers_page = CarriersWindow(self.user)
        self.carriers_page.chat_with.connect(self._open_chat_with)
        self.stack.addWidget(self.carriers_page)                 # 2

        self.chat_page = ChatWindow(self.user)
        self.stack.addWidget(self.chat_page)                     # 3

        self.stack.addWidget(self._build_notifications())        # 4

        self.stack.addWidget(self._build_profile())              # 5

        self.stack.addWidget(self._build_create_order_page())   # 6
        self.stack.addWidget(self._build_balance_page())         # 7
        self.stack.addWidget(self._build_settings_page())        # 8

        self._prev_page = 0
        self._nav(0)

    # ── Home ──────────────────────────────────────────────────────

    def _build_home(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        w.setFrameShape(QFrame.Shape.NoFrame)
        w.setStyleSheet("background: transparent; border: none;")

        self._home_inner = QWidget()
        self._home_inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(self._home_inner)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)

        name = self.user.get("full_name") or self.user["username"]
        greeting = QLabel(f"Добро пожаловать, {name}! 👋")
        greeting.setStyleSheet(f"font-size: 22pt; font-weight: 800; color: {C_TEXT};")
        l.addWidget(greeting)

        sub = QLabel("Управляйте своими заявками на перевозку из одного места")
        sub.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt;")
        l.addWidget(sub)

        # Stats row — store refs for live update
        self._home_stats_row = QHBoxLayout()
        self._home_stats_row.setSpacing(14)
        self._home_stat_frames: list[tuple[QLabel, QLabel]] = []
        for val, lbl, color in [("—", "Всего заявок", C_PRIMARY),
                                  ("—", "Новых", "#F59E0B"),
                                  ("—", "В работе", "#0EA5E9"),
                                  ("—", "Завершено", C_SUCCESS)]:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 2px solid {color}; border-radius: 12px; }} "
                f"QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(24, 22, 24, 22)
            cl.setSpacing(6)
            vl = QLabel(val)
            vl.setStyleSheet(f"font-size: 38pt; font-weight: 800; color: {color};")
            ll = QLabel(lbl)
            ll.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; font-weight: 600;")
            cl.addWidget(vl)
            cl.addWidget(ll)
            self._home_stat_frames.append((vl, ll))
            self._home_stats_row.addWidget(card)
        l.addLayout(self._home_stats_row)

        # Quick actions
        qa_lbl = QLabel("Быстрые действия")
        qa_lbl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {C_TEXT};")
        l.addWidget(qa_lbl)

        qa_row = QHBoxLayout()
        qa_row.setSpacing(12)

        btn_new = self._action_card("➕", "Новая заявка", "Разместить заявку на перевозку", C_PRIMARY)
        btn_new.clicked.connect(self._create_order)
        qa_row.addWidget(btn_new)

        btn_carriers = self._action_card("🚚", "Перевозчики", "Найти надёжного перевозчика", "#0EA5E9")
        btn_carriers.clicked.connect(lambda: self._nav(2))
        qa_row.addWidget(btn_carriers)

        btn_orders = self._action_card("📋", "Мои заявки", "Управление текущими заявками", "#7C3AED")
        btn_orders.clicked.connect(lambda: self._nav(1))
        qa_row.addWidget(btn_orders)

        l.addLayout(qa_row)

        # Recent orders label + container
        recent_lbl = QLabel("Последние заявки")
        recent_lbl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {C_TEXT};")
        l.addWidget(recent_lbl)

        self._home_recent_container = QVBoxLayout()
        self._home_recent_container.setSpacing(10)
        l.addLayout(self._home_recent_container)

        l.addStretch()
        w.setWidget(self._home_inner)
        self._refresh_home_data()
        return w

    def _refresh_home_data(self):
        orders = OrderModel.get_by_customer(self.user["id"])
        total   = len(orders)
        active  = sum(1 for o in orders if o["status"] == "in_progress")
        done    = sum(1 for o in orders if o["status"] == "completed")
        new_cnt = sum(1 for o in orders if o["status"] == "new")

        for (vl, _), val in zip(self._home_stat_frames,
                                 [str(total), str(new_cnt), str(active), str(done)]):
            vl.setText(val)

        # Clear and repopulate recent orders
        while self._home_recent_container.count():
            item = self._home_recent_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        recent = orders[:3]
        if recent:
            from ui.widgets.order_card import OrderCard
            for o in recent:
                oc = OrderCard(o, mode="customer")
                oc.clicked.connect(lambda _: self._nav(1))
                oc.status_changed.connect(self._quick_status_change)
                self._home_recent_container.addWidget(oc)
        else:
            emp = QFrame()
            emp.setStyleSheet(
                f"QFrame {{ background: {C_CARD_BG}; border: 1.5px dashed {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
            )
            el = QVBoxLayout(emp)
            el.setContentsMargins(24, 32, 24, 32)
            el_lbl = QLabel("У вас пока нет заявок\nНажмите «Новая заявка», чтобы разместить первую")
            el_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            el_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt;")
            el.addWidget(el_lbl)
            self._home_recent_container.addWidget(emp)

    def _action_card(self, icon: str, title: str, desc: str, color: str) -> QPushButton:
        btn = QPushButton()
        btn.setFixedHeight(130)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_CARD_BG};
                border: 1.5px solid {C_BORDER};
                border-radius: 14px;
                text-align: left;
                padding: 16px;
            }}
            QPushButton:hover {{
                border-color: {color};
                background: {C_CARD_BG};
            }}
        """)
        inner = QVBoxLayout(btn)
        inner.setContentsMargins(20, 16, 20, 16)
        inner.setSpacing(8)
        ico = QLabel(icon)
        ico.setStyleSheet(f"font-size: 28pt; color: {color}; background: transparent;")
        inner.addWidget(ico)
        tl = QLabel(title)
        tl.setStyleSheet(f"font-weight: 700; font-size: 13pt; color: {C_TEXT}; background: transparent;")
        inner.addWidget(tl)
        dl = QLabel(desc)
        dl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10pt; background: transparent;")
        dl.setWordWrap(True)
        inner.addWidget(dl)
        return btn

    # ── Notifications ─────────────────────────────────────────────

    def _build_notifications(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        w.setFrameShape(QFrame.Shape.NoFrame)
        w.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(12)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Уведомления")
        hdr.setProperty("heading", "true")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        btn_mark = QPushButton("Прочитать все")
        btn_mark.setProperty("cls", "secondary")
        btn_mark.setFixedSize(150, 34)
        btn_mark.clicked.connect(lambda: (
            NotificationModel.mark_all_read(self.user["id"]),
            self._refresh_badges()
        ))
        hdr_row.addWidget(btn_mark)
        l.addLayout(hdr_row)

        notifs = NotificationModel.get_by_user(self.user["id"])
        type_icons = {
            "message":            "💬",
            "order_accepted":     "✅",
            "order_rejected":     "❌",
            "new_response":       "📩",
            "vehicle_assigned":   "🚛",
            "dispatch_confirmed": "📦",
            "cargo_dispatched":   "📦",
            "cargo_arrived":      "📍",
            "payment_released":   "💳",
            "direct_invitation":  "🎯",
        }

        # Pages: 0=Home, 1=Orders, 2=Carriers, 3=Chat, 4=Notifications, 5=Profile
        _dest = {
            "message":            3,   # → Chat
            "new_response":       1,   # → Orders
            "order_accepted":     1,
            "order_rejected":     1,
            "vehicle_assigned":   1,
            "dispatch_confirmed": 1,
            "cargo_dispatched":   1,
            "cargo_arrived":      1,
            "payment_released":   1,
            "direct_invitation":  2,   # → Carriers
        }

        from utils.helpers import fmt_datetime

        def _on_notif_click(notif_id: int, ntype: str):
            NotificationModel.mark_read(notif_id)
            self._refresh_badges()
            dest = _dest.get(ntype, 1)
            self._nav(dest)

        for n in notifs:
            is_read = bool(n["is_read"])
            bg       = C_CARD_BG if is_read else "#EFF6FF"
            border   = C_BORDER  if is_read else "#2563EB"

            nf = _ClickableFrame()
            oid = f"nc_{n['id']}"
            nf.setObjectName(oid)
            nf.setStyleSheet(
                f"#{oid} {{ background: {bg}; border: 1.5px solid {border}; border-radius: 10px; }}"
                f"#{oid}:hover {{ background: #F1F5F9; border: 1.5px solid #3B82F6; }}"
            )
            nf.setCursor(Qt.CursorShape.PointingHandCursor)
            nf.clicked.connect(lambda _=None, nid=n["id"], nt=n["type"]: _on_notif_click(nid, nt))

            nl = QHBoxLayout(nf)
            nl.setContentsMargins(18, 14, 18, 14)
            nl.setSpacing(14)

            ico = QLabel(type_icons.get(n["type"], "🔔"))
            ico.setStyleSheet("font-size: 24pt; background: transparent;")
            ico.setFixedSize(44, 44)
            nl.addWidget(ico)

            text_col = QVBoxLayout()
            text_col.setSpacing(4)
            title_l = QLabel(n["title"])
            fw = "700" if not is_read else "600"
            title_l.setStyleSheet(f"font-weight: {fw}; font-size: 13pt; color: {C_TEXT}; background: transparent;")
            text_col.addWidget(title_l)
            if n.get("message"):
                msg_l = QLabel(n["message"])
                msg_l.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt; background: transparent;")
                msg_l.setWordWrap(True)
                text_col.addWidget(msg_l)
            dt_l = QLabel(fmt_datetime(n.get("created_at", "")))
            dt_l.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10pt; background: transparent;")
            text_col.addWidget(dt_l)

            nl.addLayout(text_col)
            nl.addStretch()

            if not is_read:
                dot = QLabel("●")
                dot.setStyleSheet(f"color: {C_PRIMARY}; font-size: 10pt; background: transparent;")
                nl.addWidget(dot)

            arrow = QLabel("›")
            arrow.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 14pt; background: transparent;")
            nl.addWidget(arrow)

            l.addWidget(nf)

        if not notifs:
            emp = QLabel("Уведомлений нет")
            emp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emp.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12pt; margin: 40px;")
            l.addWidget(emp)

        l.addStretch()
        w.setWidget(inner)
        return w

    # ── Profile ───────────────────────────────────────────────────

    def _build_profile(self) -> QWidget:
        w = QScrollArea()
        w.setWidgetResizable(True)
        w.setFrameShape(QFrame.Shape.NoFrame)
        w.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)

        hdr = QLabel("Мой профиль")
        hdr.setProperty("heading", "true")
        l.addWidget(hdr)

        prof_card = QFrame()
        prof_card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )
        pcl = QVBoxLayout(prof_card)
        pcl.setContentsMargins(28, 24, 28, 24)
        pcl.setSpacing(16)

        # Avatar + info row
        av_row = QHBoxLayout()
        av_row.setSpacing(20)
        self.prof_avatar = QLabel("👤")
        self.prof_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prof_avatar.setFixedSize(90, 90)
        self.prof_avatar.setStyleSheet(
            f"font-size: 44pt; background: {C_CONTENT_BG}; border-radius: 45px; "
            f"border: 3px solid {C_PRIMARY};"
        )
        self._refresh_profile_avatar()
        av_row.addWidget(self.prof_avatar)

        av_info = QVBoxLayout()
        av_info.setSpacing(6)
        av_name = QLabel(self.user.get("full_name") or self.user["username"])
        av_name.setStyleSheet(f"font-size: 16pt; font-weight: 700; color: {C_TEXT};")
        av_info.addWidget(av_name)

        orders = OrderModel.get_by_customer(self.user["id"])
        done_cnt = sum(1 for o in orders if o["status"] == "completed")
        av_stat = QLabel(f"Заявок: {len(orders)}  |  Завершено: {done_cnt}")
        av_stat.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10pt;")
        av_info.addWidget(av_stat)

        # Balance in profile
        bal = UserModel.get_balance(self.user["id"])
        bal_lbl = QLabel(f"💰 Баланс: {fmt_money(bal)}")
        bal_lbl.setStyleSheet(f"color: #16A34A; font-size: 10pt; font-weight: 600;")
        av_info.addWidget(bal_lbl)

        btn_av = QPushButton("✎ Изменить фото")
        btn_av.setFixedSize(150, 34)
        btn_av.setStyleSheet(
            "QPushButton { background: transparent; color: #3B82F6; border: 1.5px solid #3B82F6; "
            "border-radius: 8px; font-size: 9pt; font-weight: 600; }"
            "QPushButton:hover { background: rgba(59,130,246,0.12); }"
        )
        btn_av.clicked.connect(self._change_avatar)
        av_info.addWidget(btn_av)
        av_row.addLayout(av_info)
        av_row.addStretch()
        pcl.addLayout(av_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {C_BORDER}; max-height: 1px; border: none; border-radius: 0;")
        pcl.addWidget(sep)

        fl = QFormLayout()
        fl.setSpacing(12)
        fl.setContentsMargins(0, 0, 0, 0)

        _inp = (
            "QLineEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
            "color: #0F172A; padding: 4px 12px; font-size: 11pt; }"
            "QLineEdit:focus { border-color: #2563EB; border-width: 2px; background: #EFF6FF; }"
        )
        _ta = (
            "QTextEdit { background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 8px; "
            "color: #0F172A; padding: 6px 12px; font-size: 11pt; }"
            "QTextEdit:focus { border-color: #2563EB; border-width: 2px; }"
        )
        self.pf_fullname = QLineEdit(self.user.get("full_name", ""))
        self.pf_fullname.setFixedHeight(42)
        self.pf_fullname.setStyleSheet(_inp)
        fl.addRow("Полное имя", self.pf_fullname)

        self.pf_phone = QLineEdit(self.user.get("phone", ""))
        self.pf_phone.setFixedHeight(42)
        self.pf_phone.setStyleSheet(_inp)
        fl.addRow("Телефон", self.pf_phone)

        self.pf_city = QLineEdit(self.user.get("city", ""))
        self.pf_city.setFixedHeight(42)
        self.pf_city.setStyleSheet(_inp)
        fl.addRow("Город", self.pf_city)

        self.pf_bio = QTextEdit(self.user.get("bio", ""))
        self.pf_bio.setFixedHeight(100)
        self.pf_bio.setPlaceholderText("Расскажите о себе...")
        self.pf_bio.setStyleSheet(_ta)
        fl.addRow("О себе", self.pf_bio)
        pcl.addLayout(fl)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background: {C_BORDER}; max-height: 1px; border: none; border-radius: 0;")
        pcl.addWidget(sep2)

        pw_lbl = QLabel("Изменение пароля")
        pw_lbl.setStyleSheet(f"font-weight: 600; color: {C_TEXT}; font-size: 11pt;")
        pcl.addWidget(pw_lbl)

        pw_fl = QFormLayout()
        pw_fl.setSpacing(10)
        self.pf_old_pw = QLineEdit()
        self.pf_old_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.pf_old_pw.setFixedHeight(42)
        self.pf_old_pw.setPlaceholderText("Введите текущий пароль")
        self.pf_old_pw.setStyleSheet(_inp)
        pw_fl.addRow("Текущий пароль", self.pf_old_pw)

        self.pf_new_pw = QLineEdit()
        self.pf_new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.pf_new_pw.setFixedHeight(42)
        self.pf_new_pw.setPlaceholderText("Новый пароль (мин. 6 символов)")
        self.pf_new_pw.setStyleSheet(_inp)
        pw_fl.addRow("Новый пароль", self.pf_new_pw)

        self.pf_new_pw2 = QLineEdit()
        self.pf_new_pw2.setEchoMode(QLineEdit.EchoMode.Password)
        self.pf_new_pw2.setFixedHeight(42)
        self.pf_new_pw2.setPlaceholderText("Повторите новый пароль")
        self.pf_new_pw2.setStyleSheet(_inp)
        pw_fl.addRow("Подтвердите пароль", self.pf_new_pw2)
        pcl.addLayout(pw_fl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_pw = QPushButton("🔒 Сменить пароль")
        btn_pw.setFixedSize(190, 44)
        btn_pw.setStyleSheet(
            "QPushButton { background: transparent; color: #3B82F6; border: 2px solid #3B82F6; "
            "border-radius: 8px; font-size: 11pt; font-weight: 600; }"
            "QPushButton:hover { background: rgba(59,130,246,0.12); }"
        )
        btn_pw.clicked.connect(self._change_password)
        btn_row.addWidget(btn_pw)

        btn_save = QPushButton("💾 Сохранить профиль")
        btn_save.setFixedSize(210, 44)
        btn_save.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; font-size: 11pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_save.clicked.connect(self._save_profile)
        btn_row.addWidget(btn_save)
        pcl.addLayout(btn_row)

        l.addWidget(prof_card)
        l.addStretch()
        w.setWidget(inner)
        return w

    # ── Create order (inline page) ────────────────────────────────

    def _build_create_order_page(self) -> QWidget:
        from ui.customer.create_order_dialog import CreateOrderPage
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        vl = QVBoxLayout(page)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # Top bar with back button
        top = QWidget()
        top.setStyleSheet(f"background: {C_CARD_BG}; border-bottom: 1px solid {C_BORDER};")
        top.setFixedHeight(56)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(20, 0, 20, 0)
        btn_back = QPushButton("← Мои заявки")
        btn_back.setStyleSheet(
            "QPushButton { background: transparent; color: #2563EB; border: 2px solid #2563EB; "
            "border-radius: 8px; font-size: 11pt; font-weight: 600; padding: 0 16px; }"
            "QPushButton:hover { background: #EFF6FF; }"
        )
        btn_back.setFixedHeight(40)
        btn_back.clicked.connect(lambda: self._nav(1))
        tl.addWidget(btn_back)
        tl.addStretch()
        vl.addWidget(top)

        self._create_order_form = CreateOrderPage(self.user["id"])
        self._create_order_form.order_created.connect(self._on_order_created)
        self._create_order_form.cancelled.connect(lambda: self._nav(1))
        vl.addWidget(self._create_order_form)

        return page

    # ── Balance page (fullscreen) ─────────────────────────────────

    def _build_balance_page(self) -> QWidget:
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
        btn_back = QPushButton("← Назад")
        btn_back.setStyleSheet(
            "QPushButton { background: transparent; color: #2563EB; border: 2px solid #2563EB; "
            "border-radius: 8px; font-size: 11pt; font-weight: 600; padding: 0 16px; }"
            "QPushButton:hover { background: #EFF6FF; }"
        )
        btn_back.setFixedHeight(40)
        btn_back.clicked.connect(lambda: self._nav(self._prev_page))
        tb.addWidget(btn_back)
        tb.addStretch()
        title = QLabel("💳 Пополнение баланса")
        title.setStyleSheet(f"font-size: 12pt; font-weight: 700; color: {C_TEXT};")
        tb.addWidget(title)
        tb.addSpacing(16)
        outer.addWidget(top_bar)

        # Centered content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 40, 32, 40)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; border-radius: 16px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )
        card.setMaximumWidth(580)
        card.setMinimumWidth(400)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 36, 40, 36)
        cl.setSpacing(20)

        # Current balance display
        bal_bg = QFrame()
        bal_bg.setStyleSheet(
            f"QFrame {{ background: {C_CONTENT_BG}; border: 1.5px solid {C_BORDER}; border-radius: 12px; }} QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )
        bfl = QVBoxLayout(bal_bg)
        bfl.setContentsMargins(24, 18, 24, 18)
        bfl.setSpacing(4)
        ml = QLabel("ТЕКУЩИЙ БАЛАНС")
        ml.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 8pt; font-weight: 700;")
        bfl.addWidget(ml)
        current = UserModel.get_balance(self.user["id"])
        self._bal_page_lbl = QLabel(fmt_money(current))
        self._bal_page_lbl.setStyleSheet(
            f"font-size: 30pt; font-weight: 800; color: {C_PRIMARY};"
        )
        bfl.addWidget(self._bal_page_lbl)
        cl.addWidget(bal_bg)

        # Quick amounts
        qa_lbl = QLabel("Быстрое пополнение")
        qa_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt; font-weight: 700;")
        cl.addWidget(qa_lbl)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(10)
        for amount in [5000, 10000, 25000, 50000]:
            btn = QPushButton(fmt_money(amount))
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {C_PRIMARY}; "
                f"border: 2px solid {C_PRIMARY}; border-radius: 8px; "
                "font-size: 10pt; font-weight: 600; }}"
                "QPushButton:hover { background: rgba(59,130,246,0.12); }"
            )
            btn.setFixedHeight(46)
            btn.clicked.connect(lambda _, a=amount: self._bal_spn.setValue(a))
            quick_row.addWidget(btn)
        cl.addLayout(quick_row)

        # Custom amount
        ca_lbl = QLabel("✏ Или введите сумму:")
        ca_lbl.setStyleSheet("color: #94A3B8; font-size: 10pt; font-weight: 700;")
        cl.addWidget(ca_lbl)

        self._bal_spn = QDoubleSpinBox()
        self._bal_spn.setRange(100, 10_000_000)
        self._bal_spn.setSuffix(" ₽")
        self._bal_spn.setDecimals(0)
        self._bal_spn.setSingleStep(1000)
        self._bal_spn.setValue(10000)
        self._bal_spn.setFixedHeight(56)
        self._bal_spn.setStyleSheet(
            "QDoubleSpinBox { background: #FFFFFF; border: 2px solid #2563EB; border-radius: 10px; "
            "color: #0F172A; padding: 4px 14px; font-size: 15pt; font-weight: 700; }"
            "QDoubleSpinBox:focus { border-color: #1D4ED8; background: #EFF6FF; }"
            "QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 24px; }"
        )
        cl.addWidget(self._bal_spn)

        # Info
        info = QLabel(
            "ℹ️  Средства зачисляются мгновенно и доступны для оплаты заказов."
        )
        info.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9pt;")
        info.setWordWrap(True)
        cl.addWidget(info)

        # Top-up button
        btn_ok = QPushButton("💳  Пополнить")
        btn_ok.setFixedHeight(52)
        btn_ok.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; background: {C_PRIMARY}; "
            "color: white; border-radius: 10px;"
        )
        btn_ok.clicked.connect(lambda: self._do_topup(self._bal_spn.value()))
        cl.addWidget(btn_ok)

        # ── Withdrawal section ────────────────────────────────────
        sep_w = QFrame()
        sep_w.setFrameShape(QFrame.Shape.HLine)
        sep_w.setStyleSheet(f"background: {C_BORDER}; max-height: 1px; border: none; border-radius: 0;")
        cl.addWidget(sep_w)

        wd_lbl = QLabel("💸 Вывод средств")
        wd_lbl.setStyleSheet("color: #94A3B8; font-size: 10pt; font-weight: 700;")
        cl.addWidget(wd_lbl)

        self._withdraw_spn = QDoubleSpinBox()
        self._withdraw_spn.setRange(100, 10_000_000)
        self._withdraw_spn.setSuffix(" ₽")
        self._withdraw_spn.setDecimals(0)
        self._withdraw_spn.setSingleStep(1000)
        self._withdraw_spn.setValue(5000)
        self._withdraw_spn.setFixedHeight(52)
        self._withdraw_spn.setStyleSheet(
            "QDoubleSpinBox { background: #FFFFFF; border: 2px solid #16A34A; border-radius: 10px; "
            "color: #0F172A; padding: 4px 14px; font-size: 14pt; font-weight: 700; }"
            "QDoubleSpinBox:focus { border-color: #15803D; background: #F0FDF4; }"
            "QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 24px; }"
        )
        cl.addWidget(self._withdraw_spn)

        wd_info = QLabel(
            "⚠️  Средства будут списаны с баланса. "
            "Убедитесь, что сумма не превышает текущий баланс."
        )
        wd_info.setStyleSheet("color: #F59E0B; font-size: 9pt;")
        wd_info.setWordWrap(True)
        cl.addWidget(wd_info)

        btn_wd = QPushButton("💸  Вывести средства")
        btn_wd.setFixedHeight(50)
        btn_wd.setStyleSheet(
            "QPushButton { font-size: 11pt; font-weight: 700; background: #16A34A; "
            "color: white; border: 2px solid #22C55E; border-radius: 10px; }"
            "QPushButton:hover { background: #15803D; }"
        )
        btn_wd.clicked.connect(lambda: self._do_withdraw(self._withdraw_spn.value()))
        cl.addWidget(btn_wd)

        center = QHBoxLayout()
        center.addStretch()
        center.addWidget(card)
        center.addStretch()
        root.addLayout(center)

        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    def _do_topup(self, amount: float):
        new_bal = UserModel.add_balance(self.user["id"], amount)
        self.user["balance"] = new_bal
        self._bal_lbl.setText(fmt_money(new_bal))
        if hasattr(self, "_bal_page_lbl"):
            self._bal_page_lbl.setText(fmt_money(new_bal))
        show_info(
            self, "Баланс пополнен",
            f"На ваш счёт зачислено {fmt_money(amount)}.\n"
            f"Текущий баланс: {fmt_money(new_bal)}"
        )
        self._nav(self._prev_page)

    def _do_withdraw(self, amount: float):
        current = UserModel.get_balance(self.user["id"])
        if amount <= 0:
            show_warning(self, "Ошибка", "Введите сумму больше нуля")
            return
        if amount > current:
            show_warning(
                self, "Недостаточно средств",
                f"На балансе {fmt_money(current)}, а запрошено {fmt_money(amount)}.\n"
                "Уменьшите сумму вывода."
            )
            return
        if not show_question(
            self, "Подтверждение вывода",
            f"Вывести {fmt_money(amount)} с баланса?\n"
            f"Остаток после вывода: {fmt_money(current - amount)}"
        ):
            return
        new_bal = UserModel.add_balance(self.user["id"], -amount)
        self.user["balance"] = new_bal
        self._bal_lbl.setText(fmt_money(new_bal))
        if hasattr(self, "_bal_page_lbl"):
            self._bal_page_lbl.setText(fmt_money(new_bal))
        show_info(
            self, "Вывод выполнен",
            f"Выведено {fmt_money(amount)}.\n"
            f"Текущий баланс: {fmt_money(new_bal)}"
        )
        self._nav(self._prev_page)

    # ── Settings page (fullscreen) ────────────────────────────────

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {C_CONTENT_BG};")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setFixedHeight(52)
        top_bar.setStyleSheet(
            f"background: {C_CARD_BG}; border-bottom: 1px solid {C_BORDER};"
        )
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(16, 0, 16, 0)
        btn_back = QPushButton("← Назад")
        btn_back.setStyleSheet(
            "QPushButton { background: transparent; color: #2563EB; border: 2px solid #2563EB; "
            "border-radius: 8px; font-size: 11pt; font-weight: 600; padding: 0 16px; }"
            "QPushButton:hover { background: #EFF6FF; }"
        )
        btn_back.setFixedHeight(40)
        btn_back.clicked.connect(lambda: self._nav(self._prev_page))
        tb.addWidget(btn_back)
        tb.addStretch()
        title_lbl = QLabel("⚙  Настройки")
        title_lbl.setStyleSheet(f"font-size: 12pt; font-weight: 700; color: {C_TEXT};")
        tb.addWidget(title_lbl)
        tb.addSpacing(16)
        outer.addWidget(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        l = QVBoxLayout(inner)
        l.setContentsMargins(24, 20, 24, 20)
        l.setSpacing(14)

        pg_hdr = QLabel("Настройки")
        pg_hdr.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {C_TEXT};")
        l.addWidget(pg_hdr)

        _card_ss = (
            f"QFrame {{ background: {C_CARD_BG}; border: 1.5px solid {C_BORDER}; "
            f"border-radius: 12px; }} "
            f"QLabel {{ border: none; background: transparent; color: {C_TEXT}; }}"
        )

        # ── Уведомления ───────────────────────────────────────────
        notif_card = QFrame()
        notif_card.setStyleSheet(_card_ss)
        ncl = QVBoxLayout(notif_card)
        ncl.setContentsMargins(20, 16, 20, 16)
        ncl.setSpacing(10)

        nc_hdr = QLabel("🔔 Уведомления")
        nc_hdr.setStyleSheet(f"font-size: 15pt; font-weight: 700; color: {C_TEXT};")
        ncl.addWidget(nc_hdr)

        nc_desc = QLabel("Выберите, о чём вы хотите получать уведомления:")
        nc_desc.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt;")
        ncl.addWidget(nc_desc)
        ncl.addSpacing(4)

        for text in [
            "Новые отклики на мои заявки",
            "Сообщения в чате",
            "Изменение статуса заказа",
            "Подтверждение платежа",
        ]:
            cb = QCheckBox(text)
            cb.setChecked(True)
            cb.setStyleSheet(
                "QCheckBox { color: #0F172A; font-size: 12pt; background: transparent; "
                "border: none; spacing: 10px; }"
                "QCheckBox::indicator { width: 20px; height: 20px; border: 2px solid #CBD5E1; "
                "border-radius: 5px; background: #FFFFFF; }"
                "QCheckBox::indicator:checked { background: #2563EB; border-color: #2563EB; }"
                "QCheckBox::indicator:hover { border-color: #2563EB; }"
            )
            ncl.addWidget(cb)

        sv_row = QHBoxLayout()
        sv_row.addStretch()
        btn_sv = QPushButton("💾 Сохранить настройки")
        btn_sv.setFixedSize(220, 44)
        btn_sv.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; font-size: 11pt; font-weight: 700; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        sv_row.addWidget(btn_sv)
        ncl.addLayout(sv_row)
        l.addWidget(notif_card)

        # ── О программе ───────────────────────────────────────────
        about_card = QFrame()
        about_card.setStyleSheet(_card_ss)
        acl = QVBoxLayout(about_card)
        acl.setContentsMargins(20, 20, 20, 20)
        acl.setSpacing(8)

        row_about = QHBoxLayout()
        row_about.setSpacing(16)
        logo = QLabel("🚛")
        logo.setStyleSheet("font-size: 36pt;")
        logo.setFixedSize(60, 60)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_about.addWidget(logo)

        about_info = QVBoxLayout()
        about_info.setSpacing(3)
        app_name = QLabel("FreightExchange")
        app_name.setStyleSheet("font-size: 16pt; font-weight: 800; color: #3B82F6;")
        about_info.addWidget(app_name)
        for line in [
            "Биржа фрахта — Дипломный проект 2026",
            "Python + PyQt6 + PostgreSQL",
        ]:
            ll = QLabel(line)
            ll.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11pt;")
            about_info.addWidget(ll)
        row_about.addLayout(about_info)
        row_about.addStretch()
        acl.addLayout(row_about)
        l.addWidget(about_card)

        l.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    # ── Navigation ────────────────────────────────────────────────

    def _nav(self, index: int):
        # Pages 7+ (balance, settings) don't correspond to sidebar buttons
        if index < len(self._nav_btns):
            for i, btn in enumerate(self._nav_btns):
                btn.setProperty("active", "true" if i == index else "false")
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        if index == 4:
            self.stack.removeWidget(self.stack.widget(4))
            notif_page = self._build_notifications()
            self.stack.insertWidget(4, notif_page)
            self.stack.setCurrentIndex(4)
            NotificationModel.mark_all_read(self.user["id"])
            self._refresh_badges()
        else:
            self.stack.setCurrentIndex(index)

    # ── Actions ───────────────────────────────────────────────────

    def _create_order(self):
        self._nav(6)

    def _on_order_created(self, order_id: int):
        self.orders_page.refresh()
        self._refresh_home_data()
        self._create_order_form.reset()
        show_info(
            self, "Заявка создана",
            "Заявка успешно размещена!\nПеревозчики смогут подать отклики."
        )
        self._nav(1)

    def _quick_status_change(self, order_id: int, status: str):
        OrderModel.update_status(order_id, status)
        self._refresh_home_data()

    def _open_chat_with(self, user: dict):
        self._nav(3)
        self.chat_page.open_with_user(user)

    def _topup_balance(self):
        self._prev_page = self.stack.currentIndex()
        # Rebuild to show fresh balance
        old = self.stack.widget(7)
        self.stack.removeWidget(old)
        old.deleteLater()
        self.stack.insertWidget(7, self._build_balance_page())
        self._nav(7)

    def _on_balance_updated(self, new_bal: float):
        self.user["balance"] = new_bal
        self._bal_lbl.setText(fmt_money(new_bal))

    def _open_settings(self):
        self._prev_page = self.stack.currentIndex()
        self._nav(8)

    # ── Profile actions ───────────────────────────────────────────

    def _change_avatar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            dest = save_avatar(path, self.user["id"])
            UserModel.update_avatar(self.user["id"], dest)
            self.user["avatar_path"] = dest
            self._refresh_avatar()
            self._refresh_profile_avatar()

    @staticmethod
    def _circular_pixmap(path: str, size: int) -> QPixmap:
        """Return a circular-cropped QPixmap from an image file."""
        source = QPixmap(path)
        if source.isNull():
            return source
        scaled = source.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Centre-crop to exact square
        x = (scaled.width()  - size) // 2
        y = (scaled.height() - size) // 2
        scaled = scaled.copy(x, y, size, size)
        # Mask to circle
        result = QPixmap(size, size)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        clip = QPainterPath()
        clip.addEllipse(0, 0, float(size), float(size))
        painter.setClipPath(clip)
        painter.drawPixmap(0, 0, scaled)
        painter.end()
        return result

    def _refresh_avatar(self):
        path = self.user.get("avatar_path", "")
        if path:
            try:
                pix = self._circular_pixmap(path, 54)
                self.avatar_lbl.setPixmap(pix)
                self.avatar_lbl.setText("")
            except Exception:
                pass

    def _refresh_profile_avatar(self):
        path = self.user.get("avatar_path", "")
        if path and hasattr(self, "prof_avatar"):
            try:
                pix = self._circular_pixmap(path, 88)
                self.prof_avatar.setPixmap(pix)
                self.prof_avatar.setText("")
            except Exception:
                pass

    def _save_profile(self):
        UserModel.update_profile(
            self.user["id"],
            self.pf_fullname.text().strip(),
            self.pf_phone.text().strip(),
            self.pf_city.text().strip(),
            self.pf_bio.toPlainText().strip()
        )
        self.user["full_name"] = self.pf_fullname.text().strip()
        self.name_lbl.setText(self.user["full_name"] or self.user["username"])
        show_info(self, "Готово", "Профиль сохранён")

    def _change_password(self):
        old_pw  = self.pf_old_pw.text()
        new_pw  = self.pf_new_pw.text()
        new_pw2 = self.pf_new_pw2.text()
        if not all([old_pw, new_pw, new_pw2]):
            show_warning(self, "Ошибка", "Заполните все поля пароля")
            return
        if new_pw != new_pw2:
            show_warning(self, "Ошибка", "Новые пароли не совпадают")
            return
        if len(new_pw) < 6:
            show_warning(self, "Ошибка", "Пароль должен быть не менее 6 символов")
            return
        ok, msg = UserModel.change_password(self.user["id"], old_pw, new_pw)
        if ok:
            show_info(self, "Готово", msg)
            self.pf_old_pw.clear()
            self.pf_new_pw.clear()
            self.pf_new_pw2.clear()
        else:
            show_warning(self, "Ошибка", msg)

    def _logout(self):
        from ui.auth.login_window import LoginWindow
        self._login = LoginWindow()
        self._login.show()
        self.close()

    # ── Timers — real-time refresh ────────────────────────────────

    def _start_timers(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(4000)

    def _tick(self):
        self._refresh_badges()
        idx = self.stack.currentIndex()
        if idx == 0:
            self._refresh_home_data()
        elif idx == 1:
            self.orders_page.refresh()
        elif idx == 3:
            self.chat_page.refresh() if hasattr(self.chat_page, "refresh") else None

    def _refresh_badges(self):
        count     = NotificationModel.get_unread_count(self.user["id"])
        msg_count = MessageModel.get_unread_count(self.user["id"])
        self._nav_btns[4].setText(
            f"  🔔  Уведомления{f'  ({count})' if count else ''}"
        )
        self._nav_btns[3].setText(
            f"  💬  Сообщения{f'  ({msg_count})' if msg_count else ''}"
        )
        # Refresh balance display
        bal = UserModel.get_balance(self.user["id"])
        self._bal_lbl.setText(fmt_money(bal))
        self.user["balance"] = bal
