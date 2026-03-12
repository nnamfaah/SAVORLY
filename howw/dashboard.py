from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QScrollArea,
    QSizePolicy, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QTimer, QRectF, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QPixmap, QIcon

import stylesheet as ss

slots = ["Breakfast", "Lunch", "Dinner", "Late-night"]

def _slot_from_time(dt=None) -> str:
    h = (dt or datetime.now()).hour
    if  5 <= h < 10: return "Breakfast"
    if 10 <= h < 14: return "Lunch"
    if 14 <= h < 21: return "Dinner"
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
    "avocado":  ("fats",     "avocado"),
    "almond":   ("fats",     "almonds"),
    "olive":    ("fats",     "olive oil"),
    "milk":     ("fats",     "milk"),
    "cheese":   ("fats",     "cheese"),
    "spinach":  ("minerals", "spinach"),
    "broccoli": ("minerals", "broccoli"),
    "apple":    ("fiber",    "apple"),
    "carrot":   ("fiber",    "carrots"),
    "bean":     ("fiber",    "beans"),
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
    has_fats     = "fats"     in found
    has_minerals = "minerals" in found
    has_fiber    = "fiber"    in found

    parts = []
    if has_protein and has_carbs and has_fats:
        parts.append("Great balance of protein, carbs, and fats")
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
    if not has_fats:    missing.append("healthy fats like avocado or almonds")
    if not has_fiber and not has_minerals: missing.append("some vegetables for minerals and fiber")

    if missing:
        parts.append("consider adding " + " and ".join(missing[:2]))
    if has_minerals:
        parts.append(f"{found['minerals'].capitalize()} adds great minerals to your meal")
    if has_fiber:
        parts.append(f"{found['fiber'].capitalize()} boosts your fiber intake")

    sentence = " — ".join(parts[:2])
    if len(parts) > 2:
        sentence += f". {parts[2].capitalize()}."
    else:
        sentence += "."
    return sentence

def _slot_from_time(dt=None):
    hour = (dt or datetime.now()).hour
    if 5  <= hour < 10: return "Breakfast"
    if 10 <= hour < 14: return "Lunch"
    if 14 <= hour < 18: return "Dinner"
    if 19 <= hour: return "Late-night"

# Shadow helper
def _shadow(w, radius=12, offset=3, alpha=18):
    eff = QGraphicsDropShadowEffect(w)
    eff.setBlurRadius(radius); eff.setOffset(0, offset)
    eff.setColor(QColor(0, 0, 0, alpha)); w.setGraphicsEffect(eff)

# TDEE
class _Donut(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedSize(150, 150)
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(14, 14, 122, 122)
        # track
        p.setPen(QPen(QColor("#D8D2C5"), 14, Qt.SolidLine, Qt.FlatCap))
        p.setBrush(Qt.NoBrush); p.drawEllipse(rect)
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
    bar = QFrame(); bar.setFixedHeight(3)
    bar.setStyleSheet(f"background:rgba(0,0,0,0.08); border-radius:2px;")
    v.addWidget(bar); v.addStretch()
    return w

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

    def update_tips(self, foods: list):
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
        self._user_override = False
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
        if not text: return
        new_foods = [f.strip() for f in text.split(",") if f.strip()]
        for food in new_foods:
            self._foods.append(food); self._add_chip(food)
        self._inp.clear(); self._food_scroll.setVisible(True)
        if not self._has_added_once:
            self._has_added_once = True; self.meal_added.emit()
        self.foods_changed.emit(self._foods)

    def _add_chip(self, food):
        row_w = QWidget()
        row_w.setStyleSheet(f"background:rgba(255,255,255,0.7); border-radius:{ss.radius_sm}px;")
        row = QHBoxLayout(row_w); row.setContentsMargins(10,5,6,5); row.setSpacing(8)
        lbl = QLabel(food); lbl.setStyleSheet(f"font-size:12px; color:{ss.text}; background:transparent;")
        row.addWidget(lbl); row.addStretch()
        del_btn = QPushButton("x"); del_btn.setFixedSize(18,18); del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"QPushButton{{border:none; border-radius:9px; font-size:12px; font-weight:700; color:{ss.text_muted}; background:transparent;}} QPushButton:hover{{color:#c00;}}")
        del_btn.clicked.connect(lambda _, f=food, w=row_w: self._remove_food(f, w))
        row.addWidget(del_btn); self._chips_layout.addWidget(row_w)

    def _remove_food(self, food, widget):
        if food in self._foods: self._foods.remove(food)
        widget.deleteLater()
        if not self._foods: self._food_scroll.setVisible(False)
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

# DashboardPage
class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setStyleSheet(ss.page_bg)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(ss.scroll_transparent)

        inner = QWidget(); inner.setStyleSheet(ss.page_bg)
        v = QVBoxLayout(inner); v.setContentsMargins(36,28,36,36); v.setSpacing(20)

        # Header
        hdr = QHBoxLayout()
        head_col = QVBoxLayout(); head_col.setSpacing(4)
        t = QLabel(f"Welcome back, {"username"}!"); t.setStyleSheet(ss.page_title)
        s = QLabel("Track your nutrients and stay healthy."); s.setStyleSheet(ss.page_subtitle )
        head_col.addWidget(t); head_col.addWidget(s)
        hdr.addLayout(head_col); hdr.addStretch()
        bell = QLabel("🔔"); bell.setFixedSize(40,40); bell.setAlignment(Qt.AlignCenter)
        bell.setStyleSheet(ss.bell_icon)
        # Avatar circle with photo placeholder
        av_wrap = QWidget(); av_wrap.setFixedSize(44,44)
        av_wrap.setStyleSheet(f"background:{ss.light_green}; border-radius:22px;")
        av_inner = QVBoxLayout(av_wrap); av_inner.setContentsMargins(0,0,0,0)
        av_lbl = QLabel("👤"); av_lbl.setAlignment(Qt.AlignCenter)
        av_lbl.setStyleSheet("font-size:20px; background:transparent;")
        av_inner.addWidget(av_lbl)
        hdr.addWidget(bell); hdr.addSpacing(8); hdr.addWidget(av_wrap)
        v.addLayout(hdr)

        # Today's Balance (Donut + macros)
        bal_card = QWidget(); bal_card.setStyleSheet(ss.cream_card)
        bv = QVBoxLayout(bal_card); bv.setContentsMargins(24,20,24,20); bv.setSpacing(14)
        bt = QLabel("Today's Balance"); bt.setStyleSheet(ss.section)
        bv.addWidget(bt)
        macro_row = QHBoxLayout(); macro_row.setSpacing(14)
        macro_row.addWidget(_Donut())
        for lbl, color in [("Protein",ss.protein),("Carbs",ss.carbs),("Fats",ss.fats),("Mineral",ss.mineral),("Fiber",ss.fiber)]:
            macro_row.addWidget(_macro_tile(lbl,color))
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