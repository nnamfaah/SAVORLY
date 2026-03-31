STYLESHEET = """
* {
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

/* App Name (override font) */
QLabel#appName 

QMainWindow {
    background-color: #F6F7F5;
}

QWidget#centralWidget {
    background-color: #F6F7F5;
}

/* ── Sidebar ── */
QWidget#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #D6D9D3;
}

QLabel#appSubtitle {
    font-size: 13px;
    color: #6B7280;
}

QWidget#logoIcon {
    background-color: #DCE5D3;
    border-radius: 12px;
}

/* Menu Buttons */
QPushButton#menuBtn {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    height: 48px;
    text-align: left;
    padding-left: 14px;
    font-size: 14px;
    color: #1F2A24;
}

QPushButton#menuBtn:hover {
    background-color: #F0F3ED;
}

QPushButton#menuBtnActive {
    background-color: #8FA27A;
    border: none;
    border-radius: 10px;
    height: 48px;
    text-align: left;
    padding-left: 14px;
    font-size: 14px;
    color: #FFFFFF;
    font-weight: bold;
}

/* ── Content Area ── */
QWidget#contentArea {
    background-color: #F6F7F5;
}

QLabel#pageTitle {
    font-size: 24px;
    font-weight: bold;
    color: #1F2A24;
}

QLabel#pageSubtitle {
    font-size: 14px;
    color: #6B7280;
}

QLabel#fieldLabel {
    font-size: 13px;
    font-weight: 600;
    color: #1F2A24;
}

/* ── Inputs ── */
QLineEdit {
    height: 44px;
    border: 1px solid #D1D5DB;
    border-radius: 10px;
    padding: 0px 12px;
    font-size: 14px;
    color: #1F2A24;
    background-color: #FFFFFF;
}

QLineEdit:focus {
    border: 1.5px solid #8FA27A;
}

QComboBox {
    height: 44px;
    border: 1px solid #D1D5DB;
    border-radius: 10px;
    padding: 0px 12px;
    font-size: 14px;
    color: #1F2A24;
    background-color: #FFFFFF;
}

QComboBox:focus {
    border: 1.5px solid #8FA27A;
}

/* Buttons */
QPushButton#primaryBtn {
    background-color: #8FA27A;
    color: #FFFFFF;
    border-radius: 10px;
    height: 44px;
}

QPushButton#primaryBtn:hover {
    background-color: #7D9168;
}

QPushButton#secondaryBtn {
    background-color: #FFFFFF;
    border: 1px solid #C7C7C7;
    border-radius: 10px;
    height: 40px;
}

/* Result Card */
QWidget#resultCard {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
}

/* Avatar */
QLabel#avatarLabel {
    border-radius: 18px;
    background-color: #DCE5D3;
}
"""