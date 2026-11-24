"""Insignia metálica y serigrafía de marca estilo minicomponente Sony Hi-Fi."""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import QWidget


class SonyBadge(QWidget):
    """Insignia metálica institucional estilo Sony Hi-Fi 90s."""

    def __init__(self, vertical: bool = False, parent=None):
        super().__init__(parent)
        self._vertical = vertical
        if vertical:
            self.setFixedSize(140, 26)
        else:
            self.setFixedSize(76, 40)

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        # ── 1. Logotipo SONY en tipografía Serif clásica con brillo metálico ──
        # Sony usa tradicionalmente una variante de Clarendon / Century Schoolbook
        sony_font = QFont("Segoe UI", 8, QFont.Bold)
        sony_font.setLetterSpacing(QFont.AbsoluteSpacing, 0.2)
        p.setFont(sony_font)

        # Sombra grabada en relieve
        p.setPen(QColor("#08090c"))
        sony_rect_shadow = QRectF(1, 4, w, 18)
        align = Qt.AlignCenter if self._vertical else (Qt.AlignLeft | Qt.AlignVCenter)
        p.drawText(sony_rect_shadow, align, "TECNOMATA")

        # Texto frontal con brillo plata titanio
        p.setPen(QColor("#eae6dc"))
        sony_rect = QRectF(0, 3, w, 18)
        p.drawText(sony_rect, align, "TECNOMATA")

        # ── 2. Subtítulo serigrafiado dorado tenue ──
        sub_font = QFont("Segoe UI", 5, QFont.Bold)
        sub_font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        p.setFont(sub_font)
        p.setPen(QColor("#b5aa85"))

        sub_text = "Hi-Fi COMPONENT" if not self._vertical else "COMPACT AUDIO SYSTEM"
        sub_rect = QRectF(0, 21 if not self._vertical else 16, w, 12)
        p.drawText(sub_rect, align, sub_text)

        p.end()
