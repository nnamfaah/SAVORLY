import sys
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget,
)
import stylesheet as ss

from daily_meals import DailyMealsSubPage
from weekly_mood import WeeklyMoodSubPage, MOOD_DATA
from week_meals_window import MealPlannerPage


# ── WeeklySummaryPage  (used by mainwindow.py) ────────────────────────────
class WeeklySummaryPage(QWidget):
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