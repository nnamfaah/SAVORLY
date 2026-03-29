import sys
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QInputDialog,
    QDialog, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QMimeData, Signal, QDate
from PySide6.QtGui import QFont, QDrag, QColor

#  Calendar Popup Dialog
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

class DetailPopup(QDialog):
    def __init__(self, food):
        super().__init__(); self.setWindowTitle("Food Detail"); self.setFixedSize(200,110)
        l=QVBoxLayout(self); t=QLabel(food); t.setFont(QFont("Segoe UI",13))
        t.setAlignment(Qt.AlignCenter); l.addWidget(t)

class FoodList(QListWidget):
    def __init__(self, meal_cell=None):
        super().__init__()
        self.meal_cell = meal_cell  # ref กลับ MealCell เพื่อบันทึก meal_data
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
        # บันทึกลง meal_data
        if self.meal_cell:
            mc = self.meal_cell
            mc.parent_page.meal_data.setdefault(mc.date_key, {}).setdefault(str(mc.row), []).append(food)
            mc.parent_page.update_mood()

class MealCell(QFrame):
    def __init__(self, meal_name, row, col, parent_page, date_key):
        super().__init__()
        self.row=row; self.col=col; self.parent_page=parent_page; self.date_key=date_key
        self.setObjectName(f"cell_{row}_{col}")
        self.setStyleSheet(f"QFrame#cell_{row}_{col}{{background-color:#a8bb96;border-radius:10px;}}")
        lay=QVBoxLayout(self); lay.setContentsMargins(5,5,5,5); lay.setSpacing(3); lay.setAlignment(Qt.AlignCenter)
        self.food_list=FoodList(meal_cell=self); self.food_list.setMaximumHeight(50)
        self.food_list.setStyleSheet("background:transparent;border:none;"); lay.addWidget(self.food_list)
        self.food_list.itemDoubleClicked.connect(self.delete_food)
        self.food_list.itemClicked.connect(self.show_detail)
        self.add_btn=QPushButton("+"); self.add_btn.setFixedSize(26,26); self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.60);border:none;border-radius:13px;font-size:16px;color:#3d5240;font-weight:bold;}QPushButton:hover{background:rgba(255,255,255,0.90);}")
        lay.addWidget(self.add_btn,alignment=Qt.AlignCenter); self.add_btn.clicked.connect(self.add_food)
        self._load_existing()

    def _load_existing(self):
        for food in self.parent_page.meal_data.get(self.date_key,{}).get(str(self.row),[]):
            self.food_list.addItem(f"{self.food_list.count()+1}. {food}")
    
    def add_food(self):
        text,ok=QInputDialog.getText(self,"Add Food","Food name:")
        if ok and text.strip():
            self.food_list.addItem(f"{self.food_list.count()+1}. {text.strip()}")
            self.parent_page.meal_data.setdefault(self.date_key,{}).setdefault(str(self.row),[]).append(text.strip())
            self.parent_page.update_mood()
    
    def delete_food(self,item):
        name=item.text().split(". ",1)[1]
        foods=self.parent_page.meal_data.get(self.date_key,{}).get(str(self.row),[])
        if name in foods: foods.remove(name)
        self.food_list.takeItem(self.food_list.row(item))
        for i in range(self.food_list.count()):
            old=self.food_list.item(i).text(); n=old.split(". ",1)[1] if ". " in old else old
            self.food_list.item(i).setText(f"{i+1}. {n}")
        self.parent_page.update_mood()
    
    def show_detail(self,item):
        DetailPopup(item.text().split(". ",1)[1]).exec()

#  Meal Label Cell (column 0) — แสดง icon + meal name
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

#  Main Page
class MealPlannerPage(QWidget):
    go_to_mood = Signal()
    go_to_daily = Signal(QDate)
    def __init__(self):
        super().__init__()
        self.current_date = datetime.today()
        self.meal_types = ["Breakfast","Lunch","Dinner","Night","Snack","Note"]
        self.meal_icons = {"Breakfast":"☀","Lunch":"≡","Dinner":"⊟","Night":"☽","Snack":"◎","Note":"☐"}
        self.meal_data = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28,20,28,16)
        main_layout.setSpacing(10)

        #Header
        hdr=QHBoxLayout(); tc=QVBoxLayout(); tc.setSpacing(2)
        t=QLabel("Weekly Meals Overview"); t.setFont(QFont("Segoe UI",17,QFont.Bold))
        t.setStyleSheet("color:#1a2b1b;background:transparent;")
        s=QLabel("Manage your nutrition and track your daily habits.")
        s.setFont(QFont("Segoe UI",10)); s.setStyleSheet("color:#8a9e8b;background:transparent;")
        tc.addWidget(t); tc.addWidget(s); hdr.addLayout(tc); hdr.addStretch()
        self.mood_label=QLabel("😊"); self.mood_label.setFont(QFont("Segoe UI Emoji",26))
        self.mood_label.setStyleSheet("background:transparent;"); hdr.addWidget(self.mood_label)
        main_layout.addLayout(hdr)

        #Week Nav 
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

        # ── Table ──
        # column 0 = meal label, columns 1-7 = days
        self.table = QTableWidget()
        self.table.setRowCount(len(self.meal_types))
        self.table.setColumnCount(8)   # col0=PERIOD label + 7 days
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # ซ่อน vertical header
        self.table.verticalHeader().setVisible(False)

        # horizontal header: col0="PERIOD", col1-7=วัน
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 110)

        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # click header to daily meals
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        main_layout.addWidget(self.table, stretch=1)
        self.update_week()

 
    def _on_header_clicked(self, col_index):
        """click header date (col 1-7) → emit go_to_daily"""
        if col_index == 0:
            return
        dks = self.get_week_date_keys()
        date_str = dks[col_index - 1]
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        qdate = QDate(dt.year, dt.month, dt.day)
        self.go_to_daily.emit(qdate)

    # Calendar
    def open_calendar(self):
        cal=CalendarDialog(self.current_date,self)
        cal.date_selected.connect(self._on_date_picked)
        pos=self.week_btn.mapToGlobal(self.week_btn.rect().bottomLeft())
        cal.move(pos.x(),pos.y()+4); cal.exec()

    def _on_date_picked(self,dt):
        self.current_date=dt; self.update_week()

    #Week 
    def get_start_of_week(self,date):
        return date - timedelta(days=(date.weekday()+1)%7)

    def get_week_date_keys(self):
        start=self.get_start_of_week(self.current_date)
        return [(start+timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    def update_week(self):
        start=self.get_start_of_week(self.current_date)

        headers=["PERIOD"] + [(start+timedelta(days=i)).strftime("%a\n%d %b") for i in range(7)]
        self.table.setHorizontalHeaderLabels(headers)
        end=start+timedelta(days=6)
        self.week_btn.setText(f"📅  {start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}")
        self.setup_cells(); self.update_mood()

    def setup_cells(self):
        dks=self.get_week_date_keys()
        for row,meal in enumerate(self.meal_types):

            label_cell=MealLabelCell(self.meal_icons[meal], meal)
            self.table.setCellWidget(row, 0, label_cell)

            for col in range(7):
                self.table.setCellWidget(row, col+1,
                    MealCell(meal, row, col, self, dks[col]))

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
        self.mood_label.setText({"excellent":"😍","normal":"😊","low":"☺️","stress":"😃"}.get(self.calculate_mood(),"😊"))

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
