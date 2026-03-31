from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QPushButton, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import  Qt, QDate, Signal, QRectF,Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, Property, QObject
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QConicalGradient
import stylesheet as ss
import math

# ── Helpers ─────────────────────────────────────────────
def _card(radius: int, bg: str) -> QFrame:
    f = QFrame()
    f.setStyleSheet(f"QFrame {{ background:{bg}; border-radius:{radius}px; border: none; }}")
    return f

def _label(text: str, style: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(style)
    return lbl

# ── Donut Widget ───────────────────────────────────────
class DonutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0   # 0 → 1
        self._target = 0.0
        self.anim = QPropertyAnimation(self, b"progress")
        self.anim.setDuration(800)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(0)
        self.glow.setColor(QColor("#FFFFFF"))
        self.glow.setOffset(0)
        self.setGraphicsEffect(self.glow)

        self.glow_anim = QPropertyAnimation(self.glow, b"blurRadius")
        self.glow_anim.setDuration(600)
        self.glow_anim.setStartValue(0)
        self.glow_anim.setEndValue(25)
        self.glow_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.glow_fade = QPropertyAnimation(self.glow, b"blurRadius")
        self.glow_fade.setDuration(600)
        self.glow_fade.setStartValue(25)
        self.glow_fade.setEndValue(0)
        self.glow_fade.setEasingCurve(QEasingCurve.InOutCubic)

    def getProgress(self):
        return self._progress
    
    def setProgress(self, value):
        self._progress = value
        self.update()

    progress = Property(float, getProgress, setProgress)

    def set_value(self, percent):
        percent = max(0.0, min(1.0, percent))  # clamp

        self.anim.stop()
        self.anim.setStartValue(self._progress)
        self.anim.setEndValue(percent)
        self.anim.start()

        self.trigger_glow()

    def trigger_glow(self):
        self.glow_anim.start()

        # fade out after glow
        self.glow_anim.finished.connect(
            lambda: QTimer.singleShot(150, self.glow_fade.start)
        )

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(14, 14, 122, 122)
        # track
        p.setPen(QPen(QColor("#D8D2C5"), 14, Qt.SolidLine, Qt.FlatCap)) # Circle
        p.setBrush(Qt.NoBrush); p.drawEllipse(rect)
        p.setPen(QPen(QColor("#FFFFFF"), 14, Qt.SolidLine, Qt.FlatCap)) # Progress
        span_angle = int(-360 * self._progress * 16)
        p.drawArc(rect, 90 * 16, span_angle)
        p.setPen(QColor(ss.tdee))
        p.setFont(QFont("Inria Serif", 13, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, "TDEE"); p.end()

# ── Daily Meals Page ───────────────────────────────────
class DailyMealsSubPage(QWidget):
    go_to_weekly_meal = Signal()
    go_to_mood = Signal()
    meal_data_changed = Signal(str, dict)  # date_key, day_meals

    _MEALS = [
        ("Breakfast", "🌤️"),
        ("Lunch", "🍜"),
        ("Dinner", "🥗"),
        ("Night", "🌙"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ss.page_bg)
        self._current_date = QDate.currentDate()
        self.meal_data = {}
        self._tdee_target = 2000
        self._current_calories = 0

        # Scroll area
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

    # ── Header ───────────────────────────────────────────
    def _build_header(self):
        hdr = QVBoxLayout()
        hdr.setSpacing(4)
        hdr.addWidget(_label("Record of Daily Meals", ss.page_title))
        hdr.addWidget(_label("Track your nutrition and reach your wellness goals.", ss.page_subtitle))
        self._v.addLayout(hdr)

    # ── Date Navigation ──────────────────────────────────
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

    # ── Body ────────────────────────────────────────────
    def _build_body(self):
        body = QHBoxLayout()
        body.setSpacing(30)
        body.addWidget(self._build_macro_card(), 2)

        self._meal_col = QVBoxLayout()
        self._meal_col.setSpacing(15)
        body.addLayout(self._meal_col, 3)
        self._v.addLayout(body)

    # ── Macro Card ─────────────────────────────────────
    def _build_macro_card(self) -> QFrame:
        c = _card(ss.radius_xl, ss.light_green)
        v = QVBoxLayout(c)
        v.setContentsMargins(25, 30, 25, 30)
        v.setSpacing(15)

        v.addWidget(_label("Macro Balance", f"font-size:18px; color:{ss.text}; qproperty-alignment:AlignCenter; font-family: 'Inria Serif';"))

        self._donut = DonutWidget()
        self._donut.setFixedSize(140, 140)

        h_c = QHBoxLayout()
        h_c.addStretch()
        h_c.addWidget(self._donut)
        h_c.addStretch()
        v.addLayout(h_c)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {ss.text}; margin: 10px 0;")
        v.addWidget(sep)

        self._macro_labels: dict[str, QLabel] = {}
        for key in ("Protein", "Carbs", "Fats", "Vitamins", "Mineral"):
            row = QHBoxLayout()
            val_lbl = _label("0", f"font-size:14px; font-weight:700; color:{ss.text};")
            self._macro_labels[key] = val_lbl
            row.addWidget(_label(f"{key}:", f"font-size:14px; color:{ss.text};"))
            row.addStretch()
            row.addWidget(val_lbl)
            v.addLayout(row)

        v.addStretch()
        return c

    # ── Meal Row ───────────────────────────────────────
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

    # ── Refresh ─────────────────────────────────────────
    def _refresh(self):
        from food_database import FOOD_DATABASE

        self._date_lbl.setText(self._current_date.toString("dddd, d MMM"))

        while self._meal_col.count():
            item = self._meal_col.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        date_key = self._current_date.toString("yyyy-MM-dd")
        day_meals = self.meal_data.get(date_key, {})
        print(f"[DEBUG] daily _refresh: date_key={date_key}, day_meals={day_meals}, all_keys={list(self.meal_data.keys())}")

        grouped = {meal: [] for meal, _ in self._MEALS}
        macros = {"protein":0,"carbs":0,"fat":0,"vitamins":0,"minerals":0}

        for meal_type, foods in day_meals.items():
            for food in foods:
                if isinstance(food, dict):
                    name = food.get("name", "Unknown")
                    qty = food.get("quantity", 1)
                    grouped.setdefault(meal_type, []).append(name)
                    profile = food.get("macros") or food.get("profile") or {}
                elif isinstance(food, str):
                    name = food
                    qty = 1
                    grouped.setdefault(meal_type, []).append(name)
                    profile = FOOD_DATABASE.get(food, {})
                else:
                    continue

                macros["protein"]  += profile.get("protein", 0) * qty
                macros["carbs"]    += profile.get("carbs", 0) * qty
                macros["fat"]      += profile.get("fat", 0) * qty
                macros["vitamins"] += profile.get("vitamins", 0) * qty
                macros["minerals"] += profile.get("minerals", profile.get("mineral",0)) * qty

        # Build meal rows
        for meal_name, icon in self._MEALS:
            foods_list = grouped.get(meal_name, [])
            foods_text = ", ".join(foods_list) if foods_list else ""
            self._meal_col.addWidget(self._build_meal_row(meal_name, icon, foods_text))

        # Update macros
        key_map = {"Protein":"protein","Carbs":"carbs","Fats":"fat","Vitamins":"vitamins","Mineral":"minerals"}
        for key, lbl in self._macro_labels.items():
            real_key = key_map.get(key, key.lower())
            lbl.setText(str(round(macros.get(real_key,0),2)))

        # Update donut
        total_calories = macros["protein"]*4 + macros["carbs"]*4 + macros["fat"]*9
        self.update_calorie_visual(total_calories, self._tdee_target)

    # ── Date Navigation ─────────────────────────────────
    def _go_prev(self):
        self._current_date = self._current_date.addDays(-1)
        self._refresh()

    def _go_next(self):
        self._current_date = self._current_date.addDays(1)
        self._refresh()

    # ── Meal Data ──────────────────────────────────────
    def sync_from_main(self, date_str, meal_data):
        print(f"[DEBUG] daily sync_from_main: date={date_str}")
        self._current_date = QDate.fromString(date_str, "yyyy-MM-dd")
        if isinstance(meal_data, dict) and meal_data:
            # ถ้า key แรกเป็น dict แสดงว่าส่ง meal_data ทั้งก้อน (หลายวัน)
            first_val = next(iter(meal_data.values()), None)
            if isinstance(first_val, dict):
                self.meal_data = meal_data          # รับทั้งก้อน
            else:
                self.meal_data[date_str] = meal_data  # รับแค่วันเดียว
        self._refresh()

    def set_date(self, date_str):
        print(f"[DEBUG] daily set_date: date={date_str}")
        self._current_date = QDate.fromString(date_str, "yyyy-MM-dd")
        self._refresh()

    def add_food_to_meal(self, meal_type: str, food_item):
        date_key = self._current_date.toString("yyyy-MM-dd")
        if date_key not in self.meal_data:
            self.meal_data[date_key] = {}
        if meal_type not in self.meal_data[date_key]:
            self.meal_data[date_key][meal_type] = []
        self.meal_data[date_key][meal_type].append(food_item)

        # Emit signal so parent can save/update
        self.meal_data_changed.emit(date_key, self.meal_data[date_key])

        self._refresh()

    def update_tdee(self, tdee_value):
        self._tdee_target = tdee_value
        # recalc calories
        protein = float(self._macro_labels["Protein"].text())
        carbs   = float(self._macro_labels["Carbs"].text())
        fats    = float(self._macro_labels["Fats"].text())
        total_calories = protein*4 + carbs*4 + fats*9
        progress = min(max(total_calories / self._tdee_target if self._tdee_target>0 else 0, 0.0), 1.0)
        self._donut.setProgress(progress)

    def update_calorie_visual(self, total_calories, tdee):
        self._current_calories = total_calories
        self._tdee_target = tdee
        progress = min(max(total_calories / tdee if tdee > 0 else 0, 0.0), 1.0)
        self._donut.setProgress(progress)

    def set_meals(self, meals_for_day: dict, date_str: str = None):
        """Update the page for the given day."""
        from food_database import FOOD_DATABASE
        from PySide6.QtCore import QDate

        if date_str:
            self._current_date = QDate.fromString(date_str, "yyyy-MM-dd")

        key = self._current_date.toString("yyyy-MM-dd")
        if meals_for_day:
            self.meal_data[key] = meals_for_day
        elif key in self.meal_data:
            del self.meal_data[key]
        # --- Compute macros ---
        macros = {"protein":0,"carbs":0,"fat":0,"vitamins":0,"minerals":0}
        grouped = {meal: [] for meal, _ in getattr(self, "_MEALS", [])}

        for meal_type, foods in (meals_for_day or {}).items():
            for food in foods:
                if isinstance(food, dict):
                    name = food.get("name", "Unknown")
                    qty = food.get("quantity", 1)
                    grouped.setdefault(meal_type, []).append(name)
                    profile = food.get("macros") or food.get("profile") or {}
                elif isinstance(food, str):
                    name = food
                    qty = 1
                    grouped.setdefault(meal_type, []).append(name)
                    profile = FOOD_DATABASE.get(food, {})
                else:
                    continue

                macros["protein"]  += profile.get("protein",0)*qty
                macros["carbs"]    += profile.get("carbs",0)*qty
                macros["fat"]      += profile.get("fat",0)*qty
                macros["vitamins"] += profile.get("vitamins",0)*qty
                macros["minerals"] += profile.get("minerals", profile.get("mineral",0))*qty

        # --- Update meal rows in UI ---
        if hasattr(self, "_meal_col"):
            while self._meal_col.count():
                item = self._meal_col.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            for meal_name, icon in getattr(self, "_MEALS", []):
                foods_list = grouped.get(meal_name, [])
                foods_text = ", ".join(foods_list) if foods_list else ""
                self._meal_col.addWidget(self._build_meal_row(meal_name, icon, foods_text))

        # --- Update macro labels ---
        key_map = {"Protein":"protein","Carbs":"carbs","Fats":"fat","Vitamins":"vitamins","Mineral":"minerals"}
        for key, lbl in getattr(self, "_macro_labels", {}).items():
            real_key = key_map.get(key, key.lower())
            lbl.setText(str(round(macros.get(real_key,0),2)))

        # --- Update TDEE Donut ---
        total_calories = macros["protein"]*4 + macros["carbs"]*4 + macros["fat"]*9
        tdee = getattr(self, "_tdee_target", 2000)  # fallback to 2000 if not set
        if hasattr(self, "update_calorie_visual"):
            self.update_calorie_visual(total_calories, tdee)
