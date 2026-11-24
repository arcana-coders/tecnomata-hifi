"""Paleta de colores y hojas de estilo retro Sony Hi-Fi 80s/90s y Apple Design."""

# ═══════════════════════════════════════════
#  Paleta — minicomponente Sony CFD / MHC / LBT
# ═══════════════════════════════════════════

# Chasis (cuerpo robusto de plástico moldeado oscuro / titanio)
CHASSIS_DARK   = "#0b0c10"
CHASSIS_MID    = "#15161f"
CHASSIS_LIGHT  = "#202330"
CHASSIS_BORDER = "#35394a"
METAL_TRIM     = "#464a5c"
BEVEL_HIGHLIGHT= "#545970"

# Display VFD (Vacuum Fluorescent Display)
VFD_BG     = "#020704"
VFD_CYAN   = "#00ffd5"
VFD_GREEN  = "#00ff66"
VFD_ORANGE = "#ff9900"
VFD_RED    = "#ff3344"
VFD_BLUE   = "#00ccff"
VFD_DIM    = "#003b29"

# Acentos Sony 90s
ACCENT      = "#ff9900"
ACCENT_CYAN = "#00ffd5"
ACCENT_GLOW = "rgba(0, 255, 213, 0.4)"

# Texto serigrafiado
TEXT_DIM   = "#5c6072"
TEXT_MID   = "#8e94a8"
TEXT_LIGHT = "#c2c7d8"
TEXT_WHITE = "#f0f2f8"

# ═══════════════════════════════════════════
#  Tipografía
# ═══════════════════════════════════════════
FONT_VFD      = "Consolas"
FONT_VFD_SIZE = 12
FONT_UI       = "Segoe UI"
FONT_UI_SIZE  = 10
FONT_LYRICS   = "Segoe UI"

# ═══════════════════════════════════════════
#  Dimensiones base (chasis robusto con más aire y presencia física)
# ═══════════════════════════════════════════
BAR_HEIGHT   = 76
BAR_RADIUS   = 10


def bar_qss() -> str:
    """Estilo para la barra principal Hi-Fi de chasis plástico moldeado / titanio robusto."""
    return f"""
    QWidget#hifi-bar {{
        background: qlineargradient(x1:0,y1:0, x2:0,y2:1,
            stop:0 #323646, stop:0.02 #262936, stop:0.08 #1c1e28, stop:0.5 #14151e, stop:0.95 #0d0e14, stop:1 #06070a);
        border: 2px solid #3c4154;
        border-radius: {BAR_RADIUS}px;
    }}
    QSlider::groove:horizontal {{
        border: 1px solid #0d0f15;
        height: 6px;
        background: #06070a;
        border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0,y1:0, x2:1,y2:0,
            stop:0 #00aa88, stop:0.8 #00ffd5, stop:1 #80ffee);
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 #50566b, stop:0.35 #3a3e4e, stop:0.5 #2a2d3a, stop:1 #1c1d26);
        border: 1px solid #101218;
        width: 12px;
        height: 22px;
        margin: -8px 0;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal:hover {{
        border-color: #00ffd5;
    }}
    QLabel#vol-label {{
        color: #72788e;
        font-family: "{FONT_VFD}";
        font-size: 8px;
        font-weight: bold;
        letter-spacing: 0.5px;
    }}
    """


def expanded_qss() -> str:
    """Estilo para el panel expandido estilo módulo deck de casete / CD Sony."""
    return f"""
    QWidget#expanded-panel {{
        background: qlineargradient(x1:0,y1:0, x2:0,y2:1,
            stop:0 #222532, stop:0.05 #1a1b24, stop:0.95 #101118, stop:1 #08090d);
        border: 2px solid #3c4154;
        border-radius: {BAR_RADIUS}px;
    }}
    QListWidget {{
        background: {VFD_BG};
        color: #66e6b8;
        border: 1px solid #0d1712;
        font-family: "{FONT_VFD}";
        font-size: 11px;
        outline: 0;
    }}
    QListWidget::item {{
        padding: 5px 8px;
        border-bottom: 1px solid #06140e;
    }}
    QListWidget::item:hover {{
        background: #081c14;
        color: #00ffd5;
    }}
    QListWidget::item:selected {{
        background: #0a291d;
        color: #00ffd5;
        border-left: 3px solid #00ffd5;
    }}
    QComboBox {{
        background: #191b24;
        color: #00ffd5;
        border: 1px solid #2e3242;
        border-radius: 3px;
        padding: 4px 8px;
        font-family: "{FONT_VFD}";
        font-size: 11px;
        min-height: 24px;
    }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox QAbstractItemView {{
        background: #101117;
        color: #66e6b8;
        selection-background-color: #0a291d;
        selection-color: #00ffd5;
        border: 1px solid #2e3242;
    }}
    QLineEdit#search-input {{
        background: {VFD_BG};
        color: #00ffd5;
        border: 1px solid #0d1712;
        border-radius: 3px;
        padding: 4px 8px;
        font-family: "{FONT_VFD}";
        font-size: 11px;
    }}
    QLineEdit#search-input:focus {{
        border-color: #00ffd5;
    }}
    QPushButton.search-action {{
        background: #1c1e28;
        color: #a4aabf;
        border: 1px solid #323648;
        border-radius: 3px;
        padding: 3px 8px;
        font-family: "{FONT_VFD}";
        font-size: 10px;
    }}
    QPushButton.search-action:hover {{
        border-color: #00ffd5;
        color: #ffffff;
    }}
    QSlider#progress::groove:horizontal {{
        height: 4px;
        background: #08090d;
        border-radius: 2px;
    }}
    QSlider#progress::handle:horizontal {{
        background: #00ffd5;
        width: 10px;
        margin: -3px 0;
        border-radius: 5px;
    }}
    QSlider#progress::sub-page:horizontal {{
        background: #00ff66;
        border-radius: 2px;
    }}
    QLabel#info-label {{
        color: #72788e;
        font-family: "{FONT_VFD}";
        font-size: 10px;
    }}
    QPushButton.mode-btn {{
        background: #14151c;
        border: 1px solid #2a2d3c;
        border-radius: 3px;
        color: #696e80;
        font-family: "{FONT_VFD}";
        font-size: 10px;
        padding: 2px 6px;
        min-height: 20px;
    }}
    QPushButton.mode-btn:checked {{
        color: #ff9900;
        border-color: #ff9900;
    }}
    QPushButton.mode-btn:hover {{
        border-color: #00ffd5;
        color: #00ffd5;
    }}
    """


def lyrics_qss() -> str:
    """Diseño inspirado en Apple Music Lyrics: fondo oscuro OLED, tipografía de alta jerarquía y legibilidad."""
    return f"""
    QWidget#lyrics-popup {{
        background: qlineargradient(x1:0,y1:0, x2:0,y2:1,
            stop:0 #0f1016, stop:.6 #13141c, stop:1 #0c0d12);
        border: 1px solid #2e303f;
        border-radius: 16px;
    }}
    QScrollArea#lyrics-scroll {{
        background: transparent;
        border: none;
    }}
    QWidget#lyrics-content {{
        background: transparent;
    }}
    QLabel#lyrics-song-title {{
        color: #ffffff;
        font-family: "{FONT_LYRICS}", "Segoe UI Variable Display", -apple-system, sans-serif;
        font-size: 15px;
        font-weight: 700;
        padding: 2px 0;
    }}
    QLabel#lyrics-artist {{
        color: #8e92a0;
        font-family: "{FONT_LYRICS}", "Segoe UI Variable Text", -apple-system, sans-serif;
        font-size: 12px;
        font-weight: 500;
        padding-bottom: 4px;
    }}
    QPushButton#lyrics-close {{
        background: rgba(255, 255, 255, 0.08);
        color: #8e92a0;
        border: none;
        border-radius: 14px;
        font-size: 13px;
        font-weight: bold;
    }}
    QPushButton#lyrics-close:hover {{
        background: rgba(255, 255, 255, 0.16);
        color: #ffffff;
    }}
    QPushButton#lyrics-search-btn {{
        background: rgba(255, 255, 255, 0.08);
        color: #8e92a0;
        border: none;
        border-radius: 14px;
        font-size: 12px;
    }}
    QPushButton#lyrics-search-btn:hover {{
        background: rgba(255, 255, 255, 0.16);
        color: #00ffcc;
    }}
    QLabel#lyrics-badge {{
        background: rgba(0, 255, 204, 0.10);
        color: #00ffcc;
        border: 1px solid rgba(0, 255, 204, 0.25);
        border-radius: 4px;
        font-family: "{FONT_VFD}";
        font-size: 9px;
        font-weight: bold;
        padding: 2px 6px;
    }}
    QLineEdit.lyrics-input {{
        background: rgba(255, 255, 255, 0.06);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        padding: 6px 10px;
        font-family: "{FONT_LYRICS}", sans-serif;
        font-size: 13px;
    }}
    QLineEdit.lyrics-input:focus {{
        border-color: #00ffcc;
        background: rgba(255, 255, 255, 0.10);
    }}
    QPushButton.lyrics-action-btn {{
        background: #00aa88;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-family: "{FONT_LYRICS}", sans-serif;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton.lyrics-action-btn:hover {{
        background: #00ffcc;
        color: #000000;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 6px 0;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.18);
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(255, 255, 255, 0.35);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """


def login_qss() -> str:
    return f"""
    QDialog {{
        background: #101117;
    }}
    QLabel {{
        color: #c2c7d8;
        font-family: {FONT_UI};
        font-size: 11px;
    }}
    QLabel#title {{
        color: #00ffd5;
        font-family: {FONT_VFD};
        font-size: 16px;
        font-weight: bold;
    }}
    QLineEdit {{
        background: {VFD_BG};
        color: #00ffd5;
        border: 1px solid #2e3242;
        border-radius: 4px;
        padding: 6px;
        font-family: {FONT_VFD};
        font-size: 12px;
        selection-background-color: #0a291d;
    }}
    QLineEdit:focus {{
        border-color: #00ffd5;
    }}
    QPushButton {{
        background: #1e202a;
        color: #00ffd5;
        border: 1px solid #383c4e;
        border-radius: 4px;
        padding: 8px 20px;
        font-family: {FONT_UI};
        font-weight: bold;
        font-size: 11px;
    }}
    QPushButton:hover {{
        border-color: #00ffd5;
        background: #252834;
    }}
    QPushButton:pressed {{
        background: #14151c;
    }}
    QPushButton#cancel {{
        color: #72788e;
    }}
    """
