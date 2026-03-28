import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

import stylesheet as ss

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
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(48, 48)
        self.setAlignment(Qt.AlignCenter)

        self.pix = QPixmap("savorly.png")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # ✅ DRAW BACKGROUND
        painter.setBrush(QColor(ss.dark_green))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

        # ✅ DRAW ICON MANUALLY (instead of QLabel)
        if not self.pix.isNull():
            icon_size = int(48 * 0.65)
            pix = self.pix.scaled(icon_size, icon_size,
                                 Qt.KeepAspectRatio, Qt.SmoothTransformation)

            x = (self.width() - pix.width()) // 2
            y = (self.height() - pix.height()) // 2

            painter.drawPixmap(x, y, pix)
        else:
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "🍴")

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
        self.setStyleSheet(ss.nav_btn(active))
        icon = _icon(icon_file)
        if not icon.isNull():
            self.setIcon(icon)
    
    def set_active(self, active: bool):
        self.setObjectName("menuBtnActive" if active else "menuBtn")

    # 🔥 force refresh style
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


# ── Sidebar ────────────────────────────────────────────────────────

class Sidebar(QWidget):
    nav_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ss.sidebar)
        self.setFixedWidth(220)

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
        app_name.setStyleSheet(ss.sidebar_app_name)
        subtitle = QLabel("Meal Balancing App")
        subtitle.setObjectName("appSubtitle")
        subtitle.setStyleSheet(ss.sidebar_app_subtitle)
        text_col.addWidget(app_name)
        text_col.addWidget(subtitle)
        logo_row.addLayout(text_col)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        layout.addSpacing(32)

        # ── Menu Buttons ──
        # (icon_filename, label, nav_key)
        self.menu_items = [
            ("dashboard.png",      "Dashboard",      "dashboard"),
            ("weekly.png", "Weekly Summary", "weekly"),
            ("support.png", "Support",        "support"),
            ("setting.png",       "Settings",       "settings"),
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
            btn.setStyleSheet(ss.nav_btn(k == key))
