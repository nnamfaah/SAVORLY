from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QFrame,
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont
import stylesheet as ss


# ── Mood data ─────────────────────────────────────────────────────────────
# (week_start, mood_label, emoji, energy_text, advice)
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
    (
        QDate(2026, 3, 8),
        "Slightly Tired", "😴",
        "a bit low on energy.",
        "Consider adding more protein-rich foods and shorter workout bursts.",
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
    """Weekly Mood & Activity Insight sub-page."""
    # Signal: คลิกปฏิทิน → ไปหน้า weekly_meal
    go_to_weekly_meal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ss.page_bg)

        self._idx   = 0
        self._total = len(MOOD_DATA)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(ss.scroll_transparent)

        inner = QWidget()
        inner.setStyleSheet(ss.page_bg)
        v = QVBoxLayout(inner)
        v.setContentsMargins(36, 28, 36, 36)
        v.setSpacing(16)

        # Header
        col = QVBoxLayout()
        col.addWidget(_label("Weekly Mood & Activity Insight",
                             "font-size:22px; font-weight:700; color:#1a1a1a;"))
        col.addWidget(_label("A deep dive into your emotional well-being for the past 7 days.",
                             "font-size:13px; color:#888;"))
        v.addLayout(col)

        # Week navigator
        nav = QHBoxLayout()
        nav.addStretch()
        self._btn_prev = QPushButton("‹")
        self._btn_next = QPushButton("›")
        for b in (self._btn_prev, self._btn_next):
            b.setFixedSize(32, 32)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton { background:#f0ece5; border-radius:8px; font-size:18px; }"
                "QPushButton:hover { background:#ddd8ce; }"
            )
        self._btn_prev.clicked.connect(self._go_prev)
        self._btn_next.clicked.connect(self._go_next)

        self._week_lbl = QLabel()
        self._week_lbl.setAlignment(Qt.AlignCenter)
        self._week_lbl.setStyleSheet(
            "font-size:14px; font-weight:600; color:#333; padding:0 12px;"
        )

        # ปุ่มปฏิทิน → ไปหน้า weekly_meal
        self._cal_btn = QPushButton("📅")
        self._cal_btn.setFixedSize(32, 32)
        self._cal_btn.setCursor(Qt.PointingHandCursor)
        self._cal_btn.setToolTip("คลิกเพื่อดู Weekly Meals")
        self._cal_btn.setStyleSheet(
            "QPushButton { background:#f0ece5; border-radius:8px; font-size:16px; border:none; }"
            "QPushButton:hover { background:#ddd8ce; }"
        )
        self._cal_btn.clicked.connect(self.go_to_weekly_meal.emit)

        nav.addWidget(self._btn_prev)
        nav.addWidget(self._week_lbl)
        nav.addWidget(self._cal_btn)
        nav.addWidget(self._btn_next)
        v.addLayout(nav)

        # Mood card
        self._mood_card = self._build_mood_card()
        v.addWidget(self._mood_card)
        v.addStretch()

        scroll.setWidget(inner)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        self._refresh()

    # ── Mood card ─────────────────────────────────────────────────────────

    def _build_mood_card(self) -> QFrame:
        outer = QFrame()
        outer.setStyleSheet("QFrame { background:#c5d6b2; border-radius:20px; }")
        outer.setMinimumHeight(260)

        h = QHBoxLayout(outer)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # Left green panel
        left = QFrame()
        left.setStyleSheet(
            "QFrame { background:#7fa66e; border-top-left-radius:20px;"
            "border-bottom-left-radius:20px; }"
        )
        lv = QVBoxLayout(left)
        lv.setContentsMargins(32, 32, 32, 32)
        lv.setSpacing(16)

        self._emoji_lbl = QLabel()
        self._emoji_lbl.setAlignment(Qt.AlignCenter)
        f = QFont(); f.setPointSize(52)
        self._emoji_lbl.setFont(f)
        self._emoji_lbl.setStyleSheet("background:transparent;")

        self._mood_tag = QLabel()
        self._mood_tag.setAlignment(Qt.AlignCenter)
        self._mood_tag.setStyleSheet(
            "background:rgba(255,255,255,0.35); border-radius:12px;"
            "padding:6px 18px; font-size:13px; color:#333;"
        )
        lv.addStretch()
        lv.addWidget(self._emoji_lbl)
        lv.addWidget(self._mood_tag)
        lv.addStretch()

        # Right beige panel
        right = QFrame()
        right.setStyleSheet(
            "QFrame { background:#e8e2d9; border-top-right-radius:20px;"
            "border-bottom-right-radius:20px; }"
        )
        rv = QVBoxLayout(right)
        rv.setContentsMargins(28, 28, 28, 28)
        rv.setSpacing(14)

        badge = QLabel("WEEKLY REPORT")
        badge.setFixedHeight(24)
        badge.setStyleSheet(
            "background:#c5d6b2; border-radius:8px; padding:3px 10px;"
            "font-size:11px; font-weight:700; color:#4a6a38;"
        )

        self._week_title_lbl = QLabel()
        self._week_title_lbl.setWordWrap(True)
        self._week_title_lbl.setStyleSheet(
            "font-size:26px; font-weight:800; color:#1a1a1a;"
        )

        self._energy_lbl = QLabel()
        self._energy_lbl.setWordWrap(True)
        self._energy_lbl.setStyleSheet("font-size:14px; color:#333;")

        self._advice_lbl = QLabel()
        self._advice_lbl.setWordWrap(True)
        self._advice_lbl.setStyleSheet("font-size:14px; color:#555;")

        rv.addWidget(badge)
        rv.addWidget(self._week_title_lbl)
        rv.addWidget(self._energy_lbl)
        rv.addWidget(self._advice_lbl)
        rv.addStretch()

        h.addWidget(left,  4)
        h.addWidget(right, 5)
        return outer

    # ── Refresh ───────────────────────────────────────────────────────────

    def _refresh(self):
        start, mood, emoji, energy, advice = MOOD_DATA[self._idx]

        self._week_lbl.setText(_week_label(start))
        self._emoji_lbl.setText(emoji)
        self._mood_tag.setText(mood)
        self._week_title_lbl.setText(f"Mood of Week {self._total - self._idx}")
        self._energy_lbl.setText(
            f"This week you've been <b style='color:#4a8a28'>{energy}</b>"
        )
        self._energy_lbl.setTextFormat(Qt.RichText)
        self._advice_lbl.setText(advice)

        self._btn_prev.setEnabled(self._idx < self._total - 1)
        self._btn_next.setEnabled(self._idx > 0)

    def _go_prev(self):
        if self._idx < self._total - 1:
            self._idx += 1
            self._refresh()

    def _go_next(self):
        if self._idx > 0:
            self._idx -= 1
            self._refresh()