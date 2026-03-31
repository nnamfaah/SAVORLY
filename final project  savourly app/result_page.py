import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QIcon

import stylesheet as ss

_DIR = os.path.dirname(os.path.abspath(__file__))


def _icon(filename: str) -> QIcon:
    path = os.path.join(_DIR, filename)
    return QIcon(path) if os.path.exists(path) else QIcon()


def make_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("""
        font-size: 12px;
        font-weight: 600;
        color: #888;
        letter-spacing: 1px;
    """)
    return lbl


class ResultPage(QWidget):
    confirmed = Signal()
    cancelled = Signal()

    data_confirmed = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("contentArea")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(0)

        self.bmi = None
        self.tdee = None

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        # Top bar
        top_bar = QHBoxLayout()
        header_col = QVBoxLayout()
        header_col.setSpacing(6)
        title = QLabel("Settings Nutritional Profile")
        title.setStyleSheet(ss.page_title)
        sub = QLabel("Update your physical metrics to personalize your calorie targets.")
        sub.setStyleSheet(ss.page_subtitle)
        header_col.addWidget(title)
        header_col.addWidget(sub)
        top_bar.addLayout(header_col)
        top_bar.addStretch()

        notif_btn = QPushButton()
        notif_btn.setObjectName("notifBtn")
        notif_btn.setFixedSize(36, 36)
        notif_btn.setCursor(Qt.PointingHandCursor)
        notif_icon = _icon("icon_notification.png")
        if not notif_icon.isNull():
            notif_btn.setIcon(notif_icon)
            notif_btn.setIconSize(QSize(20, 20))
        else:
            notif_btn.setText("🔔")

        avatar = QLabel("👤")
        avatar.setStyleSheet(ss.sidebar_avatar)
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)

        top_bar.addWidget(notif_btn)
        top_bar.addSpacing(10)
        top_bar.addWidget(avatar)
        outer.addLayout(top_bar)
        outer.addSpacing(24)

        # Result Card
        card = QWidget()
        card.setStyleSheet(ss.white_card)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        result_layout = QVBoxLayout()
        result_layout.setSpacing(18)

        self.bmi_title = make_label("BMI")
        self.bmi_value = QLabel("--")
        self.bmi_value.setAlignment(Qt.AlignCenter)
        self.bmi_value.setStyleSheet("""
            font-size: 40px;
            font-weight: 700;
            color: #2E7D32;
        """)
        result_layout.addWidget(self.bmi_title)
        result_layout.addWidget(self.bmi_value)
        result_layout.addSpacing(8)

        self.tdee_title = make_label("TDEE")
        self.tdee_value = QLabel("--")
        self.tdee_value.setAlignment(Qt.AlignCenter)
        self.tdee_value.setStyleSheet("""
            font-size: 36px;
            font-weight: 700;
            color: #C62828;
        """)
        result_layout.addWidget(self.tdee_title)
        result_layout.addWidget(self.tdee_value)

        card_layout.addLayout(result_layout)
        card_layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.setFixedSize(120, 40)
        self.cancel_btn.setStyleSheet(ss.btn_primary(bg=ss.white, fg=ss.text))
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.cancelled.emit)

        self.confirm_btn = QPushButton("Confirm BMI, TDEE")
        self.confirm_btn.setObjectName("primaryBtn")
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.setMinimumWidth(200)
        self.confirm_btn.setStyleSheet(ss.btn_primary())
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.clicked.connect(self._on_confirm)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addSpacing(12)
        btn_row.addWidget(self.confirm_btn)
        card_layout.addLayout(btn_row)

        outer.addWidget(card)
        outer.addStretch()

    def set_results(self, bmi, tdee):
        self.bmi = bmi
        self.tdee = tdee
        self.bmi_value.setText(f"{bmi:.2f}")
        self.tdee_value.setText(f"{tdee:.0f}")

    def clear_results(self):
        self.bmi = None
        self.tdee = None
        self.bmi_value.setText("--")
        self.tdee_value.setText("--")

    def update_data(self, data):
        try:
            age = int(data["age"])
            height = float(data["height"])
            weight = float(data["weight"])
            gender = data["gender"]
            activity = data["activity"]

            # ===== CALCULATE BMR =====
            if gender.lower() == "male":
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            else:
                bmr = 10 * weight + 6.25 * height - 5 * age - 161

            # ===== TDEE =====
            multipliers = [1.2, 1.375, 1.55, 1.725, 1.9]
            if 0 <= activity < len(multipliers):
                tdee = bmr * multipliers[activity]
            else:
                tdee = bmr

            # ===== BMI =====
            bmi = weight / ((height / 100) ** 2)

            self.set_results(bmi, tdee)

        except Exception as e:
            print("Update data error:", e)

    def _on_confirm(self):
        if self.bmi is not None and self.tdee is not None:
            self.data_confirmed.emit(self.bmi, self.tdee)  
            self.confirmed.emit()

    def play_entry_animation(self):
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(400)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        start_pos = self.pos() + QPoint(0, 30)
        end_pos = self.pos()
        self.move(start_pos)

        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(400)
        self.slide_anim.setStartValue(start_pos)
        self.slide_anim.setEndValue(end_pos)
        self.slide_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_anim.start()
        self.slide_anim.start()
