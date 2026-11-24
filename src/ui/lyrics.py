"""Popup de letras sincronizadas con estilo Apple Music y búsqueda automática (Navidrome + LRCLIB + manual)."""
import threading
from PySide6.QtCore import Qt, QPoint, QObject, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QLineEdit, QSizePolicy,
)
from src.ui import styles
from src.api.lyrics_provider import LyricsProvider


class LyricsSignals(QObject):
    """Puente de señales Qt para recibir resultados de búsqueda desde hilos daemon de Python."""

    lyrics_found = Signal(int, dict)        # (req_id, data)
    lyrics_not_found = Signal(int, str)     # (req_id, reason)


class LyricLineLabel(QLabel):
    """Línea individual de letra con feedback táctil e interacción directa (Apple Design)."""

    def __init__(self, text: str, start_ms: int = 0, on_click=None, parent=None):
        super().__init__(text, parent)
        self.start_ms = start_ms
        self.on_click = on_click
        self.setWordWrap(True)
        self.setCursor(Qt.PointingHandCursor if start_ms >= 0 else Qt.ArrowCursor)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setContentsMargins(12, 6, 12, 6)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.on_click and self.start_ms >= 0:
            self.on_click(self.start_ms)
        super().mousePressEvent(event)


class LyricsPopup(QWidget):
    """Ventana flotante de letras inspirada en Apple Music Lyrics: espaciosa, legible,
    con búsqueda automática online (LRCLIB), caché local y opción de búsqueda manual."""

    def __init__(self, engine, client, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.client = client
        self.provider = LyricsProvider()

        self._lines: list[dict] = []
        self._synced = False
        self._current_line = -1
        self._labels: list[LyricLineLabel] = []
        self._current_song: dict = {}
        self._search_id: int = 0

        self._signals = LyricsSignals()
        self._signals.lyrics_found.connect(self._on_lyrics_found)
        self._signals.lyrics_not_found.connect(self._on_lyrics_not_found)

        self._drag_pos = QPoint()

        self._setup_window()
        self._build_ui()
        self._connect_signals()

    def _setup_window(self):
        self.setObjectName("lyrics-popup")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.resize(480, 640)
        self.setMinimumSize(420, 520)
        self.setStyleSheet(styles.lyrics_qss())

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 16)
        root.setSpacing(8)

        # Header con jerarquía tipográfica Apple (Canción + Artista + Badge de Fuente)
        header = QHBoxLayout()
        header.setSpacing(8)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.song_title_lbl = QLabel("Sin reproducción")
        self.song_title_lbl.setObjectName("lyrics-song-title")

        artist_row = QHBoxLayout()
        artist_row.setSpacing(8)
        self.artist_lbl = QLabel("Toca una canción para ver sus letras")
        self.artist_lbl.setObjectName("lyrics-artist")
        artist_row.addWidget(self.artist_lbl, 0)

        # Badge indicador de fuente de letra (LRCLIB, Navidrome, Caché)
        self.source_badge = QLabel("")
        self.source_badge.setObjectName("lyrics-badge")
        self.source_badge.setVisible(False)
        artist_row.addWidget(self.source_badge, 0)
        artist_row.addStretch()

        title_box.addWidget(self.song_title_lbl)
        title_box.addLayout(artist_row)
        header.addLayout(title_box, 1)

        # Botón de búsqueda manual
        self.search_btn = QPushButton("🔍")
        self.search_btn.setObjectName("lyrics-search-btn")
        self.search_btn.setFixedSize(28, 28)
        self.search_btn.setToolTip("Buscar letra manualmente en LRCLIB")
        self.search_btn.clicked.connect(self._toggle_manual_search)
        header.addWidget(self.search_btn, 0, Qt.AlignTop)

        # Botón cerrar
        close_btn = QPushButton("✕")
        close_btn.setObjectName("lyrics-close")
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip("Cerrar letras")
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn, 0, Qt.AlignTop)

        root.addLayout(header)

        # Línea divisoria
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: rgba(255, 255, 255, 0.08); max-height: 1px;")
        root.addWidget(sep)

        # Scroll area para letras con fondo transparente garantizado
        self.scroll = QScrollArea()
        self.scroll.setObjectName("lyrics-scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.content = QWidget()
        self.content.setObjectName("lyrics-content")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 16, 10, 30)
        self.content_layout.setSpacing(6)
        self.content_layout.addStretch()
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

    def _connect_signals(self):
        self.engine.position_changed.connect(self._on_position)

    # ── API pública ──

    def load_lyrics(self, song: dict):
        self._current_song = song
        artist = song.get("artist", "Desconocido").strip()
        title = song.get("title", song.get("path", "Sin título")).strip()
        self.song_title_lbl.setText(title)
        self.artist_lbl.setText(artist)
        self.source_badge.setVisible(False)

        self._clear_content()

        if not song.get("id") and not title:
            self._show_info_message("Selecciona una canción para ver o buscar sus letras.")
            return

        # 1. ¿Está en la caché local? (0 ms)
        cached = self.provider.get_cached(artist, title)
        if cached:
            self._render_lyrics_data(cached)
            return

        # 2. Si no está en caché, mostrar estado de búsqueda y lanzar worker daemon en segundo plano
        self._show_searching_state(artist, title)
        self._start_search_worker(song)

    def _start_search_worker(self, song: dict, custom_artist: str = "", custom_title: str = ""):
        self._search_id += 1
        current_id = self._search_id

        def worker_task():
            try:
                if custom_artist or custom_title:
                    artist = custom_artist or song.get("artist", "")
                    title = custom_title or song.get("title", "")
                    album = song.get("album", "")
                    duration = song.get("duration", 0)

                    res = self.provider.fetch_lrclib(artist, title, album=album, duration=duration)
                    if not res:
                        res = self.provider.fetch_lyrics_ovh(artist, title)

                    if res:
                        self.provider.save_cached(artist, title, res)
                        orig_a = song.get("artist", "")
                        orig_t = song.get("title", "")
                        if orig_a and orig_t and (orig_a != artist or orig_t != title):
                            self.provider.save_cached(orig_a, orig_t, res)
                        self._signals.lyrics_found.emit(current_id, res)
                    else:
                        self._signals.lyrics_not_found.emit(current_id, "No se encontraron letras con los términos ingresados.")
                else:
                    res = self.provider.resolve_lyrics(song, subsonic_client=self.client)
                    if res:
                        self._signals.lyrics_found.emit(current_id, res)
                    else:
                        self._signals.lyrics_not_found.emit(current_id, "No se encontró letra automática.")
            except Exception as e:
                self._signals.lyrics_not_found.emit(current_id, str(e))

        t = threading.Thread(target=worker_task, daemon=True)
        t.start()

    def _on_lyrics_found(self, req_id: int, data: dict):
        if req_id != self._search_id:
            return  # Respuesta obsoleta de una pista anterior, descartar silenciosamente
        self._clear_content()
        self._render_lyrics_data(data)

    def _on_lyrics_not_found(self, req_id: int, reason: str):
        if req_id != self._search_id:
            return  # Respuesta obsoleta, descartar
        self._clear_content()
        self.source_badge.setVisible(False)
        artist = self._current_song.get("artist", "")
        title = self._current_song.get("title", "")
        self._show_manual_search_card(artist, title, reason)

    # ── Renderizado de Letras ──

    def _render_lyrics_data(self, data: dict):
        self._clear_content()

        if data.get("instrumental", False):
            self._show_instrumental_state()
            return

        source = data.get("source", "Online")
        is_synced = data.get("synced", False)
        structured = data.get("structuredLyrics", [])
        plain_text = data.get("plainLyrics", "")

        # Actualizar badge de origen
        if is_synced:
            self.source_badge.setText(f"✓ {source.upper()} · SINCRONIZADA")
            self.source_badge.setStyleSheet("""
                background: rgba(0, 255, 204, 0.12);
                color: #00ffcc;
                border: 1px solid rgba(0, 255, 204, 0.35);
                border-radius: 4px;
                font-family: "Consolas", monospace;
                font-size: 9px;
                font-weight: bold;
                padding: 2px 6px;
            """)
        else:
            self.source_badge.setText(f"✓ {source.upper()} · TEXTO PLANO")
            self.source_badge.setStyleSheet("""
                background: rgba(255, 170, 0, 0.12);
                color: #ffaa00;
                border: 1px solid rgba(255, 170, 0, 0.35);
                border-radius: 4px;
                font-family: "Consolas", monospace;
                font-size: 9px;
                font-weight: bold;
                padding: 2px 6px;
            """)
        self.source_badge.setVisible(True)

        if structured and is_synced:
            best_entry = structured[0]
            for s in structured:
                if s.get("synced"):
                    best_entry = s
                    break

            self._synced = True
            self._lines = best_entry.get("line", [])
            self._current_line = -1

            for line in self._lines:
                text = line.get("value", "").strip()
                if not text:
                    text = "· · ·"
                start_ms = line.get("start", 0)

                lbl = LyricLineLabel(
                    text,
                    start_ms=start_ms,
                    on_click=self._on_line_clicked,
                    parent=self.content
                )
                self._apply_line_style(lbl, state="distant")
                self._labels.append(lbl)
                self.content_layout.insertWidget(self.content_layout.count() - 1, lbl)

        elif plain_text:
            self._synced = False
            for line_str in plain_text.splitlines():
                t = line_str.strip()
                lbl = LyricLineLabel(t if t else "· · ·", start_ms=-1, parent=self.content)
                lbl.setStyleSheet("""
                    color: rgba(255, 255, 255, 0.82);
                    font-family: "Segoe UI", sans-serif;
                    font-size: 17px;
                    font-weight: 500;
                    padding: 8px 12px;
                    background: transparent;
                """)
                self._labels.append(lbl)
                self.content_layout.insertWidget(self.content_layout.count() - 1, lbl)
        else:
            artist = self._current_song.get("artist", "")
            title = self._current_song.get("title", "")
            self._show_manual_search_card(artist, title, "El resultado no contiene texto.")

    # ── Estados visuales (Searching, Instrumental, Manual Search) ──

    def _show_searching_state(self, artist: str, title: str):
        card = QWidget()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 50, 20, 50)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignCenter)

        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 32px; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        title_lbl = QLabel("Buscando letra en línea…")
        title_lbl.setStyleSheet("color: #00ffd5; font-family: 'Segoe UI', sans-serif; font-size: 17px; font-weight: 600; background: transparent;")
        title_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(title_lbl)

        sub_lbl = QLabel(f"Consultando catálogo global de LRCLIB para:\n«{title}» de {artist}")
        sub_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.50); font-family: 'Segoe UI', sans-serif; font-size: 13px; background: transparent;")
        sub_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub_lbl)

        self._labels.append(card)
        self.content_layout.insertWidget(0, card)

    def _show_instrumental_state(self):
        self.source_badge.setText("PURA INSTRUMENTAL")
        self.source_badge.setStyleSheet("""
            background: rgba(0, 204, 255, 0.12);
            color: #00ccff;
            border: 1px solid rgba(0, 204, 255, 0.35);
            border-radius: 4px;
            font-family: "Consolas", monospace;
            font-size: 9px;
            font-weight: bold;
            padding: 2px 6px;
        """)
        self.source_badge.setVisible(True)

        card = QWidget()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 60, 20, 60)
        lay.setSpacing(12)
        lay.setAlignment(Qt.AlignCenter)

        icon = QLabel("🎸")
        icon.setStyleSheet("font-size: 36px; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        title_lbl = QLabel("Pista Instrumental")
        title_lbl.setStyleSheet("color: #ffffff; font-family: 'Segoe UI', sans-serif; font-size: 18px; font-weight: 600; background: transparent;")
        title_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(title_lbl)

        desc_lbl = QLabel("Esta obra está identificada oficialmente como instrumental (sin pista vocal).")
        desc_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.55); font-family: 'Segoe UI', sans-serif; font-size: 13px; background: transparent;")
        desc_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(desc_lbl)

        self._labels.append(card)
        self.content_layout.insertWidget(0, card)

    def _show_manual_search_card(self, artist: str, title: str, note: str = ""):
        card = QWidget()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 30, 18, 30)
        lay.setSpacing(12)

        icon = QLabel("🎵")
        icon.setStyleSheet("font-size: 28px; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        head = QLabel("No se encontró letra automática")
        head.setStyleSheet("color: #ffffff; font-size: 17px; font-weight: 600; background: transparent;")
        head.setAlignment(Qt.AlignCenter)
        lay.addWidget(head)

        desc = QLabel(
            "Puedes ajustar el nombre del artista o título para buscar de nuevo en la base de datos de LRCLIB:"
        )
        desc.setStyleSheet("color: rgba(255, 255, 255, 0.55); font-size: 13px; background: transparent;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        lay.addWidget(desc)

        # Campos de texto interactivos
        art_lbl = QLabel("Artista:")
        art_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px; font-weight: 600; margin-top: 6px;")
        lay.addWidget(art_lbl)

        artist_input = QLineEdit(artist)
        artist_input.setProperty("class", "lyrics-input")
        lay.addWidget(artist_input)

        tit_lbl = QLabel("Título de la canción:")
        tit_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px; font-weight: 600; margin-top: 4px;")
        lay.addWidget(tit_lbl)

        title_input = QLineEdit(title)
        title_input.setProperty("class", "lyrics-input")
        lay.addWidget(title_input)

        # Botón buscar
        btn_search = QPushButton("🔍  Buscar en LRCLIB")
        btn_search.setProperty("class", "lyrics-action-btn")
        btn_search.setCursor(Qt.PointingHandCursor)

        def do_search():
            a = artist_input.text().strip()
            t = title_input.text().strip()
            if a or t:
                self._clear_content()
                self._show_searching_state(a, t)
                self._start_search_worker(self._current_song, custom_artist=a, custom_title=t)

        btn_search.clicked.connect(do_search)
        artist_input.returnPressed.connect(do_search)
        title_input.returnPressed.connect(do_search)

        lay.addWidget(btn_search)

        self._labels.append(card)
        self.content_layout.insertWidget(0, card)

    def _toggle_manual_search(self):
        """Permite al usuario forzar la pantalla de búsqueda manual para corregir o refinar letras."""
        artist = self._current_song.get("artist", "")
        title = self._current_song.get("title", "")
        self._clear_content()
        self.source_badge.setVisible(False)
        self._show_manual_search_card(artist, title, "Búsqueda manual")

    def _show_info_message(self, msg: str):
        lbl = QLabel(msg)
        lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.45);
            font-family: "Segoe UI", sans-serif;
            font-size: 14px;
            padding: 50px 20px;
            background: transparent;
        """)
        lbl.setAlignment(Qt.AlignCenter)
        self._labels.append(lbl)
        self.content_layout.insertWidget(0, lbl)

    def _clear_content(self):
        for lbl in self._labels:
            lbl.deleteLater()
        self._labels.clear()
        self._lines.clear()
        self._current_line = -1
        self._synced = False

    # ── Sincronización y jerarquía visual (Apple Design) ──

    def _on_position(self, ms: int):
        if not self.isVisible() or not self._synced or not self._lines:
            return

        new_line = -1
        for i, line in enumerate(self._lines):
            start = line.get("start", 0)
            if ms >= start:
                new_line = i
            else:
                break

        if new_line != self._current_line and new_line >= 0:
            self._current_line = new_line
            self._highlight(new_line)

    def _highlight(self, active_idx: int):
        for i, lbl in enumerate(self._labels):
            if not isinstance(lbl, LyricLineLabel):
                continue
            if i == active_idx:
                self._apply_line_style(lbl, state="active")
                self.scroll.ensureWidgetVisible(lbl, 10, self.scroll.height() // 3)
            elif abs(i - active_idx) <= 2:
                self._apply_line_style(lbl, state="near")
            else:
                self._apply_line_style(lbl, state="distant")

    def _apply_line_style(self, lbl: QLabel, state: str):
        if state == "active":
            lbl.setStyleSheet("""
                color: #ffffff;
                font-family: "Segoe UI Variable Display", "Segoe UI", -apple-system, sans-serif;
                font-size: 21px;
                font-weight: 700;
                padding: 10px 14px;
                background: rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                border-left: 3px solid #00ffcc;
            """)
        elif state == "near":
            lbl.setStyleSheet("""
                color: rgba(255, 255, 255, 0.65);
                font-family: "Segoe UI Variable Text", "Segoe UI", -apple-system, sans-serif;
                font-size: 16px;
                font-weight: 500;
                padding: 7px 14px;
                background: transparent;
                border-left: 3px solid transparent;
            """)
        else:
            lbl.setStyleSheet("""
                color: rgba(255, 255, 255, 0.32);
                font-family: "Segoe UI Variable Text", "Segoe UI", -apple-system, sans-serif;
                font-size: 15px;
                font-weight: 400;
                padding: 5px 14px;
                background: transparent;
                border-left: 3px solid transparent;
            """)

    def _on_line_clicked(self, start_ms: int):
        if start_ms >= 0:
            self.engine.seek(start_ms)

    # ── drag ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
