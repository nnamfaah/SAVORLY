from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QPushButton, QFrame,)
from PySide6.QtCore import Qt, QDate, Signal
import stylesheet as ss

def _card(radius: int, bg: str) -> QFrame:
    f = QFrame()
    f.setStyleSheet(f"QFrame {{ background:{bg}; border-radius:{radius}px; border: none; }}")
    return f

def _label(text: str, style: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(style)
    return lbl

class DailyMealsSubPage(QWidget):
    """Record of Daily Meals sub-page cleaned up for SAVORLY theme."""
    go_to_weekly_meal = Signal()
    go_to_mood        = Signal()

    _SAMPLE: dict = {}  # {QDate: {"MealName": [foods], "macros": {...}}}

    _MEALS = [
        ("Breakfast", "🌤️"),
        ("Lunch",     "🍜"),
        ("Dinner",    "🥗"),
        ("Night",     "🌙"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ss.page_bg)
        self._current_date = QDate.currentDate()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(ss.scroll_transparent)

        self._inner = QWidget()
        self._inner.setStyleSheet(ss.inner_transparent)
        self._v = QVBoxLayout(self._inner)
        self._v.setContentsMargins(40, 30, 40, 40)
        self._v.setSpacing(25)

        self._build_header()
        self._build_date_nav()
        self._build_body()
        self._v.addStretch()

        scroll.setWidget(self._inner)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        self._refresh()

    def _build_header(self):
        hdr = QVBoxLayout()
        hdr.setSpacing(4)
        hdr.addWidget(_label("Record of Daily Meals", ss.page_title))
        hdr.addWidget(_label("Track your nutrition and reach your wellness goals.", ss.page_subtitle))
        self._v.addLayout(hdr)

    def _build_date_nav(self):
        row = QHBoxLayout()
        row.addStretch()

        nav_frame = QFrame()
        nav_frame.setStyleSheet(f"background: {ss.white}; border-radius: {ss.radius_md}px; border: none;") 
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(8, 4, 8, 4)

        self._btn_prev = QPushButton("<")
        self._btn_next = QPushButton(">")
        
        cal_btn = QPushButton("📅")
        cal_btn.setFixedSize(30, 30)
        cal_btn.setCursor(Qt.PointingHandCursor)
        cal_btn.setStyleSheet("border: none; font-size: 16px;")
        cal_btn.clicked.connect(self.go_to_weekly_meal.emit)

        self._date_lbl = QLabel()
        self._date_lbl.setStyleSheet(f"font-size:14px; font-weight:600; color:{ss.text}; padding: 0 10px;")

        for b in (self._btn_prev, self._btn_next):
            b.setFixedSize(30, 30)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"QPushButton {{ border: none; font-size: 20px; color: {ss.text_muted}; }} QPushButton:hover {{ color: {ss.text}; }}")

        self._btn_prev.clicked.connect(self._go_prev)
        self._btn_next.clicked.connect(self._go_next)

        nav_layout.addWidget(self._btn_prev)
        nav_layout.addWidget(cal_btn)
        nav_layout.addWidget(self._date_lbl)
        nav_layout.addWidget(self._btn_next)
        
        row.addWidget(nav_frame)
        self._v.addLayout(row)

    def _build_body(self):
        body = QHBoxLayout()
        body.setSpacing(30)
        body.addWidget(self._build_macro_card(), 2)
        
        self._meal_col = QVBoxLayout()
        self._meal_col.setSpacing(15)
        body.addLayout(self._meal_col, 3)
        self._v.addLayout(body)

    def _build_macro_card(self) -> QFrame:
        c = _card(ss.radius_xl, ss.light_green)
        v = QVBoxLayout(c)
        v.setContentsMargins(25, 30, 25, 30)
        v.setSpacing(15)

        v.addWidget(_label("Macro Balance",
                           f"font-size:18px; color:{ss.text}; qproperty-alignment:AlignCenter; font-family: 'Inria Serif';"))

        self._donut = QLabel("TDEE")
        self._donut.setFixedSize(140, 140)
        self._donut.setAlignment(Qt.AlignCenter)

        progress_percent = 25 
        self._donut.setStyleSheet(
            f"background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, "
            f"stop:0.6 {ss.light_green}, "
            f"stop:0.601 rgba(255,255,255,0.3), "
            f"stop:{0.6 + (0.4 * progress_percent/100)} {ss.white}, "
            f"stop:{0.601 + (0.4 * progress_percent/100)} rgba(255,255,255,0.3)); "
            f"border-radius: 70px; font-size:18px; font-weight:700; color:{ss.text};"
        )
        
        h_c = QHBoxLayout()
        h_c.addStretch(); h_c.addWidget(self._donut); h_c.addStretch()
        v.addLayout(h_c)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {ss.text}; margin: 10px 0;")
        v.addWidget(sep)

        self._macro_labels: dict[str, QLabel] = {}
        for key in ("Protein", "Carbs", "Fats", "Mineral", "Fiber"):
            row = QHBoxLayout()
            val_lbl = _label("0", f"font-size:14px; font-weight:700; color:{ss.text};")
            self._macro_labels[key] = val_lbl
            row.addWidget(_label(f"{key}:", f"font-size:14px; color:{ss.text};"))
            row.addStretch()
            row.addWidget(val_lbl)
            v.addLayout(row)

        v.addStretch()
        return c

    def _build_meal_row(self, name: str, icon: str, foods: str) -> QFrame:
        c = _card(ss.radius_lg, ss.light_green)
        h = QHBoxLayout(c)
        h.setContentsMargins(15, 15, 15, 15)
        h.setSpacing(15)

        ico_bg = QFrame()
        ico_bg.setFixedSize(45, 45)
        ico_bg.setStyleSheet(f"background: rgba(255,255,255,0.4); border-radius: {ss.radius_md}px;")
        ico_lay = QVBoxLayout(ico_bg)
        ico_lay.setContentsMargins(0,0,0,0)
        ico = _label(icon, "font-size: 20px; qproperty-alignment: AlignCenter;")
        ico_lay.addWidget(ico)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(_label(name,  f"font-size:15px; font-weight:700; color:{ss.text};"))
        col.addWidget(_label(foods, f"font-size:13px; color: {ss.text_muted};"))

        h.addWidget(ico_bg)
        h.addLayout(col)
        h.addStretch()
        return c

    def _refresh(self):
        self._date_lbl.setText(self._current_date.toString("dddd, d MMM"))

        while self._meal_col.count():
            item = self._meal_col.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        current_data = self._SAMPLE.get(self._current_date)
        if not current_data:
            current_data = {
                "macros": {"Protein": 0, "Carbs": 0, "Fats": 0, "Mineral": 0, "Fiber": 0},
                "meals": {meal: [] for meal, _ in self._MEALS}
            }

        for meal_name, icon in self._MEALS:
            foods_list = current_data["meals"].get(meal_name, [])
            foods_text = ", ".join(foods_list) if foods_list else ""
            self._meal_col.addWidget(
                self._build_meal_row(meal_name, icon, foods_text)
            )

        macros = current_data.get("macros", {})
        for key, lbl in self._macro_labels.items():
            lbl.setText(str(macros.get(key, 0)))

        progress_percent = 0 
        self._donut.setStyleSheet(
            f"background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, "
            f"stop:0.6 {ss.light_green}, "                                
            f"stop:0.601 rgba(255,255,255,0.3), "                       
            f"stop:{0.6 + (0.4 * progress_percent/100)} {ss.white}, "     
            f"stop:{0.601 + (0.4 * progress_percent/100)} rgba(255,255,255,0.3)); "
            f"border-radius: 70px; font-size:18px; font-weight:700; color:{ss.text};"
        )

    def _go_prev(self):
        self._current_date = self._current_date.addDays(-1)
        self._refresh()

    def _go_next(self):
        self._current_date = self._current_date.addDays(1)
        self._refresh()

    def get_current_date(self) -> QDate:
        return self._current_date

    def set_date(self, d: QDate):
        self._current_date = d
        self._refresh()