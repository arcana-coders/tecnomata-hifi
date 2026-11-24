"""Display VFD retro con cristal acrílico ahumado, reflejo especular, marquee amplio y annunciators."""
from PySide6.QtCore import Qt, QTimer, QRect, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QLinearGradient
from PySide6.QtWidgets import QWidget
from src.ui import styles


class VFDDisplay(QWidget):
    """Widget custom que simula un display de vacío fluorescente (VFD) tras una ventana de acrílico ahumado estilo Sony."""

    def __init__(self, orientation: str = "horizontal", parent=None):
        super().__init__(parent)
        self._orientation = orientation  # "horizontal" | "vertical"
        self._artist = "TECNOMATA"
        self._title = "Hi-Fi"
        self._text = "TECNOMATA Hi-Fi"
        self._time_text = "--:-- / --:--"
        self._state = "stopped"
        self._track_num = 1
        self._offset = 0
        self._needs_scroll = False

        self._font = QFont(styles.FONT_VFD, 12, QFont.Bold)
        self._font_small = QFont(styles.FONT_VFD, 9)
        self._font_micro = QFont(styles.FONT_VFD, 7, QFont.Bold)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(45)

        self._update_sizing()

    def set_orientation(self, orientation: str):
        self._orientation = orientation
        self._update_sizing()
        self._check_scroll()
        self.update()

    def _update_sizing(self):
        if self._orientation == "horizontal":
            # Pantalla más larga con generosa área de visualización
            self.setMinimumSize(360, 46)
            self.setMaximumHeight(50)
            self.setMaximumWidth(16777215)
        else:
            self.setMinimumSize(180, 76)
            self.setFixedHeight(78)
            self.setMaximumWidth(16777215)

    # ── API pública ──

    def set_track(self, artist: str, title: str, track_num: int = 1):
        self._artist = artist or "Desconocido"
        self._title = title or "Sin título"
        self._track_num = max(1, track_num)
        self._text = f"  {self._artist}  —  {self._title}  "
        self._offset = 0
        self._check_scroll()

    def set_time(self, elapsed_ms: int, total_ms: int):
        self._time_text = f"{self._fmt(elapsed_ms)} / {self._fmt(total_ms)}"
        self.update()

    def set_state(self, state: str):
        self._state = state
        if state == "playing":
            self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def show_message(self, msg: str):
        self._text = f"  {msg}  "
        self._artist = ""
        self._title = msg
        self._offset = 0
        self._check_scroll()

    # ── internos ──

    def _fmt(self, ms: int) -> str:
        if ms < 0:
            return "--:--"
        s = ms // 1000
        return f"{s // 60}:{s % 60:02d}"

    def _check_scroll(self):
        fm = QFontMetrics(self._font)
        if self._orientation == "horizontal":
            tw = fm.horizontalAdvance(self._text)
            area = max(50, self.width() - 170)
            self._needs_scroll = tw > area
        else:
            tw = fm.horizontalAdvance(self._text)
            area = max(50, self.width() - 20)
            self._needs_scroll = tw > area

        if not self._needs_scroll:
            self._offset = 0
        self.update()

    def _tick(self):
        if self._needs_scroll:
            self._offset -= 1
            fm = QFontMetrics(self._font)
            tw = fm.horizontalAdvance(self._text)
            margin = 170 if self._orientation == "horizontal" else 20
            if self._offset < -tw:
                self._offset = self.width() - margin
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._check_scroll()

    # ── rendering ──

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        # ── 1. Bisel exterior hundido del marco de plástico moldeado ──
        # Borde exterior oscuro
        p.setPen(QColor("#080a0f"))
        p.setBrush(QColor("#040705"))
        p.drawRoundedRect(QRectF(0, 0, w, h), 4, 4)

        # Marco interior con resalte y sombra (efecto de cristal embutido)
        p.setPen(QColor(255, 255, 255, 18))
        p.drawLine(QPointF(2, h - 1), QPointF(w - 2, h - 1))
        p.setPen(QColor(0, 0, 0, 160))
        p.drawLine(QPointF(2, 1), QPointF(w - 2, 1))

        glass_rect = QRectF(1.5, 1.5, w - 3, h - 3)
        p.fillRect(glass_rect, QColor("#020704"))

        # ── 2. Contenido VFD según orientación ──
        if self._orientation == "horizontal":
            self._paint_horizontal(p, w, h)
        else:
            self._paint_vertical(p, w, h)

        # ── 3. Reflejo especular diagonal en el cristal acrílico (Gloss Sheen) ──
        # Simula la luz de la habitación rebotando en el panel de plástico/acrílico pulido
        sheen_grad = QLinearGradient(0, 0, w * 0.7, h)
        sheen_grad.setColorAt(0.0, QColor(255, 255, 255, 28))
        sheen_grad.setColorAt(0.25, QColor(255, 255, 255, 12))
        sheen_grad.setColorAt(0.55, QColor(255, 255, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(sheen_grad)
        p.drawRoundedRect(glass_rect, 3, 3)

        # ── 4. Scanlines CRT/VFD overlay ──
        p.setPen(Qt.NoPen)
        scanline = QColor(0, 0, 0, 36)
        for y in range(2, h - 2, 3):
            p.fillRect(2, y, w - 4, 1, scanline)

        p.end()

    def _paint_horizontal(self, p: QPainter, w: int, h: int):
        is_playing = (self._state == "playing")

        # ── Annunciator izquierdo: TR-01 & [STEREO] ──
        p.setFont(self._font_micro)
        tr_text = f"TR-{self._track_num:02d}"
        p.setPen(QColor(styles.VFD_CYAN))
        p.drawText(10, 16, tr_text)

        # Indicador STEREO iluminado si reproduce
        stereo_color = QColor(styles.VFD_GREEN) if is_playing else QColor(styles.VFD_DIM)
        p.setPen(stereo_color)
        p.drawText(10, 33, "STEREO")

        # Separador vertical punteado
        p.setPen(QColor("#0b2419"))
        p.drawLine(56, 6, 56, h - 6)

        # ── Marquee central amplio del Track ──
        text_x = 64
        text_w = max(10, w - 180)
        p.setClipRect(QRect(text_x, 0, text_w, h))

        offset_x = text_x + (self._offset if self._needs_scroll else 0)
        cy = h // 2 + 5

        # Resplandor VFD cyan (glow)
        p.setFont(self._font)
        glow = QColor(styles.VFD_CYAN)
        glow.setAlpha(45)
        p.setPen(glow)
        p.drawText(offset_x + 1, cy + 1, self._text)
        p.drawText(offset_x - 1, cy - 1, self._text)

        # Texto frontal nítido
        p.setPen(QColor(styles.VFD_CYAN))
        p.drawText(offset_x, cy, self._text)
        p.setClipping(False)

        # Separador vertical punteado derecho
        time_x = w - 114
        p.setPen(QColor("#0b2419"))
        p.drawLine(time_x, 6, time_x, h - 6)

        # ── Tiempo a la derecha ──
        p.setFont(self._font_small)
        p.setPen(QColor(styles.VFD_GREEN))
        time_rect = QRect(time_x + 4, 0, 104, h)
        p.drawText(time_rect, Qt.AlignRight | Qt.AlignVCenter, self._time_text)

    def _paint_vertical(self, p: QPainter, w: int, h: int):
        is_playing = (self._state == "playing")

        # Fila 1: Indicadores VFD (TR-01, STEREO, Tiempo)
        p.setFont(self._font_micro)
        p.setPen(QColor(styles.VFD_CYAN))
        p.drawText(8, 16, f"TR-{self._track_num:02d}")

        stereo_color = QColor(styles.VFD_GREEN) if is_playing else QColor(styles.VFD_DIM)
        p.setPen(stereo_color)
        p.drawText(46, 16, "STEREO")

        p.setFont(self._font_small)
        p.setPen(QColor(styles.VFD_GREEN))
        p.drawText(QRect(w - 110, 4, 102, 16), Qt.AlignRight | Qt.AlignVCenter, self._time_text)

        # Separador horizontal
        p.setPen(QColor("#0b2419"))
        p.drawLine(8, 22, w - 8, 22)

        # Fila 2: Título con marquee
        p.setFont(self._font)
        text_w = max(10, w - 16)
        p.setClipRect(QRect(8, 24, text_w, 28))

        offset_x = 8 + (self._offset if self._needs_scroll else 0)
        p.setPen(QColor(styles.VFD_CYAN))
        p.drawText(offset_x, 44, self._text)
        p.setClipping(False)

        # Fila 3: Indicadores de formato de audio
        p.setFont(QFont(styles.FONT_VFD, 7))
        p.setPen(QColor(styles.VFD_DIM))
        p.drawText(QRect(8, 56, w - 16, 16), Qt.AlignLeft | Qt.AlignVCenter, "SUBSONIC AUDIO · 16/44.1 FLAC")
