"""Barra compacta principal — soporte horizontal y vertical (dock lateral) estilo Sony Hi-Fi."""
from PySide6.QtCore import Qt, Signal, QPoint, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient, QPen
)
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QLabel, QSizePolicy, QMenu,
)
from src.ui import styles
from src.ui.vfd_display import VFDDisplay
from src.ui.equalizer import EqualizerWidget
from src.ui.transport_buttons import SonyTransportButton
from src.ui.sony_badge import SonyBadge


class HiFiBar(QWidget):
    """Widget de chasis robusto estilo minicomponente Sony Hi-Fi de los 90s con marco 3D,
    reflejo especular, controles de transporte táctiles, VFD amplio y analizador de espectro."""

    expand_toggled = Signal(bool)
    song_clicked = Signal()
    settings_requested = Signal()
    orientation_changed = Signal(str)
    bar_moved = Signal(int, int)

    def __init__(self, engine, client, config, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.client = client
        self.config = config

        self._expanded = False
        self._drag_pos = QPoint()
        self._orientation = self.config.get("orientation", "horizontal")
        self._engine_connected = False

        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._apply_style()

    # ── ventana ──

    def _setup_window(self):
        self.setObjectName("hifi-bar")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._apply_geometry_for_orientation()

    def _apply_geometry_for_orientation(self):
        if self._orientation == "horizontal":
            bw = self.config.get("bar_width", 1020)
            self.setFixedHeight(styles.BAR_HEIGHT)
            self.setMinimumWidth(800)
            self.setMaximumWidth(16777215)
            self.resize(bw, styles.BAR_HEIGHT)

            x = self.config.get("bar_x", -1)
            y = self.config.get("bar_y", 20)
            if x < 0:
                from PySide6.QtWidgets import QApplication
                screen = QApplication.primaryScreen()
                if screen:
                    sg = screen.availableGeometry()
                    x = (sg.width() - bw) // 2
            self.move(x, y)
        else:
            vw = self.config.get("vert_width", 230)
            vh = self.config.get("vert_height", 560)
            self.setFixedWidth(vw)
            self.setMinimumHeight(460)
            self.setMaximumHeight(16777215)
            self.resize(vw, vh)

            x = self.config.get("vert_x", 20)
            y = self.config.get("vert_y", 120)
            self.move(x, y)

    # ── UI Dinámica ──

    def _build_ui(self):
        if self.layout() is not None:
            QWidget().setLayout(self.layout())

        if self._orientation == "horizontal":
            self._build_horizontal_ui()
        else:
            self._build_vertical_ui()

    def _build_horizontal_ui(self):
        lay = QHBoxLayout(self)
        # Más aire alrededor de los controles (arriba, abajo y a los lados)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(7)

        # 1. Insignia metálica SONY
        self.badge = SonyBadge(vertical=False)
        lay.addWidget(self.badge)

        lay.addWidget(self._sep(vertical=True))

        # 2. Tecla Sistema / Drag
        self.menu_btn = SonyTransportButton("menu", label="SYS")
        self.menu_btn.setToolTip("Arrastrar barra · Clic derecho para opciones")
        lay.addWidget(self.menu_btn)

        lay.addWidget(self._sep(vertical=True))

        # 3. Teclas físicas de transporte Sony Hi-Fi
        self.prev_btn = SonyTransportButton("prev", label="PREV")
        self.play_btn = SonyTransportButton("play", label="PLAY", tally_color="green")
        self.pause_btn = SonyTransportButton("pause", label="PAUSE", tally_color="amber")
        self.next_btn = SonyTransportButton("next", label="NEXT")

        lay.addWidget(self.prev_btn)
        lay.addWidget(self.play_btn)
        lay.addWidget(self.pause_btn)
        lay.addWidget(self.next_btn)

        lay.addWidget(self._sep(vertical=True))

        # 4. Display VFD fluorescente más amplio
        self.vfd = VFDDisplay(orientation="horizontal")
        self.vfd.setCursor(Qt.PointingHandCursor)
        self.vfd.setToolTip("Clic → Ver letras sincronizadas (Lyrics)")
        self.vfd.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lay.addWidget(self.vfd, stretch=1)

        lay.addWidget(self._sep(vertical=True))

        # 5. Analizador de espectro VFD por segmentos
        self.eq = EqualizerWidget(12)
        self.eq.setFixedSize(94, 44)
        lay.addWidget(self.eq)

        lay.addWidget(self._sep(vertical=True))

        # 6. Fader de volumen LEVEL
        vol_box = QVBoxLayout()
        vol_box.setSpacing(2)
        vol_box.setAlignment(Qt.AlignCenter)

        self.vol_label = QLabel("LEVEL")
        self.vol_label.setObjectName("vol-label")
        self.vol_label.setAlignment(Qt.AlignCenter)
        vol_box.addWidget(self.vol_label)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(int(self.engine.volume * 100))
        self.vol_slider.setFixedWidth(66)
        self.vol_slider.setToolTip("Control de Volumen")
        vol_box.addWidget(self.vol_slider)
        lay.addLayout(vol_box)

        # 7. Teclas de reproducción aleatoria (SHUF) y repetición (REP) junto al LEVEL
        self.shuffle_btn = SonyTransportButton("shuffle", label="SHUF", tally_color="amber")
        self.shuffle_btn.setToolTip("Modo Aleatorio (Shuffle)")
        self.repeat_btn = SonyTransportButton("repeat", label="REP", tally_color="amber")
        self.repeat_btn.setToolTip("Modo Repetición (Repeat)")

        lay.addWidget(self.shuffle_btn)
        lay.addWidget(self.repeat_btn)

        lay.addWidget(self._sep(vertical=True))

        # 8. Tecla EJECT / LIST para expandir lista
        self.expand_btn = SonyTransportButton("eject", label="LIST")
        self.expand_btn.setToolTip("Mostrar / Ocultar lista de reproducción y buscador")
        lay.addWidget(self.expand_btn)

    def _build_vertical_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(8)

        # 1. Header con branding SONY & Menú
        header = QHBoxLayout()
        self.badge = SonyBadge(vertical=True)
        header.addWidget(self.badge)
        header.addStretch()

        self.menu_btn = SonyTransportButton("menu", label="SYS")
        self.menu_btn.setFixedSize(30, 36)
        self.menu_btn.setToolTip("Arrastrar / Opciones")
        header.addWidget(self.menu_btn)
        lay.addLayout(header)

        lay.addWidget(self._sep(vertical=False))

        # 2. Display VFD
        self.vfd = VFDDisplay(orientation="vertical")
        self.vfd.setCursor(Qt.PointingHandCursor)
        self.vfd.setToolTip("Clic → Ver letras de la canción")
        lay.addWidget(self.vfd)

        # 3. Analizador de espectro VFD
        self.eq = EqualizerWidget(14)
        self.eq.setFixedHeight(48)
        lay.addWidget(self.eq)

        lay.addWidget(self._sep(vertical=False))

        # 4. Teclas de transporte en fila
        trans = QHBoxLayout()
        trans.setSpacing(4)
        self.prev_btn = SonyTransportButton("prev", label="PREV")
        self.play_btn = SonyTransportButton("play", label="PLAY", tally_color="green")
        self.pause_btn = SonyTransportButton("pause", label="PAUSE", tally_color="amber")
        self.next_btn = SonyTransportButton("next", label="NEXT")

        trans.addWidget(self.prev_btn)
        trans.addWidget(self.play_btn)
        trans.addWidget(self.pause_btn)
        trans.addWidget(self.next_btn)
        lay.addLayout(trans)

        lay.addWidget(self._sep(vertical=False))

        # 5. Control de Volumen LEVEL con botones SHUF y REP
        vol_row = QHBoxLayout()
        vol_row.setSpacing(6)

        self.vol_label = QLabel("VOL")
        self.vol_label.setObjectName("vol-label")
        vol_row.addWidget(self.vol_label)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(int(self.engine.volume * 100))
        self.vol_slider.setToolTip("Volumen")
        vol_row.addWidget(self.vol_slider, 1)

        self.shuffle_btn = SonyTransportButton("shuffle", label="SHUF", tally_color="amber")
        self.repeat_btn = SonyTransportButton("repeat", label="REP", tally_color="amber")
        vol_row.addWidget(self.shuffle_btn)
        vol_row.addWidget(self.repeat_btn)
        lay.addLayout(vol_row)

        lay.addStretch()

        # 6. Tecla Expandir Canciones estilo deck
        self.expand_btn = QPushButton("⏏  LISTA DE REPRODUCCIÓN" if not self._expanded else "⏏  OCULTAR LISTA")
        self.expand_btn.setFixedHeight(34)
        self.expand_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0, x2:0,y2:1,
                    stop:0 #252834, stop:0.5 #1a1c24, stop:1 #121319);
                color: #00ffd5;
                border: 1px solid #363a4c;
                border-radius: 4px;
                font-family: {styles.FONT_VFD};
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                border-color: #00ffd5;
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background: #0f1015;
            }}
        """)
        lay.addWidget(self.expand_btn)

    def _sep(self, vertical: bool = True) -> QWidget:
        s = QWidget()
        if vertical:
            s.setFixedWidth(1)
            s.setFixedHeight(42)
        else:
            s.setFixedHeight(1)
        s.setStyleSheet("background: #282b3a;")
        return s

    def _apply_style(self):
        self.setStyleSheet(styles.bar_qss())

    # ── Pintado del chasis físico (Plástico moldeado 90s, biseles, sombras y reflejos) ──

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()
        pad = 2.0
        chassis_rect = QRectF(pad, pad, w - pad * 2, h - pad * 2)
        radius = 8.0

        # 1. Sombra exterior suave del aparato sobre el fondo
        shadow_rect = chassis_rect.adjusted(1, 1.5, -1, -1.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 110))
        p.drawRoundedRect(shadow_rect, radius, radius)

        # 2. Bisel 3D del chasis (plástico moldeado oscuro texturizado)
        body_grad = QLinearGradient(chassis_rect.topLeft(), chassis_rect.bottomLeft())
        body_grad.setColorAt(0.0, QColor("#363a4b"))   # Borde superior iluminado
        body_grad.setColorAt(0.03, QColor("#222532"))  # Cara superior
        body_grad.setColorAt(0.12, QColor("#181922"))  # Plástico negro grafito
        body_grad.setColorAt(0.60, QColor("#13141d"))
        body_grad.setColorAt(0.96, QColor("#0d0e14"))  # Zona inferior en sombra
        body_grad.setColorAt(1.0, QColor("#050609"))   # Rebaje inferior

        p.setPen(QPen(QColor("#40465c"), 1.2))
        p.setBrush(body_grad)
        p.drawRoundedRect(chassis_rect, radius, radius)

        # 3. Ranura moldeada de ensamble (parting line estilo componente de audio 90s)
        p.setPen(QColor("#07080c"))
        split_y = chassis_rect.bottom() - 6.0
        p.drawLine(QPointF(chassis_rect.left() + 10, split_y),
                   QPointF(chassis_rect.right() - 10, split_y))
        p.setPen(QColor(255, 255, 255, 24))
        p.drawLine(QPointF(chassis_rect.left() + 10, split_y + 1),
                   QPointF(chassis_rect.right() - 10, split_y + 1))

        # 4. Reflejo especular diagonal en el chasis (Gloss Sheen del plástico pulido)
        sheen_grad = QLinearGradient(chassis_rect.topLeft(),
                                     QPointF(chassis_rect.left() + w * 0.45, chassis_rect.bottom()))
        sheen_grad.setColorAt(0.0, QColor(255, 255, 255, 22))
        sheen_grad.setColorAt(0.2, QColor(255, 255, 255, 8))
        sheen_grad.setColorAt(0.5, QColor(255, 255, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(sheen_grad)
        p.drawRoundedRect(chassis_rect.adjusted(1, 1, -1, -1), radius - 1, radius - 1)

        # 5. Puntos de fijación / tornillos embutidos en las 4 esquinas del chasis
        dimples = [
            QPointF(chassis_rect.left() + 8, chassis_rect.top() + 7),
            QPointF(chassis_rect.right() - 8, chassis_rect.top() + 7),
            QPointF(chassis_rect.left() + 8, chassis_rect.bottom() - 10),
            QPointF(chassis_rect.right() - 8, chassis_rect.bottom() - 10),
        ]
        for pt in dimples:
            p.setPen(QColor(255, 255, 255, 25))
            p.setBrush(QColor("#07080c"))
            p.drawEllipse(pt, 1.8, 1.8)

        p.end()

    # ── alternar orientación ──

    def set_orientation(self, orientation: str):
        if orientation == self._orientation:
            return
        self._orientation = orientation
        self.config.set("orientation", orientation)
        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._apply_style()

        song = self.engine.current_song
        if song:
            self._on_track(song)
        state = "playing" if self.engine.is_playing else ("paused" if self.engine.is_paused else "stopped")
        self._on_state(state)
        self._on_position(self.engine.position)

        self.orientation_changed.emit(orientation)

    @property
    def orientation(self) -> str:
        return self._orientation

    # ── señales ──

    def _connect_signals(self):
        self.prev_btn.clicked.connect(self.engine.prev_track)
        self.play_btn.clicked.connect(self._on_play_click)
        self.pause_btn.clicked.connect(self._on_pause_click)
        self.next_btn.clicked.connect(self.engine.next_track)
        self.vol_slider.valueChanged.connect(self._on_vol)
        self.shuffle_btn.clicked.connect(self._on_shuffle_toggle)
        self.repeat_btn.clicked.connect(self._on_repeat_toggle)
        self.expand_btn.clicked.connect(self._on_expand)
        self.vfd.mousePressEvent = self._on_vfd_click

        # Sincronizar estado inicial de SHUF y REP
        self.shuffle_btn.set_tally(self.engine.shuffle)
        self.repeat_btn.set_tally(self.engine.repeat != "off")

        if self._engine_connected:
            try:
                self.engine.track_changed.disconnect(self._on_track)
                self.engine.state_changed.disconnect(self._on_state)
                self.engine.position_changed.disconnect(self._on_position)
                self.engine.shuffle_changed.disconnect(self._on_engine_shuffle)
                self.engine.repeat_changed.disconnect(self._on_engine_repeat)
                self.engine.error_occurred.disconnect(self.show_error)
            except Exception:
                pass
        else:
            self._engine_connected = True

        self.engine.track_changed.connect(self._on_track)
        self.engine.state_changed.connect(self._on_state)
        self.engine.position_changed.connect(self._on_position)
        self.engine.shuffle_changed.connect(self._on_engine_shuffle)
        self.engine.repeat_changed.connect(self._on_engine_repeat)
        self.engine.error_occurred.connect(self.show_error)

    # ── callbacks de transporte y modos ──

    def _on_play_click(self):
        if not self.engine.is_playing:
            self.engine.play()

    def _on_pause_click(self):
        if self.engine.is_playing:
            self.engine.pause()
        elif self.engine.is_paused:
            self.engine.play()

    def _on_shuffle_toggle(self):
        self.engine.set_shuffle(not self.engine.shuffle)

    def _on_repeat_toggle(self):
        next_mode = "all" if self.engine.repeat == "off" else "off"
        self.engine.set_repeat(next_mode)

    def _on_engine_shuffle(self, enabled: bool):
        self.shuffle_btn.set_tally(enabled)

    def _on_engine_repeat(self, mode: str):
        self.repeat_btn.set_tally(mode != "off")

    def _on_track(self, song: dict):
        artist = song.get("artist", "")
        title = song.get("title", song.get("path", ""))
        track_num = self.engine.current_index + 1
        self.vfd.set_track(artist, title, track_num)

    def _on_state(self, state: str):
        if state == "playing":
            self.play_btn.set_tally(True)
            self.pause_btn.set_tally(False)
            self.vfd.set_state("playing")
            self.eq.set_playing(True)
        elif state == "paused":
            self.play_btn.set_tally(False)
            self.pause_btn.set_tally(True)
            self.vfd.set_state("paused")
            self.eq.set_playing(False)
        else:
            self.play_btn.set_tally(False)
            self.pause_btn.set_tally(False)
            self.vfd.set_state("stopped")
            self.eq.set_playing(False)

    def _on_position(self, ms: int):
        total = self.engine.duration
        self.vfd.set_time(ms, total)

    def _on_vol(self, val: int):
        self.engine.volume = val / 100.0
        self.config.set("volume", val / 100.0)

    def _on_expand(self):
        self._expanded = not self._expanded
        if self._orientation == "vertical":
            self.expand_btn.setText("⏏  OCULTAR LISTA" if self._expanded else "⏏  LISTA DE REPRODUCCIÓN")
        self.expand_toggled.emit(self._expanded)

    def _on_vfd_click(self, event):
        if event.button() == Qt.LeftButton:
            self.song_clicked.emit()

    def show_error(self, msg: str):
        self.vfd.show_message(msg)

    # ── drag (mover la barra) ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            self.bar_moved.emit(new_pos.x(), new_pos.y())
            event.accept()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.bar_moved.emit(self.x(), self.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.pos()
            if self._orientation == "horizontal":
                self.config.set("bar_x", pos.x())
                self.config.set("bar_y", pos.y())
            else:
                self.config.set("vert_x", pos.x())
                self.config.set("vert_y", pos.y())

    # ── context menu ──

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: #121319;
                color: #c2c7d8;
                border: 1px solid #323544;
                font-family: {styles.FONT_UI};
                font-size: 11px;
            }}
            QMenu::item:selected {{
                background: #202330;
                color: #00ffd5;
            }}
        """)

        if self._orientation == "horizontal":
            menu.addAction("📐  Cambiar a Barra Lateral (Vertical)", lambda: self.set_orientation("vertical"))
        else:
            menu.addAction("📐  Cambiar a Barra Superior (Horizontal)", lambda: self.set_orientation("horizontal"))

        menu.addSeparator()
        menu.addAction("⚙  Configuración Servidor…", self.settings_requested.emit)
        menu.addSeparator()
        from PySide6.QtWidgets import QApplication
        menu.addAction("✕  Salir", QApplication.quit)
        menu.exec(event.globalPos())

    def closeEvent(self, event):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
        super().closeEvent(event)
