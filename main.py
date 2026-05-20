import sys
import os
from pathlib import Path

# ── WebEngine stability (must be set BEFORE QApplication) ──────────
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --no-sandbox")
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

# Project root on sys.path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from database.db_manager import DatabaseManager
from ui.auth.login_window import LoginWindow
import utils.theme_manager as tm


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FreightExchange")
    app.setApplicationDisplayName("Биржа Фрахта")
    app.setOrganizationName("FreightExchange Corp")

    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    # Apply dark theme (single theme, no switching)
    tm.apply("dark", app)

    db = DatabaseManager()
    try:
        db.initialize()
    except Exception as e:
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("Ошибка подключения к БД")
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(
            "<b>Не удалось подключиться к PostgreSQL.</b><br><br>"
            "Проверьте:<br>"
            "1. PostgreSQL установлен и запущен<br>"
            "2. Файл <code>.env</code> содержит верный <code>DATABASE_URL</code><br>"
            "3. База данных создана (запустите <code>python setup_db.py</code>)<br><br>"
            f"<small>Ошибка: {e}</small>"
        )
        msg.exec()
        sys.exit(1)

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# привет андрей4