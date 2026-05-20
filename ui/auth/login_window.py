from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QSizePolicy, QMessageBox,
    QStackedWidget, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt

from database.models import UserModel


# ── Shared helpers ─────────────────────────────────────────────────────

def _field_row(parent_layout, label_text: str, placeholder: str = "",
               password: bool = False) -> QLineEdit:
    lbl = QLabel(label_text)
    lbl.setStyleSheet(
        "font-weight: 600; font-size: 9pt; color: #94A3B8; "
        "background: transparent; border: none;"
    )
    parent_layout.addWidget(lbl)
    inp = QLineEdit()
    inp.setPlaceholderText(placeholder if placeholder else "Введите текст...")
    inp.setFixedHeight(46)
    inp.setStyleSheet(
        "QLineEdit { background: #1A2540; border: 2px solid #3B82F6; border-radius: 10px; "
        "color: #F1F5F9; padding: 8px 14px; font-size: 11pt; }"
        "QLineEdit:focus { border-color: #60A5FA; background: #1E3050; }"
    )
    if password:
        inp.setEchoMode(QLineEdit.EchoMode.Password)
    parent_layout.addWidget(inp)
    return inp


def _section(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "font-size: 10pt; font-weight: 700; color: #64748B; "
        "background: transparent; border: none; margin-top: 4px;"
    )
    return lbl


# ── Login page ─────────────────────────────────────────────────────────

class _LoginPage(QFrame):
    def __init__(self, on_login, on_go_register, parent=None):
        super().__init__(parent)
        self._on_login       = on_login
        self._on_go_register = on_go_register
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #1E293B;
                border: 1.5px solid #334155;
                border-radius: 18px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.setFixedWidth(420)

        cl = QVBoxLayout(self)
        cl.setContentsMargins(44, 48, 44, 44)
        cl.setSpacing(16)

        logo = QLabel("🚛")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 44pt; background: transparent; border: none;")
        cl.addWidget(logo)

        title = QLabel("FreightExchange")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 22pt; font-weight: 800; color: #3B82F6; "
            "background: transparent; border: none;"
        )
        cl.addWidget(title)

        subtitle = QLabel("Биржа грузоперевозок")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "color: #64748B; font-size: 10pt; background: transparent; border: none;"
        )
        cl.addWidget(subtitle)
        cl.addSpacing(8)

        self.inp_user = _field_row(cl, "Логин", "Введите логин")
        self.inp_pass = _field_row(cl, "Пароль", "Введите пароль", password=True)
        self.inp_pass.returnPressed.connect(self._do_login)

        self.chk_remember = QCheckBox("Запомнить меня")
        self.chk_remember.setStyleSheet(
            "background: transparent; border: none; color: #64748B;"
        )
        cl.addWidget(self.chk_remember)

        btn_login = QPushButton("Войти")
        btn_login.setFixedHeight(48)
        btn_login.setStyleSheet(
            "background: #2563EB; color: white; border: none; border-radius: 10px; "
            "font-size: 12pt; font-weight: 700;"
        )
        btn_login.clicked.connect(self._do_login)
        cl.addWidget(btn_login)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #334155; border: none; max-height: 1px;")
        cl.addWidget(sep)

        reg_row = QHBoxLayout()
        reg_lbl = QLabel("Нет аккаунта?")
        reg_lbl.setStyleSheet("color: #64748B; background: transparent; border: none;")
        reg_row.addWidget(reg_lbl)
        btn_reg = QPushButton("Зарегистрироваться →")
        btn_reg.setStyleSheet(
            "color: #3B82F6; background: transparent; border: none; "
            "font-weight: 600; font-size: 10pt;"
        )
        btn_reg.clicked.connect(self._on_go_register)
        reg_row.addWidget(btn_reg)
        reg_row.addStretch()
        cl.addLayout(reg_row)

    def _do_login(self):
        username = self.inp_user.text().strip()
        password = self.inp_pass.text()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
        user = UserModel.login(username, password)
        if not user:
            QMessageBox.warning(self, "Ошибка входа", "Неверный логин или пароль")
            self.inp_pass.clear()
            return
        self._on_login(user)


# ── Register page ──────────────────────────────────────────────────────

class _RegisterPage(QFrame):
    def __init__(self, on_registered, on_go_login, parent=None):
        super().__init__(parent)
        self._on_registered = on_registered
        self._on_go_login   = on_go_login
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame#regCard {
                background: #1E293B;
                border: 1.5px solid #334155;
                border-radius: 18px;
            }
        """)
        self.setObjectName("regCard")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.setFixedWidth(460)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(inner)
        cl.setContentsMargins(44, 44, 44, 40)
        cl.setSpacing(12)

        # Header
        hdr_row = QHBoxLayout()
        btn_back = QPushButton("← Назад")
        btn_back.setStyleSheet(
            "color: #3B82F6; background: transparent; border: none; "
            "font-weight: 600; font-size: 10pt;"
        )
        btn_back.clicked.connect(self._on_go_login)
        hdr_row.addWidget(btn_back)
        hdr_row.addStretch()
        cl.addLayout(hdr_row)

        title = QLabel("Создать аккаунт")
        title.setStyleSheet(
            "font-size: 20pt; font-weight: 800; color: #3B82F6; "
            "background: transparent; border: none;"
        )
        cl.addWidget(title)

        subtitle = QLabel("Присоединитесь к платформе FreightExchange")
        subtitle.setStyleSheet(
            "color: #64748B; font-size: 10pt; background: transparent; border: none;"
        )
        cl.addWidget(subtitle)
        cl.addSpacing(6)

        # Section: basic info
        cl.addWidget(_section("— Основные данные"))
        self.inp_username = _field_row(cl, "Логин *", "Введите логин (мин. 3 символа)")
        self.inp_email    = _field_row(cl, "Email *", "example@mail.ru")
        self.inp_fullname = _field_row(cl, "Полное имя *", "Иванов Иван Иванович")

        # Section: contacts
        cl.addWidget(_section("— Контакты (необязательно)"))
        self.inp_phone = _field_row(cl, "Телефон", "+7 (___) ___-__-__")
        self.inp_city  = _field_row(cl, "Город", "Москва")

        # Section: security
        cl.addWidget(_section("— Безопасность"))
        self.inp_password  = _field_row(cl, "Пароль *", "Не менее 6 символов", password=True)
        self.inp_password2 = _field_row(cl, "Подтвердите пароль *", "", password=True)

        # Role
        cl.addWidget(_section("— Роль"))
        role_lbl = QLabel("Выберите роль *")
        role_lbl.setStyleSheet(
            "font-weight: 600; font-size: 9pt; color: #94A3B8; "
            "background: transparent; border: none;"
        )
        cl.addWidget(role_lbl)
        self.cmb_role = QComboBox()
        self.cmb_role.addItem("🏭  Грузоотправитель (Заказчик)", "customer")
        self.cmb_role.addItem("🚛  Перевозчик (Исполнитель)", "carrier")
        self.cmb_role.setFixedHeight(46)
        self.cmb_role.setStyleSheet(
            "QComboBox { background: #1A2540; border: 2px solid #3B82F6; border-radius: 10px; "
            "color: #F1F5F9; padding: 8px 14px; font-size: 10pt; }"
            "QComboBox:focus { border-color: #60A5FA; }"
            "QComboBox::drop-down { border: none; width: 24px; }"
            "QComboBox QAbstractItemView { background: #1E293B; color: #F1F5F9; border: 1px solid #3B82F6; }"
        )
        cl.addWidget(self.cmb_role)
        cl.addSpacing(8)

        btn_reg = QPushButton("Создать аккаунт")
        btn_reg.setFixedHeight(48)
        btn_reg.setStyleSheet(
            "background: #2563EB; color: white; border: none; border-radius: 10px; "
            "font-size: 12pt; font-weight: 700;"
        )
        btn_reg.clicked.connect(self._do_register)
        cl.addWidget(btn_reg)

        login_row = QHBoxLayout()
        login_lbl = QLabel("Уже есть аккаунт?")
        login_lbl.setStyleSheet("color: #64748B; background: transparent; border: none;")
        login_row.addWidget(login_lbl)
        btn_login = QPushButton("Войти")
        btn_login.setStyleSheet(
            "color: #3B82F6; background: transparent; border: none; "
            "font-weight: 600; font-size: 10pt;"
        )
        btn_login.clicked.connect(self._on_go_login)
        login_row.addWidget(btn_login)
        login_row.addStretch()
        cl.addLayout(login_row)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _do_register(self):
        username  = self.inp_username.text().strip()
        email     = self.inp_email.text().strip()
        fullname  = self.inp_fullname.text().strip()
        phone     = self.inp_phone.text().strip()
        city      = self.inp_city.text().strip()
        password  = self.inp_password.text()
        password2 = self.inp_password2.text()
        role      = self.cmb_role.currentData()

        if not all([username, email, fullname, password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля (*)")
            return
        if len(username) < 3:
            QMessageBox.warning(self, "Ошибка", "Логин должен быть не менее 3 символов")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов")
            return
        if password != password2:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
        if "@" not in email:
            QMessageBox.warning(self, "Ошибка", "Введите корректный email")
            return

        ok, msg = UserModel.register(username, email, password, role, fullname, phone, city)
        if ok:
            QMessageBox.information(
                self, "Аккаунт создан",
                f"Добро пожаловать, {fullname or username}!\nТеперь войдите в систему."
            )
            self._on_registered()
        else:
            QMessageBox.warning(self, "Ошибка регистрации", msg)


# ── Combined Login window ───────────────────────────────────────────────

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FreightExchange — Вход")
        self.setMinimumSize(520, 640)
        self.resize(520, 680)
        self._build()

    def _build(self):
        self.setStyleSheet("background: #0F172A;")

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setContentsMargins(30, 30, 30, 30)

        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        # Page 0: Login
        self._login_page = _LoginPage(
            on_login=self._open_dashboard,
            on_go_register=lambda: self._stack.setCurrentIndex(1),
        )
        self._stack.addWidget(self._login_page)

        # Page 1: Register
        self._register_page = _RegisterPage(
            on_registered=self._go_to_login,
            on_go_login=lambda: self._stack.setCurrentIndex(0),
        )
        self._stack.addWidget(self._register_page)

        root.addWidget(self._stack)

    def _go_to_login(self):
        self._stack.setCurrentIndex(0)
        # Clear register fields
        for attr in ("inp_username", "inp_email", "inp_fullname",
                     "inp_phone", "inp_city", "inp_password", "inp_password2"):
            getattr(self._register_page, attr, QLineEdit()).clear()

    def _open_dashboard(self, user: dict):
        role = user["role"]
        if role == "customer":
            from ui.customer.customer_dashboard import CustomerDashboard
            self._dash = CustomerDashboard(user)
        elif role == "carrier":
            from ui.carrier.carrier_dashboard import CarrierDashboard
            self._dash = CarrierDashboard(user)
        else:
            from ui.admin.admin_dashboard import AdminDashboard
            self._dash = AdminDashboard(user)

        self._dash.showMaximized()
        self.close()
