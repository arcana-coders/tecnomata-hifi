"""Ecualizador gráfico animado estilo analizador de espectro VFD Sony de los 90s."""
import random
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QLinearGradient
from PySide6.QtWidgets import QWidget


class EqualizerWidget(QWidget):
    """Analizador de espectro gráfico por segmentos discretos VFD con retención de pico (peak hold).
    
    A diferencia de barras continuas genéricas, reproduce fielmente el analizador
    fluorescente de minicomponentes Sony (MHC / LBT / CFD):
    - Matriz de fósforos VFD con celdas rectangulares discretas (ladders de 10 segmentos).
    - Rejilla oscura visible de segmentos inactivos (ghost segments tras el acrílico ahumado).
    - Segmentos tricolor: 6 cian fluorescente (#00ffd5), 2 ámbar (#ffb300), 2 rojo coral (#ff3344).
    - Segmento de pico flotante (peak-hold) que se suspende ~500ms antes de caer gradualmente.
    - Filtro de cristal ahumado con reflejo especular y líneas de barrido raster/scanlines.
    """

    def __init__(self, num_bars: int = 12, parent=None):
        super().__init__(parent)
        self._num = num_bars
        self._levels = [0.0] * num_bars
        self._targets = [0.0] * num_bars
        self._peak_segs = [0] * num_bars
        self._peak_holds = [0] * num_bars
        self._playing = False
        self._tick_counter = 0

        self.setMinimumSize(92, 44)
        self.setMaximumHeight(50)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.setInterval(48)
        self._timer.start()

    def set_playing(self, playing: bool):
        self._playing = playing
        if not playing:
            self._targets = [0.0] * self._num

    def _animate(self):
        self._tick_counter += 1
        num_segs = 10

        if self._playing:
            beat = 1.0 if (self._tick_counter % 8 < 3) else 0.4
            for i in range(self._num):
                if i < 3:
                    bias = 0.9 * beat + random.uniform(0.1, 0.4)
                elif i < 8:
                    bias = 0.7 + random.uniform(-0.3, 0.3)
                else:
                    bias = 0.5 + random.uniform(-0.25, 0.25)

                val = random.uniform(0.1, 0.95) * bias
                self._targets[i] = max(0.05, min(1.0, val))
        else:
            for i in range(self._num):
                self._targets[i] = 0.0

        for i in range(self._num):
            diff = self._targets[i] - self._levels[i]
            speed = 0.35 if diff > 0 else 0.14
            self._levels[i] += diff * speed
            self._levels[i] = max(0.0, min(1.0, self._levels[i]))

            active_seg = int(round(self._levels[i] * num_segs))

            if active_seg >= self._peak_segs[i]:
                self._peak_segs[i] = active_seg
                self._peak_holds[i] = 11
            else:
                if self._peak_holds[i] > 0:
                    self._peak_holds[i] -= 1
                else:
                    if self._tick_counter % 2 == 0 and self._peak_segs[i] > 0:
                        self._peak_segs[i] -= 1

        self.update()

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        w, h = self.width(), self.height()

        # ── 1. Bisel exterior hundido del marco plástico ──
        p.fillRect(0, 0, w, h, QColor("#030706"))
        p.setPen(QColor("#080a0e"))
        p.drawRect(0, 0, w - 1, h - 1)

        # Resalte y sombra en el borde del marco
        p.setPen(QColor(255, 255, 255, 18))
        p.drawLine(QPointF(2, h - 1), QPointF(w - 2, h - 1))
        p.setPen(QColor(0, 0, 0, 160))
        p.drawLine(QPointF(2, 1), QPointF(w - 2, 1))

        # ── 2. Geometría de bandas y segmentos ──
        margin_x = 5
        margin_top = 4
        margin_bottom = 9
        usable_w = w - (margin_x * 2)
        usable_h = h - margin_top - margin_bottom

        num_segs = 10
        gap_y = 1.5
        col_gap = 2.0

        col_w = max(2.0, (usable_w - (self._num - 1) * col_gap) / self._num)
        seg_h = max(1.5, (usable_h - (num_segs - 1) * gap_y) / num_segs)

        CYAN_CORE = QColor("#d6fffa")
        CYAN_LIT = QColor("#00ffd5")
        CYAN_GHOST = QColor(0, 48, 38, 90)

        AMBER_CORE = QColor("#fff3cc")
        AMBER_LIT = QColor("#ffaa00")
        AMBER_GHOST = QColor(48, 34, 0, 90)

        RED_CORE = QColor("#ffccd0")
        RED_LIT = QColor("#ff3344")
        RED_GHOST = QColor(48, 12, 14, 90)

        for col in range(self._num):
            cx = margin_x + col * (col_w + col_gap)
            active_count = int(round(self._levels[col] * num_segs))
            peak_seg = self._peak_segs[col]

            for s in range(num_segs):
                sy = margin_top + (num_segs - 1 - s) * (seg_h + gap_y)
                rect = QRectF(cx, sy, col_w, seg_h)

                if s < 6:
                    core_c, lit_c, ghost_c = CYAN_CORE, CYAN_LIT, CYAN_GHOST
                elif s < 8:
                    core_c, lit_c, ghost_c = AMBER_CORE, AMBER_LIT, AMBER_GHOST
                else:
                    core_c, lit_c, ghost_c = RED_CORE, RED_LIT, RED_GHOST

                is_lit = (s < active_count)
                is_peak = (s == (peak_seg - 1) and peak_seg > 0)

                if is_lit or is_peak:
                    p.fillRect(rect, lit_c)
                    if seg_h >= 2.5 and col_w >= 3:
                        inner = rect.adjusted(0.5, 0.5, -0.5, -0.5)
                        p.fillRect(inner, core_c)
                else:
                    p.fillRect(rect, ghost_c)

        # ── 3. Serigrafía VFD inferior ──
        p.setFont(QFont("Consolas", 6))
        p.setPen(QColor("#007755"))
        label_rect = QRectF(0, h - 9, w, 8)
        p.drawText(label_rect, Qt.AlignCenter, "SPECTRUM ANALYZER")

        # ── 4. Reflejo especular diagonal en el cristal del ecualizador ──
        p.setRenderHint(QPainter.Antialiasing, True)
        sheen_grad = QLinearGradient(0, 0, w * 0.8, h)
        sheen_grad.setColorAt(0.0, QColor(255, 255, 255, 25))
        sheen_grad.setColorAt(0.3, QColor(255, 255, 255, 10))
        sheen_grad.setColorAt(0.6, QColor(255, 255, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(sheen_grad)
        p.drawRoundedRect(QRectF(1.5, 1.5, w - 3, h - 3), 3, 3)

        # ── 5. Filtro de líneas de barrido raster/scanline ──
        p.setPen(Qt.NoPen)
        scanline_color = QColor(0, 0, 0, 36)
        for y in range(0, h, 3):
            p.fillRect(0, y, w, 1, scanline_color)

        p.end()
