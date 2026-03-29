import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QSizePolicy
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


class SettingsPage(QWidget):
    calculate_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("contentArea")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(0)

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(0)

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
        outer.addSpacing(32)

        # Form Grid
        grid = QGridLayout()
        grid.setSpacing(24)
        grid.setHorizontalSpacing(24)

        grid.addWidget(make_label("Gender"), 0, 0, 1, 2)
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("select the a gender.")
        self.gender_combo.addItem("Male")
        self.gender_combo.addItem("Female")
        self.gender_combo.setMinimumWidth(280)
        self.gender_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        grid.addWidget(self.gender_combo, 1, 0)

        grid.addWidget(make_label("Weight"), 2, 0)
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("Enter your weight")
        grid.addWidget(self.weight_input, 3, 0)

        grid.addWidget(make_label("Height"), 2, 1)
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("Enter your height")
        grid.addWidget(self.height_input, 3, 1)

        grid.addWidget(make_label("Age"), 4, 0)
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Enter your age")
        grid.addWidget(self.age_input, 5, 0)

        grid.addWidget(make_label("Activity Level"), 4, 1)
        self.activity_combo = QComboBox()
        self.activity_combo.addItem("Select your activity level")
        for level in ["Sedentary", "Lightly active", "Moderately active", "Very active", "Extra active"]:
            self.activity_combo.addItem(level)
        grid.addWidget(self.activity_combo, 5, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        outer.addLayout(grid)
        outer.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.calc_btn = QPushButton("Calculate")
        self.calc_btn.setObjectName("primaryBtn")
        self.calc_btn.setFixedHeight(44)
        self.calc_btn.setMinimumWidth(140)
        self.calc_btn.setCursor(Qt.PointingHandCursor)
        self.calc_btn.clicked.connect(self._on_calculate)
        btn_row.addWidget(self.calc_btn)
        outer.addLayout(btn_row)

    def _on_calculate(self):
        data = {
            "gender": self.gender_combo.currentText(),
            "weight": self.weight_input.text(),
            "height": self.height_input.text(),
            "age": self.age_input.text(),
            "activity": self.activity_combo.currentIndex(),
        }
        self.calculate_requested.emit(data)
