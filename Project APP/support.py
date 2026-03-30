from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,QHBoxLayout, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys

class SupportPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("contentArea")
        self.setStyleSheet("QWidget#contentArea { background: #f0f2ec; }")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(0)

        title = QLabel("Support Section")
        title.setFont(QFont("Segoe UI", 17, QFont.Bold))
        title.setStyleSheet("color: #1a2b1b; background: transparent;")
        outer.addWidget(title)
        outer.addSpacing(20)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #d0d8cc;
                border-radius: 14px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 22, 28, 22)

        # Card title
        card_title = QLabel("Contact Support")
        card_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        card_title.setStyleSheet("color: #1a2b1b; background: transparent; border: none;")
        card_layout.addWidget(card_title)
        card_layout.addSpacing(16)

        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.HLine)
        div1.setFixedHeight(1)
        div1.setStyleSheet("background: #e4e8e0; border: none;")
        card_layout.addWidget(div1)
        card_layout.addSpacing(16)

        # Email row
        email_row = QHBoxLayout()
        email_row.setSpacing(14)

        email_icon = QLabel("📧")
        email_icon.setFixedSize(36, 36)
        email_icon.setAlignment(Qt.AlignCenter)
        email_icon.setFont(QFont("Segoe UI Emoji", 16))
        email_icon.setStyleSheet("background: transparent; border: none;")

        email_text = QVBoxLayout()
        email_text.setSpacing(1)
        email_label = QLabel("Email Us")
        email_label.setFont(QFont("Segoe UI", 9))
        email_label.setStyleSheet("color: #8a9e8b; background: transparent; border: none;")
        email_value = QLabel("support@savorly.com")
        email_value.setFont(QFont("Segoe UI", 11))
        email_value.setStyleSheet("color: #4a7fa5; background: transparent; border: none;")
        email_text.addWidget(email_label)
        email_text.addWidget(email_value)

        email_row.addWidget(email_icon)
        email_row.addLayout(email_text)
        email_row.addStretch()
        card_layout.addLayout(email_row)
        card_layout.addSpacing(14)

        # Divider
        div2 = QFrame()
        div2.setFrameShape(QFrame.HLine)
        div2.setFixedHeight(1)
        div2.setStyleSheet("background: #e4e8e0; border: none;")
        card_layout.addWidget(div2)
        card_layout.addSpacing(14)

        # Phone row
        phone_row = QHBoxLayout()
        phone_row.setSpacing(14)

        phone_icon = QLabel("📞")
        phone_icon.setFixedSize(36, 36)
        phone_icon.setAlignment(Qt.AlignCenter)
        phone_icon.setFont(QFont("Segoe UI Emoji", 16))
        phone_icon.setStyleSheet("background: transparent; border: none;")

        phone_text = QVBoxLayout()
        phone_text.setSpacing(1)
        phone_label = QLabel("Call Us")
        phone_label.setFont(QFont("Segoe UI", 9))
        phone_label.setStyleSheet("color: #8a9e8b; background: transparent; border: none;")
        phone_value = QLabel("06x-xxxx-xxxx")
        phone_value.setFont(QFont("Segoe UI", 11))
        phone_value.setStyleSheet("color: #1a2b1b; background: transparent; border: none;")
        phone_text.addWidget(phone_label)
        phone_text.addWidget(phone_value)

        phone_row.addWidget(phone_icon)
        phone_row.addLayout(phone_text)
        phone_row.addStretch()
        card_layout.addLayout(phone_row)

        outer.addWidget(card)
        outer.addStretch()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = SupportPage()
    window.setWindowTitle("Savorly - Support")
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()