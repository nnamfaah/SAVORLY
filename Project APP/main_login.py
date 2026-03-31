import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QFrame,
    QSizePolicy, QSpacerItem, QMessageBox
)
from PySide6.QtGui import QFontDatabase, QFont, QPixmap, QIcon, QColor
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve

from mainwindow import MainWindow 
from Database_sor import login_user, register_user, user_has_health_data, get_user_by_id, init_database, run_migrations, fix_db_on_startup, update_password
from session import Session
from dashboard import DashboardPage
from main_input import MainWindow_input

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, 'fonts')
ICONS_DIR = os.path.join(BASE_DIR, 'Icon')


# ==================== COLOR PALETTE ====================
class Colors:
    """Color palette matching Figma design exactly"""
    # Header
    HEADER_BG = "#A8C5A2"  # Light green/moss

    # Main backgrounds
    MAIN_BG = "#FFFFFF"  # White
    FORM_BG = "#DDD8C4"  # Beige/tan form background (matches Figma)

    # Buttons
    BUTTON_PRIMARY = "#6B7C5C"  # Dark olive green (matches Figma Sign in button)
    BUTTON_PRIMARY_HOVER = "#5A6B4B"
    BUTTON_TEXT = "#FFFFFF"
    BUTTON_CANCEL = "#FFFFFF"
    BUTTON_CANCEL_BORDER = "#CCCCCC"
    BUTTON_CANCEL_TEXT = "#555555"

    # Text colors
    TEXT_PRIMARY = "#2C2C2C"       # Header brand text
    TEXT_HEADING = "#7B5B2E"       # Brown heading like "Welcome back" (Figma)
    TEXT_TERTIARY = "#666666"      # Gray subtext
    TEXT_INPUT = "#333333"
    TEXT_PLACEHOLDER = "#999999"
    TEXT_LINK = "#6B7C5C"          # Olive green link (Sign up for free)

    # Input fields
    INPUT_BG = "#FFFFFF"
    INPUT_BORDER = "#DDDDDD"


# ==================== FONT MANAGER ====================
class FontManager:
    _instance = None
    _fonts_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._fonts_loaded:
            self.load_fonts()
            self._fonts_loaded = True

    def load_fonts(self):
        font_files = {
            'Inria Serif': ['InriaSerif-Regular.ttf', 'InriaSerif-Bold.ttf', 'InriaSerif-Light.ttf'],
            'Inter': ['Inter-Regular.ttf', 'Inter-Medium.ttf', 'Inter-Bold.ttf'],
            'Inika': ['Inika-Regular.ttf', 'Inika-Bold.ttf']
        }
        self.font_ids = {}
        for font_family, files in font_files.items():
            for font_file in files:
                font_path = os.path.join(FONTS_DIR, font_file)
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        if font_family not in self.font_ids:
                            self.font_ids[font_family] = []
                        self.font_ids[font_family].append(font_id)

        self.inria_serif = "Inria Serif"
        self.inter = "Inter"
        self.inika = "Inika"

    def get_font(self, family, size, weight=QFont.Normal):
        font = QFont(family, size, weight)
        return font


# ==================== CUSTOM WIDGETS ====================
class HeaderWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border: none;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 0, 30, 0)

        self.brand_label = QLabel("SAVORLY")
        font_manager = FontManager()
        self.brand_label.setFont(font_manager.get_font(font_manager.inria_serif, 26, QFont.Bold))
        self.brand_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")
        self.brand_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(self.brand_label)
        layout.addStretch()


class IconLineEdit(QFrame):
    textChanged = Signal(str)
    returnPressed = Signal()

    def __init__(self, icon_name="", placeholder="", parent=None, show_toggle=False):
        super().__init__(parent)
        self.show_toggle = show_toggle
        self.password_visible = False
        self.icon_name = icon_name
        self.placeholder_text = placeholder
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.INPUT_BG};
                border: 1px solid {Colors.INPUT_BORDER};
                border-radius: 8px;
            }}
        """)
        self.setFixedHeight(46)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        icon_path = os.path.join(ICONS_DIR, f"{self.icon_name}.png")

        print(f"[DEBUG] ICONS_DIR = {ICONS_DIR}")
        print(f"[DEBUG] icon_path = {icon_path}")
        print(f"[DEBUG] exists = {os.path.exists(icon_path)}")

        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(self.placeholder_text)
        font_manager = FontManager()
        self.line_edit.setFont(font_manager.get_font(font_manager.inter, 12))
        self.line_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: {Colors.TEXT_INPUT};
                padding: 0px;
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_PLACEHOLDER};
            }}
        """)
        self.line_edit.textChanged.connect(self.textChanged.emit)
        self.line_edit.returnPressed.connect(self.returnPressed.emit)

        if self.show_toggle:
            self.line_edit.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.line_edit, 1)

        if self.show_toggle:
            self.toggle_btn = QPushButton()
            self.toggle_btn.setFixedSize(24, 24)
            self.toggle_btn.setCursor(Qt.PointingHandCursor)
            self.toggle_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
            self.update_toggle_icon()
            self.toggle_btn.clicked.connect(self.toggle_password)
            layout.addWidget(self.toggle_btn)

    def update_toggle_icon(self):
        icon_name = "eye_icon" if not self.password_visible else "eye_off_icon"
        icon_path = os.path.join(ICONS_DIR, f"{icon_name}.png")
        if os.path.exists(icon_path):
            self.toggle_btn.setIcon(QIcon(icon_path))
            self.toggle_btn.setIconSize(QSize(20, 20))

    def toggle_password(self):
        self.password_visible = not self.password_visible
        self.line_edit.setEchoMode(QLineEdit.Normal if self.password_visible else QLineEdit.Password)
        self.update_toggle_icon()

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)

class PrimaryButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()

    def setup_style(self):
        font_manager = FontManager()
        self.setFont(font_manager.get_font(font_manager.inter, 11, QFont.Medium))
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BUTTON_PRIMARY};
                color: {Colors.BUTTON_TEXT};
                border: none;
                border-radius: 8px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BUTTON_PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #4A5A3B;
            }}
        """)


class SecondaryButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()

    def setup_style(self):
        font_manager = FontManager()
        self.setFont(font_manager.get_font(font_manager.inter, 11, QFont.Medium))
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BUTTON_CANCEL};
                color: {Colors.BUTTON_CANCEL_TEXT};
                border: 1px solid {Colors.BUTTON_CANCEL_BORDER};
                border-radius: 8px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #F5F5F5;
            }}
            QPushButton:pressed {{
                background-color: #ECECEC;
            }}
        """)


class LinkLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()

    def setup_style(self):
        font_manager = FontManager()
        self.setFont(font_manager.get_font(font_manager.inter, 12))
        self.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_LINK};
                background: transparent;
                font-weight: bold;
            }}
            QLabel:hover {{
                text-decoration: underline;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ==================== PAGE WIDGETS ====================

class LoginPage(QWidget):
    """
    Layout structure (matches Figma):
      - HeaderWidget (green bar with SAVORLY)
      - White area:
          - "Welcome back" (brown serif, large, centered) — OUTSIDE the beige box
          - "Please enter your details..." (gray, centered) — OUTSIDE the beige box
          - Beige FormBox:
              - username input
              - password input
              - Forgot password? (right-aligned)
              - Sign in button (full width)
              - "Don't have an account? Sign up for free"
    """

    login_requested = Signal(str, str)
    signup_clicked = Signal()
    forgot_password_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        font_manager = FontManager()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setStyleSheet(f"background-color: {Colors.MAIN_BG};")

        # Header
        self.header = HeaderWidget()
        main_layout.addWidget(self.header)

        # Outer content (white bg, centered)
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        content_layout.setSpacing(0)

        # --- Title: "Welcome back" above form box ---
        title_label = QLabel("Welcome back")
        title_label.setFont(font_manager.get_font(font_manager.inria_serif, 30, QFont.Normal))
        title_label.setStyleSheet(f"color: {Colors.TEXT_HEADING}; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        content_layout.addSpacing(8)

        # --- Subtitle ---
        subtitle_label = QLabel("Please enter your details to sign in to your account.")
        subtitle_label.setFont(font_manager.get_font(font_manager.inter, 12))
        subtitle_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle_label)
        content_layout.addSpacing(20)

        # --- Beige form box ---
        form_box = QFrame()
        form_box.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.FORM_BG};
                border-radius: 12px;
                border: none;
            }}
        """)
        form_box.setMinimumWidth(420)
        form_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        form_layout = QVBoxLayout(form_box)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(14)

        # Username input
        self.username_input = IconLineEdit(icon_name="user_icon", placeholder="Enter your username or email")
        form_layout.addWidget(self.username_input)

        # Password input
        self.password_input = IconLineEdit(icon_name="lock_icon", placeholder="Enter your password", show_toggle=True)
        form_layout.addWidget(self.password_input)

        # Forgot password (right-aligned)
        forgot_container = QWidget()
        forgot_container.setStyleSheet("background: transparent;")
        forgot_layout = QHBoxLayout(forgot_container)
        forgot_layout.setContentsMargins(0, 0, 0, 0)
        forgot_layout.addStretch()
        self.forgot_link = LinkLabel("Forgot password ?")
        self.forgot_link.clicked.connect(self.forgot_password_clicked.emit)
        forgot_layout.addWidget(self.forgot_link)
        form_layout.addWidget(forgot_container)

        # Sign in button
        self.signin_btn = PrimaryButton("Sign in")
        self.signin_btn.clicked.connect(self.on_signin)
        form_layout.addWidget(self.signin_btn)

        # "Don't have an account? Sign up for free"
        signup_container = QWidget()
        signup_container.setStyleSheet("background: transparent;")
        signup_layout = QHBoxLayout(signup_container)
        signup_layout.setContentsMargins(0, 0, 0, 0)
        signup_layout.setSpacing(4)
        signup_layout.setAlignment(Qt.AlignCenter)

        no_account = QLabel("Don't have an account?")
        no_account.setFont(font_manager.get_font(font_manager.inter, 12))
        no_account.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; background: transparent;")

        self.signup_link = LinkLabel("Sign up for free")
        self.signup_link.clicked.connect(self.signup_clicked.emit)

        signup_layout.addWidget(no_account)
        signup_layout.addWidget(self.signup_link)
        form_layout.addWidget(signup_container)

        content_layout.addWidget(form_box)
        content_layout.addStretch()

        main_layout.addWidget(content_widget, 1)

    def on_signin(self):
        self.login_requested.emit(self.username_input.text(), self.password_input.text())

    def clear_inputs(self):
        self.username_input.setText("")
        self.password_input.setText("")


class SignUpPage(QWidget):
    """
    Layout (matches Figma):
      - Header
      - White area:
          - "Sign up" (brown serif, large, centered) — OUTSIDE beige box
          - "Register for a new account." (gray) — OUTSIDE beige box
          - Beige FormBox:
              - username input
              - password input
              - confirm password input
              - Sign up button
              - "Have an account? Sign in"
    """

    signup_requested = Signal(str, str, str)
    signin_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        font_manager = FontManager()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setStyleSheet(f"background-color: {Colors.MAIN_BG};")

        self.header = HeaderWidget()
        main_layout.addWidget(self.header)

        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        content_layout.setSpacing(0)

        # Title
        title_label = QLabel("Sign up")
        title_label.setFont(font_manager.get_font(font_manager.inria_serif, 30, QFont.Normal))
        title_label.setStyleSheet(f"color: {Colors.TEXT_HEADING}; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        content_layout.addSpacing(8)

        # Subtitle
        subtitle_label = QLabel("Register for a new account.")
        subtitle_label.setFont(font_manager.get_font(font_manager.inter, 12))
        subtitle_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle_label)
        content_layout.addSpacing(20)

        # Beige form box
        form_box = QFrame()
        form_box.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.FORM_BG};
                border-radius: 12px;
                border: none;
            }}
        """)
        form_box.setMinimumWidth(420)
        form_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        form_layout = QVBoxLayout(form_box)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(14)

        self.username_input = IconLineEdit(icon_name="user_icon", placeholder="Enter your username or email")
        form_layout.addWidget(self.username_input)

        self.password_input = IconLineEdit(icon_name="lock_icon", placeholder="Enter your password", show_toggle=True)
        form_layout.addWidget(self.password_input)

        self.confirm_password_input = IconLineEdit(icon_name="lock_icon", placeholder="Enter your password again", show_toggle=True)
        form_layout.addWidget(self.confirm_password_input)

        self.signup_btn = PrimaryButton("Sign up")
        self.signup_btn.clicked.connect(self.on_signup)
        form_layout.addWidget(self.signup_btn)

        # "Have an account? Sign in"
        signin_container = QWidget()
        signin_container.setStyleSheet("background: transparent;")
        signin_layout = QHBoxLayout(signin_container)
        signin_layout.setContentsMargins(0, 0, 0, 0)
        signin_layout.setSpacing(4)
        signin_layout.setAlignment(Qt.AlignCenter)

        have_account = QLabel("Have an account?")
        have_account.setFont(font_manager.get_font(font_manager.inter, 12))
        have_account.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; background: transparent;")

        self.signin_link = LinkLabel("Sign in")
        self.signin_link.clicked.connect(self.signin_clicked.emit)

        signin_layout.addWidget(have_account)
        signin_layout.addWidget(self.signin_link)
        form_layout.addWidget(signin_container)

        content_layout.addWidget(form_box)
        content_layout.addStretch()

        main_layout.addWidget(content_widget, 1)

    def on_signup(self):
        self.signup_requested.emit(
            self.username_input.text(),
            self.password_input.text(),
            self.confirm_password_input.text()
        )

    def clear_inputs(self):
        self.username_input.setText("")
        self.password_input.setText("")
        self.confirm_password_input.setText("")


class ResetPasswordSearchPage(QWidget):
    """
    Layout (matches Figma):
      - Header
      - White area:
          - "Reset your password" (brown serif) — OUTSIDE beige box
          - "Locate your email account or username." — OUTSIDE beige box
          - Beige FormBox:
              - username input
              - Cancel + Search buttons (right-aligned)
    """

    search_requested = Signal(str)
    cancel_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        font_manager = FontManager()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setStyleSheet(f"background-color: {Colors.MAIN_BG};")

        self.header = HeaderWidget()
        main_layout.addWidget(self.header)

        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        content_layout.setSpacing(0)

        # Title
        title_label = QLabel("Reset your password")
        title_label.setFont(font_manager.get_font(font_manager.inria_serif, 30, QFont.Normal))
        title_label.setStyleSheet(f"color: {Colors.TEXT_HEADING}; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        content_layout.addSpacing(8)

        # Subtitle
        subtitle_label = QLabel("Locate your email account or username.")
        subtitle_label.setFont(font_manager.get_font(font_manager.inter, 12))
        subtitle_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle_label)
        content_layout.addSpacing(20)

        # Beige form box
        form_box = QFrame()
        form_box.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.FORM_BG};
                border-radius: 12px;
                border: none;
            }}
        """)
        form_box.setMinimumWidth(420)
        form_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        form_layout = QVBoxLayout(form_box)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)

        self.username_input = IconLineEdit(
            icon_name="user_icon",
            placeholder="To access your account, enter your username or email."
        )
        form_layout.addWidget(self.username_input)

        # Buttons row: Cancel | Search and browse your account.
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background: transparent;")
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(12)
        buttons_layout.addStretch()

        self.cancel_btn = SecondaryButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        self.cancel_btn.setFixedWidth(90)

        self.search_btn = PrimaryButton("Search your account.")
        self.search_btn.clicked.connect(self.on_search)
        self.search_btn.setFixedWidth(230)

        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.search_btn)

        form_layout.addWidget(buttons_widget)

        content_layout.addWidget(form_box)
        content_layout.addStretch()

        main_layout.addWidget(content_widget, 1)

    def on_search(self):
        self.search_requested.emit(self.username_input.text())

    def clear_inputs(self):
        self.username_input.setText("")


class ResetPasswordNewPage(QWidget):
    """
    Layout (matches Figma):
      - Header
      - White area:
          - "Reset your password" (brown serif) — OUTSIDE beige box
          - "Please enter your new password below." — OUTSIDE beige box
          - Beige FormBox:
              - new password input
              - confirm password input
              - "Reset your password" button (centered)
    """

    reset_requested = Signal(str, str)
    cancel_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        font_manager = FontManager()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setStyleSheet(f"background-color: {Colors.MAIN_BG};")

        self.header = HeaderWidget()
        main_layout.addWidget(self.header)

        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        content_layout.setSpacing(0)

        # Title
        title_label = QLabel("Reset your password")
        title_label.setFont(font_manager.get_font(font_manager.inria_serif, 30, QFont.Normal))
        title_label.setStyleSheet(f"color: {Colors.TEXT_HEADING}; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        content_layout.addSpacing(8)

        # Subtitle
        subtitle_label = QLabel("Please enter your new password below.")
        subtitle_label.setFont(font_manager.get_font(font_manager.inter, 12))
        subtitle_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle_label)
        content_layout.addSpacing(20)

        # Beige form box
        form_box = QFrame()
        form_box.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.FORM_BG};
                border-radius: 12px;
                border: none;
            }}
        """)
        form_box.setMinimumWidth(420)
        form_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        form_layout = QVBoxLayout(form_box)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(14)

        self.new_password_input = IconLineEdit(icon_name="lock_icon", placeholder="Enter your password", show_toggle=True)
        form_layout.addWidget(self.new_password_input)

        self.confirm_password_input = IconLineEdit(icon_name="lock_icon", placeholder="Enter your password again", show_toggle=True)
        form_layout.addWidget(self.confirm_password_input)

        form_layout.addSpacing(10)

        # Centered reset button
        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.reset_btn = PrimaryButton("Reset your password")
        self.reset_btn.clicked.connect(self.on_reset)
        self.reset_btn.setFixedWidth(200)
        btn_layout.addWidget(self.reset_btn)

        form_layout.addWidget(btn_container)

        content_layout.addWidget(form_box)
        content_layout.addStretch()

        main_layout.addWidget(content_widget, 1)

    def on_reset(self):
        self.reset_requested.emit(self.new_password_input.text(), self.confirm_password_input.text())

    def clear_inputs(self):
        self.new_password_input.setText("")
        self.confirm_password_input.setText("")


# ==================== MAIN WINDOW ====================
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAVORLY - Login")
        self.setMinimumSize(700, 560)
        self.resize(700, 560)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()

        self.login_page = LoginPage()
        self.signup_page = SignUpPage()
        self.reset_search_page = ResetPasswordSearchPage()
        self.reset_new_page = ResetPasswordNewPage()

        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.signup_page)
        self.stacked_widget.addWidget(self.reset_search_page)
        self.stacked_widget.addWidget(self.reset_new_page)

        self.login_page.login_requested.connect(self.handle_login)
        self.login_page.signup_clicked.connect(self.show_signup)
        self.login_page.forgot_password_clicked.connect(self.show_reset_search)

        self.signup_page.signup_requested.connect(self.handle_signup)
        self.signup_page.signin_clicked.connect(self.show_login)

        self.reset_search_page.search_requested.connect(self.handle_reset_search)
        self.reset_search_page.cancel_clicked.connect(self.show_login)

        self.reset_new_page.reset_requested.connect(self.handle_reset_password)

        main_layout.addWidget(self.stacked_widget)

    def show_login(self):
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.setWindowTitle("SAVORLY - Login")

    def show_signup(self):
        self.stacked_widget.setCurrentWidget(self.signup_page)
        self.setWindowTitle("SAVORLY - Sign Up")

    def show_reset_search(self):
        self.stacked_widget.setCurrentWidget(self.reset_search_page)
        self.setWindowTitle("SAVORLY - Reset Password")

    def show_reset_new(self):
        self.stacked_widget.setCurrentWidget(self.reset_new_page)
        self.setWindowTitle("SAVORLY - New Password")

    def handle_login(self, username, password):
        ok, result = login_user(username, password)
        if ok:
            user_id, uname = result   
            Session.user_id = user_id
            Session.username = uname

            if user_has_health_data(user_id):
            # ✅ HAS DATA → DASHBOARD
                self.main_app = MainWindow()
                self.main_app.show()
            else:
            # ❗ NO DATA → INPUT PAGE
                self.main_input = MainWindow_input()
                self.main_input.show()

            self.close()
        else:
            QMessageBox.warning(self, "Error", result)

    def handle_signup(self, username, password, confirm_password):
        if not username or not password or not confirm_password:
            QMessageBox.warning(self, "Sign Up Failed", "Please fill in all fields.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Sign Up Failed", "Passwords do not match.")
            return
        
        # ── Validate password rules ──
        import re
        errors = []
        if len(password) < 8:
            errors.append("At least 8 characters required.")
        if not re.search(r'[A-Z]', password):
            errors.append("Must contain at least one uppercase letter (A-Z).")
        if not re.search(r'[a-z]', password):
            errors.append("Must contain at least one lowercase letter (a-z).")
        if not re.search(r'\d', password):
            errors.append("Must contain at least one number (0-9).")
        if errors:
            QMessageBox.warning(self, "Sign Up Failed", "\n".join(errors))
            return

        ok, msg = register_user(username, password)

        if ok:
            QMessageBox.information(self, "Success", msg)
            self.signup_page.clear_inputs()
            self.show_login()
        else:
            QMessageBox.warning(self, "Sign Up Failed", msg)

    def handle_reset_search(self, username):
        if not username:
            QMessageBox.warning(self, "Search Failed", "Please enter your username or email.")
            return
        conn = __import__('Database_sor').connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()
        if not user:
            QMessageBox.warning(self, "Not Found", "Username not found.")
            return
        self._reset_username = username
        self.show_reset_new()

    def handle_reset_password(self, new_password, confirm_password):
        if not new_password or not confirm_password:
            QMessageBox.warning(self, "Reset Failed", "Please fill in all fields.")
            return
        if new_password != confirm_password:
            QMessageBox.warning(self, "Reset Failed", "Passwords do not match.")
            return
        username = getattr(self, "_reset_username", None)
        if not username:
            QMessageBox.warning(self, "Error", "Session expired, please try again.")
            self.show_login()
            return
        
        success, msg = update_password(username, new_password)
        if success:
            QMessageBox.information(self, "Password Reset", "Your password has been reset successfully!")
            self.reset_new_page.clear_inputs()
            self.reset_search_page.clear_inputs()
            self._reset_username = None
            self.show_login()
        else:
            QMessageBox.warning(self, "Error", msg)

    def refresh_user(self):
        """
        Updates the welcome label with the current session username.
        Overwrites text instead of appending.
        """
        username = getattr(Session, "username", None)
        if username:
            self.welcome_label.setText(f"Welcome back, {username}!")
        else:
            self.welcome_label.setText("Welcome back, Guest!")


# ==================== MAIN ENTRY POINT ====================
def main():
    init_database()
    run_migrations()
    fix_db_on_startup() 

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    FontManager()
    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()