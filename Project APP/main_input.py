import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt

import stylesheet as ss
from sidebar_input import Sidebar
from settings_page_input import SettingsPage
from result_page import ResultPage
from mainwindow  import MainWindow
from session import Session
from Database_sor import save_user_profile
from dashboard import DashboardPage


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
    multiplier = multipliers[activity_index] if 1 <= activity_index <= 5 else 1.2
    return bmr * multiplier


# Main Window ─

class MainWindow_input(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Savorly — Meal Balancing App")
        self.resize(1200, 700)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(ss.mainwindow)
        self.last_data = None

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
        self.result_page.data_confirmed.connect(self.update_dashboard)
        self.stack.addWidget(self.result_page)    # index 1

        self.dashboard_page = DashboardPage()
        self.stack.addWidget(self.dashboard_page)

        self.stack.setCurrentIndex(0)

    def update_dashboard(self, bmi, tdee):
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.update_data(bmi, tdee)

    def _on_nav(self, key: str):
        self.sidebar.set_active(key)
        # Only Settings is implemented; others show a placeholder message
        if key == "settings":
            self.stack.setCurrentIndex(0)

    def _on_calculate(self, data: dict):
        errors = []
        self.settings_page.auto_save()

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
        if activity < 0:
            errors.append("Please select an activity level.")

        if errors:
            QMessageBox.warning(self, "Missing Information", "\n".join(errors))
            return

        bmi = calculate_bmi(weight, height)
        tdee = calculate_tdee(weight, height, age, gender, activity)

        self.last_data = data

        self.result_page.set_results(bmi, tdee)
        self.stack.setCurrentIndex(1)

    def _on_cancel(self):
        self.result_page.clear_results()
        self.stack.setCurrentIndex(0)

    def _on_confirm(self):
        if self.result_page.bmi is None:
            QMessageBox.warning(self, "Error", "No result")
            return

        data = self.last_data

        age = int(data["age"])
        gender = data["gender"]
        height = float(data["height"])
        weight = float(data["weight"])

        if gender.lower() == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        save_user_profile(
            Session.user_id,
            age,
            gender,
            height,
            weight,
            self.result_page.bmi,
            bmr,
            self.result_page.tdee
        )

        self.result_page.data_confirmed.emit(
            self.result_page.bmi,
            self.result_page.tdee
        )

        QMessageBox.information(self, "Saved", "Saved successfully ✅")

        self.stack.setCurrentIndex(0)

# Entry Poin 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(ss.app_global)
    window = MainWindow_input()
    window.show()
    sys.exit(app.exec())


