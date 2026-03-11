import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
import stylesheet as ss
from mainwindow import MainWindow

app = QApplication(sys.argv)
app.setFont(QFont("Inria Serif", 10))
app.setStyleSheet(ss.app_global)

MainWindow().show()
sys.exit(app.exec())