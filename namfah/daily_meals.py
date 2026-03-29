from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QFrame,
)
from PySide6.QtCore import Qt, QDate, Signal
import stylesheet as ss


def _card(radius: int = 16, bg: str = "#e8e2d9") -> QFrame:
    f = QFrame()
    f.setStyleSheet(f"QFrame {{ background:{bg}; border-radius:{radius}px; }}")
    return f


def _label(text: str, style: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(style)
    return lbl


class DailyMealsSubPage(QWidget):
    """Record of Daily Meals sub-page."""
    go_to_weekly_meal = Signal()
    go_to_mood        = Signal()

    _SAMPLE: dict = {}  # {QDate: {"MealName": [foods], "macros": {...}}}

    _MEALS = [
        ("Breakfast", "🌅"),
        ("Lunch",     "☀️"),
        ("Dinner",    "🍽️"),
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
        self._inner.setStyleSheet(ss.page_bg)
        self._v = QVBoxLayout(self._inner)
        self._v.setContentsMargins(36, 28, 36, 36)
        self._v.setSpacing(16)

        self._build_header()
        self._build_date_nav()
        self._build_body()
        self._v.addStretch()

        scroll.setWidget(self._inner)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        self._refresh()

    # ── Header ────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = QHBoxLayout()
        col = QVBoxLayout()
        col.addWidget(_label("Record of Daily Meals",
                             "font-size:22px; font-weight:700; color:#1a1a1a;"))
        col.addWidget(_label("Track your nutrition and reach your wellness goals.",
                             "font-size:13px; color:#888;"))
        hdr.addLayout(col)
        hdr.addStretch()
        self._v.addLayout(hdr)

    # ── Date navigator ────────────────────────────────────────────────────

    def _build_date_nav(self):
        row = QHBoxLayout()
        row.addStretch()

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

        # ปุ่มปฏิทิน 📅 → ไปหน้า Weekly Meals (อยู่ระหว่าง ‹ และวันที่)
        cal_btn = QPushButton("📅")
        cal_btn.setFixedSize(32, 32)
        cal_btn.setCursor(Qt.PointingHandCursor)
        cal_btn.setToolTip("ดู Weekly Meals")
        cal_btn.setStyleSheet(
            "QPushButton { background:#f0ece5; border-radius:8px; font-size:16px; border:none; }"
            "QPushButton:hover { background:#ddd8ce; }"
        )
        cal_btn.clicked.connect(self.go_to_weekly_meal.emit)

        self._date_lbl = QLabel()
        self._date_lbl.setAlignment(Qt.AlignCenter)
        self._date_lbl.setStyleSheet(
            "font-size:14px; font-weight:600; color:#333; padding:0 12px;"
        )

        row.addWidget(self._btn_prev)
        row.addWidget(cal_btn)
        row.addWidget(self._date_lbl)
        row.addWidget(self._btn_next)
        self._v.addLayout(row)

    # ── Body ──────────────────────────────────────────────────────────────

    def _build_body(self):
        body = QHBoxLayout()
        body.setSpacing(24)
        body.addWidget(self._build_macro_card(), 3)
        self._meal_col = QVBoxLayout()
        self._meal_col.setSpacing(12)
        body.addLayout(self._meal_col, 5)
        self._v.addLayout(body)

    def _build_macro_card(self) -> QFrame:
        c = _card(16, "#e8e2d9")
        v = QVBoxLayout(c)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(10)

        v.addWidget(_label("Macro Balance",
                           "font-size:14px; color:#555; qproperty-alignment:AlignCenter;"))

        donut = QLabel("TDEE")
        donut.setFixedSize(140, 140)
        donut.setAlignment(Qt.AlignCenter)
        donut.setStyleSheet(
            "background:transparent; border:10px solid #7fa66e;"
            "border-radius:70px; font-size:16px; font-weight:700; color:#333;"
        )
        h_c = QHBoxLayout()
        h_c.addStretch(); h_c.addWidget(donut); h_c.addStretch()
        v.addLayout(h_c)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#ccc;")
        v.addWidget(sep)

        self._macro_labels: dict[str, QLabel] = {}
        for key in ("Protein", "Carbs", "Fats", "Mineral", "Fiber"):
            row = QHBoxLayout()
            val_lbl = _label("0", "font-size:13px; font-weight:600; color:#333;")
            self._macro_labels[key] = val_lbl
            row.addWidget(_label(f"{key}:", "font-size:13px; color:#555;"))
            row.addStretch()
            row.addWidget(val_lbl)
            v.addLayout(row)

        v.addStretch()
        return c

    def _build_meal_row(self, name: str, icon: str, foods: str) -> QFrame:
        c = _card(12, "#f0ece5")
        h = QHBoxLayout(c)
        h.setContentsMargins(14, 14, 14, 14)
        h.setSpacing(14)

        ico = QLabel(icon)
        ico.setFixedSize(36, 36)
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet("background:#7fa66e; border-radius:10px; font-size:18px;")

        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(_label(name,  "font-size:14px; font-weight:700; color:#333;"))
        col.addWidget(_label(foods, "font-size:12px; color:#888;"))

        plus = QPushButton("+")
        plus.setFixedSize(28, 28)
        plus.setCursor(Qt.PointingHandCursor)
        plus.setStyleSheet(
            "QPushButton { background:transparent; font-size:20px; color:#aaa; border:none; }"
            "QPushButton:hover { color:#555; }"
        )

        h.addWidget(ico)
        h.addLayout(col)
        h.addStretch()
        h.addWidget(plus)
        return c

    # ── Refresh ───────────────────────────────────────────────────────────

    def _refresh(self):
        self._date_lbl.setText(self._current_date.toString("dddd, d MMM"))

        while self._meal_col.count():
            item = self._meal_col.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        data = self._SAMPLE.get(self._current_date, {})
        for meal_name, icon in self._MEALS:
            foods = data.get(meal_name, ["Banana, Oat milk, Sourdough"])
            self._meal_col.addWidget(
                self._build_meal_row(meal_name, icon, ", ".join(foods))
            )

        macros = data.get("macros", {"Protein": 0, "Carbs": 2,
                                     "Fats": 0, "Mineral": 0, "Fiber": 1})
        for key, lbl in self._macro_labels.items():
            lbl.setText(str(macros.get(key, 0)))

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