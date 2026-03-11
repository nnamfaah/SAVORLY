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

def _slot_from_time(dt=None):
    hour = (dt or datetime.now()).hour
    if 5  <= hour < 10: return "Breakfast"
    if 10 <= hour < 14: return "Lunch"
    if 14 <= hour < 18: return "Dinner"
    if 19 <= hour: return "Late-night"

# Tips
_food_tips = {}
_default_tips = []

def _tips_for_foods(foods):
    found = {}
    for food in foods:
        fl = food.lower().strip()
        for kw, (cat, tip) in _food_tips.items():
            if kw in fl and cat not in found:
                found[cat] = tip
    tips = list(found.values())
    if not tips:
        return list(_default_tips)
    if "Protein" not in found:
        tips.append("Protein looks low — try eggs, chicken, or yogurt.")
    if "Fats" not in found:
        tips.append("Add healthy fats like avocado or almonds.")
    return tips[:5]

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
        self.setStyleSheet(ss.white_card)
        self._active_filter = "All"; self._all_tips = list(_default_tips)
        v = QVBoxLayout(self); v.setContentsMargins(20,18,20,18); v.setSpacing(12)
        hdr = QHBoxLayout()
        title = QLabel("Recommendation")
        title.setStyleSheet(f"font-size:15px; font-weight:700; color:{ss.text}; background:transparent;")
        hdr.addWidget(title); hdr.addStretch(); v.addLayout(hdr)

        self._fil_btns = {}
        fil_row = QHBoxLayout(); fil_row.setSpacing(6)
        for f in ["All","Protein","Carbs","Fats","Balance"]:
            btn = QPushButton(f); btn.setCheckable(True); btn.setFixedHeight(26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, fl=f: self._set_filter(fl))
            self._fil_btns[f] = btn; fil_row.addWidget(btn)
        fil_row.addStretch(); v.addLayout(fil_row)

        self._tips_widget = QWidget(); self._tips_widget.setStyleSheet("background:transparent;")
        self._tips_layout = QVBoxLayout(self._tips_widget)
        self._tips_layout.setContentsMargins(0,0,0,0); self._tips_layout.setSpacing(10)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")
        scroll.setWidget(self._tips_widget); v.addWidget(scroll)
        self._refresh_filter("All")

    def update_tips(self, foods):
        self._all_tips = _tips_for_foods(foods); self._refresh_filter(self._active_filter)

    def _set_filter(self, f):
        self._active_filter = f; self._refresh_filter(f)

    def _refresh_filter(self, active_filter):
        for f, btn in self._fil_btns.items():
            active = f == active_filter
            btn.setChecked(active)
            btn.setStyleSheet(
                f"QPushButton{{padding:4px 12px; border-radius:13px; border:none; font-size:11px; font-weight:600;"
                f"background:{ss.green if active else 'rgba(0,0,0,0.06)'};"
                f"color:{'white' if active else ss.text_muted};}}"
                f"QPushButton:hover{{background:{ss.light_green if not active else ss.dark_green}; color:white;}}")
        while self._tips_layout.count():
            item = self._tips_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        tips = self._all_tips
        if active_filter != "All":
            kw = active_filter.lower()
            tips = [t for t in tips if kw in t.lower()] or ["No tips for this category yet."]
        for tip in tips:
            wrap = QWidget(); wrap.setStyleSheet("background:transparent;")
            wv = QHBoxLayout(wrap); wv.setContentsMargins(0,0,0,0); wv.setSpacing(10)
            dot = QLabel("•"); dot.setStyleSheet(f"font-size:16px; color:{ss.green}; background:transparent;")
            lbl = QLabel(tip); lbl.setWordWrap(True)
            lbl.setStyleSheet(f"font-size:12px; color:{ss.text}; background:transparent; line-height:1.5;")
            wv.addWidget(dot,0,Qt.AlignTop); wv.addWidget(lbl)
            self._tips_layout.addWidget(wrap)
        self._tips_layout.addStretch()

# Add Meals Panel
class _AddMealsPanel(QWidget):
    slot_changed  = Signal(str)
    foods_changed = Signal(list)
    meal_added    = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ss.cream_card)
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

# Drag-drop panel
slot_icons = {"Breakfast":"☀️","Lunch":"🌤️","Dinner":"🌙","Late-night":"🌛"}
class _DragDropPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); v.setSpacing(12)
        title = QLabel("Drag & Drop to Swap Meals"); title.setStyleSheet(ss.section)
        v.addWidget(title)
        cols = QHBoxLayout(); cols.setSpacing(12)
        for slot, icon in slot_icons.items():
            col = QWidget()
            col.setStyleSheet(f"background:{ss.white}; border-radius:{ss.radius_xl}px; border:1px solid rgba(0,0,0,0.06);")
            col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred); col.setMinimumHeight(140)
            cv = QVBoxLayout(col); cv.setContentsMargins(12,12,12,12); cv.setSpacing(10)
            hdr = QHBoxLayout()
            ico = QLabel(icon); ico.setFixedSize(34,34); ico.setAlignment(Qt.AlignCenter)
            ico.setStyleSheet(f"background:{ss.light_green}; border-radius:10px; font-size:16px;")
            lbl = QLabel(slot); lbl.setStyleSheet(f"font-size:13px; font-weight:700; color:{ss.text}; background:transparent;")
            hdr.addWidget(ico); hdr.addWidget(lbl); hdr.addStretch(); cv.addLayout(hdr)
            hint = QLabel("Drop food here"); hint.setAlignment(Qt.AlignCenter)
            hint.setStyleSheet(f"font-size:11px; color:{ss.text_muted}; background:transparent;"
                               f"border:2px dashed {ss.brown}; border-radius:{ss.radius_md}px; padding:18px 10px;")
            cv.addWidget(hint); cv.addStretch(); cols.addWidget(col)
            _shadow(col, radius=10, offset=2, alpha=12)
        v.addLayout(cols)

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
        self._meals_panel = _AddMealsPanel()
        self._meals_panel.slot_changed.connect(self._timeline.set_active)
        v.addWidget(self._meals_panel)

        # Recommendation (hidden until first add)
        self._rec_panel = _RecPanel()
        self._rec_panel.setVisible(False)
        self._meals_panel.foods_changed.connect(self._rec_panel.update_tips)
        self._meals_panel.meal_added.connect(lambda: self._rec_panel.setVisible(True))
        v.addWidget(self._rec_panel)

        # Drag & Drop (hidden until first add)
        self._dd_panel = _DragDropPanel()
        self._dd_panel.setVisible(False)
        self._meals_panel.meal_added.connect(lambda: self._dd_panel.setVisible(True))
        v.addWidget(self._dd_panel)

        v.addStretch()
        scroll.setWidget(inner)
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.addWidget(scroll)