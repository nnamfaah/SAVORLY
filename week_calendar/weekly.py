import sys
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget,
)
from PySide6.QtCore import Signal
import stylesheet as ss

from daily_meals import DailyMealsSubPage
from weekly_mood import WeeklyMoodSubPage, MOOD_DATA
from week_meals_window import MealPlannerPage


# ── WeeklySummaryPage  (used by mainwindow.py) ────────────────────────────
class WeeklySummaryPage(QWidget):
    meal_data_changed = Signal(str, dict)
    go_back = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ss.page_bg)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sub-pages
        self._stack       = QStackedWidget()
        self._daily_page  = DailyMealsSubPage()
        self._mood_page   = WeeklyMoodSubPage()
        self._weekly_meal = MealPlannerPage()

        self._stack.addWidget(self._daily_page)    # 0
        self._stack.addWidget(self._mood_page)     # 1
        self._stack.addWidget(self._weekly_meal)   # 2
        root.addWidget(self._stack)

        self._daily_page.meal_data_changed.connect(self._sync_to_weekly)
        self._weekly_meal.meal_data_changed.connect(self._sync_to_daily)

        # Sync mood week when daily date changes
        self._daily_page._btn_prev.clicked.connect(self._sync_mood_from_daily)
        self._daily_page._btn_next.clicked.connect(self._sync_mood_from_daily)

        # ── Navigation signals ──────────────────────────────────────────
        # daily_meal  → 📅  → Weekly Meals
        self._daily_page.go_to_weekly_meal.connect(lambda: self._show(2))
        # daily_meal  → 😊  → Weekly Mood
        self._daily_page.go_to_mood.connect(lambda: self._show(1))

        # weekly_mood → 📅  → Weekly Meals
        self._mood_page.go_to_weekly_meal.connect(lambda: self._show(2))

        # weekly_meal → emoji → Weekly Mood
        self._weekly_meal.go_to_mood.connect(lambda: self._show(1))
        # weekly_meal → date → Daily Meals and set date
        self._weekly_meal.go_to_daily.connect(self._go_to_daily_with_date)

        self._show(0)  # start with Daily Meals

    def _show(self, idx: int):
        self._stack.setCurrentIndex(idx)

    def _go_to_daily_with_date(self, qdate):
        self._daily_page.set_date(qdate)
        self._show(0)

    def _sync_mood_from_daily(self):
        d = self._daily_page.get_current_date()
        dow = d.dayOfWeek()
        week_start = d.addDays(-(dow - 1))
        for i, (start, *_) in enumerate(MOOD_DATA):
            if start <= week_start:
                self._mood_page._idx = i
                self._mood_page._refresh()
                break

    def _sync_to_weekly(self, date_key, meals_for_day):
        self._weekly_meal.meal_data[date_key] = meals_for_day
        self._weekly_meal.update_week()
        self.meal_data_changed.emit(date_key, meals_for_day)

    def _sync_to_daily(self, date_key, meals_for_day):
        self._daily_page.meal_data[date_key] = meals_for_day
        if self._daily_page.get_current_date().toString("yyyy-MM-dd") == date_key:
            self._daily_page.refresh_ui()
        self.meal_data_changed.emit(date_key, meals_for_day)

    def _emit_weekly_change(self, date_str, meals_for_day):
        """
        Called by MealPlannerPage whenever weekly meals change.
        Re-emits to MainWindow.
        """
        self.meal_data_changed.emit(date_str, meals_for_day)

    def update_from_meal_data(self, meal_data):
        """
        Called from MainWindow when daily meals change, so weekly view is updated.
        """
        self._weekly_meal.meal_data = meal_data
        self._weekly_meal.update_week()

    def select_day(self, date_str):
        """
        Jump to a specific date in the weekly view.
        """
        self._weekly_meal.select_date(date_str)
        self._show(2)

    def set_meal_data(self, meal_data):
        self.meal_data = meal_data

    def load_day(self, date_str, meals):
        """Load selected day data"""
        self.current_date = date_str
        if hasattr(self, "_weekly_meal"):
            self._weekly_meal.select_day(date_str)
        self.current_meals = meals

    def select_day(self, date_str):
        """Alias for compatibility"""
        self.load_day(date_str, [])