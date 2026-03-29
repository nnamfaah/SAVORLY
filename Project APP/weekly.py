from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea)
from PySide6.QtCore import Qt
import stylesheet as ss

class WeeklySummaryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ss.page_bg)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(ss.scroll_transparent)

        inner = QWidget()
        inner.setStyleSheet(ss.page_bg)
        v = QVBoxLayout(inner)
        v.setContentsMargins(36, 28, 36, 36)
        v.setSpacing(10)

        title = QLabel("Weekly Summary")
        title.setStyleSheet(ss.page_title)
        sub = QLabel("Your nutrition overview for the week.")
        sub.setStyleSheet(ss.page_subtitle )
        v.addWidget(title)
        v.addWidget(sub)

        # Legend
        leg = QHBoxLayout()
        for lbl, color in [("Protein", ss.protein), ("Carbs", ss.carbs), ("Fats", ss.fats)]:
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background:{color}; border-radius:4px;")
            txt = QLabel(lbl)
            txt.setStyleSheet(ss.label)
            leg.addWidget(dot, 0, Qt.AlignVCenter)
            leg.addWidget(txt)
            leg.addSpacing(12)
        leg.addStretch()

        v.addStretch()

        scroll.setWidget(inner)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)