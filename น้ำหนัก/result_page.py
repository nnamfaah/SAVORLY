import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

_DIR = os.path.dirname(os.path.abspath(__file__))


def _icon(filename: str) -> QIcon:
    path = os.path.join(_DIR, filename)
    return QIcon(path) if os.path.exists(path) else QIcon()


def make_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    return lbl


class ResultPage(QWidget):
    confirmed = Signal()
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("contentArea")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(0)

        # Top bar
        top_bar = QHBoxLayout()
        header_col = QVBoxLayout()
        header_col.setSpacing(6)
        title = QLabel("Settings Nutritional Profile")
        title.setObjectName("pageTitle")
        sub = QLabel("Update your physical metrics to personalize your calorie targets.")
        sub.setObjectName("pageSubtitle")
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
        avatar.setObjectName("avatarLabel")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)

        top_bar.addWidget(notif_btn)
        top_bar.addSpacing(10)
        top_bar.addWidget(avatar)
        outer.addLayout(top_bar)
        outer.addSpacing(24)

        # Result Card
        card = QWidget()
        card.setObjectName("resultCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        card_layout.addWidget(make_label("BMI"))
        self.bmi_field = QLineEdit()
        self.bmi_field.setPlaceholderText("Awaiting information...")
        self.bmi_field.setReadOnly(True)
        self.bmi_field.setFixedHeight(44)
        card_layout.addWidget(self.bmi_field)

        card_layout.addSpacing(8)

        card_layout.addWidget(make_label("TDEE"))
        self.tdee_field = QLineEdit()
        self.tdee_field.setPlaceholderText("Awaiting information...")
        self.tdee_field.setReadOnly(True)
        self.tdee_field.setFixedHeight(44)
        card_layout.addWidget(self.tdee_field)

        card_layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.setFixedSize(120, 40)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.cancelled.emit)

        self.confirm_btn = QPushButton("Confirm BMI, TDEE")
        self.confirm_btn.setObjectName("primaryBtn")
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.setMinimumWidth(200)
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.clicked.connect(self.confirmed.emit)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addSpacing(12)
        btn_row.addWidget(self.confirm_btn)
        card_layout.addLayout(btn_row)

        outer.addWidget(card)
        outer.addStretch()

    def set_results(self, bmi: float, tdee: float):
        self.bmi_field.setText(f"{bmi:.2f}")
        self.tdee_field.setText(f"{tdee:.0f} kcal/day")

    def clear_results(self):
        self.bmi_field.clear()
        self.tdee_field.clear()
