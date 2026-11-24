"""Botones de transporte táctiles estilo minicomponente Sony Hi-Fi de los 90s."""
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QPolygonF, QFont, QPen
)
from PySide6.QtWidgets import QAbstractButton, QSizePolicy


class SonyTransportButton(QAbstractButton):
    """Botón físico de transporte estilo deck Sony Hi-Fi años 90.
    
    Características:
    - Acabado plástico moldeado / titanio oscuro con bisel 3D mecanizado y relieve.
    - Iconos vectoriales nítidos con micro-tipografía serigrafiada.
    - Lámpara piloto LED (tally lamp) rectangular con brillo fluorescente (verde para PLAY, ámbar para PAUSE, SHUF, REP).
    - Respuesta táctil física en clic (hundimiento mecánico e iluminación activa).
    """

    def __init__(
        self,
        btn_type: str,           # 'prev', 'play', 'pause', 'next', 'shuffle', 'repeat', 'eject', 'menu'
        label: str = "",         # 'PREV', 'PLAY', 'PAUSE', 'NEXT', 'SHUF', 'REP', etc.
        tally_color: str = "green",  # 'green', 'amber', 'cyan'
        parent=None,
    ):
        super().__init__(parent)
        self.btn_type = btn_type
        self.label = label
        self.tally_color = tally_color
        self._tally_active = False
        self._hover = False

        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

        # Dimensiones robustas según tipo de tecla (con más presencia física)
        if btn_type == "play":
            self.setFixedSize(46, 44)
        elif btn_type in ("pause", "prev", "next"):
            self.setFixedSize(38, 44)
        elif btn_type in ("shuffle", "repeat"):
            self.setFixedSize(36, 44)
        elif btn_type == "eject":
            self.setFixedSize(46, 44)
        elif btn_type == "menu":
            self.setFixedSize(32, 44)
        else:
            self.setFixedSize(38, 44)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_tally(self, active: bool):
        """Activa o desactiva la lámpara LED indicadora."""
        if self._tally_active != active:
            self._tally_active = active
            self.update()

    @property
    def is_tally_active(self) -> bool:
        return self._tally_active

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()
        is_pressed = self.isDown()
        offset = 1 if is_pressed else 0

        # ── 1. Pozo / Chasis hundido exterior (Sombra de encaje en el plástico) ──
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#06070a"))
        p.drawRoundedRect(QRectF(0, 0, w, h), 4, 4)

        # ── 2. Bisel exterior 3D de la tecla ──
        key_rect = QRectF(1 + offset, 1 + offset, w - 2, h - 2)
        radius = 3.0

        # Gradiente frontal del cuerpo de la tecla (plástico mate texturizado 90s)
        grad = QLinearGradient(key_rect.topLeft(), key_rect.bottomLeft())
        if is_pressed:
            grad.setColorAt(0.0, QColor("#121319"))
            grad.setColorAt(0.5, QColor("#171822"))
            grad.setColorAt(1.0, QColor("#101117"))
        elif self._hover:
            grad.setColorAt(0.0, QColor("#383d4e"))
            grad.setColorAt(0.15, QColor("#2d303e"))
            grad.setColorAt(0.7, QColor("#222430"))
            grad.setColorAt(1.0, QColor("#191a24"))
        else:
            grad.setColorAt(0.0, QColor("#2d303e"))
            grad.setColorAt(0.12, QColor("#242733"))
            grad.setColorAt(0.7, QColor("#1b1d26"))
            grad.setColorAt(1.0, QColor("#14151e"))

        p.setPen(QColor("#0a0b0f") if is_pressed else QColor("#0e1017"))
        p.setBrush(grad)
        p.drawRoundedRect(key_rect, radius, radius)

        # ── 3. Resalte superior del bisel (Borde de luz que delata el material plástico) ──
        if not is_pressed:
            p.setPen(QColor(255, 255, 255, 50 if self._hover else 32))
            p.drawLine(QPointF(key_rect.left() + 2, key_rect.top() + 1),
                       QPointF(key_rect.right() - 2, key_rect.top() + 1))
            # Sombra inferior de encaje
            p.setPen(QColor(0, 0, 0, 110))
            p.drawLine(QPointF(key_rect.left() + 2, key_rect.bottom() - 1),
                       QPointF(key_rect.right() - 2, key_rect.bottom() - 1))

        # ── 4. Lámpara LED Tally (Pilot lamp) ──
        has_tally = self.btn_type in ("play", "pause", "shuffle", "repeat")
        if has_tally:
            tally_w = 18 if self.btn_type == "play" else 12
            tally_h = 3.5
            tally_x = (w - tally_w) / 2 + offset
            tally_y = key_rect.top() + 4.5

            tally_slot = QRectF(tally_x, tally_y, tally_w, tally_h)
            p.setPen(QColor("#06070a"))
            p.setBrush(QColor("#0a0b0f"))
            p.drawRoundedRect(tally_slot, 1.5, 1.5)

            if self._tally_active:
                if self.tally_color == "green":
                    glow_color = QColor(0, 255, 102, 110)
                    core_color = QColor("#00ff66")
                    hi_color = QColor("#d5ffe5")
                elif self.tally_color == "amber":
                    glow_color = QColor(255, 153, 0, 120)
                    core_color = QColor("#ff9900")
                    hi_color = QColor("#fff0cc")
                else:
                    glow_color = QColor(0, 255, 213, 110)
                    core_color = QColor("#00ffd5")
                    hi_color = QColor("#d6fffa")

                # Resplandor exterior (Halo)
                glow_rect = tally_slot.adjusted(-2, -1.5, 2, 1.5)
                p.setPen(Qt.NoPen)
                p.setBrush(glow_color)
                p.drawRoundedRect(glow_rect, 2.5, 2.5)

                # Núcleo del LED
                p.setBrush(core_color)
                p.drawRoundedRect(tally_slot, 1.5, 1.5)

                # Filamento brillante
                p.setPen(hi_color)
                p.drawLine(QPointF(tally_x + 2, tally_y + 1),
                           QPointF(tally_x + tally_w - 2, tally_y + 1))
            else:
                off_color = QColor("#002414") if self.tally_color == "green" else QColor("#261400")
                p.setPen(Qt.NoPen)
                p.setBrush(off_color)
                p.drawRoundedRect(tally_slot, 1.5, 1.5)

        # ── 5. Dibujar Icono Vectorial Centrado ──
        icon_center_y = (key_rect.top() + 23) if has_tally else (key_rect.center().y() - 4)
        center = QPointF(key_rect.center().x(), icon_center_y)

        if self._tally_active:
            if self.tally_color == "green":
                icon_color = QColor("#b3ffd9")
            elif self.tally_color == "amber":
                icon_color = QColor("#ffe5b3")
            else:
                icon_color = QColor("#00ffd5")
        elif self._hover:
            icon_color = QColor("#ffffff")
        else:
            icon_color = QColor("#b6bac8")

        self._draw_vector_icon(p, self.btn_type, center, icon_color)

        # ── 6. Micro-tipografía Serigrafiada 90s (PREV, PLAY, PAUSE, NEXT, SHUF, REP) ──
        if self.label:
            lbl_font = QFont("Segoe UI", 6, QFont.Bold)
            lbl_font.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
            p.setFont(lbl_font)

            if self._tally_active:
                p.setPen(QColor("#a4b0c8"))
            elif self._hover:
                p.setPen(QColor("#9ca5bc"))
            else:
                p.setPen(QColor("#696e80"))

            label_rect = QRectF(key_rect.left(), key_rect.bottom() - 11, key_rect.width(), 10)
            p.drawText(label_rect, Qt.AlignCenter, self.label)

        p.end()

    def _draw_vector_icon(self, p: QPainter, btn_type: str, center: QPointF, color: QColor):
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(color)

        cx, cy = center.x(), center.y()

        if btn_type == "play":
            # Triángulo PLAY nítido equilátero
            size = 6.5
            pts = [
                QPointF(cx - size * 0.7, cy - size),
                QPointF(cx + size * 0.9, cy),
                QPointF(cx - size * 0.7, cy + size),
            ]
            p.drawPolygon(QPolygonF(pts))

        elif btn_type == "pause":
            # Dos barras verticales PAUSE
            bw, bh, sp = 2.8, 11.0, 3.2
            p.drawRoundedRect(QRectF(cx - bw - sp / 2, cy - bh / 2, bw, bh), 0.8, 0.8)
            p.drawRoundedRect(QRectF(cx + sp / 2, cy - bh / 2, bw, bh), 0.8, 0.8)

        elif btn_type == "prev":
            # Barra vertical + dos triángulos apuntando a la izquierda (|◀◀)
            sz = 4.8
            p.drawRoundedRect(QRectF(cx - 7.5, cy - 5.5, 1.8, 11.0), 0.5, 0.5)
            pts1 = [
                QPointF(cx - 5.2, cy),
                QPointF(cx - 0.4, cy - sz),
                QPointF(cx - 0.4, cy + sz),
            ]
            p.drawPolygon(QPolygonF(pts1))
            pts2 = [
                QPointF(cx - 0.2, cy),
                QPointF(cx + 4.6, cy - sz),
                QPointF(cx + 4.6, cy + sz),
            ]
            p.drawPolygon(QPolygonF(pts2))

        elif btn_type == "next":
            # Dos triángulos apuntando a la derecha + barra vertical (▶▶|)
            sz = 4.8
            pts1 = [
                QPointF(cx - 4.6, cy - sz),
                QPointF(cx + 0.2, cy),
                QPointF(cx - 4.6, cy + sz),
            ]
            p.drawPolygon(QPolygonF(pts1))
            pts2 = [
                QPointF(cx + 0.4, cy - sz),
                QPointF(cx + 5.2, cy),
                QPointF(cx + 0.4, cy + sz),
            ]
            p.drawPolygon(QPolygonF(pts2))
            p.drawRoundedRect(QRectF(cx + 5.7, cy - 5.5, 1.8, 11.0), 0.5, 0.5)

        elif btn_type == "shuffle":
            # Flechas cruzadas estilo Hi-Fi Deck (Aleatorio / Shuffle)
            p.setPen(QPen(color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(Qt.NoBrush)
            # Línea 1: arriba-izq a abajo-der
            p.drawLine(QPointF(cx - 6, cy - 3.5), QPointF(cx + 3, cy + 3.5))
            # Flecha 1
            p.drawLine(QPointF(cx + 1, cy + 3.5), QPointF(cx + 5, cy + 3.5))
            p.drawLine(QPointF(cx + 3.5, cy + 1), QPointF(cx + 5, cy + 3.5))

            # Línea 2: abajo-izq a arriba-der
            p.drawLine(QPointF(cx - 6, cy + 3.5), QPointF(cx - 2, cy + 1))
            p.drawLine(QPointF(cx + 0.5, cy - 1), QPointF(cx + 3, cy - 3.5))
            # Flecha 2
            p.drawLine(QPointF(cx + 1, cy - 3.5), QPointF(cx + 5, cy - 3.5))
            p.drawLine(QPointF(cx + 3.5, cy - 1), QPointF(cx + 5, cy - 3.5))

        elif btn_type == "repeat":
            # Bucle de repetición con flecha (Repeat / Loop)
            p.setPen(QPen(color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(Qt.NoBrush)
            # Rectángulo con extremos curvos
            p.drawRoundedRect(QRectF(cx - 5.5, cy - 4.5, 11, 9), 2.5, 2.5)
            # Flecha en la parte superior derecha
            p.drawLine(QPointF(cx + 3.5, cy - 7), QPointF(cx + 5.5, cy - 4.5))
            p.drawLine(QPointF(cx + 3.5, cy - 2), QPointF(cx + 5.5, cy - 4.5))

        elif btn_type == "eject":
            # Símbolo EJECT / DISC (triángulo arriba + barra abajo ⏏)
            sz = 4.5
            pts = [
                QPointF(cx, cy - sz - 1),
                QPointF(cx - sz, cy),
                QPointF(cx + sz, cy),
            ]
            p.drawPolygon(QPolygonF(pts))
            p.drawRoundedRect(QRectF(cx - sz, cy + 2.5, sz * 2, 1.8), 0.5, 0.5)

        elif btn_type == "menu":
            # Tres nervaduras metálicas horizontales estilo rejilla Hi-Fi
            rw, rh, sp = 12.0, 2.0, 2.2
            for i in (-1, 0, 1):
                p.drawRoundedRect(QRectF(cx - rw / 2, cy + i * (rh + sp) - rh / 2, rw, rh), 0.6, 0.6)

