from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QScrollArea,
    QSizePolicy, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QTimer, QRectF, Signal, QPropertyAnimation, QEasingCurve, QRect, Property, QObject
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QPixmap, QIcon

import stylesheet as ss
from session import Session
from Analyzer import FoodAnalyzer
from Input_section_food import InputProcessor 
from Database_sor import get_user_by_id
from food_database import FOOD_DATABASE

slots = ["Breakfast", "Lunch", "Dinner", "Late-night"]

def _slot_from_time(dt=None) -> str:
    h = (dt or datetime.now()).hour
    if  5 <= h < 10: return "Breakfast"
    if 10 <= h < 16: return "Lunch"
    if 16 <= h < 21: return "Dinner"
    return "Late-night"

# ── Tips (single sentence output) ────────────────────────────────────────────
_food_tips = {
    "egg":      ("protein",  "eggs"),
    "chicken":  ("protein",  "chicken"),
    "yogurt":   ("protein",  "yogurt"),
    "fish":     ("protein",  "fish"),
    "tofu":     ("protein",  "tofu"),
    "rice":     ("carbs",    "rice"),
    "bread":    ("carbs",    "bread"),
    "oat":      ("carbs",    "oats"),
    "pasta":    ("carbs",    "pasta"),
    "banana":   ("carbs",    "banana"),
    "avocado":  ("fat",     "avocado"),
    "almond":   ("fat",     "almonds"),
    "olive":    ("fat",     "olive oil"),
    "milk":     ("fat",     "milk"),
    "cheese":   ("fat",     "cheese"),
    "spinach":  ("minerals", "spinach"),
    "broccoli": ("minerals", "broccoli"),
    "apple":    ("vitamins",    "apple"),
    "carrot":   ("vitamins",    "carrots"),
    "bean":     ("vitamins",    "beans"),
}

def _tip_sentence(foods: list) -> str:
    if not foods:
        return "Start adding meals to get personalised nutrition tips."
    found = {}
    for food in foods:
        fl = food.lower().strip()
        for kw, (cat, name) in _food_tips.items():
            if kw in fl and cat not in found:
                found[cat] = name
    has_protein  = "protein"  in found
    has_carbs    = "carbs"    in found
    has_fats     = "fat"     in found
    has_minerals = "minerals" in found
    has_vitamins    = "vitamins"    in found

    parts = []
    if has_protein and has_carbs and has_fats:
        parts.append("Great balance of protein, carbs, and fat")
    elif has_protein and has_carbs:
        parts.append(f"Good combo of {found['protein']} and {found['carbs']}")
    elif has_protein:
        parts.append(f"{found['protein'].capitalize()} gives you solid protein")
    elif has_carbs:
        parts.append(f"{found['carbs'].capitalize()} provides your carbs")
    else:
        parts.append("Looks like a light meal")

    missing = []
    if not has_protein: missing.append("a protein source like eggs or chicken")
    if not has_fats:    missing.append("healthy fat like avocado or almonds")
    if not has_vitamins and not has_minerals: missing.append("some vegetables for minerals and vitamins")

    if missing:
        parts.append("consider adding " + " and ".join(missing[:2]))
    if has_minerals:
        parts.append(f"{found['minerals'].capitalize()} adds great minerals to your meal")
    if has_vitamins:
        parts.append(f"{found['vitamins'].capitalize()} boosts your vitamins intake")

    sentence = " — ".join(parts[:2])
    if len(parts) > 2:
        sentence += f". {parts[2].capitalize()}."
    else:
        sentence += "."
    return sentence
    
# Shadow helper
def _shadow(w, radius=12, offset=3, alpha=18):
    eff = QGraphicsDropShadowEffect(w)
    eff.setBlurRadius(radius); eff.setOffset(0, offset)
    eff.setColor(QColor(0, 0, 0, alpha)); w.setGraphicsEffect(eff)

# TDEE
class _Donut(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedSize(150, 150)
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

# Macro tile
def _macro_tile(label, color):
    w = QWidget(); w.setMinimumWidth(110); w.setFixedHeight(90)
    w.setStyleSheet(f"background:{ss.white}; border-radius:{ss.radius_lg}px; border:1px solid rgba(0,0,0,0.06);")
    v = QVBoxLayout(w); v.setContentsMargins(14,12,14,12); v.setSpacing(6)
    row = QHBoxLayout(); row.setSpacing(6)
    dot = QLabel(); dot.setFixedSize(8,8); dot.setStyleSheet(f"background:{color}; border-radius:4px;")
    lbl = QLabel(label.upper()); lbl.setStyleSheet(f"font-size:9px; font-weight:700; color:{ss.text_muted}; letter-spacing:0.5px;")
    row.addWidget(dot,0,Qt.AlignVCenter); row.addWidget(lbl,0,Qt.AlignVCenter); row.addStretch()
    v.addLayout(row)

     # Value label 
    value_lbl = QLabel("0")
    value_lbl.setStyleSheet(
        f"font-size:16px; font-weight:700; color:{color};"
    )
    v.addWidget(value_lbl)

    # Bar Progess
    bar_bg = QFrame()
    bar_bg.setFixedHeight(6)
    bar_bg.setStyleSheet("background:rgba(0,0,0,0.08); border-radius:3px;")
    bar_bg.setMinimumWidth(80)
    bar_bg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    bar_layout = QVBoxLayout(bar_bg)
    bar_layout.setContentsMargins(0,0,0,0)

    bar_fill = QFrame()
    bar_fill.setFixedHeight(6)
    bar_fill.setMaximumWidth(0)   # start empty
    bar_fill.setStyleSheet(f"background:{color}; border-radius:3px;")

    bar_layout.addWidget(bar_fill)
    v.addWidget(bar_bg)
    v.addStretch()

    anim = QPropertyAnimation(bar_fill, b"maximumWidth")
    anim.setDuration(400)
    anim.setEasingCurve(QEasingCurve.OutCubic)

    return w, value_lbl, bar_fill, anim

class AnimatedValue(QObject):
    def __init__(self, value=0):
        super().__init__()
        self._value = value

    def getValue(self):
        return self._value

    def setValue(self, val):
        self._value = val
        self.on_change(val)

    value = Property(float, getValue, setValue)

    def on_change(self, val):
        pass

# Meal Timeline
class _MealTimeline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setStyleSheet("background:transparent;")
        self._dots = {}; self._labels = {}
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(8)
        row = QHBoxLayout(); row.setSpacing(0)
        for i, slot in enumerate(slots):
            col = QVBoxLayout(); col.setSpacing(6); col.setAlignment(Qt.AlignHCenter)
            dot = QLabel(); dot.setFixedSize(18,18); dot.setAlignment(Qt.AlignCenter)
            self._dots[slot] = dot; col.addWidget(dot, 0, Qt.AlignHCenter)
            name = QLabel(slot.upper()); name.setAlignment(Qt.AlignHCenter)
            name.setStyleSheet(f"font-size:9px; font-weight:500; color:{ss.text_muted}; background:transparent; letter-spacing:0.5px;")
            self._labels[slot] = name; col.addWidget(name)
            row.addLayout(col)
            if i < len(slots)-1:
                line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFixedHeight(1)
                line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                line.setStyleSheet(f"background:rgba(0,0,0,0.12); border:none;")
                wrap = QVBoxLayout(); wrap.setContentsMargins(0,0,0,0)
                wrap.addSpacing(9); wrap.addWidget(line); wrap.addStretch()
                row.addLayout(wrap)
        lay.addLayout(row)
        self.set_active(_slot_from_time())

    def set_active(self, active_slot):
        for slot in slots:
            active = slot == active_slot
            if active:
                self._dots[slot].setStyleSheet(
                    f"background:{ss.green}; border-radius:9px; border:2px solid {ss.dark_green};")
                self._labels[slot].setStyleSheet(
                    f"font-size:9px; font-weight:700; color:{ss.dark_green}; background:transparent; letter-spacing:0.5px;")
            else:
                self._dots[slot].setStyleSheet(
                    f"background:#C8C4BC; border-radius:9px; border:2px solid transparent;")
                self._labels[slot].setStyleSheet(
                    f"font-size:9px; font-weight:400; color:{ss.text_muted}; background:transparent; letter-spacing:0.5px;")

# Recommendation Panel
class _RecPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        v = QVBoxLayout(self); v.setContentsMargins(20, 18, 20, 18); v.setSpacing(10)
        title = QLabel("Recommendation"); title.setStyleSheet(ss.section)
        v.addWidget(title)
        self._tip_lbl = QLabel()
        self._tip_lbl.setWordWrap(True)
        self._tip_lbl.setStyleSheet(
            f"font-size:13px; color:{ss.text}; background:transparent; line-height:1.6;")
        self._tip_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        v.addWidget(self._tip_lbl)
        self._set_text([])

    def update_tips(self, analysis_results):
        foods = [food["name"] for food in analysis_results]
        self._set_text(foods)

    def _set_text(self, foods):
        self._tip_lbl.setText(_tip_sentence(foods))

# Add Meals Panel
class _AddMealsPanel(QWidget):
    slot_changed  = Signal(str)
    foods_changed = Signal(list)
    meal_added    = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._current_slot = _slot_from_time()
        self.analyzer = FoodAnalyzer()
        self.input_processor = InputProcessor()
        self._user_override = True
        self._tab_btns = {}; self._foods = []
        self._has_added_once = False

        v = QVBoxLayout(self); v.setContentsMargins(20,18,20,18); v.setSpacing(12)

        # Title
        title = QLabel("Add Meals")
        title.setStyleSheet(ss.section); v.addWidget(title)

        # Detected meal label (auto time)
        self._detect_label = QLabel()
        self._detect_label.setStyleSheet(ss.label); v.addWidget(self._detect_label)

        # Input row
        inp_row = QHBoxLayout(); inp_row.setSpacing(10)
        self._inp = QLineEdit()
        self._inp.setPlaceholderText("Add to your meals.")
        self._inp.setStyleSheet(ss.line_edit)
        self._inp.returnPressed.connect(self._add_foods)
        inp_row.addWidget(self._inp)
        add_btn = QPushButton("Add"); add_btn.setFixedHeight(42); add_btn.setFixedWidth(72)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(ss.btn_primary(padding="8px 16px"))
        add_btn.clicked.connect(self._add_foods)
        inp_row.addWidget(add_btn); v.addLayout(inp_row)

        # Food chips area
        self._chips_widget = QWidget(); self._chips_widget.setStyleSheet("background:transparent;")
        self._chips_layout = QVBoxLayout(self._chips_widget)
        self._chips_layout.setContentsMargins(0,0,0,0); self._chips_layout.setSpacing(4)
        food_scroll = QScrollArea(); food_scroll.setWidgetResizable(True); food_scroll.setFixedHeight(80)
        food_scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")
        food_scroll.setWidget(self._chips_widget)
        food_scroll.setVisible(False); self._food_scroll = food_scroll
        v.addWidget(food_scroll)

        self._apply(self._current_slot, auto=True)
        self._timer = QTimer(self); self._timer.timeout.connect(self._tick); self._timer.start(30_000)

    def _add_foods(self):
        text = self._inp.text().strip()
        if not text:
            return
        
        processed = self.input_processor.process(text)
        analysis_results = self.analyzer.analyze(processed.food_text)

        current_slot = self._current_slot

        from datetime import datetime
        date_key = datetime.now().strftime("%Y-%m-%d")

        new_foods = []

        for food in analysis_results:
            name = food.get("name", "Unknown")
            portion_name = food.get("portion_name", "medium")
            quantity = food.get("quantity", 1)

            raw_macros = food.get("macros", {}) or {}
            macros = {
                "protein": int(raw_macros.get("protein", 0)),
                "carbs": int(raw_macros.get("carbs", 0)),
                "fat": int(raw_macros.get("fat", 0)),
                "vitamins": int(raw_macros.get("vitamins", 0)),
                "minerals": int(raw_macros.get("minerals", raw_macros.get("mineral", 0)))
            }

            normalized_food = {
                "name": name,
                "macros": macros,
                "quantity": int(quantity),
                "meal": current_slot,   
                "date": date_key             
            }

            display_text = f"{name} • {portion_name} x{quantity}"

            self._foods.append(normalized_food)
            self._add_chip(display_text, normalized_food)
        
        self._foods.extend(new_foods)

        self._inp.clear()
        self._food_scroll.setVisible(True)

        if not self._has_added_once:
            self._has_added_once = True
            self.meal_added.emit()

        self.foods_changed.emit(self._foods)

    def _add_chip(self, text, food_name):
        row_w = QWidget()
        row_w.setStyleSheet(f"background:rgba(255,255,255,0.7); border-radius:{ss.radius_sm}px;")
        row = QHBoxLayout(row_w); row.setContentsMargins(10,5,6,5); row.setSpacing(8)
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size:12px; color:{ss.text}; background:transparent;")
        row.addWidget(lbl); row.addStretch()
        del_btn = QPushButton("x"); del_btn.setFixedSize(18,18); del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(
            f"QPushButton{{border:none; border-radius:9px; font-size:12px; font-weight:700; color:{ss.text_muted}; background:transparent;}} QPushButton:hover{{color:#c00;}}"
        )
        del_btn.clicked.connect(lambda _, f=food_name, w=row_w: self._remove_food(f, w))
        row.addWidget(del_btn); self._chips_layout.addWidget(row_w)

    def _remove_food(self, food_obj, widget):
        try:
            self._foods.remove(food_obj)  # removes only ONE
        except ValueError:
            pass
        widget.deleteLater()
        if not self._foods:
            self._food_scroll.setVisible(False)
        self.foods_changed.emit(self._foods)

    def _tick(self):
        self._update_detect()
        if not self._user_override: self._apply(_slot_from_time(), auto=True)

    def _apply(self, slot, auto):
        self._current_slot = slot; self._update_detect()
        self.slot_changed.emit(slot)

    def _update_detect(self):
        now = datetime.now()
        slot = _slot_from_time(now)
        time_str = now.strftime("%H:%M")
        date_str = now.strftime("%d %b %Y")
        self._detect_label.setText(
            f"Detected: <b>{slot}</b>  •  {date_str}  {time_str}"
        )
        self._detect_label.setTextFormat(Qt.RichText)

    def update_macro_display(self, foods):
        total_protein = sum(f["macros"]["protein"] for f in foods)
        total_carbs   = sum(f["macros"]["carbs"] for f in foods)
        total_fat     = sum(f["macros"]["fat"] for f in foods)
        total_vit     = sum(f["macros"]["vitamins"] for f in foods)
        total_min     = sum(f["macros"]["minerals"] for f in foods)

        self.protein_label.setText(f"Protein: {total_protein} g")
        self.carbs_label.setText(f"Carbs: {total_carbs} g")
        self.fat_label.setText(f"Fat: {total_fat} g")
        self.vit_label.setText(f"Vitamins: {total_vit}")
        self.min_label.setText(f"minerals: {total_min}")

# DashboardPage
class DashboardPage(QWidget):
    open_planner_requested = Signal()
    meal_added = Signal()

    def __init__(self, parent=None):
        super().__init__(parent); self.setStyleSheet(ss.page_bg)
        self.load_user_data()
        self._tdee_target = 2000
        self._current_calories = 0

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(ss.scroll_transparent)

        inner = QWidget(); inner.setStyleSheet(ss.page_bg)
        v = QVBoxLayout(inner); v.setContentsMargins(36,28,36,36); v.setSpacing(20)

        # Header
        hdr = QHBoxLayout()
        head_col = QVBoxLayout(); head_col.setSpacing(4)
        # Welcome user
        self.user_label = QLabel(); self.user_label.setStyleSheet(ss.page_title)
        s = QLabel("Track your nutrients and stay healthy."); s.setStyleSheet(ss.page_subtitle )
        head_col.addWidget(self.user_label); head_col.addWidget(s)
        hdr.addLayout(head_col); hdr.addStretch()
        # Avatar circle with photo placeholder
        v.addLayout(hdr)

        # Today's Balance (Donut + macros)
        # Donut
        bal_card = QWidget(); bal_card.setStyleSheet(ss.cream_card)
        bv = QVBoxLayout(bal_card); bv.setContentsMargins(24,20,24,20); bv.setSpacing(14)
        bt = QLabel("Today's Balance"); bt.setStyleSheet(ss.section)
        bv.addWidget(bt)
        macro_row = QHBoxLayout(); macro_row.setSpacing(14)
        donut_layout = QVBoxLayout()
        self.donut = _Donut()

        donut_layout.addWidget(self.donut, alignment=Qt.AlignCenter)
        self.anim_value = AnimatedValue(1.0)
        self.anim_value.on_change = self._apply_progress

        macro_row.addLayout(donut_layout)

        # Macro
        self.macro_labels = {}
        self.macro_bars = {}
        self.macro_anims = {}

        for lbl, color in [("Protein",ss.protein),("Carbs",ss.carbs),("Fat",ss.fats),("Vitamins",ss.vitamins),("Minerals",ss.mineral)]:
            tile, value_lbl, bar_fill, anim  = _macro_tile(lbl, color)
            key = lbl.lower()
            self.macro_labels[key] = value_lbl
            self.macro_bars[key] = bar_fill
            self.macro_anims[key] = anim

            macro_row.addWidget(tile)

        macro_row.addStretch(); bv.addLayout(macro_row)
        v.addWidget(bal_card)

        # Meal Schedule (Timeline)
        sched_card = QWidget(); sched_card.setStyleSheet(ss.cream_card)
        sv = QVBoxLayout(sched_card); sv.setContentsMargins(24,18,24,18); sv.setSpacing(14)
        st = QLabel("Meal Schedule"); st.setStyleSheet(ss.section)
        sv.addWidget(st)
        self._timeline = _MealTimeline(); sv.addWidget(self._timeline)
        v.addWidget(sched_card)

        # Add Meals card
        meals_card = QWidget(); meals_card.setStyleSheet(ss.cream_card)
        mv = QVBoxLayout(meals_card); mv.setContentsMargins(0,0,0,0); mv.setSpacing(0)
        self._meals_panel = _AddMealsPanel()
        self._meals_panel.slot_changed.connect(self._timeline.set_active)
        self._meals_panel.foods_changed.connect(self.update_dashboard_macros)
        mv.addWidget(self._meals_panel)
        v.addWidget(meals_card)

        # Recommendation (hidden until first add)
        self._rec_card = QWidget(); self._rec_card.setStyleSheet(ss.cream_card)
        rv = QVBoxLayout(self._rec_card); rv.setContentsMargins(0,0,0,0); rv.setSpacing(0)
        self._rec_panel = _RecPanel()
        self._rec_card.setVisible(False)
        rv.addWidget(self._rec_panel)
        self._meals_panel.foods_changed.connect(self._rec_panel.update_tips)
        self._meals_panel.meal_added.connect(lambda: self._rec_card.setVisible(True))
        v.addWidget(self._rec_card)
        
        v.addStretch()
        scroll.setWidget(inner)
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.addWidget(scroll)

        
        self._update_donut()
        self.update_user()
    
    def update_user(self):
        """Update the welcome label with the current username from Session"""
        try:
            username = getattr(Session, "username", None) or "Guest"
            self.user_label.setText(f"Welcome back, {username}!")
        except Exception as e:
            print("User update error:", e)
            self.user_label.setText("Welcome back, Guest!")
    
    def load_user_data(self):
        user = get_user_by_id(Session.user_id)

        if not user:
            return

        bmi = user.get("bmi", 0)
        tdee = user.get("tdee", 0)

    # Example display (you can customize UI)
        #self.bmi_label.setText(f"{bmi:.2f}")
        #self.tdee_label.setText(f"{int(tdee)}")

    # If you have labels:
    # self.bmi_label.setText(str(bmi))
    # self.tdee_label.setText(str(tdee))
    def update_data(self, bmi, tdee):
        self.bmi_label.setText(f"{bmi:.2f}")
        self.tdee_label.setText(f"{int(tdee)}")

    def update_from_meals(self, meal_data):
        """Wrapper for meal update events from planner"""
        self.update_dashboard_macros(meal_data)

    def update_dashboard_macros(self, foods):
        total = {
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "vitamins": 0,
            "minerals": 0
        }

        for item in foods:
            if isinstance(item, str):
                profile = FOOD_DATABASE.get(item, {})
                qty = 1
        # If item is already a dict with 'profile' or 'macros', keep old logic
            elif isinstance(item, dict):
                profile = item.get("profile") or item.get("macros") or {}
                qty = item.get("quantity", 1)
            else:
                continue 

            if not profile:
                continue

            total["protein"]  += profile.get("protein", 0) * qty
            total["carbs"]    += profile.get("carbs", 0) * qty
            total["fat"]      += profile.get("fat", 0) * qty
            total["minerals"] += profile.get("minerals", profile.get("mineral", 0)) * qty
            total["vitamins"] += profile.get("vitamins", 0) * qty

        # Update labels
        for key, value in total.items():
            if key in self.macro_labels:
                self.macro_labels[key].setText(str(round(value, 2)))

        max_values = {
            "protein": 150,
            "carbs": 300,
            "fat": 100,
            "vitamins": 100,
            "minerals": 100
        }

        for key, value in total.items():
            if key not in self.macro_labels:
                continue
            percent = min(value / max_values[key], 1.0)
            QTimer.singleShot(
                300,
                lambda k=key, p=percent: self._animate_bar(k, p)
            )

        calories = (
            total["protein"] * 4 +
            total["carbs"] * 4 +
            total["fat"] * 9
        )
        tdee = getattr(self, "_tdee_target", 2000)
        remaining = max(tdee - calories, 0)
        percent = remaining / self._tdee_target if self._tdee_target > 0 else 0
        percent = max(0.0, min(percent, 1.0))
        self.donut.set_value(percent)

    def update_tdee(self, tdee):
        self._tdee_target = tdee
        self._current_calories = 0  # reset or track separately
        self._update_donut()

    def _update_donut(self):
        remaining = max(self._tdee_target - self._current_calories, 0)
        percent = remaining / self._tdee_target if self._tdee_target > 0 else 0

        self.donut.set_value(percent)

    def _animate_bar(self, key, percent):
        bar = self.macro_bars[key]
        anim = self.macro_anims[key]
        container = bar.parent()

    # Ensure layout is calculated
        container.updateGeometry()
        container.repaint()

        full_width = container.width()

    # If still not ready → retry
        if full_width <= 0:
            QTimer.singleShot(100, lambda: self._animate_bar(key, percent))
            return

        new_width = int(full_width * percent)

        anim.stop()
        anim.setStartValue(bar.maximumWidth())
        anim.setEndValue(new_width)
        anim.start()

    def animate_to(self, target):
        self.anim = QPropertyAnimation(self.anim_value, b"value")
        self.anim.setDuration(500)  # smooth
        self.anim.setStartValue(self.anim_value.getValue())
        self.anim.setEndValue(target)
        self.anim.start()

    def _apply_progress(self, percent):
        self.donut.setStyleSheet(f"""
            background: qradialgradient(
                cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
                stop:0.6 #B7C9A8,
                stop:0.601 rgba(255,255,255,0.3),
                stop:{0.6 + (0.4 * percent)} white,
                stop:{0.601 + (0.4 * percent)} rgba(255,255,255,0.3)
            );
            border-radius: 70px;
        """)