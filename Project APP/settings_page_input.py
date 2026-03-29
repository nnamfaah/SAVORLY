import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PySide6.QtGui import QIcon, QCursor

from Database_sor import get_user_profile
from session import Session
import stylesheet as ss

_DIR = os.path.dirname(os.path.abspath(__file__))


def _icon(filename: str) -> QIcon:
    path = os.path.join(_DIR, filename)
    return QIcon(path) if os.path.exists(path) else QIcon()


def make_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(ss.section)  
    return lbl

class AnimatedComboBox(QComboBox):
    def showPopup(self):
        super().showPopup()

        popup = self.view().window()

        # Get position
        start_pos = popup.pos() - QPoint(0, 10)
        end_pos = popup.pos()

        popup.move(start_pos)

        # Slide animation
        self.anim = QPropertyAnimation(popup, b"pos")
        self.anim.setDuration(150)
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.setEasingCurve(QEasingCurve.OutBack)

        # Fade animation
        self.fade = QPropertyAnimation(popup, b"windowOpacity")
        self.fade.setDuration(150)
        self.fade.setStartValue(0)
        self.fade.setEndValue(1)


        self.anim.start()
        self.fade.start()

class SettingsPage(QWidget):
    calculate_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("contentArea")
        top_bar = QHBoxLayout()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        title = QLabel("Settings Nutritional Profile")
        title.setStyleSheet(ss.page_title)
        sub = QLabel("Update your physical metrics to personalize your calorie targets.")
        sub.setStyleSheet(ss.page_subtitle)
        header = QVBoxLayout()
        header.addWidget(title)
        header.addWidget(sub)
        outer.addLayout(header)
        outer.addSpacing(24)

        notif_btn = QPushButton()
        notif_btn.setObjectName("notifBtn")
        notif_btn.setFixedSize(36, 36)
        notif_btn.setCursor(Qt.PointingHandCursor)
        bell = QLabel("🔔"); bell.setFixedSize(40,40); bell.setAlignment(Qt.AlignCenter)
        bell.setStyleSheet(ss.bell_icon)

        av_wrap = QWidget(); av_wrap.setFixedSize(44,44)
        av_wrap.setStyleSheet(f"background:{ss.light_green}; border-radius:22px;")
        av_inner = QVBoxLayout(av_wrap); av_inner.setContentsMargins(0,0,0,0)
        av_lbl = QLabel("👤"); av_lbl.setAlignment(Qt.AlignCenter)
        av_lbl.setStyleSheet("font-size:20px; background:transparent;")
        av_inner.addWidget(av_lbl)

        top_bar.addWidget(notif_btn)
        top_bar.addSpacing(10)
        top_bar.addWidget(av_wrap)
        outer.addLayout(top_bar)
        outer.addSpacing(24)

        self.autosave_timer = QTimer()
        self.autosave_timer.setInterval(800)  # 0.8 sec delay
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.auto_save)

        self.status_label = QLabel("Saved ✅")

        self.gender_combo = AnimatedComboBox()
        self.gender_combo.addItems(["Male", "Female"])
        self.gender_combo.setPlaceholderText("Select gender")
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("Enter your weight")
        self.weight_input.setStyleSheet(ss.line_edit)
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("Enter your height")
        self.height_input.setStyleSheet(ss.line_edit)
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Enter your age")
        self.age_input.setStyleSheet(ss.line_edit)

        self.activity_combo = AnimatedComboBox()
        self.activity_combo.addItems([
            "Sedentary", "Lightly active",
            "Moderately active", "Very active", "Extra active"
        ])
        self.activity_combo.setPlaceholderText("Select activity")
        self.gender_combo.setStyleSheet(ss.combo_box)
        self.activity_combo.setStyleSheet(ss.combo_box)

        for w in [
            self.gender_combo,
            self.weight_input,
            self.height_input,
            self.age_input,
            self.activity_combo
        ]:
            w.setFixedHeight(44)
            w.setMinimumWidth(260)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(16)
        grid.addWidget(make_label("Gender"), 0, 0)
        grid.addWidget(self.gender_combo, 1, 0)
        grid.addWidget(make_label("Weight"), 2, 0)
        grid.addWidget(make_label("Height"), 2, 1)
        grid.addWidget(self.weight_input, 3, 0)
        grid.addWidget(self.height_input, 3, 1)
        grid.addWidget(make_label("Age"), 4, 0)
        grid.addWidget(make_label("Activity Level"), 4, 1)
        grid.addWidget(self.age_input, 5, 0)
        grid.addWidget(self.activity_combo, 5, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        outer.addLayout(grid)
        outer.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.calc_btn = QPushButton("Calculate")
        self.calc_btn.setStyleSheet(ss.btn_primary())
        self.calc_btn.setFixedHeight(44)
        self.calc_btn.setEnabled(False)
        self.calc_btn.clicked.connect(self._on_calculate)
        btn_row.addWidget(self.calc_btn)
        outer.addLayout(btn_row)

        self.weight_input.textChanged.connect(self.trigger_autosave)
        self.height_input.textChanged.connect(self.trigger_autosave)
        self.age_input.textChanged.connect(self.trigger_autosave)
        self.gender_combo.currentIndexChanged.connect(self.trigger_autosave)
        self.activity_combo.currentIndexChanged.connect(self.trigger_autosave)


        self.load_user_data()

    def _build_user_row(self):
        row = QHBoxLayout()
        avatar = QLabel("👤")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(ss.sidebar_avatar)
        row.addWidget(avatar)


    def validate_inputs(self):
        valid = True
        # Weight
        text = self.weight_input.text().strip()
        if not text:
            self.weight_input.setStyleSheet(ss.input_invalid)
            valid = False
        else:
            try:
                if float(text) > 0:
                    self.weight_input.setStyleSheet(ss.input_valid)
                else:
                    raise ValueError
            except:
                self.weight_input.setStyleSheet(ss.input_invalid)
                valid = False
        # Height
        text = self.height_input.text().strip()
        if not text:
            self.height_input.setStyleSheet(ss.input_invalid)
            valid = False
        else:
            try:
                if float(text) > 0:
                    self.height_input.setStyleSheet(ss.input_valid)
                else:
                    raise ValueError
            except:
                self.height_input.setStyleSheet(ss.input_invalid)
                valid = False
        # Age
        text = self.age_input.text().strip()
        if not text:
            self.age_input.setStyleSheet(ss.input_invalid)
            valid = False
        else:
            try:
                if int(text) > 0:
                    self.age_input.setStyleSheet(ss.input_valid)
                else:
                    raise ValueError
            except:
                self.age_input.setStyleSheet(ss.input_invalid)
                valid = False
        # Gender
        if "select" in self.gender_combo.currentText().lower():
            valid = False
        # Activity
        if self.activity_combo.currentIndex() == 0:
            valid = False
        self.calc_btn.setEnabled(valid)
        return valid
    
    def trigger_autosave(self):
        self.validate_inputs()   # keep validation working
        self.autosave_timer.start()

    def _on_calculate(self):
        if not self.validate_inputs():
            return

        self.calculate_requested.emit({
            "gender": self.gender_combo.currentText(),
            "weight": self.weight_input.text(),
            "height": self.height_input.text(),
            "age": self.age_input.text(),
            "activity": self.activity_combo.currentIndex(),
        })

    def get_data(self):
        return {
            "gender": self.gender_combo.currentText(),
            "weight": self.weight_input.text(),
            "height": self.height_input.text(),
            "age": self.age_input.text(),
            "activity": self.activity_combo.currentIndex(),
        }
    
    def load_user_data(self):
        user = get_user_profile(Session.user_id)
        if not user:
            return

        try:
            _, age, gender, height, weight, *_ = user

            self.age_input.setText(str(age))
            self.height_input.setText(str(height))
            self.weight_input.setText(str(weight))

            if isinstance(gender, (int, float)):
                gender = "Male" if int(gender) == 1 else "Female"

            gender = str(gender).strip().capitalize()

            index = self.gender_combo.findText(gender, Qt.MatchFixedString)
            if index >= 0:
                self.gender_combo.setCurrentIndex(index)

            # Trigger validation after loading
            self.validate_inputs()

        except Exception as e:
            print("Load user error:", e)

    def auto_save(self):
        if not self.validate_inputs():
            return  # ❌ don't save invalid data

        try:
            age = int(self.age_input.text())
            height = float(self.height_input.text())
            weight = float(self.weight_input.text())
            gender = self.gender_combo.currentText()
            activity = self.activity_combo.currentIndex()

            # ===== CALCULATE =====
            if gender.lower() == "male":
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            else:
                bmr = 10 * weight + 6.25 * height - 5 * age - 161

            multipliers = [1.2, 1.375, 1.55, 1.725, 1.9]
            tdee = bmr * multipliers[activity - 1] if activity > 0 else bmr

            bmi = weight / ((height / 100) ** 2)

            # ===== SAVE TO DB =====
            from Database_sor import save_user_profile

            save_user_profile(
                Session.user_id,
                age,
                gender,
                height,
                weight,
                bmi,
                bmr,
                tdee
            )

            self.status_label.setText("Saved ✅")

        except Exception as e:
            print("Auto-save error:", e)


    
