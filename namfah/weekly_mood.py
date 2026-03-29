from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QFrame,
)
from PySide6.QtCore import Qt, QDate, Signal
import stylesheet as ss

# ── Mood data ─────────────────────────────────────────────────────────────
MOOD_DATA = [
    (
        QDate(2026, 3, 22),
        "Excellent Mood Overall", "😍",
        "more energetic!",
        "Thus, next week you should try more activities. Let's clear your energy.",
    ),
    (
        QDate(2026, 3, 15),
        "Calm and Balanced", "😊",
        "steady and focused!",
        "Keep up the balanced routine — your body loves consistency.",
    ),
]

def _week_label(start: QDate) -> str:
    end = start.addDays(6)
    return f"{start.toString('MMM d')} - {end.toString('MMM d, yyyy')}"

def _label(text: str, style: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(style)
    return lbl

class WeeklyMoodSubPage(QWidget):
    go_to_weekly_meal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ss.page_bg)
        self._idx = 0
        self._total = len(MOOD_DATA)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(ss.scroll_transparent)

        self._inner = QWidget()
        self._inner.setStyleSheet(ss.inner_transparent)
        self._v = QVBoxLayout(self._inner)
        self._v.setContentsMargins(40, 30, 40, 40)
        self._v.setSpacing(25)

        self._build_header()
        self._build_nav()
        self._v.addWidget(self._build_mood_card())
        self._v.addStretch()

        scroll.setWidget(self._inner)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        self._refresh()

    def _build_header(self):
        hdr = QVBoxLayout()
        hdr.setSpacing(4)
        hdr.addWidget(_label("Weekly Mood & Activity Insight", ss.page_title))
        hdr.addWidget(_label("A deep dive into your emotional well-being for the past 7 days.", ss.page_subtitle))
        self._v.addLayout(hdr)

    def _build_nav(self):
        row = QHBoxLayout()
        row.addStretch()
        
        nav_frame = QFrame()
        nav_frame.setStyleSheet(f"background: {ss.white}; border-radius: {ss.radius_md}px; border: none;")
        nav_lay = QHBoxLayout(nav_frame)
        
        self._btn_prev = QPushButton("‹")
        self._btn_next = QPushButton("›")
        self._week_lbl = _label("", f"font-size:13px; font-weight:600; color:{ss.text}; padding: 0 10px;")

        cal_btn = QPushButton("📅")
        cal_btn.setFixedSize(30, 30)
        cal_btn.setStyleSheet("border: none; font-size: 16px;")
        cal_btn.clicked.connect(self.go_to_weekly_meal.emit)

        for b in (self._btn_prev, self._btn_next):
            b.setFixedSize(30, 30)
            b.setStyleSheet(f"QPushButton {{ border: none; font-size: 20px; color: {ss.text_muted}; }}")

        self._btn_prev.clicked.connect(self._go_prev)
        self._btn_next.clicked.connect(self._go_next)

        nav_lay.addWidget(self._btn_prev)
        nav_lay.addWidget(cal_btn)
        nav_lay.addWidget(self._week_lbl)
        nav_lay.addWidget(self._btn_next)
        row.addWidget(nav_frame)
        self._v.addLayout(row)

    def _build_mood_card(self) -> QFrame:
        outer = QFrame()
        outer.setFixedHeight(380)
        outer.setStyleSheet(f"background: {ss.white}; border-radius: 30px;")
        
        layout = QHBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._left_panel = QFrame()
        self._left_panel.setStyleSheet(
            f"background: {ss.light_green}; border-top-left-radius: 30px; border-bottom-left-radius: 30px;"
        )
        left_v = QVBoxLayout(self._left_panel)
        self._emoji_lbl = _label("😍", "font-size: 120px; qproperty-alignment: AlignCenter;")
        left_v.addWidget(self._emoji_lbl)

        right_panel = QFrame()
        right_v = QVBoxLayout(right_panel)
        right_v.setContentsMargins(40, 40, 40, 40)
        right_v.setSpacing(20)

        badge = _label("WEEKLY REPORT", 
                       f"background: {ss.light_green}; color: {ss.dark_green}; "
                       f"padding: 5px 12px; border-radius: 10px; font-weight: 800; font-size: 11px;")
        badge.setFixedWidth(120)

        self._title_lbl = _label("Mood of Week 1", 
                                f"font-size: 36px; font-weight: 800; color: {ss.text};")
        
        self._content_lbl = QLabel()
        self._content_lbl.setWordWrap(True)
        self._content_lbl.setStyleSheet(f"font-size: 18px; color: {ss.text}; line-height: 160%;")

        right_v.addWidget(badge)
        right_v.addWidget(self._title_lbl)
        right_v.addSpacing(10)
        right_v.addWidget(self._content_lbl)
        right_v.addStretch()

        layout.addWidget(self._left_panel, 1)
        layout.addWidget(right_panel, 1)
        return outer

    def _refresh(self):
        if not (0 <= self._idx < self._total): return
        start, mood, emoji, energy, advice = MOOD_DATA[self._idx]

        self._week_lbl.setText(_week_label(start))
        self._emoji_lbl.setText(emoji)
        self._title_lbl.setText(f"Mood of Week {self._total - self._idx}")

        bullet_text = (
            f"<ul style='margin-left: -20px; list-style-type: disc;'>"
            f"<li>This week you've been <b style='color:{ss.tdee}'>{energy}</b></li>"
            f"<br>"
            f"<li>{advice}</li>"
            f"</ul>"
        )
        self._content_lbl.setText(bullet_text)
        self._content_lbl.setTextFormat(Qt.RichText)

        self._btn_prev.setEnabled(self._idx < self._total - 1)
        self._btn_next.setEnabled(self._idx > 0)

    def _go_prev(self):
        self._idx += 1
        self._refresh()

    def _go_next(self):
        self._idx -= 1
        self._refresh()