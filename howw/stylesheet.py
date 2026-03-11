# Palette
bg          = "#F0EDE6"   # page background
sidebar_bg  = "#FFFFFF"
white       = "#FFFFFF"
card_bg     = "#E8E3D9"   # card
green       = "#6E8F5E"   # active nav, button
light_green = "#A8BF98"
dark_green  = "#4A6741"
brown       = "#C8BFA8"
brown_bg    = "#E8E3D9"
text        = "#1A1A1A"
text_muted  = "#888880"
tdee        = "#8B6914"
protein     = "#5B9BD5"
carbs       = "#E8A838"
fats        = "#E8C838"
mineral     = "#9B5FD4"
fiber       = "#E84FA0"
radius_sm   = 8
radius_md   = 12
radius_lg   = 16
radius_xl   = 20

app_global = f"""
    QWidget {{
        font-family: 'Inria Serif', Inter;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        border: none; background: transparent;
        width: 5px; border-radius: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #c0bdb5; border-radius: 2px; min-height: 20px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{ height: 0px; }}
"""

mainwindow = f"background-color: {bg};"
page_bg = f"background-color: {bg};"

sidebar = f"background-color: {sidebar_bg}; border-right: 1px solid rgba(0,0,0,0.06);"
sidebar_app_name = f"font-size: 18px; font-weight: 800; color: {text}; background:transparent;"
sidebar_app_subtitle = f"font-size: 11px; color: {text_muted}; background:transparent;"
sidebar_avatar = f"background: {light_green}; border-radius: 18px; font-size: 16px;"
sidebar_username = f"font-size: 13px; font-weight: 600; color: {text}; background:transparent;"

white_card = f"background: {white}; border-radius: {radius_xl}px; border: 1px solid rgba(0,0,0,0.06);"
brown_card = f"background: {card_bg}; border-radius: {radius_xl}px;"
cream_card = f"background: {card_bg}; border-radius: {radius_xl}px;"

section = f"font-size: 16px; font-weight: 700; color: {text}; background: transparent;"
page_title = f"font-size: 24px; font-weight: 800; color: {text}; background:transparent;"
page_subtitle = f"font-size: 13px; color: {text_muted}; background:transparent;"
label = f"font-size: 12px; color: {text_muted}; background: transparent;"

line_edit = f"""
    QLineEdit {{
        background-color: {white};
        border: 1.5px solid rgba(180,170,155,0.5);
        border-radius: {radius_md}px;
        padding: 10px 14px;
        font-size: 13px;
        color: {text};
    }}
    QLineEdit:focus {{
        border: 1.5px solid {green};
        background-color: {white};
    }}
"""

inner_transparent = "background: transparent;"
scroll_transparent = "QScrollArea { border: none; background: transparent; }"

bell_icon = f"background: {white}; border-radius: 10px; font-size: 16px; border: 1px solid rgba(0,0,0,0.08);"
avatar_icon = f"background: {light_green}; border-radius: 20px;"

# Dynamic styles
def nav_btn(active: bool) -> str:
    if active:
        return f"""
            QPushButton {{
                background-color: {green}; color: white; border: none;
                border-radius: {radius_md}px; padding: 10px 16px;
                font-size: 14px; font-weight: 600; text-align: left;
            }}"""
    return f"""
        QPushButton {{
            background-color: transparent; color: {text}; border: none;
            border-radius: {radius_md}px; padding: 10px 16px;
            font-size: 14px; font-weight: 400; text-align: left;
        }}
        QPushButton:hover {{ background-color: rgba(0,0,0,0.04); }}"""

def btn_primary(bg=green, fg=white, hover=dark_green,
                radius=radius_md, padding="10px 20px", font_size=13) -> str:
    return f"""
        QPushButton {{
            background-color: {bg}; color: {fg}; border: none;
            border-radius: {radius}px; padding: {padding};
            font-size: {font_size}px; font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {dark_green}; }}"""

def btn_toolbar(bg: str, hover: str) -> str:
    return f"""
        QPushButton {{
            background: {bg}; color: white; border: none;
            border-radius: {radius_sm}px; padding: 6px 14px;
            font-size: 12px; font-weight: 600;
        }}
        QPushButton:hover {{ background: {hover}; }}"""