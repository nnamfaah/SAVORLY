import sys
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QInputDialog,
    QDialog, QFrame, QGridLayout, QSizePolicy, QScrollArea, QLineEdit
)
from PySide6.QtCore import QDate, Qt, QMimeData, Signal, QRect
from PySide6.QtGui import QFont, QDrag, QColor, QPainter, QPen
from collections import defaultdict

#Calendar Popup
class CalendarDialog(QDialog):
    date_selected = Signal(object)
    MONTH_NAMES = ["","January","February","March","April","May","June",
                   "July","August","September","October","November","December"]

    def __init__(self, current_date, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 320)
        self.view_date = current_date.replace(day=1)
        self.selected_date = current_date
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        self.card = QFrame(); self.card.setObjectName("calCard")
        self.card.setStyleSheet("QFrame#calCard{background:#fafaf7;border:1.5px solid #c8d4c4;border-radius:16px;}")
        cl = QVBoxLayout(self.card); cl.setContentsMargins(16,14,16,14); cl.setSpacing(8)
        outer.addWidget(self.card)
        nav = QHBoxLayout()
        bs = "QPushButton{background:#e8dfc8;border:none;border-radius:8px;font-size:16px;color:#3d5240;font-weight:bold;}QPushButton:hover{background:#d4c9aa;}"
        self.pb = QPushButton("‹"); self.pb.setFixedSize(30,30); self.pb.setStyleSheet(bs)
        self.pb.setCursor(Qt.PointingHandCursor); self.pb.clicked.connect(self._prev_month)
        self.ml = QLabel(); self.ml.setAlignment(Qt.AlignCenter)
        self.ml.setFont(QFont("Segoe UI",11,QFont.Bold)); self.ml.setStyleSheet("color:#1a2b1b;background:transparent;")
        self.nb = QPushButton("›"); self.nb.setFixedSize(30,30); self.nb.setStyleSheet(bs)
        self.nb.setCursor(Qt.PointingHandCursor); self.nb.clicked.connect(self._next_month)
        nav.addWidget(self.pb); nav.addStretch(); nav.addWidget(self.ml); nav.addStretch(); nav.addWidget(self.nb)
        cl.addLayout(nav)
        dg = QGridLayout(); dg.setSpacing(2)
        for i,d in enumerate(["Su","Mo","Tu","We","Th","Fr","Sa"]):
            l=QLabel(d); l.setAlignment(Qt.AlignCenter); l.setFixedHeight(20)
            l.setFont(QFont("Segoe UI",8,QFont.Bold)); l.setStyleSheet("color:#8a9e8b;background:transparent;")
            dg.addWidget(l,0,i)
        cl.addLayout(dg)
        self.grid = QGridLayout(); self.grid.setSpacing(3); cl.addLayout(self.grid)
        tb = QPushButton("Go to Today"); tb.setFixedHeight(30); tb.setCursor(Qt.PointingHandCursor)
        tb.setStyleSheet("QPushButton{background:#a8bb96;border:none;border-radius:8px;color:white;font-size:10px;font-weight:bold;}QPushButton:hover{background:#8faa7a;}")
        tb.clicked.connect(self._go_today); cl.addWidget(tb)
        self._render_calendar()

    def _render_calendar(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.ml.setText(f"{self.MONTH_NAMES[self.view_date.month]}  {self.view_date.year}")
        today = datetime.today().date()
        first = self.view_date.replace(day=1)
        sc = (first.weekday()+1)%7
        last = (first.replace(month=self.view_date.month%12+1,day=1,year=self.view_date.year+(1 if self.view_date.month==12 else 0)) - timedelta(days=1))
        r,c = 0,sc
        for day in range(1, last.day+1):
            d = self.view_date.replace(day=day).date()
            is_sel = (d==self.selected_date.date()); is_today = (d==today)
            btn = QPushButton(str(day)); btn.setFixedSize(34,34); btn.setCursor(Qt.PointingHandCursor)
            if is_sel: s="QPushButton{background:#3d5240;color:white;border:none;border-radius:17px;font-size:10px;font-weight:bold;}"
            elif is_today: s="QPushButton{background:#a8bb96;color:white;border:none;border-radius:17px;font-size:10px;font-weight:bold;}"
            else: s="QPushButton{background:transparent;color:#2d3a2e;border:none;border-radius:17px;font-size:10px;}QPushButton:hover{background:#e8dfc8;}"
            btn.setStyleSheet(s); btn.clicked.connect(lambda _,dt=d: self._pick(dt))
            self.grid.addWidget(btn,r,c); c+=1
            if c==7: c=0; r+=1

    def _pick(self,d):
        self.selected_date=datetime(d.year,d.month,d.day)
        self.date_selected.emit(self.selected_date); self.accept()

    def _prev_month(self):
        y,m=self.view_date.year,self.view_date.month
        self.view_date=self.view_date.replace(year=y-1 if m==1 else y,month=12 if m==1 else m-1,day=1); self._render_calendar()

    def _next_month(self):
        y,m=self.view_date.year,self.view_date.month
        self.view_date=self.view_date.replace(year=y+1 if m==12 else y,month=1 if m==12 else m+1,day=1); self._render_calendar()

    def _go_today(self):
        today=datetime.today(); self.view_date=today.replace(day=1); self.selected_date=today
        self._render_calendar(); self.date_selected.emit(today); self.accept()

class CellDetailPopup(QDialog):
    """A popup displays all food items in the list, with a delete button for each item."""

    def __init__(self, meal_name, foods: list, on_delete, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(220)
        self.setMaximumWidth(260)
        self.on_delete = on_delete
        self._build_ui(meal_name, foods)

    def _build_ui(self, meal_name, foods):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("cdCard")
        card.setStyleSheet("""
            QFrame#cdCard {
                background: #f7f9f5;
                border-radius: 14px;
                border: 1.5px solid #c8d4c4;
            }
        """)
        outer.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        hdr = QLabel(meal_name.upper())
        hdr.setAlignment(Qt.AlignCenter)
        hdr.setFont(QFont("Segoe UI", 9, QFont.Bold))
        hdr.setStyleSheet("""
            color: #5a7a5c;
            background: #e4edde;
            padding: 10px 16px 8px 16px;
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
            letter-spacing: 1px;
            background: #dde8da;
        """)
        lay.addWidget(hdr)
        self._add_divider(lay)

        if not foods:
            empty = QLabel("No food items available.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setFont(QFont("Segoe UI", 10))
            empty.setStyleSheet("color:#aab8ab; padding: 16px; background:transparent;")
            lay.addWidget(empty)
        else:
            for i, food in enumerate(foods):
                row = self._make_food_row(food, i, len(foods))
                lay.addWidget(row)
                if i < len(foods) - 1:
                    self._add_divider(lay)

        self._add_divider(lay)
        close_btn = QPushButton("close")
        close_btn.setFixedHeight(40)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFont(QFont("Segoe UI", 10))
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-bottom-left-radius: 14px;
                border-bottom-right-radius: 14px;
                color: #3d5240;
                font-weight: bold;
            }
            QPushButton:hover { background: #e4edde; }
        """)
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)

    def _add_divider(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background: #d4e0d0; border: none;")
        layout.addWidget(line)

    def _make_food_row(self, food, index, total):
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(row)
        hl.setContentsMargins(14, 0, 8, 0)
        hl.setSpacing(6)

        lbl = QLabel(f"{index+1}.  {food}")
        lbl.setFont(QFont("Segoe UI", 11))
        lbl.setStyleSheet("color: #2d3a2e; background: transparent;")
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        hl.addWidget(lbl)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(26, 26)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setToolTip(f"delete {food}")
        del_btn.setStyleSheet("""
            QPushButton {
                background: rgba(180,60,50,0.10);
                border: none;
                border-radius: 13px;
                color: #b03030;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(180,60,50,0.30);
                color: #8b1a1a;
            }
        """)
        del_btn.clicked.connect(lambda _, f=food: self._delete(f))
        hl.addWidget(del_btn)

        row.setFixedHeight(42)
        return row

    def _delete(self, food):
        self.on_delete(food)
        self.accept()


#FoodList
class FoodList(QListWidget):
    def __init__(self, meal_cell=None):
        super().__init__()
        self.meal_cell = meal_cell
        self.setDragEnabled(True); self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.CopyAction)

    def startDrag(self, actions):
        item = self.currentItem()
        if item:
            d = QDrag(self); m = QMimeData(); m.setText(item.text())
            d.setMimeData(m); d.exec(Qt.CopyAction)

    def dragEnterEvent(self, e): e.accept()
    def dragMoveEvent(self, e): e.accept()

    def dropEvent(self, e):
        text = e.mimeData().text()
        food = text.split(". ", 1)[1] if ". " in text else text
        self.addItem(f"{self.count()+1}. {food}")
        e.accept()
        if self.meal_cell:
            mc = self.meal_cell
            mc.parent_page.meal_data.setdefault(mc.date_key, {}).setdefault(str(mc.row), []).append(food)
            mc.parent_page.update_mood()


#MealCell
class MealCell(QFrame):
    def __init__(self, meal_name, row, col, parent_page, date_key):
        super().__init__()
        self.meal_name = meal_name
        self.row=row; self.col=col; self.parent_page=parent_page; self.date_key=date_key
        self._col_hovered = False
        self.setObjectName(f"cell_{row}_{col}")
        self.setStyleSheet(f"QFrame#cell_{row}_{col}{{background-color:#a8bb96;border-radius:10px;}}")
        lay=QVBoxLayout(self); lay.setContentsMargins(5,5,5,5); lay.setSpacing(3); lay.setAlignment(Qt.AlignCenter)
        self.food_list=FoodList(meal_cell=self); self.food_list.setMaximumHeight(50)
        self.food_list.setStyleSheet("background:transparent;border:none;"); lay.addWidget(self.food_list)
        self.food_list.itemDoubleClicked.connect(self.delete_food)
        self.food_list.itemClicked.connect(self.show_cell_popup)   #คลิกดู popup
        self.add_btn=QPushButton("+"); self.add_btn.setFixedSize(26,26); self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.60);border:none;border-radius:13px;font-size:16px;color:#3d5240;font-weight:bold;}QPushButton:hover{background:rgba(255,255,255,0.90);}")
        lay.addWidget(self.add_btn,alignment=Qt.AlignCenter); self.add_btn.clicked.connect(self.add_food)
        self._load_existing()

    def set_col_hover(self, active: bool):
        if self._col_hovered != active:
            self._col_hovered = active
            self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._col_hovered:
            p = QPainter(self)
            p.setBrush(QColor(255, 255, 255, 35))
            p.setPen(QColor(80, 120, 70, 140))
            r = self.rect().adjusted(1, 1, -1, -1)
            p.drawRoundedRect(r, 10, 10)
            p.end()

    def _get_foods(self):
        return list(self.parent_page.meal_data.get(self.date_key, {}).get(str(self.row), []))

    def _load_existing(self):
        for food in self._get_foods():
            self.food_list.addItem(f"{self.food_list.count()+1}. {food}")
    def add_food(self):
        dialog = QDialog()        
        dialog.setWindowTitle("Add Food")
        dialog.setFixedSize(300, 150)

        label = QLabel("Food name:")
        input_field = QLineEdit()
        input_field.setPlaceholderText("Enter food name")
        self.parent_page.meal_data.setdefault(self.date_key, {})
        self.parent_page.meal_data_changed.emit(
            self.date_key,
            self.parent_page.meal_data.get(self.date_key, {})
        )

        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(input_field)
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 14px;
                color: #2d3a2e;
                background-color: #f5f5f5;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #b0b8b0;
                border-radius: 4px;
                background-color: #ffffff;
                color: #1a2b1b;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1.5px solid #a8bb96;
            }
            QPushButton {
                min-width: 70px;
                padding: 5px 12px;
                border-radius: 6px;
                background-color: #a8bb96;
                color: #ffffff;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8faa7a;
            }
            QPushButton:pressed {
                background-color: #3d5240;
            }
        """)

        def on_ok():
            text = input_field.text().strip()
            if text:
                self.food_list.addItem(f"{self.food_list.count()+1}. {text}")
                self.parent_page.meal_data.setdefault(self.date_key, {}) \
                    .setdefault(str(self.row), []).append(text)
                self.parent_page.update_mood()
                dialog.accept()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec_()
    
    def delete_food(self, item):
        name=item.text().split(". ",1)[1]
        foods=self.parent_page.meal_data.get(self.date_key,{}).get(str(self.row),[])
        if name in foods: foods.remove(name)
        self.food_list.takeItem(self.food_list.row(item))
        for i in range(self.food_list.count()):
            old=self.food_list.item(i).text(); n=old.split(". ",1)[1] if ". " in old else old
            self.food_list.item(i).setText(f"{i+1}. {n}")
        self.parent_page.update_mood()
        self.parent_page.meal_data_changed.emit(
            self.date_key,
            self.parent_page.meal_data.get(self.date_key, {})
        )

    def _delete_by_name(self, food_name):
        """Delete from the data and the list widget by name."""
        foods = self.parent_page.meal_data.get(self.date_key, {}).get(str(self.row), [])
        if food_name in foods:
            foods.remove(food_name)
        # ลบออกจาก QListWidget
        for i in range(self.food_list.count()):
            txt = self.food_list.item(i).text()
            name = txt.split(". ", 1)[1] if ". " in txt else txt
            if name == food_name:
                self.food_list.takeItem(i)
                break
        # renumber
        for i in range(self.food_list.count()):
            old = self.food_list.item(i).text()
            n = old.split(". ", 1)[1] if ". " in old else old
            self.food_list.item(i).setText(f"{i+1}. {n}")
        self.parent_page.update_mood()
        self.parent_page.meal_data_changed.emit(
            self.date_key,
            self.parent_page.meal_data[self.date_key]
        )

    def show_cell_popup(self, item):
        """Click an item to open a popup showing all food items in this section."""
        foods = self._get_foods()
        popup = CellDetailPopup(
            meal_name=self.meal_name,
            foods=foods,
            on_delete=self._delete_by_name,
        )

        rect = self.food_list.visualItemRect(item)
        gpos = self.food_list.mapToGlobal(rect.bottomLeft())
        popup.move(gpos.x(), gpos.y() + 4)
        popup.exec()


#ClickableHeader
class ClickableHeader(QHeaderView):
    col_hovered = Signal(int)

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setSectionsClickable(True)
        self._hovered_col = -1

    def mouseMoveEvent(self, e):
        col = self.logicalIndexAt(e.pos())
        if col != self._hovered_col:
            self._hovered_col = col
            self.update()
            self.col_hovered.emit(col if col > 0 else -1)
        cur = Qt.PointingHandCursor if col > 0 else Qt.ArrowCursor
        self.setCursor(cur); self.viewport().setCursor(cur)
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        if self._hovered_col != -1:
            self._hovered_col = -1
            self.update()
            self.col_hovered.emit(-1)
        self.setCursor(Qt.ArrowCursor); self.viewport().setCursor(Qt.ArrowCursor)
        super().leaveEvent(e)

    def paintSection(self, painter, rect, logical_index):
        super().paintSection(painter, rect, logical_index)
        if logical_index > 0 and logical_index == self._hovered_col:
            painter.save()
            painter.fillRect(rect, QColor(61, 82, 64, 55))
            pen = QPen(QColor(61, 82, 64, 200)); pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
            painter.restore()

#MealLabelCell
class MealLabelCell(QWidget):
    def __init__(self, icon, name):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 0, 4, 0)
        lay.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        lbl = QLabel(f"{icon}  {name.upper()}")
        lbl.setFont(QFont("Segoe UI", 8, QFont.Bold))
        lbl.setStyleSheet("color: #5a6e5b; background: transparent; letter-spacing: 0.4px;")
        lbl.setWordWrap(False)
        lay.addWidget(lbl)


#MealPlannerPage
class MealPlannerPage(QWidget):
    meal_data_changed = Signal(str, object) 
    jump_to_week_day = Signal(str)
    day_selected = Signal(str)
    date_picked = Signal(str)

    go_to_mood  = Signal()
    go_to_daily = Signal(str) 

    def __init__(self):
        super().__init__()
        self.current_date = datetime.today()
        self.meal_types = ["Breakfast","Lunch","Dinner","Night","Snack","Note"]
        self.meal_icons = {"Breakfast":"☀","Lunch":"≡","Dinner":"⊟","Night":"☽","Snack":"◎","Note":"☐"}
        self.meal_data = defaultdict(dict)
        self.setStyleSheet("""
            MealPlannerPage { background: #f0f2ec; }
            QTableWidget {
                background: white; border: 1px solid #dce0d8;
                border-radius: 14px; outline: none;
            }
            QTableWidget::item { background: transparent; padding: 4px; }
            QHeaderView { background: #e8dfc8; }
            QHeaderView::section:horizontal {
                background: #e8dfc8; border: none;
                border-bottom: 1px solid #dce0d8;
                padding: 6px 4px; font-weight: bold; font-size: 11px; color: #1a2b1b;
            }
            QHeaderView::section:horizontal:first {
                color: #5a6e5b; font-size: 9px; letter-spacing: 0.6px;
                border-right: 1px solid #dce0d8;
            }
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item {
                background: rgba(255,255,255,0.75); border: none;
                border-radius: 6px; padding: 2px 5px; margin: 1px;
                color: #2d3a2e; font-size: 10px;
            }
            QListWidget::item:hover { background: rgba(255,255,255,0.95); }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28,20,28,16)
        main_layout.setSpacing(10)

        hdr=QHBoxLayout(); tc=QVBoxLayout(); tc.setSpacing(2)
        t=QLabel("Weekly Meals Overview"); t.setFont(QFont("Segoe UI",17,QFont.Bold))
        t.setStyleSheet("color:#1a2b1b;background:transparent;")
        s=QLabel("Manage your nutrition and track your daily habits.")
        s.setFont(QFont("Segoe UI",10)); s.setStyleSheet("color:#8a9e8b;background:transparent;")
        tc.addWidget(t); tc.addWidget(s); hdr.addLayout(tc); hdr.addStretch()
        self.mood_label=QPushButton("😊"); self.mood_label.setFont(QFont("Segoe UI Emoji",26))
        self.mood_label.setFixedSize(48,48); self.mood_label.setCursor(Qt.PointingHandCursor)
        self.mood_label.setToolTip("View Weekly Mood")
        self.mood_label.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:24px;}"
            "QPushButton:hover{background:rgba(168,187,150,0.25);}"
        )
        self.mood_label.clicked.connect(self._handle_mood_click)
        hdr.addWidget(self.mood_label)
        main_layout.addLayout(hdr)

        wl=QHBoxLayout()
        nav_s="QPushButton{background:white;border:1px solid #d0d5cc;border-radius:8px;font-size:11px;color:#4a5e4b;}QPushButton:hover{background:#eef2ec;}"
        self.prev_btn=QPushButton("❮"); self.prev_btn.setFixedSize(30,30)
        self.prev_btn.setCursor(Qt.PointingHandCursor); self.prev_btn.setStyleSheet(nav_s)
        self.prev_btn.clicked.connect(self.prev_week)
        self.week_btn=QPushButton(); self.week_btn.setFont(QFont("Segoe UI",11))
        self.week_btn.setCursor(Qt.PointingHandCursor); self.week_btn.setMinimumWidth(200); self.week_btn.setFixedHeight(30)
        self.week_btn.setStyleSheet("QPushButton{color:#2d3a2e;padding:4px 14px;background:white;border:1px solid #d0d5cc;border-radius:8px;}QPushButton:hover{background:#f0f5ee;border-color:#a8bb96;}")
        self.week_btn.setToolTip("📅 Click to jump to a specific date")
        self.week_btn.clicked.connect(self.open_calendar)
        self.next_btn=QPushButton("❯"); self.next_btn.setFixedSize(30,30)
        self.next_btn.setCursor(Qt.PointingHandCursor); self.next_btn.setStyleSheet(nav_s)
        self.next_btn.clicked.connect(self.next_week)
        wl.addStretch(); wl.addWidget(self.prev_btn); wl.addWidget(self.week_btn)
        wl.addWidget(self.next_btn); wl.addStretch()
        main_layout.addLayout(wl)

        self.table = QTableWidget()
        self.table.setRowCount(len(self.meal_types))
        self.table.setColumnCount(8)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        clickable_hdr = ClickableHeader(Qt.Horizontal, self.table)
        clickable_hdr.setSectionResizeMode(QHeaderView.Stretch)
        clickable_hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        clickable_hdr.sectionClicked.connect(self._on_header_clicked)
        clickable_hdr.col_hovered.connect(self._on_col_hovered)
        self.table.setHorizontalHeader(clickable_hdr)
        self.table.setColumnWidth(0, 110)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table, stretch=1)
        self.update_week()

    def _on_header_clicked(self, col_index):
        if col_index == 0: return
        dks = self.get_week_date_keys()
        date_str = dks[col_index - 1]
        self.go_to_daily.emit(date_str)
        self.jump_to_week_day.emit(date_str)

    def open_calendar(self):
        cal=CalendarDialog(self.current_date,self)
        cal.date_selected.connect(self._on_date_picked)
        pos=self.week_btn.mapToGlobal(self.week_btn.rect().bottomLeft())
        cal.move(pos.x(),pos.y()+4); cal.exec()

    def _on_date_picked(self, dt):
        self.current_date = dt
        self.update_week()

        date_str = dt.strftime("%Y-%m-%d")

        self.date_picked.emit(date_str)

    def get_start_of_week(self,date):
        return date - timedelta(days=(date.weekday()+1)%7)

    def get_week_date_keys(self):
        start=self.get_start_of_week(self.current_date)
        return [(start+timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    def _handle_mood_click(self):
        date_str = self.current_date.strftime("%Y-%m-%d")

        self.go_to_mood.emit()   
        self.jump_to_week_day.emit(date_str)

    def update_week(self):
        start=self.get_start_of_week(self.current_date)
        headers=["PERIOD"] + [(start+timedelta(days=i)).strftime("%a\n%d %b") for i in range(7)]
        self.table.setHorizontalHeaderLabels(headers)
        end=start+timedelta(days=6)
        self.week_btn.setText(f"📅  {start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}")
        self.setup_cells(); self.update_mood()

    def setup_cells(self):
        dks=self.get_week_date_keys()
        self._meal_cells: dict = {c: [] for c in range(1, 8)}
        for row,meal in enumerate(self.meal_types):
            label_cell=MealLabelCell(self.meal_icons[meal], meal)
            self.table.setCellWidget(row, 0, label_cell)
            for col in range(7):
                cell = MealCell(meal, row, col, self, dks[col])
                self.table.setCellWidget(row, col+1, cell)
                self._meal_cells[col+1].append(cell)

    def _on_col_hovered(self, col: int):
        for c, cells in self._meal_cells.items():
            for cell in cells:
                cell.set_col_hover(c == col)

    def prev_week(self):
        self.current_date-=timedelta(weeks=1); self.update_week()
    def next_week(self):
        self.current_date+=timedelta(weeks=1); self.update_week()

    def calculate_mood(self):
        dks=self.get_week_date_keys()
        snack_row=self.meal_types.index("Snack")
        snack_count=0; breakfast_skipped=False; balanced=0
        for dk in dks:
            d=self.meal_data.get(dk,{})
            b=bool(d.get(str(self.meal_types.index("Breakfast"))))
            l=bool(d.get(str(self.meal_types.index("Lunch"))))
            dn=bool(d.get(str(self.meal_types.index("Dinner"))))
            snack_count+=len(d.get(str(snack_row),[]))
            if not b: breakfast_skipped=True
            if b and l and dn: balanced+=1
        if snack_count>5: return "stress"
        if breakfast_skipped: return "low"
        if balanced>=4: return "excellent"
        return "normal"

    def update_mood(self):
        emoji = {"excellent":"😍","normal":"😊","low":"☺️","stress":"😃"}.get(self.calculate_mood(),"😊")
        self.mood_label.setText(emoji)

    def select_day(self, date_str: str):
        from datetime import datetime

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        self.current_date = dt
        self.update_week()

        meals_for_day = self.meal_data.get(date_str, {})
        self.meal_data_changed.emit(date_str, meals_for_day)

    def select_day(self, date_str: str):
        """
        Highlight / jump to a specific date in the weekly view
        and sync current_date properly.
        """
        dt = datetime.strptime(date_str, "%Y-%m-%d")

        self.current_date = dt

        self.update_week()
        week_keys = self.get_week_date_keys()

        if date_str in week_keys:
            col_index = week_keys.index(date_str) + 1  
            self._on_col_hovered(col_index)

    def set_meal_data(self, meal_data):
        self.meal_data = meal_data
        self.update_week()


if __name__=="__main__":
    app=QApplication(sys.argv)
    app.setFont(QFont("Segoe UI",10))
    app.setStyleSheet("""
        QWidget { background: #f0f2ec; }
        QTableWidget {
            background: white; border: 1px solid #dce0d8;
            border-radius: 14px; outline: none;
        }
        QTableWidget::item { background: transparent; padding: 4px; }
        QHeaderView { background: #e8dfc8; }
        QHeaderView::section:horizontal {
            background: #e8dfc8; border: none;
            border-bottom: 1px solid #dce0d8;
            padding: 6px 4px; font-weight: bold; font-size: 11px; color: #1a2b1b;
        }
        QHeaderView::section:horizontal:first {
            color: #5a6e5b; font-size: 9px; letter-spacing: 0.6px;
            border-right: 1px solid #dce0d8;
        }
        QListWidget { background: transparent; border: none; outline: none; }
        QListWidget::item {
            background: rgba(255,255,255,0.75); border: none;
            border-radius: 6px; padding: 2px 5px; margin: 1px;
            color: #2d3a2e; font-size: 10px;
        }
        QListWidget::item:hover { background: rgba(255,255,255,0.95); }
    """)
    w=MealPlannerPage()
    w.setWindowTitle("Savorly – Weekly Meals")
    w.resize(1200,700)
    w.show()
    sys.exit(app.exec())
