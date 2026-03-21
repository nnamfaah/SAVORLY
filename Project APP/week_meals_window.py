import sys
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget,
    QHeaderView, QListWidget, QInputDialog,
    QDialog, QFrame
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QFont, QDrag, QPalette, QColor


class DetailPopup(QDialog):
    def __init__(self, food):
        super().__init__()
        self.setWindowTitle("Food Detail")
        self.setFixedSize(200, 110)
        layout = QVBoxLayout(self)
        title = QLabel(food)
        title.setFont(QFont("Segoe UI", 13))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)


class FoodList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.CopyAction)

    def startDrag(self, actions):
        item = self.currentItem()
        if item:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(item.text())
            drag.setMimeData(mime)
            drag.exec(Qt.CopyAction)

    def dragEnterEvent(self, event): event.accept()
    def dragMoveEvent(self, event): event.accept()

    def dropEvent(self, event):
        text = event.mimeData().text()
        food = text.split(". ", 1)[1] if ". " in text else text
        self.addItem(f"{self.count()+1}. {food}")
        event.accept()


GREEN_MEALS = {"Breakfast", "Lunch", "Dinner"}

class MealCell(QFrame):
    """ใช้ QFrame แทน QWidget เพื่อให้ stylesheet border-radius ทำงาน"""

    def __init__(self, meal_name, row, col, parent_page):
        super().__init__()
        self.row = row
        self.col = col
        self.parent_page = parent_page

        bg = "#a8bb96"
        btn_color = "#3d5240"
        
        self.setObjectName(f"cell_{row}_{col}")
        self.setStyleSheet(f"""
            QFrame#cell_{row}_{col} {{
                background-color: {bg};
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignCenter)

        self.food_list = FoodList()
        self.food_list.setMaximumHeight(50)
        self.food_list.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.food_list)

        self.food_list.itemDoubleClicked.connect(self.delete_food)
        self.food_list.itemClicked.connect(self.show_detail)

        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(26, 26)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.60);
                border: none;
                border-radius: 13px;
                font-size: 16px;
                color: {btn_color};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.90);
            }}
        """)
        layout.addWidget(self.add_btn, alignment=Qt.AlignCenter)
        self.add_btn.clicked.connect(self.add_food)

    def add_food(self):
        text, ok = QInputDialog.getText(self, "Add Food", "Food name:")
        if ok and text.strip():
            self.food_list.addItem(f"{self.food_list.count()+1}. {text}")
            self.parent_page.save_meal(self.row, self.col, text)
            self.parent_page.update_mood()

    def delete_food(self, item):
        self.food_list.takeItem(self.food_list.row(item))

    def show_detail(self, item):
        popup = DetailPopup(item.text().split(". ", 1)[1])
        popup.exec()


class MealPlannerPage(QWidget):

    def __init__(self):
        super().__init__()
        self.current_date = datetime.today()
        self.meal_types = ["Breakfast", "Lunch", "Dinner", "Night", "Snack", "Note"]
        self.meal_icons = {
            "Breakfast": "☀", "Lunch": "≡", "Dinner": "⊟",
            "Night": "☽", "Snack": "◎", "Note": "☐",
        }
        self.meal_data = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 16)
        main_layout.setSpacing(10)

        #Header
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        page_title = QLabel("Weekly Meal Overview")
        page_title.setFont(QFont("Segoe UI", 17, QFont.Bold))
        page_title.setStyleSheet("color: #1a2b1b; background: transparent;")
        page_sub = QLabel("Manage your nutrition and track your daily habits.")
        page_sub.setFont(QFont("Segoe UI", 10))
        page_sub.setStyleSheet("color: #8a9e8b; background: transparent;")
        title_col.addWidget(page_title)
        title_col.addWidget(page_sub)
        header_row.addLayout(title_col)
        header_row.addStretch()
        self.mood_label = QLabel("😊")
        self.mood_label.setFont(QFont("Segoe UI Emoji", 26))
        self.mood_label.setStyleSheet("background: transparent;")
        header_row.addWidget(self.mood_label)
        main_layout.addLayout(header_row)

        #Week nav 
        week_layout = QHBoxLayout()
        nav_style = """
            QPushButton {
                background: white; border: 1px solid #d0d5cc;
                border-radius: 8px; font-size: 11px; color: #4a5e4b;
            }
            QPushButton:hover { background: #eef2ec; }
        """
        self.prev_btn = QPushButton("❮")
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(nav_style)
        self.prev_btn.clicked.connect(self.prev_week)

        self.week_label = QLabel()
        self.week_label.setFont(QFont("Segoe UI", 11))
        self.week_label.setAlignment(Qt.AlignCenter)
        self.week_label.setStyleSheet("""
            color: #2d3a2e; padding: 4px 14px;
            background: white; border: 1px solid #d0d5cc; border-radius: 8px;
        """)

        self.next_btn = QPushButton("❯")
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(nav_style)
        self.next_btn.clicked.connect(self.next_week)

        week_layout.addStretch()
        week_layout.addWidget(self.prev_btn)
        week_layout.addWidget(self.week_label)
        week_layout.addWidget(self.next_btn)
        week_layout.addStretch()
        main_layout.addLayout(week_layout)
        # Table
        self.table = QTableWidget()
        self.table.setRowCount(len(self.meal_types))
        self.table.setColumnCount(7)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        # ปิด scroll ทั้งหมด
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # ให้ row ขยายเต็มพื้นที่ที่เหลือ
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        labels = [f" {self.meal_icons[m]}  {m.upper()}" for m in self.meal_types]
        self.table.setVerticalHeaderLabels(labels)

        main_layout.addWidget(self.table, stretch=1)

        self.update_week()
        self.setup_cells()

    def get_start_of_week(self, date):
        return date - timedelta(days=(date.weekday() + 1) % 7)

    def update_week(self):
        start = self.get_start_of_week(self.current_date)
        headers = [( start + timedelta(days=i)).strftime("%a\n%d %b") for i in range(7)]
        self.table.setHorizontalHeaderLabels(headers)
        end = start + timedelta(days=6)
        self.week_label.setText(f"📅  {start.strftime('%b %d')} – {end.strftime('%b %d')}")
        self.update_mood()

    def setup_cells(self):
        for row, meal in enumerate(self.meal_types):
            for col in range(7):
                cell = MealCell(meal, row, col, self)
                self.table.setCellWidget(row, col, cell)

    def prev_week(self):
        self.current_date -= timedelta(weeks=1)
        self.update_week()

    def next_week(self):
        self.current_date += timedelta(weeks=1)
        self.update_week()

    def save_meal(self, row, col, food):
        wk = self.week_label.text()
        self.meal_data.setdefault(wk, {}).setdefault(f"{row}-{col}", []).append(food)

    def calculate_mood(self):
        snack_count = 0; breakfast_skipped = False; balanced_days = 0
        wk = self.week_label.text()
        if wk not in self.meal_data: return "normal"
        data = self.meal_data[wk]
        for col in range(7):
            b = l = d = False
            for row in range(len(self.meal_types)):
                foods = data.get(f"{row}-{col}", [])
                if row == 0 and foods: b = True
                if row == 1 and foods: l = True
                if row == 2 and foods: d = True
                if row == 4: snack_count += len(foods)
            if not b: breakfast_skipped = True
            if b and l and d: balanced_days += 1
        if snack_count > 5: return "stress"
        if breakfast_skipped: return "low"
        if balanced_days >= 4: return "excellent"
        return "normal"

    def update_mood(self):
        m = {"excellent":"😍","normal":"😊","low":"☺️","stress":"😃"}
        self.mood_label.setText(m.get(self.calculate_mood(), "😊"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    app.setStyleSheet("""
        QWidget { background: #f0f2ec; }

        QTableWidget {
            background: white;
            border: 1px solid #dce0d8;
            border-radius: 14px;
            outline: none;
        }
        QTableWidget::item {
            background: transparent;
            padding: 4px;
        }
        QHeaderView { background: #e8dfc8; }
        QHeaderView::section:horizontal {
            background: #e8dfc8;
            border: none;
            border-bottom: 1px solid #dce0d8;
            padding: 6px 4px;
            font-weight: bold;
            font-size: 11px;
            color: #1a2b1b;
        }
        QHeaderView::section:vertical {
            background: white;
            border: none;
            border-right: 1px solid #dce0d8;
            font-size: 9px;
            font-weight: 700;
            color: #5a6e5b;
            text-align: left;
            padding-left: 8px;
            letter-spacing: 0.4px;
        }
        QListWidget {
            background: transparent;
            border: none;
            outline: none;
        }
        QListWidget::item {
            background: rgba(255,255,255,0.75);
            border: none;
            border-radius: 6px;
            padding: 2px 5px;
            margin: 1px;
            color: #2d3a2e;
            font-size: 10px;
        }
        QListWidget::item:hover { background: rgba(255,255,255,0.95); }
    """)

    window = MealPlannerPage()
    window.setWindowTitle("Savorly – Weekly Meal")
    window.resize(1200, 700)
    window.show()
    sys.exit(app.exec())