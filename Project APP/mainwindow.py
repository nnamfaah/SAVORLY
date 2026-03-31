from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, QSize, QDate,  QObject, Property, QPropertyAnimation
from PySide6.QtGui import QIcon, QPixmap

import stylesheet as ss
from dashboard import DashboardPage
from weekly import WeeklySummaryPage
from session import Session
from Database_sor import user_has_health_data, save_meal_data, load_meal_data
from settings_page_input import SettingsPage
from result_page import ResultPage
from week_meals_window import MealPlannerPage
from food_database import FOOD_DATABASE
from daily_meals import DailyMealsSubPage
from support import SupportPage

def _logo_label(size: int = 48) -> QLabel:
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"background-color: {ss.dark_green};"
        f"border-radius: {size // 4}px;"
    )
    px = QPixmap("savorly.png")
    if not px.isNull():
        icon_size = int(size * 0.68)
        px = px.scaled(icon_size, icon_size,
                       Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl.setPixmap(px)
    else:
        lbl.setText("🍴")
    return lbl

nav_bar = [
    ("dashboard",   "Dashboard",        "dashboard.png"),
    ("weekly",      "Weekly Summary",   "weekly.png"),
    ("support",     "Support",          "support.png"),
    ("settings",    "Settings",         "setting.png"),]

class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 24, 16, 24)
        self._layout.setSpacing(4)
        self._build_logo()
        self._layout.addSpacing(28)
        self._build_nav()
        self._layout.addStretch()
        self._build_user_row()

    def _build_logo(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(_logo_label(size=48))
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        name = QLabel("Savorly");            name.setStyleSheet(ss.sidebar_app_name)
        sub  = QLabel("Meal Balancing App"); sub.setStyleSheet(ss.sidebar_app_subtitle)
        text_col.addWidget(name)
        text_col.addWidget(sub)
        row.addLayout(text_col)
        row.addStretch()
        self._layout.addLayout(row)

    def _build_nav(self):
        self._nav_buttons: dict[str, QPushButton] = {}
        for page_id, label, icon_file in nav_bar:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setFixedHeight(42)
            btn.setIconSize(QSize(20, 20))
            px = QPixmap(icon_file)
            if not px.isNull():
                btn.setIcon(QIcon(px))
            self._nav_buttons[page_id] = btn
            self._layout.addWidget(btn)

    def _build_user_row(self):
        row = QHBoxLayout()
        avatar = QLabel("👤")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(ss.sidebar_avatar)

        username = getattr(Session, "username", None) or "Guest"
        self.username_label = QLabel(username)
        self.username_label.setStyleSheet(ss.sidebar_username)

        row.addWidget(avatar)
        row.addWidget(self.username_label)
        row.addStretch()
        self._layout.addLayout(row)

        self.update_user()

    def set_active(self, page_id: str):
        for pid, btn in self._nav_buttons.items():
            btn.setChecked(pid == page_id)
            btn.setStyleSheet(ss.nav_btn(active=(pid == page_id)))

    def buttons(self) -> dict:
        return self._nav_buttons
    
    def update_user(self):
        username = getattr(Session, "username", None) or "Guest"
        self.username_label.setText(username)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Savorly Meal Balancing App")
        self.resize(1200, 780)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(ss.mainwindow)
        self._syncing = False
        self.meal_data = load_meal_data(Session.user_id) or {}
        from Database_sor import clear_all_meals
        clear_all_meals(Session.user_id)
        self.meal_data = {}
        self.result_page = ResultPage()

        root = QWidget()
        root.setStyleSheet(ss.page_bg)
        self.setCentralWidget(root)

        h = QHBoxLayout(root)
        h.setContentsMargins(0,0,0,0)
        h.setSpacing(0)

        self._sidebar = Sidebar()
        h.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(ss.page_bg)
        h.addWidget(self._stack)

        self.daily_page = DailyMealsSubPage()
        self.meal_planner = MealPlannerPage()
        self.weekly_page = WeeklySummaryPage()
        self.support_page = SupportPage()
        self.dashboard_page = DashboardPage()

        self._stack.addWidget(self.dashboard_page)
        self._stack.addWidget(self.daily_page)
        self._stack.addWidget(self.meal_planner)
        self._stack.addWidget(self.weekly_page)
        self._stack.addWidget(self.support_page)
       

        # DAILY → WEEKLY GRID
        self.daily_page.go_to_weekly_meal.connect(
            lambda: self._stack.setCurrentWidget(self.meal_planner)
        )
        # WEEKLY GRID → DAILY
        self.meal_planner.day_selected.connect(self.open_daily_page)

        # WEEKLY GRID → WEEKLY DETAIL
        self.meal_planner.jump_to_week_day.connect(self.open_weekly_detail)

        # WEEKLY DETAIL → BACK TO GRID (optional)
        self.weekly_page.go_back.connect(
            lambda: self._stack.setCurrentWidget(self.meal_planner)
        )
        # Weekly → Daily
        self.meal_planner.go_to_daily.connect(self.open_daily_page)

        # Emoji → Weekly Detail Page
        self.meal_planner.go_to_mood.connect(
            lambda: self._stack.setCurrentWidget(self.weekly_page)
        )
        
        self.meal_planner.meal_data_changed.connect(self.handle_meal_data_change)
        self.daily_page.meal_data_changed.connect(self.handle_meal_data_change)
        self.meal_planner.date_picked.connect(self.open_daily_page)
        self.dashboard_page.meal_added.connect(self.handle_dashboard_meal_added)

        # โหลด DB ครั้งเดียว แล้ว sync ทุก page
        self.meal_planner.meal_data = self.meal_data
        self.weekly_page._weekly_meal.meal_data = self.meal_data
        self.meal_planner.update_week()
        today = QDate.currentDate().toString("yyyy-MM-dd")
        self.daily_page.meal_data = self.meal_data
        self.daily_page._current_date = QDate.fromString(today, "yyyy-MM-dd")
        self.daily_page._refresh()

        self.settings_page = SettingsPage()
        self.settings_page.calculate_requested.connect(self.handle_calculation)
        self.result_page.data_confirmed.connect(self.save_results)
        self.result_page.cancelled.connect(lambda: self._stack.setCurrentWidget(self.settings_page))
        self.settings_page.tdee_updated.connect(self.dashboard_page.update_tdee)
        self.settings_page.tdee_updated.connect(self.daily_page.update_tdee)
        self._stack.addWidget(self.settings_page)
        self._stack.addWidget(self.result_page)

        for pid, btn in self._sidebar.buttons().items():
            btn.clicked.connect(lambda checked, p=pid: self._switch_page(p))

        self._switch_page("dashboard")

        self.refresh_user()
        if user_has_health_data(Session.user_id):
            self._switch_page("dashboard")
        else:
            self._switch_page("settings")  

    def _switch_page(self, page_id: str):
        page_map = {
        "dashboard": self.dashboard_page,
        "weekly": self.daily_page,
        "support": self.support_page, # support
        "settings": self.settings_page
        }

        page = page_map.get(page_id, self.dashboard_page)
        self._stack.setCurrentWidget(page)
        self._sidebar.set_active(page_id)

    def _placeholder(self, title: str, subtitle: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(ss.page_bg)
        v = QVBoxLayout(w)
        v.setContentsMargins(36, 32, 36, 32)
        t = QLabel(title);    t.setStyleSheet(ss.page_title)
        s = QLabel(subtitle); s.setStyleSheet(ss.page_subtitle )
        v.addWidget(t); v.addWidget(s); v.addStretch()
        return w
    
    def refresh_user(self):
        # Update username everywhere
        if hasattr(self, "_sidebar"):
            self._sidebar.update_user()
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.update_user()

    def handle_calculation(self, data):
        print("CALCULATE RECEIVED:", data)
        self.result_page.clear_results()
        self.result_page.update_data(data)
        self._stack.setCurrentWidget(self.result_page)

        self.result_page.play_entry_animation()

    def save_results(self, bmi, tdee):
        from Database_sor import save_user_profile, get_user_profile
        user_id = Session.user_id
        user = get_user_profile(user_id)
        if not user:
            return
        
        age, gender, height, weight, *_ = user
        if str(gender).lower() == "male":
            bmr = 10 * float(weight) + 6.25 * float(height) - 5 * int(age) + 5
        else:
            bmr = 10 * float(weight) + 6.25 * float(height) - 5 * int(age) - 161

        save_user_profile(
            user_id,
            age,
            gender,
            height,
            weight,
            bmi,
            bmr,
            tdee
        )
        print("Saved for user:", user_id)
        self.dashboard_page.update_tdee(tdee)
        self.daily_page.update_tdee(tdee)
        self._stack.setCurrentWidget(self.dashboard_page)

    def handle_meal_data_change(self, date, meals_for_day):
        if self._syncing:
            return
        self._syncing = True
        try:
            print(f"[DEBUG] handle_meal_data_change called: date={date}")

            self.meal_data[date] = meals_for_day

            self.meal_planner.meal_data = self.meal_data
            self.meal_planner.update_week()
            if hasattr(self.weekly_page, "set_meal_data"):
                self.weekly_page.set_meal_data(self.meal_data)

            self.daily_page.meal_data = self.meal_data

            if hasattr(self.weekly_page, "_daily_page"):
                wp_daily = self.weekly_page._daily_page
                wp_daily.meal_data = self.meal_data
                if hasattr(wp_daily, "_current_date"):
                    wp_date = wp_daily._current_date.toString("yyyy-MM-dd")
                    if wp_date == date:
                        wp_daily._refresh()

            today = QDate.currentDate().toString("yyyy-MM-dd")
            today_meals = self.meal_data.get(today, {})
            meal_profiles = []
            for food_list in today_meals.values():
                for food in food_list:
                    if isinstance(food, dict):
                        meal_profiles.append(food)
                    elif isinstance(food, str):
                        profile = FOOD_DATABASE.get(food, {})
                        meal_profiles.append({"profile": profile, "quantity": 1})

            total_calories = 0
            for item in meal_profiles:
                macros = item.get("macros") or item.get("profile") or {}
                qty = item.get("quantity", 1)
                total_calories += (macros.get("protein", 0)*4 + macros.get("carbs", 0)*4 + macros.get("fat", 0)*9) * qty

            from Database_sor import get_user_profile
            user = get_user_profile(Session.user_id)
            tdee = user[6] if user and len(user) > 6 else 2000

            self.dashboard_page.update_calorie_visual(total_calories, tdee)
            self.dashboard_page.update_from_meals(meal_profiles)
            self.dashboard_page.update_tdee(tdee)

            current = self.daily_page._current_date.toString("yyyy-MM-dd")
            if current == date:
                self.daily_page._refresh()

            save_meal_data(Session.user_id, date, meals_for_day)

        finally:
            self._syncing = False

    def handle_jump_to_week(self, date_str):
        self._stack.setCurrentWidget(self.weekly_page)
        self._sidebar.set_active("weekly")
        self.weekly_page.select_day(date_str)

    def open_daily_page(self, date_str):
        self._stack.setCurrentWidget(self.daily_page)

        # Ensure Daily page knows which date to show
        self.daily_page._current_date = QDate.fromString(date_str, "yyyy-MM-dd")

        # Set meals for that date and refresh UI
        self.daily_page._current_date = QDate.fromString(date_str, "yyyy-MM-dd")
        self.daily_page._refresh()


    def open_weekly_detail(self, date_str):
        self._stack.setCurrentWidget(self.weekly_page)
        self.weekly_page.load_day(
            date_str,
            self.meal_data.get(date_str, {})
        )

    def set_date(self, date_str):
        from PySide6.QtCore import QDate
        self._current_date = QDate.fromString(date_str, "yyyy-MM-dd")
    
    def open_weekly_page_from_daily(self):
        """Daily → Weekly Planner"""

        if self.meal_planner not in [self._stack.widget(i) for i in range(self._stack.count())]:
            self._stack.addWidget(self.meal_planner)

        self._stack.setCurrentWidget(self.meal_planner)
        self._sidebar.set_active("weekly")

        date_str = self.daily_page.get_current_date().toString("yyyy-MM-dd")
        self.meal_planner.select_day(date_str)

    def handle_dashboard_meal_added(self, date, food):
        import traceback
        traceback.print_stack(limit=5) 
        if self._syncing:
            return
        self._syncing = True
        try:
            meal_name = food.get("meal", "Lunch")
            self.meal_data.setdefault(date, {}).setdefault(meal_name, []).append(food)
            print(f"[DEBUG] {meal_name} now has {len(self.meal_data[date][meal_name])} items")

            self.meal_planner.meal_data = self.meal_data
            self.meal_planner.update_week()

            today = QDate.currentDate().toString("yyyy-MM-dd")
            if date == today:
                self.daily_page.meal_data = self.meal_data
                self.daily_page._refresh()

            save_meal_data(Session.user_id, date, self.meal_data[date])

        finally:
            self._syncing = False
