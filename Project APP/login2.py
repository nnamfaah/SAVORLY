import sys
import os
import re
import json
import hashlib
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QFrame,
    QSizePolicy, QMessageBox, QScrollArea
)
from PySide6.QtGui import QFontDatabase, QFont, QPixmap, QIcon
from PySide6.QtCore import Qt, QSize, Signal, QTimer

from Database_sor import login_user, register_user
from session import Session
from mainwindow import MainWindow 

# ==================== PATHS ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, 'fonts')
ICONS_DIR = os.path.join(BASE_DIR, 'icons')
DATA_FILE = os.path.join(BASE_DIR, 'users.json')


# ==================== USER DATABASE ====================
class UserDatabase:
    MAX_ATTEMPTS = 5
    LOCK_SECONDS = 300

    def __init__(self):
        self._users = {}
        self._load()

    def _load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self._users = json.load(f)
            except:
                self._users = {}

    def _save(self):
        
         with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._users, f, indent=2)
    

    @staticmethod
    def _hash(password, salt):
        return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

    def username_exists(self, username):
        return username.lower() in self._users

    def email_exists(self, email):
        email = email.lower()
        return any(u['email'].lower() == email for u in self._users.values())

    def find_by_username_or_email(self, value):
        v = value.lower()
        if v in self._users:
            return self._users[v]
        for u in self._users.values():
            if u['email'].lower() == v:
                return u
        return None

    def register(self, username, email, password):
        key = username.lower()
        if key in self._users:
            return False, "Username is already taken."
        if self.email_exists(email):
            return False, "An account with this email already exists."
        salt = os.urandom(16).hex()
        self._users[key] = {
            "username": username,
            "email": email,
            "password_hash": self._hash(password, salt),
            "salt": salt,
            "created_at": time.time(),
            "failed_attempts": 0,
            "locked_until": 0.0,
        }
        self._save()
        return True, "Account created successfully!"

    def login(self, username_or_email, password):
        user = self.find_by_username_or_email(username_or_email)
        if not user:
            return False, "No account found with that username or email."
        if time.time() < user.get('locked_until', 0):
            remaining = int(user['locked_until'] - time.time())
            return False, f"Account locked. Try again in {remaining}s."
        if self._hash(password, user['salt']) == user['password_hash']:
            user['failed_attempts'] = 0
            self._save()
            return True, user['username']
        else:
            user['failed_attempts'] = user.get('failed_attempts', 0) + 1
            if user['failed_attempts'] >= self.MAX_ATTEMPTS:
                user['locked_until'] = time.time() + self.LOCK_SECONDS
                user['failed_attempts'] = 0
                self._save()
                return False, f"Too many failed attempts. Account locked for {self.LOCK_SECONDS // 60} minutes."
            remaining = self.MAX_ATTEMPTS - user['failed_attempts']
            self._save()
            return False, f"Incorrect password. {remaining} attempt(s) remaining."

    def reset_password(self, username_or_email, new_password):
        user = self.find_by_username_or_email(username_or_email)
        if not user:
            return False, "No account found."
        salt = os.urandom(16).hex()
        user['password_hash'] = self._hash(new_password, salt)
        user['salt'] = salt
        user['failed_attempts'] = 0
        user['locked_until'] = 0.0
        self._save()
        return True, "Password reset successfully!"


# ==================== VALIDATORS ====================
class Validator:
    USERNAME_MIN = 3
    USERNAME_MAX = 20
    USERNAME_RE  = re.compile(r'^[a-zA-Z0-9_]+$')
    EMAIL_RE     = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    PASSWORD_MIN = 8

    @classmethod
    def validate_username(cls, username):
        errors = []
        if len(username) < cls.USERNAME_MIN:
            errors.append(f"At least {cls.USERNAME_MIN} characters required.")
        if len(username) > cls.USERNAME_MAX:
            errors.append(f"Must be {cls.USERNAME_MAX} characters or fewer.")
        if username and not cls.USERNAME_RE.match(username):
            errors.append("Only letters, numbers, and underscores allowed.")
        return errors

    @classmethod
    def validate_email(cls, email):
        if not cls.EMAIL_RE.match(email):
            return ["Enter a valid email address (e.g. name@example.com)."]
        return []

    @classmethod
    def password_checks(cls, password):
        return {
            "min_length": len(password) >= cls.PASSWORD_MIN,
            "uppercase":  bool(re.search(r'[A-Z]', password)),
            "lowercase":  bool(re.search(r'[a-z]', password)),
            "digit":      bool(re.search(r'\d', password)),
            "special":    bool(re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>/?\\|`~]', password)),
        }

    @classmethod
    def password_strength(cls, password):
        score = sum(cls.password_checks(password).values())
        labels = {1: "Weak", 2: "Fair", 3: "Good", 4: "Strong", 5: "Very Strong"}
        return min(score, 4), labels.get(score, "Strong")

    @classmethod
    def validate_password(cls, password):
        checks = cls.password_checks(password)
        rules = {
            "min_length": f"At least {cls.PASSWORD_MIN} characters",
            "uppercase":  "At least one uppercase letter (A-Z)",
            "lowercase":  "At least one lowercase letter (a-z)",
            "digit":      "At least one number (0-9)",
            "special":    "At least one special character (!@#$%...)",
        }
        return [msg for key, msg in rules.items() if not checks[key]]


# ==================== COLORS ====================
class Colors:
    HEADER_BG           = "#A8C5A2"
    MAIN_BG             = "#FFFFFF"
    FORM_BG             = "#DDD8C4"
    BUTTON_PRIMARY      = "#6B7C5C"
    BUTTON_PRIMARY_HOVER= "#5A6B4B"
    BUTTON_TEXT         = "#FFFFFF"
    BUTTON_CANCEL       = "#FFFFFF"
    BUTTON_CANCEL_BORDER= "#CCCCCC"
    BUTTON_CANCEL_TEXT  = "#555555"
    TEXT_PRIMARY        = "#2C2C2C"
    TEXT_HEADING        = "#7B5B2E"
    TEXT_TERTIARY       = "#666666"
    TEXT_INPUT          = "#333333"
    TEXT_PLACEHOLDER    = "#999999"
    TEXT_LINK           = "#6B7C5C"
    INPUT_BG            = "#FFFFFF"
    INPUT_BORDER        = "#DDDDDD"
    INPUT_BORDER_ERROR  = "#E05252"
    INPUT_BORDER_OK     = "#6B7C5C"
    ERROR               = "#E05252"
    SUCCESS             = "#5A7A5A"
    STRENGTH_WEAK       = "#E05252"
    STRENGTH_FAIR       = "#D4892A"
    STRENGTH_GOOD       = "#6B9E6B"
    STRENGTH_STRONG     = "#6B7C5C"


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
            self._load()
            FontManager._fonts_loaded = True

    def _load(self):
        font_files = {
            'Inria Serif': ['InriaSerif-Regular.ttf','InriaSerif-Bold.ttf','InriaSerif-Light.ttf'],
            'Inter':       ['Inter-Regular.ttf','Inter-Medium.ttf','Inter-Bold.ttf'],
            'Inika':       ['Inika-Regular.ttf','Inika-Bold.ttf'],
        }
        self.font_ids = {}
        for family, files in font_files.items():
            for fname in files:
                path = os.path.join(FONTS_DIR, fname)
                if os.path.exists(path):
                    fid = QFontDatabase.addApplicationFont(path)
                    if fid != -1:
                        self.font_ids.setdefault(family, []).append(fid)
        self.inria_serif = "Inria Serif"
        self.inter = "Inter"
        self.inika = "Inika"

    def get_font(self, family, size, weight=QFont.Normal):
        return QFont(family, size, weight)


# ==================== WIDGETS ====================
class HeaderWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet(f"QFrame {{ background-color: {Colors.HEADER_BG}; border: none; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 0, 30, 0)
        lbl = QLabel("SAVORLY")
        lbl.setFont(FontManager().get_font(FontManager().inria_serif, 26, QFont.Bold))
        lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(lbl)
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
        self._build()

    def _build(self):
        self.setFixedHeight(46)
        self._border(Colors.INPUT_BORDER)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        path = os.path.join(ICONS_DIR, f"{self.icon_name}.png")
        if os.path.exists(path):
            pix = QPixmap(path).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pix)
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(self.placeholder_text)
        self.line_edit.setFont(FontManager().get_font(FontManager().inter, 12))
        self.line_edit.setStyleSheet(f"QLineEdit {{ background: transparent; border: none; color: {Colors.TEXT_INPUT}; padding: 0; }}")
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
            self.toggle_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
            self._update_eye()
            self.toggle_btn.clicked.connect(self._toggle)
            layout.addWidget(self.toggle_btn)

    def _border(self, color):
        self.setStyleSheet(f"QFrame {{ background-color: {Colors.INPUT_BG}; border: 1.5px solid {color}; border-radius: 8px; }}")

    def set_state(self, state):
        if state == 'error':   self._border(Colors.INPUT_BORDER_ERROR)
        elif state == 'ok':    self._border(Colors.INPUT_BORDER_OK)
        else:                  self._border(Colors.INPUT_BORDER)

    def _update_eye(self):
        name = "eye_off_icon" if self.password_visible else "eye_icon"
        p = os.path.join(ICONS_DIR, f"{name}.png")
        if os.path.exists(p):
            self.toggle_btn.setIcon(QIcon(p))
            self.toggle_btn.setIconSize(QSize(20, 20))

    def _toggle(self):
        self.password_visible = not self.password_visible
        self.line_edit.setEchoMode(QLineEdit.Normal if self.password_visible else QLineEdit.Password)
        self._update_eye()

    def text(self):       return self.line_edit.text()
    def setText(self, t): self.line_edit.setText(t)


class FieldError(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(FontManager().get_font(FontManager().inter, 10))
        self.setStyleSheet(f"color: {Colors.ERROR}; background: transparent;")
        self.setWordWrap(True)
        self.hide()

    def show_error(self, msg):
        self.setText("⚠  " + msg)
        self.show()

    def clear_error(self):
        self.setText("")
        self.hide()


class PasswordStrengthWidget(QWidget):
    """Live password strength: checklist + segmented bar."""

    RULES = [
        ("min_length", f"At least {Validator.PASSWORD_MIN} characters"),
        ("uppercase",  "At least one uppercase letter (A–Z)"),
        ("lowercase",  "At least one lowercase letter (a–z)"),
        ("digit",      "At least one number (0–9)"),
        ("special",    "At least one special character  (!@#$%...)"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 6, 0, 0)
        vl.setSpacing(3)

        # Rule labels
        self._rule_labels = {}
        for key, text in self.RULES:
            lbl = QLabel(f"✗  {text}")
            lbl.setFont(FontManager().get_font(FontManager().inter, 10))
            lbl.setStyleSheet(f"color: {Colors.ERROR}; background: transparent;")
            self._rule_labels[key] = lbl
            vl.addWidget(lbl)

        vl.addSpacing(4)

        # Bar row
        bar_row = QWidget()
        bar_row.setStyleSheet("background: transparent;")
        brl = QHBoxLayout(bar_row)
        brl.setContentsMargins(0, 0, 0, 0)
        brl.setSpacing(5)

        self._segs = []
        for _ in range(4):
            seg = QFrame()
            seg.setFixedHeight(5)
            seg.setStyleSheet("QFrame { background-color: #CCCCCC; border-radius: 3px; }")
            self._segs.append(seg)
            brl.addWidget(seg)

        self._strength_lbl = QLabel("")
        self._strength_lbl.setFont(FontManager().get_font(FontManager().inter, 10, QFont.Medium))
        self._strength_lbl.setStyleSheet("background: transparent;")
        self._strength_lbl.setFixedWidth(70)
        brl.addWidget(self._strength_lbl)
        vl.addWidget(bar_row)
        self.hide()

    def update_password(self, password):
        if not password:
            self.hide()
            return
        self.show()
        checks = Validator.password_checks(password)
        for key, lbl in self._rule_labels.items():
            base_text = dict(self.RULES)[key]
            if checks[key]:
                lbl.setText(f"✓  {base_text}")
                lbl.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")
            else:
                lbl.setText(f"✗  {base_text}")
                lbl.setStyleSheet(f"color: {Colors.ERROR}; background: transparent;")

        score, label = Validator.password_strength(password)
        colour_map = {
            1: Colors.STRENGTH_WEAK,
            2: Colors.STRENGTH_FAIR,
            3: Colors.STRENGTH_GOOD,
            4: Colors.STRENGTH_STRONG,
        }
        colour = colour_map.get(score, Colors.STRENGTH_STRONG)
        for i, seg in enumerate(self._segs):
            if i < score:
                seg.setStyleSheet(f"QFrame {{ background-color: {colour}; border-radius: 3px; }}")
            else:
                seg.setStyleSheet("QFrame { background-color: #CCCCCC; border-radius: 3px; }")
        self._strength_lbl.setText(label)
        self._strength_lbl.setStyleSheet(f"color: {colour}; background: transparent;")


class PrimaryButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFont(FontManager().get_font(FontManager().inter, 11, QFont.Medium))
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BUTTON_PRIMARY};
                color: {Colors.BUTTON_TEXT};
                border: none; border-radius: 8px; padding: 0 20px;
            }}
            QPushButton:hover    {{ background-color: {Colors.BUTTON_PRIMARY_HOVER}; }}
            QPushButton:pressed  {{ background-color: #4A5A3B; }}
            QPushButton:disabled {{ background-color: #AAAAAA; }}
        """)


class SecondaryButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFont(FontManager().get_font(FontManager().inter, 11, QFont.Medium))
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BUTTON_CANCEL};
                color: {Colors.BUTTON_CANCEL_TEXT};
                border: 1px solid {Colors.BUTTON_CANCEL_BORDER};
                border-radius: 8px; padding: 0 20px;
            }}
            QPushButton:hover   {{ background-color: #F5F5F5; }}
            QPushButton:pressed {{ background-color: #ECECEC; }}
        """)


class LinkLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFont(FontManager().get_font(FontManager().inter, 12))
        self.setStyleSheet(f"QLabel {{ color: {Colors.TEXT_LINK}; background: transparent; font-weight: bold; }}")
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


def _field_lbl(text):
    lbl = QLabel(text)
    lbl.setFont(FontManager().get_font(FontManager().inter, 11, QFont.Medium))
    lbl.setStyleSheet(f"color: {Colors.TEXT_HEADING}; background: transparent;")
    return lbl


def make_form_box():
    box = QFrame()
    box.setStyleSheet(f"QFrame {{ background-color: {Colors.FORM_BG}; border-radius: 12px; border: none; }}")
    box.setMinimumWidth(420)
    box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    fl = QVBoxLayout(box)
    fl.setContentsMargins(30, 30, 30, 30)
    fl.setSpacing(6)
    return box, fl


def make_header_section(cl, title, subtitle):
    fm = FontManager()
    t = QLabel(title)
    t.setFont(fm.get_font(fm.inria_serif, 30, QFont.Normal))
    t.setStyleSheet(f"color: {Colors.TEXT_HEADING}; background: transparent;")
    t.setAlignment(Qt.AlignCenter)
    cl.addWidget(t)
    cl.addSpacing(8)
    s = QLabel(subtitle)
    s.setFont(fm.get_font(fm.inter, 12))
    s.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; background: transparent;")
    s.setAlignment(Qt.AlignCenter)
    cl.addWidget(s)
    cl.addSpacing(20)


# ==================== PAGES ====================

class LoginPage(QWidget):
    login_requested = Signal(str)
    signup_clicked  = Signal()
    forgot_password_clicked = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build()

    def _build(self):
        fm = FontManager()
        self.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        ml = QVBoxLayout(self)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)
        ml.addWidget(HeaderWidget())

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        cl.setSpacing(0)

        make_header_section(cl, "Welcome back", "Please enter your details to sign in to your account.")

        box, fl = make_form_box()

        self.username_input = IconLineEdit("user_icon", "Enter your username or email")
        fl.addWidget(self.username_input)
        self.username_err = FieldError()
        fl.addWidget(self.username_err)
        fl.addSpacing(6)

        self.password_input = IconLineEdit("lock_icon", "Enter your password", show_toggle=True)
        fl.addWidget(self.password_input)
        self.password_err = FieldError()
        fl.addWidget(self.password_err)

        forgot_row = QWidget()
        forgot_row.setStyleSheet("background: transparent;")
        fr = QHBoxLayout(forgot_row)
        fr.setContentsMargins(0, 4, 0, 0)
        fr.addStretch()
        self.forgot_link = LinkLabel("Forgot password ?")
        self.forgot_link.clicked.connect(self.forgot_password_clicked.emit)
        fr.addWidget(self.forgot_link)
        fl.addWidget(forgot_row)
        fl.addSpacing(10)

        self.signin_btn = PrimaryButton("Sign in")
        self.signin_btn.clicked.connect(self._submit)
        fl.addWidget(self.signin_btn)

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 6, 0, 0)
        rl.setSpacing(4)
        rl.setAlignment(Qt.AlignCenter)
        no_acc = QLabel("Don't have an account?")
        no_acc.setFont(fm.get_font(fm.inter, 12))
        no_acc.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; background: transparent;")
        link = LinkLabel("Sign up for free")
        link.clicked.connect(self.signup_clicked.emit)
        rl.addWidget(no_acc)
        rl.addWidget(link)
        fl.addWidget(row)

        cl.addWidget(box)
        cl.addStretch()
        ml.addWidget(content, 1)

    def _submit(self):
        u = self.username_input.text().strip()
        p = self.password_input.text()

        self.username_err.clear_error(); self.username_input.set_state('normal')
        self.password_err.clear_error(); self.password_input.set_state('normal')
        valid = True

        if not u:
            self.username_err.show_error("Please enter your username or email.")
            self.username_input.set_state('error'); valid = False
        if not p:
            self.password_err.show_error("Please enter your password.")
            self.password_input.set_state('error'); valid = False
        if not valid:
            return

        ok, result = self.db.login(u, p)
        if ok:
            Session.username = result

            self.username_input.set_state('ok')
            self.login_requested.emit(Session.username)
        else:
            self.password_err.show_error(result)
            self.password_input.set_state('error')
            self.username_input.set_state('error')

    def clear_inputs(self):
        for w in [self.username_input, self.password_input]:
            w.setText(""); w.set_state('normal')
            
        for e in [self.username_err, self.password_err]:
            e.clear_error()


class SignUpPage(QWidget):
    signup_success = Signal(str)
    signin_clicked = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._u_timer = QTimer()
        self._u_timer.setSingleShot(True)
        self._u_timer.timeout.connect(self._live_username)
        self._build()

    def _build(self):
        fm = FontManager()
        self.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        ml = QVBoxLayout(self)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)
        ml.addWidget(HeaderWidget())

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        cl.setSpacing(0)

        make_header_section(cl, "Sign up", "Register for a new account.")

        # Scrollable so content fits small windows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        il = QVBoxLayout(inner)
        il.setContentsMargins(0, 0, 0, 0)

        box, fl = make_form_box()

        # Username
        fl.addWidget(_field_lbl("Username"))
        self.username_input = IconLineEdit("user_icon", "Choose a username (letters, numbers, _)")
        self.username_input.textChanged.connect(lambda _: self._u_timer.start(500))
        fl.addWidget(self.username_input)
        self.username_err = FieldError()
        fl.addWidget(self.username_err)
        fl.addSpacing(8)

        # Email
        fl.addWidget(_field_lbl("Email"))
        self.email_input = IconLineEdit("user_icon", "Enter your email address")
        self.email_input.textChanged.connect(self._live_email)
        fl.addWidget(self.email_input)
        self.email_err = FieldError()
        fl.addWidget(self.email_err)
        fl.addSpacing(8)

        # Password
        fl.addWidget(_field_lbl("Password"))
        self.password_input = IconLineEdit("lock_icon", "Create a strong password", show_toggle=True)
        self.password_input.textChanged.connect(self._on_pw)
        fl.addWidget(self.password_input)
        self.password_err = FieldError()
        fl.addWidget(self.password_err)
        self.strength_widget = PasswordStrengthWidget()
        fl.addWidget(self.strength_widget)
        fl.addSpacing(8)

        # Confirm
        fl.addWidget(_field_lbl("Confirm Password"))
        self.confirm_input = IconLineEdit("lock_icon", "Re-enter your password", show_toggle=True)
        self.confirm_input.textChanged.connect(self._on_confirm)
        fl.addWidget(self.confirm_input)
        self.confirm_err = FieldError()
        fl.addWidget(self.confirm_err)
        fl.addSpacing(14)

        self.signup_btn = PrimaryButton("Sign up")
        self.signup_btn.clicked.connect(self._submit)
        fl.addWidget(self.signup_btn)

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 6, 0, 0)
        rl.setSpacing(4)
        rl.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Have an account?")
        lbl.setFont(fm.get_font(fm.inter, 12))
        lbl.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; background: transparent;")
        link = LinkLabel("Sign in")
        link.clicked.connect(self.signin_clicked.emit)
        rl.addWidget(lbl); rl.addWidget(link)
        fl.addWidget(row)

        il.addWidget(box)
        il.addStretch()
        scroll.setWidget(inner)
        cl.addWidget(scroll, 1)
        ml.addWidget(content, 1)

    # ── Live checks ──
    def _live_username(self):
        u = self.username_input.text().strip()
        self.username_err.clear_error(); self.username_input.set_state('normal')
        if not u: return
        errs = Validator.validate_username(u)
        if errs:
            self.username_err.show_error(errs[0]); self.username_input.set_state('error')
        elif self.db.username_exists(u):
            self.username_err.show_error("Username already taken. Try another."); self.username_input.set_state('error')
        else:
            self.username_input.set_state('ok')

    def _live_email(self, _=None):
        e = self.email_input.text().strip()
        self.email_err.clear_error(); self.email_input.set_state('normal')
        if not e: return
        errs = Validator.validate_email(e)
        if errs:
            self.email_err.show_error(errs[0]); self.email_input.set_state('error')
        elif self.db.email_exists(e):
            self.email_err.show_error("An account with this email already exists."); self.email_input.set_state('error')
        else:
            self.email_input.set_state('ok')

    def _on_pw(self, text):
        self.password_err.clear_error()
        self.strength_widget.update_password(text)
        if self.confirm_input.text():
            self._on_confirm(self.confirm_input.text())

    def _on_confirm(self, text):
        self.confirm_err.clear_error()
        if text and text != self.password_input.text():
            self.confirm_err.show_error("Passwords do not match."); self.confirm_input.set_state('error')
        elif text and text == self.password_input.text():
            self.confirm_input.set_state('ok')
        else:
            self.confirm_input.set_state('normal')

    # ── Submit ──
    def _submit(self):
        u = self.username_input.text().strip()
        e = self.email_input.text().strip()
        p = self.password_input.text()
        c = self.confirm_input.text()

        for err in [self.username_err, self.email_err, self.password_err, self.confirm_err]:
            err.clear_error()
        for inp in [self.username_input, self.email_input, self.password_input, self.confirm_input]:
            inp.set_state('normal')

        valid = True

        u_errs = Validator.validate_username(u) if u else ["Username is required."]
        if u_errs:
            self.username_err.show_error(u_errs[0]); self.username_input.set_state('error'); valid = False
        elif self.db.username_exists(u):
            self.username_err.show_error("Username already taken."); self.username_input.set_state('error'); valid = False
        else:
            self.username_input.set_state('ok')

        e_errs = Validator.validate_email(e) if e else ["Email is required."]
        if e_errs:
            self.email_err.show_error(e_errs[0]); self.email_input.set_state('error'); valid = False
        elif self.db.email_exists(e):
            self.email_err.show_error("Email already registered."); self.email_input.set_state('error'); valid = False
        else:
            self.email_input.set_state('ok')

        p_errs = Validator.validate_password(p) if p else ["Password is required."]
        if p_errs:
            self.password_err.show_error(p_errs[0]); self.password_input.set_state('error'); valid = False
        else:
            self.password_input.set_state('ok')

        if not c:
            self.confirm_err.show_error("Please confirm your password."); self.confirm_input.set_state('error'); valid = False
        elif c != p:
            self.confirm_err.show_error("Passwords do not match."); self.confirm_input.set_state('error'); valid = False
        else:
            self.confirm_input.set_state('ok')

        if not valid:
            return

        ok, msg = self.db.register(u, e, p)
        if ok:
            self.signup_success.emit(u)
        else:
            QMessageBox.warning(self.window(), "Registration Failed", msg)

    def clear_inputs(self):
        for inp in [self.username_input, self.email_input, self.password_input, self.confirm_input]:
            inp.setText(""); inp.set_state('normal')
        for err in [self.username_err, self.email_err, self.password_err, self.confirm_err]:
            err.clear_error()
        self.strength_widget.hide()


class ResetPasswordSearchPage(QWidget):
    search_success = Signal(str)
    cancel_clicked = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build()

    def _build(self):
        fm = FontManager()
        self.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        ml = QVBoxLayout(self)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)
        ml.addWidget(HeaderWidget())

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        cl.setSpacing(0)

        make_header_section(cl, "Reset your password", "Locate your email account or username.")

        box, fl = make_form_box()

        self.username_input = IconLineEdit("user_icon", "Enter your username or email.")
        fl.addWidget(self.username_input)
        self.username_err = FieldError()
        fl.addWidget(self.username_err)
        fl.addSpacing(14)

        btn_row = QWidget()
        btn_row.setStyleSheet("background: transparent;")
        br = QHBoxLayout(btn_row)
        br.setContentsMargins(0, 0, 0, 0)
        br.setSpacing(12)
        br.addStretch()

        self.cancel_btn = SecondaryButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        self.cancel_btn.setFixedWidth(90)

        self.search_btn = PrimaryButton("Search and browse your account.")
        self.search_btn.clicked.connect(self._submit)
        self.search_btn.setFixedWidth(250)

        br.addWidget(self.cancel_btn)
        br.addWidget(self.search_btn)
        fl.addWidget(btn_row)

        cl.addWidget(box)
        cl.addStretch()
        ml.addWidget(content, 1)

    def _submit(self):
        v = self.username_input.text().strip()
        self.username_err.clear_error(); self.username_input.set_state('normal')
        if not v:
            self.username_err.show_error("Please enter your username or email.")
            self.username_input.set_state('error'); return
        user = self.db.find_by_username_or_email(v)
        if not user:
            self.username_err.show_error("No account found with that username or email.")
            self.username_input.set_state('error')
        else:
            self.username_input.set_state('ok')
            self.search_success.emit(v)

    def clear_inputs(self):
        self.username_input.setText(""); self.username_input.set_state('normal')
        self.username_err.clear_error()


class ResetPasswordNewPage(QWidget):
    reset_success = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._target = ""
        self._build()

    def set_target(self, value):
        self._target = value

    def _build(self):
        fm = FontManager()
        self.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        ml = QVBoxLayout(self)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)
        ml.addWidget(HeaderWidget())

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.MAIN_BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        cl.setSpacing(0)

        make_header_section(cl, "Reset your password", "Please enter your new password below.")

        box, fl = make_form_box()

        fl.addWidget(_field_lbl("New Password"))
        self.new_pw = IconLineEdit("lock_icon", "Enter your new password", show_toggle=True)
        self.new_pw.textChanged.connect(self._on_pw)
        fl.addWidget(self.new_pw)
        self.new_pw_err = FieldError()
        fl.addWidget(self.new_pw_err)
        self.strength_widget = PasswordStrengthWidget()
        fl.addWidget(self.strength_widget)
        fl.addSpacing(8)

        fl.addWidget(_field_lbl("Confirm New Password"))
        self.confirm = IconLineEdit("lock_icon", "Re-enter your new password", show_toggle=True)
        self.confirm.textChanged.connect(self._on_confirm)
        fl.addWidget(self.confirm)
        self.confirm_err = FieldError()
        fl.addWidget(self.confirm_err)
        fl.addSpacing(14)

        btn_row = QWidget()
        btn_row.setStyleSheet("background: transparent;")
        br = QHBoxLayout(btn_row)
        br.setContentsMargins(0, 0, 0, 0)
        br.setAlignment(Qt.AlignCenter)
        self.reset_btn = PrimaryButton("Reset your password")
        self.reset_btn.clicked.connect(self._submit)
        self.reset_btn.setFixedWidth(200)
        br.addWidget(self.reset_btn)
        fl.addWidget(btn_row)

        cl.addWidget(box)
        cl.addStretch()
        ml.addWidget(content, 1)

    def _on_pw(self, text):
        self.new_pw_err.clear_error()
        self.strength_widget.update_password(text)
        if self.confirm.text():
            self._on_confirm(self.confirm.text())

    def _on_confirm(self, text):
        self.confirm_err.clear_error()
        if text and text != self.new_pw.text():
            self.confirm_err.show_error("Passwords do not match."); self.confirm.set_state('error')
        elif text == self.new_pw.text() and text:
            self.confirm.set_state('ok'); self.confirm_err.clear_error()
        else:
            self.confirm.set_state('normal')

    def _submit(self):
        p = self.new_pw.text()
        c = self.confirm.text()

        self.new_pw_err.clear_error(); self.confirm_err.clear_error()
        self.new_pw.set_state('normal'); self.confirm.set_state('normal')
        valid = True

        p_errs = Validator.validate_password(p) if p else ["Password is required."]
        if p_errs:
            self.new_pw_err.show_error(p_errs[0]); self.new_pw.set_state('error'); valid = False
        else:
            self.new_pw.set_state('ok')

        if not c:
            self.confirm_err.show_error("Please confirm your password."); self.confirm.set_state('error'); valid = False
        elif c != p:
            self.confirm_err.show_error("Passwords do not match."); self.confirm.set_state('error'); valid = False
        else:
            self.confirm.set_state('ok')

        if not valid: return

        ok, msg = self.db.reset_password(self._target, p)
        if ok:
            self.reset_success.emit()
        else:
            QMessageBox.warning(self.window(), "Reset Failed", msg)

    def clear_inputs(self):
        for inp in [self.new_pw, self.confirm]:
            inp.setText(""); inp.set_state('normal')
        for err in [self.new_pw_err, self.confirm_err]:
            err.clear_error()
        self.strength_widget.hide()


# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAVORLY - Login")
        self.setMinimumSize(700, 580)
        self.resize(700, 650)
        self.db = UserDatabase()
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        ml = QVBoxLayout(central)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self.stack = QStackedWidget()

        self.login_page        = LoginPage(self.db)
        self.signup_page       = SignUpPage(self.db)
        self.reset_search_page = ResetPasswordSearchPage(self.db)
        self.reset_new_page    = ResetPasswordNewPage(self.db)

        for page in [self.login_page, self.signup_page, self.reset_search_page, self.reset_new_page]:
            self.stack.addWidget(page)

        self.login_page.login_requested.connect(self._on_login)
        self.login_page.signup_clicked.connect(self._go_signup)
        self.login_page.forgot_password_clicked.connect(self._go_reset_search)

        self.signup_page.signup_success.connect(self._on_signup)
        self.signup_page.signin_clicked.connect(self._go_login)

        self.reset_search_page.search_success.connect(self._on_reset_search)
        self.reset_search_page.cancel_clicked.connect(self._go_login)

        self.reset_new_page.reset_success.connect(self._on_reset_success)

        ml.addWidget(self.stack)

    def _go_login(self):
        self.stack.setCurrentWidget(self.login_page)
        self.setWindowTitle("SAVORLY - Login")

    def _go_signup(self):
        self.stack.setCurrentWidget(self.signup_page)
        self.setWindowTitle("SAVORLY - Sign Up")

    def _go_reset_search(self):
        self.stack.setCurrentWidget(self.reset_search_page)
        self.setWindowTitle("SAVORLY - Reset Password")

    def _go_reset_new(self):
        self.stack.setCurrentWidget(self.reset_new_page)
        self.setWindowTitle("SAVORLY - New Password")

    def _on_login(self, username):
        Session.username = username

        QMessageBox.information(self, "Login Successful", f"Welcome back, {username}!")
    # Open Dashboard (Main App)
        from mainwindow import MainWindow as AppMainWindow
        self.app_window = AppMainWindow()
        self.app_window.show()

    # Close Login Window
        self.close()

    def _on_signup(self, username):
        QMessageBox.information(self, "Account Created", f"Welcome to SAVORLY, {username}!\nYou can now sign in.")
        self.signup_page.clear_inputs()
        self._go_login()

    def _on_reset_search(self, value):
        self.reset_new_page.set_target(value)
        self._go_reset_new()

    def _on_reset_success(self):
        QMessageBox.information(self, "Password Reset", "Your password has been reset successfully!")
        self.reset_new_page.clear_inputs()
        self.reset_search_page.clear_inputs()
        self._go_login()


# ==================== ENTRY POINT ====================
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    FontManager()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()