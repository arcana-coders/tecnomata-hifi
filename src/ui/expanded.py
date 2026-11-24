"""Panel expandido con lista de playlists, canciones y buscador global."""
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QPixmap, QImage, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QListWidget,
    QListWidgetItem, QLabel, QSlider, QPushButton, QSizePolicy, QLineEdit,
)
from src.ui import styles


class ExpandedPanel(QWidget):
    """Panel desplegable con playlists, buscador (canciones, grupos, playlists) y reproductor."""

    song_selected = Signal(int)          # índice en playlist activa
    playlist_selected = Signal(str)      # playlist_id
    play_direct_song = Signal(dict)      # reproducir canción directa desde resultado de búsqueda

    def __init__(self, engine, client, config, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.client = client
        self.config = config
        self._playlists: list[dict] = []
        self._raw_songs: list[dict] = []     # canciones de la playlist activa
        self._search_results: list[dict] = [] # resultados actuales en pantalla
        self._is_search_mode: bool = False
        self._drag_pos = QPoint()

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(350)
        self._search_timer.timeout.connect(self._on_search_query_changed)

        self._setup_window()
        self._build_ui()
        self._connect_signals()

    # ── ventana ──

    def _setup_window(self):
        self.setObjectName("expanded-panel")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.resize(740, 400)
        self.setStyleSheet(styles.expanded_qss())

    # ── UI ──

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(6)

        # Fila 1: Selector de Playlist + Shuffle / Repeat
        top = QHBoxLayout()
        top_lbl = QLabel("PLAYLIST")
        top_lbl.setStyleSheet(f"color: {styles.ACCENT}; font-family: {styles.FONT_VFD}; font-weight: bold; font-size: 11px;")
        top.addWidget(top_lbl, 0)

        self.playlist_combo = QComboBox()
        self.playlist_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top.addWidget(self.playlist_combo, 1)

        self.shuffle_btn = self._mode_btn("🔀 ALEATORIO")
        self.shuffle_btn.setCheckable(True)
        self.repeat_btn = self._mode_btn("🔁 REPETIR")
        self.repeat_btn.setCheckable(True)
        top.addWidget(self.shuffle_btn)
        top.addWidget(self.repeat_btn)
        root.addLayout(top)

        # Fila 2: Buscador integrado (canciones, grupos, playlists)
        search_row = QHBoxLayout()
        search_row.setSpacing(4)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("search-input")
        self.search_input.setPlaceholderText("🔍 Buscar canción, grupo, álbum o playlist...")
        self.search_input.setClearButtonEnabled(True)
        search_row.addWidget(self.search_input, 1)

        self.search_server_btn = QPushButton("Buscar en Servidor")
        self.search_server_btn.setProperty("class", "search-action")
        self.search_server_btn.setToolTip("Buscar en toda la biblioteca de Navidrome")
        search_row.addWidget(self.search_server_btn)

        root.addLayout(search_row)

        # Fila 3: Contenido central: carátula + lista de canciones/resultados
        mid = QHBoxLayout()

        # Carátula
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(140, 140)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet(
            f"background: {styles.VFD_BG}; border: 1px solid {styles.CHASSIS_BORDER}; border-radius: 4px;"
        )
        self.cover_label.setText("♪")
        mid.addWidget(self.cover_label)

        # Lista de canciones / resultados de búsqueda
        self.song_list = QListWidget()
        self.song_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        mid.addWidget(self.song_list, 1)
        root.addLayout(mid, 1)

        # Fila 4: Barra de progreso de la canción activa
        prog_row = QHBoxLayout()
        self.time_label = QLabel("0:00")
        self.time_label.setObjectName("info-label")
        self.time_label.setFixedWidth(40)
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setObjectName("progress")
        self.progress.setRange(0, 1000)
        self.dur_label = QLabel("0:00")
        self.dur_label.setObjectName("info-label")
        self.dur_label.setFixedWidth(40)
        self.dur_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        prog_row.addWidget(self.time_label)
        prog_row.addWidget(self.progress, 1)
        prog_row.addWidget(self.dur_label)
        root.addLayout(prog_row)

        # Fila 5: Barra de estado / conteo
        self.info = QLabel("")
        self.info.setObjectName("info-label")
        self.info.setAlignment(Qt.AlignCenter)
        root.addWidget(self.info)

    def _mode_btn(self, text: str) -> QPushButton:
        b = QPushButton(text)
        b.setProperty("class", "mode-btn")
        b.setFocusPolicy(Qt.NoFocus)
        return b

    # ── señales ──

    def _connect_signals(self):
        self.playlist_combo.currentIndexChanged.connect(self._on_playlist_chosen)
        self.song_list.itemDoubleClicked.connect(self._on_item_dbl)
        self.progress.sliderReleased.connect(self._on_seek)
        self.shuffle_btn.toggled.connect(self._on_shuffle)
        self.repeat_btn.toggled.connect(self._on_repeat)

        # Buscador
        self.search_input.textChanged.connect(lambda: self._search_timer.start())
        self.search_input.returnPressed.connect(self._trigger_server_search)
        self.search_server_btn.clicked.connect(self._trigger_server_search)

        # Player engine
        self.engine.track_changed.connect(self._on_track)
        self.engine.position_changed.connect(self._on_position)
        self.engine.duration_changed.connect(self._on_duration)
        self.engine.playlist_loaded.connect(self._on_playlist_loaded)
        self.engine.shuffle_changed.connect(lambda en: self.shuffle_btn.setChecked(en))
        self.engine.repeat_changed.connect(lambda mode: self.repeat_btn.setChecked(mode != "off"))

    # ── API pública ──

    def set_playlists(self, playlists: list):
        self._playlists = playlists
        self.playlist_combo.blockSignals(True)
        self.playlist_combo.clear()
        for pl in playlists:
            name = pl.get("name", "?")
            count = pl.get("songCount", 0)
            self.playlist_combo.addItem(f"{name}  ({count})", pl.get("id"))
        self.playlist_combo.blockSignals(False)

    # ── búsqueda ──

    def _on_search_query_changed(self):
        query = self.search_input.text().strip().lower()
        if not query:
            self._is_search_mode = False
            self._render_songs(self._raw_songs)
            return

        # 1. Filtro local instantáneo en la playlist actual y en playlists conocidas
        filtered_songs = []
        for s in self._raw_songs:
            title = s.get("title", "").lower()
            artist = s.get("artist", "").lower()
            album = s.get("album", "").lower()
            if query in title or query in artist or query in album:
                filtered_songs.append(s)

        # 2. Buscar si hay playlists que coincidan
        matching_playlists = []
        for pl in self._playlists:
            if query in pl.get("name", "").lower():
                matching_playlists.append(pl)

        self._render_search_results(query, matching_playlists, filtered_songs, server_results=None)

    def _trigger_server_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self.info.setText(f"Buscando '{query}' en Navidrome...")
        try:
            res = self.client.search3_full(query, song_count=50, album_count=8, artist_count=8)
            matching_playlists = [pl for pl in self._playlists if query.lower() in pl.get("name", "").lower()]
            self._render_search_results(query, matching_playlists, [], server_results=res)
        except Exception as e:
            self.info.setText(f"Error al buscar en servidor: {e}")

    def _render_search_results(self, query: str, playlists: list, local_songs: list, server_results: dict | None):
        self._is_search_mode = True
        self.song_list.clear()

        count_total = 0

        # Sección Playlists coincidentes
        if playlists:
            header = QListWidgetItem(f"─── PLAYLISTS ({len(playlists)}) ───")
            header.setFlags(Qt.NoItemFlags)
            header.setForeground(QColor(styles.ACCENT))
            self.song_list.addItem(header)

            for pl in playlists:
                name = pl.get("name", "?")
                sc = pl.get("songCount", 0)
                item = QListWidgetItem(f"  📁  {name}  [{sc} canciones]")
                item.setData(Qt.UserRole, {"type": "playlist", "id": pl.get("id"), "name": name})
                item.setForeground(QColor(styles.VFD_CYAN))
                self.song_list.addItem(item)
                count_total += 1

        # Resultados de servidor si existen
        if server_results:
            artists = server_results.get("artists", [])
            if artists:
                h_art = QListWidgetItem(f"─── GRUPOS / ARTISTAS ({len(artists)}) ───")
                h_art.setFlags(Qt.NoItemFlags)
                h_art.setForeground(QColor(styles.ACCENT))
                self.song_list.addItem(h_art)
                for a in artists:
                    name = a.get("name", "?")
                    ac = a.get("albumCount", 0)
                    item = QListWidgetItem(f"  🎤  {name}  [{ac} álbumes]")
                    item.setData(Qt.UserRole, {"type": "artist", "id": a.get("id"), "name": name})
                    item.setForeground(QColor(styles.VFD_CYAN))
                    self.song_list.addItem(item)
                    count_total += 1

            albums = server_results.get("albums", [])
            if albums:
                h_alb = QListWidgetItem(f"─── ÁLBUMES ({len(albums)}) ───")
                h_alb.setFlags(Qt.NoItemFlags)
                h_alb.setForeground(QColor(styles.ACCENT))
                self.song_list.addItem(h_alb)
                for alb in albums:
                    title = alb.get("title", alb.get("name", "?"))
                    artist = alb.get("artist", "")
                    item = QListWidgetItem(f"  💿  {artist} — {title}")
                    item.setData(Qt.UserRole, {"type": "album", "id": alb.get("id"), "title": title})
                    item.setForeground(QColor(styles.VFD_CYAN))
                    self.song_list.addItem(item)
                    count_total += 1

            srv_songs = server_results.get("songs", [])
            if srv_songs:
                h_s = QListWidgetItem(f"─── CANCIONES ({len(srv_songs)}) ───")
                h_s.setFlags(Qt.NoItemFlags)
                h_s.setForeground(QColor(styles.ACCENT))
                self.song_list.addItem(h_s)
                for s in srv_songs:
                    artist = s.get("artist", "")
                    title = s.get("title", "?")
                    dur = s.get("duration", 0)
                    dur_str = f"{dur // 60}:{dur % 60:02d}"
                    item = QListWidgetItem(f"  🎵  {artist} — {title}   [{dur_str}]")
                    item.setData(Qt.UserRole, {"type": "song", "data": s})
                    item.setForeground(QColor(styles.VFD_GREEN))
                    self.song_list.addItem(item)
                    count_total += 1

        elif local_songs:
            h_loc = QListWidgetItem(f"─── CANCIONES EN PLAYLIST ({len(local_songs)}) ───")
            h_loc.setFlags(Qt.NoItemFlags)
            h_loc.setForeground(QColor(styles.ACCENT))
            self.song_list.addItem(h_loc)
            for s in local_songs:
                artist = s.get("artist", "")
                title = s.get("title", "?")
                dur = s.get("duration", 0)
                dur_str = f"{dur // 60}:{dur % 60:02d}"
                # Buscar índice en lista original
                idx = self._raw_songs.index(s) if s in self._raw_songs else -1
                item = QListWidgetItem(f"  🎵  {artist} — {title}   [{dur_str}]")
                item.setData(Qt.UserRole, {"type": "playlist_index", "index": idx, "data": s})
                item.setForeground(QColor(styles.VFD_GREEN))
                self.song_list.addItem(item)
                count_total += 1

        if count_total == 0:
            none_item = QListWidgetItem("  (Sin resultados. Presiona 'Buscar en Servidor' para buscar en toda la biblioteca)")
            none_item.setFlags(Qt.NoItemFlags)
            none_item.setForeground(QColor(styles.TEXT_DIM))
            self.song_list.addItem(none_item)

        self.info.setText(f"Resultados para '{query}': {count_total} encontrados")

    # ── callbacks ──

    def _on_playlist_chosen(self, index: int):
        if 0 <= index < len(self._playlists):
            pid = self._playlists[index].get("id")
            if pid:
                self.config.set("last_playlist_id", pid)
                self.search_input.clear()
                self._is_search_mode = False
                self.playlist_selected.emit(pid)

    def _on_playlist_loaded(self, songs: list):
        self._raw_songs = songs
        self.search_input.clear()
        self._is_search_mode = False
        self._render_songs(songs)

    def _render_songs(self, songs: list):
        self.song_list.clear()
        for i, s in enumerate(songs):
            artist = s.get("artist", "")
            title = s.get("title", "?")
            dur = s.get("duration", 0)
            dur_str = f"{dur // 60}:{dur % 60:02d}"
            text = f"{i + 1:3d}.  {artist} — {title}   [{dur_str}]"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, {"type": "playlist_index", "index": i, "data": s})
            self.song_list.addItem(item)
        total = len(songs)
        self.info.setText(f"{total} canciones cargadas")

    def _on_item_dbl(self, item: QListWidgetItem):
        payload = item.data(Qt.UserRole)
        if not payload or not isinstance(payload, dict):
            return

        item_type = payload.get("type")
        if item_type == "playlist_index":
            idx = payload.get("index")
            if idx is not None and idx >= 0:
                self.song_selected.emit(idx)

        elif item_type == "playlist":
            pid = payload.get("id")
            if pid:
                # Cambiar el combo y emitir
                for i in range(self.playlist_combo.count()):
                    if self.playlist_combo.itemData(i) == pid:
                        self.playlist_combo.setCurrentIndex(i)
                        break

        elif item_type == "song":
            song_data = payload.get("data")
            if song_data:
                # Agregar y reproducir directamente
                self.play_direct_song.emit(song_data)

        elif item_type == "artist":
            # Buscar álbumes de este artista
            artist_id = payload.get("id")
            try:
                art = self.client.get_artist(artist_id)
                albums = art.get("album", [])
                if isinstance(albums, dict):
                    albums = [albums]
                if albums:
                    alb_id = albums[0].get("id")
                    alb = self.client.get_album(alb_id)
                    songs = alb.get("song", [])
                    if isinstance(songs, dict):
                        songs = [songs]
                    if songs:
                        self.engine.load_playlist(songs)
                        self.engine.play_index(0)
            except Exception as e:
                self.info.setText(f"Error cargando artista: {e}")

        elif item_type == "album":
            album_id = payload.get("id")
            try:
                alb = self.client.get_album(album_id)
                songs = alb.get("song", [])
                if isinstance(songs, dict):
                    songs = [songs]
                if songs:
                    self.engine.load_playlist(songs)
                    self.engine.play_index(0)
            except Exception as e:
                self.info.setText(f"Error cargando álbum: {e}")

    def _on_track(self, song: dict):
        if not self._is_search_mode:
            idx = self.engine.current_index
            for i in range(self.song_list.count()):
                item = self.song_list.item(i)
                data = item.data(Qt.UserRole)
                if data and data.get("index") == idx:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setForeground(QColor(styles.VFD_CYAN))
                    self.song_list.scrollToItem(item)
                else:
                    font = item.font()
                    font.setBold(False)
                    item.setFont(font)
                    item.setForeground(QColor(styles.VFD_GREEN))

        # carátula
        cover_id = song.get("coverArt", song.get("id", ""))
        if cover_id:
            self._load_cover(cover_id)

    def _load_cover(self, cover_id: str):
        try:
            data = self.client.get_cover_art_bytes(cover_id, 300)
            if data:
                img = QImage()
                img.loadFromData(data)
                pm = QPixmap.fromImage(img).scaled(
                    136, 136, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.cover_label.setPixmap(pm)
        except Exception:
            self.cover_label.setText("♪")

    def _on_position(self, ms: int):
        dur = self.engine.duration
        if dur > 0 and not self.progress.isSliderDown():
            self.progress.setValue(int(ms / dur * 1000))
        self.time_label.setText(self._fmt(ms))

    def _on_duration(self, ms: int):
        self.dur_label.setText(self._fmt(ms))

    def _on_seek(self):
        dur = self.engine.duration
        if dur > 0:
            pos = int(self.progress.value() / 1000 * dur)
            self.engine.seek(pos)

    def _on_shuffle(self, on: bool):
        self.engine.set_shuffle(on)

    def _on_repeat(self, on: bool):
        mode = "all" if on else "off"
        self.engine.set_repeat(mode)

    @staticmethod
    def _fmt(ms: int) -> str:
        if ms <= 0:
            return "0:00"
        s = ms // 1000
        return f"{s // 60}:{s % 60:02d}"

    # ── drag ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
