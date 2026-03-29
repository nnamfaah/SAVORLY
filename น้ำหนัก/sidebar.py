import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

# ── Resolve icon paths relative to this file ──────────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))


def _icon(filename: str) -> QIcon:
    path = os.path.join(_DIR, filename)
    return QIcon(path) if os.path.exists(path) else QIcon()


def _pixmap(filename: str, size: int) -> QPixmap:
    path = os.path.join(_DIR, filename)
    if os.path.exists(path):
        return QPixmap(path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return QPixmap()


# ── Logo Widget ────────────────────────────────────────────────────

class LogoIcon(QLabel):
    """Logo icon: knife + spoon image on rounded green background."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logoIcon")
        self.setFixedSize(48, 48)
        self.setAlignment(Qt.AlignCenter)
        pm = _pixmap("icon_logo.png", 36)
        if not pm.isNull():
            self.setPixmap(pm)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#DCE5D3"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 48, 48, 12, 12)
        painter.end()
        super().paintEvent(event)


# ── Menu Button ────────────────────────────────────────────────────

class MenuButton(QPushButton):
    """Sidebar menu button with real image icon + label."""
    def __init__(self, icon_file: str, text: str, active: bool = False, parent=None):
        super().__init__(parent)
        self.setText(f"    {text}")
        self.setObjectName("menuBtnActive" if active else "menuBtn")
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(20, 20))
        icon = _icon(icon_file)
        if not icon.isNull():
            self.setIcon(icon)


# ── Sidebar ────────────────────────────────────────────────────────

class Sidebar(QWidget):
    nav_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(0)

        # ── Logo Section ──
        logo_row = QHBoxLayout()
        logo_row.setSpacing(12)
        logo_icon = LogoIcon()
        logo_row.addWidget(logo_icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        app_name = QLabel("Savorly")
        app_name.setObjectName("appName")
        subtitle = QLabel("Meal Balancing App")
        subtitle.setObjectName("appSubtitle")
        text_col.addWidget(app_name)
        text_col.addWidget(subtitle)
        logo_row.addLayout(text_col)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        layout.addSpacing(32)

        # ── Menu Buttons ──
        # (icon_filename, label, nav_key)
        self.menu_items = [
            ("icon_dashboard.png",      "Dashboard",      "dashboard"),
            ("Screenshot 2026-03-25 202838.png", "Weekly Summary", "weekly"),
            ("Screenshot 2026-03-25 202842.png", "Support",        "support"),
            ("Screenshot 2026-03-25 202845.png",       "Settings",       "settings"),
        ]

        self.buttons = {}
        for icon_file, label, key in self.menu_items:
            active = key == "settings"
            btn = MenuButton(icon_file, label, active=active)
            btn.clicked.connect(lambda checked=False, k=key: self.nav_clicked.emit(k))
            layout.addWidget(btn)
            layout.addSpacing(8)
            self.buttons[key] = btn

        layout.addStretch()

    def set_active(self, key: str):
        for k, btn in self.buttons.items():
            btn.setObjectName("menuBtnActive" if k == key else "menuBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
