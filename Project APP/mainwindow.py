from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QSizePolicy, QStackedWidget,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap

import stylesheet as ss
from dashboard import DashboardPage
from weekly import WeeklySummaryPage
from session import Session
from Database_sor import user_has_health_data
from settings_page_input import SettingsPage
from support import SupportPage

def _logo_label(size: int = 48) -> QLabel:
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"background-color: {ss.dark_green};"
        f"border-radius: {size // 4}px;"
    )
    px = QPixmap("savorly.png")
    if not px.isNull():
        icon_size = int(size * 0.68)
        px = px.scaled(icon_size, icon_size,
                       Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl.setPixmap(px)
    else:
        lbl.setText("🍴")
    return lbl

nav_bar = [
    ("dashboard",   "Dashboard",        "dashboard.png"),
    ("weekly",      "Weekly Summary",   "weekly.png"),
    ("support",     "Support",          "support.png"),
    ("settings",    "Settings",         "setting.png"),]

class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 24, 16, 24)
        self._layout.setSpacing(4)
        self._build_logo()
        self._layout.addSpacing(28)
        self._build_nav()
        self._layout.addStretch()
        self._build_user_row()

    def _build_logo(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(_logo_label(size=48))
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        name = QLabel("Savorly");            name.setStyleSheet(ss.sidebar_app_name)
        sub  = QLabel("Meal Balancing App"); sub.setStyleSheet(ss.sidebar_app_subtitle)
        text_col.addWidget(name)
        text_col.addWidget(sub)
        row.addLayout(text_col)
        row.addStretch()
        self._layout.addLayout(row)

    def _build_nav(self):
        self._nav_buttons: dict[str, QPushButton] = {}
        for page_id, label, icon_file in nav_bar:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setFixedHeight(42)
            btn.setIconSize(QSize(20, 20))
            px = QPixmap(icon_file)
            if not px.isNull():
                btn.setIcon(QIcon(px))
            self._nav_buttons[page_id] = btn
            self._layout.addWidget(btn)

    def _build_user_row(self):
        row = QHBoxLayout()
        avatar = QLabel("👤")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(ss.sidebar_avatar)

        username = getattr(Session, "username", None) or "Guest"
        self.username_label = QLabel(username)
        self.username_label.setStyleSheet(ss.sidebar_username)

        row.addWidget(avatar)
        row.addWidget(self.username_label)
        row.addStretch()
        self._layout.addLayout(row)

        self.update_user()

    def set_active(self, page_id: str):
        for pid, btn in self._nav_buttons.items():
            btn.setChecked(pid == page_id)
            btn.setStyleSheet(ss.nav_btn(active=(pid == page_id)))

    def buttons(self) -> dict:
        return self._nav_buttons
    
    def update_user(self):
        username = getattr(Session, "username", None) or "Guest"
        self.username_label.setText(username)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Savorly Meal Balancing App")
        self.resize(1200, 780)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(ss.mainwindow)

        root = QWidget()
        root.setStyleSheet(ss.page_bg)
        self.setCentralWidget(root)

        h = QHBoxLayout(root)
        h.setContentsMargins(0,0,0,0)
        h.setSpacing(0)

        self._sidebar = Sidebar()
        h.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(ss.page_bg)
        h.addWidget(self._stack)

        self.dashboard_page = DashboardPage()
        self._stack.addWidget(self.dashboard_page)
        self._stack.addWidget(WeeklySummaryPage())
        self._support_page = SupportPage()
        self._stack.addWidget(self._support_page)
        self.settings_page = SettingsPage()
        self._stack.addWidget(self.settings_page)

        for pid, btn in self._sidebar.buttons().items():
            btn.clicked.connect(lambda checked, p=pid: self._switch_page(p))

        self._switch_page("dashboard")

        self.refresh_user()
        if user_has_health_data(Session.user_id):
            self._switch_page("dashboard")
        else:
            self._switch_page("settings")  

    def _switch_page(self, page_id: str):
        idx = {"dashboard": 0, "weekly": 1, "support": 2, "settings": 3}
        self._stack.setCurrentIndex(idx.get(page_id, 0))
        self._sidebar.set_active(page_id)

    def _placeholder(self, title: str, subtitle: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(ss.page_bg)
        v = QVBoxLayout(w)
        v.setContentsMargins(36, 32, 36, 32)
        t = QLabel(title);    t.setStyleSheet(ss.page_title)
        s = QLabel(subtitle); s.setStyleSheet(ss.page_subtitle )
        v.addWidget(t); v.addWidget(s); v.addStretch()
        return w
    
    def refresh_user(self):
        # Update username everywhere
        if hasattr(self, "_sidebar"):
            self._sidebar.update_user()
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.update_user()
    