import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt

from styles import STYLESHEET
from sidebar import Sidebar
from settings_page import SettingsPage
from result_page import ResultPage


#  BMI / TDEE Logic

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    return weight_kg / (height_cm / 100) ** 2


def calculate_tdee(weight_kg: float, height_cm: float, age: int,
                   gender: str, activity_index: int) -> float:
    # Mifflin-St Jeor BMR
    if gender.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    multipliers = [1.2, 1.375, 1.55, 1.725, 1.9]
    multiplier = multipliers[activity_index - 1] if 1 <= activity_index <= 5 else 1.2
    return bmr * multiplier


# Main Window ─

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Savorly — Meal Balancing App")
        self.resize(1440, 900)
        self.setMinimumSize(900, 600)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.nav_clicked.connect(self._on_nav)
        root.addWidget(self.sidebar)

        # Stacked pages
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")
        root.addWidget(self.stack, 1)

        self.settings_page = SettingsPage()
        self.settings_page.calculate_requested.connect(self._on_calculate)
        self.stack.addWidget(self.settings_page)  # index 0

        self.result_page = ResultPage()
        self.result_page.cancelled.connect(self._on_cancel)
        self.result_page.confirmed.connect(self._on_confirm)
        self.stack.addWidget(self.result_page)    # index 1

        self.stack.setCurrentIndex(0)

    def _on_nav(self, key: str):
        self.sidebar.set_active(key)
        # Only Settings is implemented; others show a placeholder message
        if key == "settings":
            self.stack.setCurrentIndex(0)

    def _on_calculate(self, data: dict):
        errors = []

        gender = data["gender"]
        if gender in ("select the a gender.", ""):
            errors.append("Please select a gender.")

        try:
            weight = float(data["weight"])
        except ValueError:
            errors.append("Weight must be a number (kg).")
            weight = None

        try:
            height = float(data["height"])
        except ValueError:
            errors.append("Height must be a number (cm).")
            height = None

        try:
            age = int(data["age"])
        except ValueError:
            errors.append("Age must be a whole number.")
            age = None

        activity = data["activity"]
        if activity == 0:
            errors.append("Please select an activity level.")

        if errors:
            QMessageBox.warning(self, "Missing Information", "\n".join(errors))
            return

        bmi = calculate_bmi(weight, height)
        tdee = calculate_tdee(weight, height, age, gender, activity)

        self.result_page.set_results(bmi, tdee)
        self.stack.setCurrentIndex(1)

    def _on_cancel(self):
        self.result_page.clear_results()
        self.stack.setCurrentIndex(0)

    def _on_confirm(self):
        QMessageBox.information(
            self, "Saved",
            "Your BMI and TDEE have been saved successfully! ✅"
        )


# Entry Poin 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
