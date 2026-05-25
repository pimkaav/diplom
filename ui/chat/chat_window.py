from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QListWidget, QListWidgetItem,
    QSplitter, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QFont

from database.models import MessageModel, UserModel
from ui.styles import (
    C_CARD_BG, C_BORDER, C_PRIMARY, C_TEXT, C_TEXT_MUTED,
    C_SIDEBAR_BG, C_CONTENT_BG
)
from utils.helpers import fmt_datetime, save_attachment


class MessageBubble(QFrame):
    def __init__(self, msg: dict, is_mine: bool, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none; background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 3, 12, 3)

        if is_mine:
            layout.addStretch()

        bubble = QFrame()
        if is_mine:
            bubble.setStyleSheet(
                "QFrame { background: #2563EB; border-radius: 16px 4px 16px 16px; }"
            )
        else:
            bubble.setStyleSheet(
                "QFrame { background: #F1F5F9; border: 1px solid #E2E8F0; "
                "border-radius: 4px 16px 16px 16px; }"
            )

        bl = QVBoxLayout(bubble)
        bl.setContentsMargins(16, 12, 16, 10)
        bl.setSpacing(5)

        if not is_mine:
            name_lbl = QLabel(msg.get("sender_name", ""))
            name_lbl.setStyleSheet(
                f"font-weight: 700; font-size: 10pt; color: #2563EB; background: transparent;"
            )
            bl.addWidget(name_lbl)

        content = msg.get("content", "")
        if content:
            text_lbl = QLabel(content)
            text_lbl.setStyleSheet(
                f"color: {'#FFFFFF' if is_mine else C_TEXT}; font-size: 12pt; "
                "background: transparent; line-height: 1.5;"
            )
            text_lbl.setWordWrap(True)
            text_lbl.setMaximumWidth(520)
            bl.addWidget(text_lbl)

        attachment = msg.get("attachment_path", "")
        if attachment:
            fname = attachment.split("/")[-1].split("\\")[-1]
            att_lbl = QLabel(f"📎 {fname}")
            att_lbl.setStyleSheet(
                "color: #93C5FD; font-size: 11pt; text-decoration: underline; background: transparent;"
            )
            bl.addWidget(att_lbl)

        time_lbl = QLabel(fmt_datetime(msg.get("created_at", "")))
        time_lbl.setStyleSheet(
            f"color: {'rgba(255,255,255,0.65)' if is_mine else '#64748B'}; "
            "font-size: 9pt; background: transparent;"
        )
        time_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight if is_mine else Qt.AlignmentFlag.AlignLeft
        )
        bl.addWidget(time_lbl)

        layout.addWidget(bubble)
        if not is_mine:
            layout.addStretch()


class ChatWindow(QWidget):
    def __init__(self, current_user: dict, contact: dict = None, parent=None):
        super().__init__(parent)
        self.current_user  = current_user
        self.contact       = contact
        self._last_msg_id  = 0

        self.setWindowTitle("FreightExchange — Сообщения")
        self.resize(900, 650)
        self._build()

        if contact:
            self._load_contact(contact)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_messages)
        self._timer.start(2000)

    def _build(self):
        self.setStyleSheet(f"background: {C_CONTENT_BG};")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Contact list ──────────────────────────────────────────
        left = QWidget()
        left.setStyleSheet(f"background: {C_CARD_BG}; border-right: 1px solid {C_BORDER};")
        left.setMinimumWidth(240)
        left.setMaximumWidth(300)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(0)

        hdr = QWidget()
        hdr.setStyleSheet(f"background: {C_SIDEBAR_BG}; padding: 0;")
        hdr.setFixedHeight(60)
        hhl = QHBoxLayout(hdr)
        hhl.setContentsMargins(16, 0, 16, 0)
        ht = QLabel("Сообщения")
        ht.setStyleSheet("color: #0F172A; font-size: 13pt; font-weight: 700;")
        hhl.addWidget(ht)
        ll.addWidget(hdr)

        self.contact_list = QListWidget()
        self.contact_list.setStyleSheet(f"""
            QListWidget {{
                background: {C_CARD_BG};
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px 16px;
                border-bottom: 1px solid {C_BORDER};
                color: {C_TEXT};
            }}
            QListWidget::item:hover {{
                background: #F1F5F9;
            }}
            QListWidget::item:selected {{
                background: #EFF6FF;
                color: #2563EB;
                border-left: 3px solid #2563EB;
            }}
        """)
        self.contact_list.itemClicked.connect(self._on_contact_clicked)
        ll.addWidget(self.contact_list)
        splitter.addWidget(left)

        # ── Chat area ─────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet(f"background: {C_CONTENT_BG};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # Chat header
        self.chat_hdr = QWidget()
        self.chat_hdr.setStyleSheet(
            f"background: {C_CARD_BG}; border-bottom: 1px solid {C_BORDER};"
        )
        self.chat_hdr.setFixedHeight(60)
        chl = QHBoxLayout(self.chat_hdr)
        chl.setContentsMargins(16, 0, 16, 0)
        self.chat_hdr_name = QLabel("Выберите диалог")
        self.chat_hdr_name.setStyleSheet(
            f"font-size: 12pt; font-weight: 700; color: {C_TEXT};"
        )
        chl.addWidget(self.chat_hdr_name)
        rl.addWidget(self.chat_hdr)

        # Messages scroll
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.msg_container = QWidget()
        self.msg_container.setStyleSheet("background: transparent;")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(8, 12, 8, 12)
        self.msg_layout.setSpacing(4)
        self.msg_layout.addStretch()

        self.scroll.setWidget(self.msg_container)
        rl.addWidget(self.scroll)

        # Input row — 62 px = 10 top + 42 content + 10 bottom, all items exactly 42 px
        inp_bar = QWidget()
        inp_bar.setStyleSheet(
            f"background: {C_CARD_BG}; border-top: 1px solid {C_BORDER};"
        )
        inp_bar.setFixedHeight(62)
        ibl = QHBoxLayout(inp_bar)
        ibl.setContentsMargins(12, 10, 12, 10)
        ibl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        ibl.setSpacing(8)

        btn_attach = QPushButton("📎")
        btn_attach.setFixedSize(42, 42)
        btn_attach.setToolTip("Прикрепить файл")
        btn_attach.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                font-size: 16pt;
                color: #64748B;
            }
            QPushButton:hover {
                border-color: #2563EB;
                color: #2563EB;
                background: rgba(37,99,235,0.08);
            }
        """)
        btn_attach.clicked.connect(self._attach_file)
        ibl.addWidget(btn_attach)

        self.inp_msg = QLineEdit()
        self.inp_msg.setPlaceholderText("✏ Напишите сообщение...")
        self.inp_msg.setFixedHeight(42)
        self.inp_msg.setStyleSheet(
            "QLineEdit { background: #FFFFFF; border: 2px solid #CBD5E1; "
            "border-radius: 8px; padding: 0px 14px; color: #0F172A; font-size: 10pt; }"
            "QLineEdit:focus { border-color: #2563EB; border-width: 2px; background: #EFF6FF; }"
        )
        self.inp_msg.returnPressed.connect(self._send)
        ibl.addWidget(self.inp_msg)

        btn_send = QPushButton("Отправить")
        btn_send.setFixedSize(140, 42)
        btn_send.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; font-size: 11pt; font-weight: 600; padding: 0 16px; }"
            "QPushButton:hover { background: #1D4ED8; }"
            "QPushButton:pressed { background: #1E40AF; }"
        )
        btn_send.clicked.connect(self._send)
        ibl.addWidget(btn_send)

        rl.addWidget(inp_bar)
        splitter.addWidget(right)

        splitter.setSizes([260, 640])
        root.addWidget(splitter)

        self._attachment_path = ""
        self._load_contacts()

    def _load_contacts(self):
        self.contact_list.clear()
        contacts = MessageModel.get_contacts(self.current_user["id"])
        self._contact_data: dict[int, dict] = {}

        for c in contacts:
            item = QListWidgetItem()
            unread = c.get("unread", 0)
            text = c.get("full_name") or f"Пользователь #{c['contact_id']}"
            if unread:
                text += f" 🔴 {unread}"
            item.setText(text)
            item.setData(Qt.ItemDataRole.UserRole, c["contact_id"])
            self.contact_list.addItem(item)
            self._contact_data[c["contact_id"]] = c

    def _load_contact(self, contact: dict):
        # "id" is present in user-dicts; "user_id"/"contact_id" in contact-list dicts
        uid = contact.get("id") or contact.get("user_id") or contact.get("contact_id")
        if not uid:
            return
        user_data = UserModel.get_by_id(uid)
        self.contact = user_data if user_data else contact
        self.chat_hdr_name.setText(
            self.contact.get("full_name") or self.contact.get("company_name") or "Диалог"
        )
        self._last_msg_id = 0
        self._clear_messages()        # wipe previous chat immediately
        self._load_messages()
        MessageModel.mark_read(uid, self.current_user["id"])

    def _on_contact_clicked(self, item: QListWidgetItem):
        uid = item.data(Qt.ItemDataRole.UserRole)
        user = UserModel.get_by_id(uid)
        if user:
            self._load_contact(user)

    def _clear_messages(self):
        while self.msg_layout.count() > 1:
            item = self.msg_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)  # immediate removal, not deferred

    def _load_messages(self):
        if not self.contact:
            return
        contact_id = self.contact.get("id")
        if not contact_id:
            return
        msgs = MessageModel.get_conversation(self.current_user["id"], contact_id)
        for msg in msgs:
            if msg["id"] > self._last_msg_id:
                is_mine = msg["sender_id"] == self.current_user["id"]
                bubble  = MessageBubble(msg, is_mine)
                self.msg_layout.insertWidget(self.msg_layout.count() - 1, bubble)
                self._last_msg_id = msg["id"]
        self._scroll_to_bottom()

    def _poll_messages(self):
        if not self.contact:
            self._load_contacts()
            return
        self._load_messages()

    def _send(self):
        text = self.inp_msg.text().strip()
        if not text and not self._attachment_path:
            return
        if not self.contact:
            return

        contact_id = self.contact.get("id")
        MessageModel.send(
            self.current_user["id"], contact_id,
            text, attachment_path=self._attachment_path
        )
        self.inp_msg.clear()
        self._attachment_path = ""
        self._load_messages()
        self._load_contacts()

    def _attach_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл", "",
            "Все файлы (*.*);; Изображения (*.png *.jpg *.jpeg);; PDF (*.pdf)"
        )
        if path:
            self._attachment_path = save_attachment(path)
            self.inp_msg.setPlaceholderText(
                f"📎 {path.split('/')[-1]} — напишите сообщение и нажмите Отправить"
            )

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)

    def open_with_user(self, user: dict):
        self._load_contact(user)
        cid = user.get("id")
        if cid and cid not in self._contact_data:
            self._load_contacts()
