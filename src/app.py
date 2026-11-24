"""Orquestador principal de Tecnomata Hi-Fi."""
import sys
from PySide6.QtCore import Qt, QRect, QUrl
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QSystemTrayIcon, QMenu,
)

from src.config import Config
from src.api.subsonic import SubsonicClient
from src.player.engine import PlayerEngine
from src.ui.bar import HiFiBar
from src.ui.expanded import ExpandedPanel
from src.ui.lyrics import LyricsPopup
from src.ui import styles


# ═══════════════════════════════════════════
#  Diálogo de Login
# ═══════════════════════════════════════════

class LoginDialog(QDialog):
    """Pide URL del servidor + credenciales Navidrome."""

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Tecnomata Hi-Fi — Conexión Navidrome")
        self.setFixedSize(420, 270)
        self.setStyleSheet(styles.login_qss())

        lay = QVBoxLayout(self)
        lay.setSpacing(6)

        title = QLabel("🎵  SONY Hi-Fi · Navidrome")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        lay.addSpacing(6)

        lay.addWidget(QLabel("Servidor Navidrome:"))
        self.url_input = QLineEdit(config.server_url)
        self.url_input.setPlaceholderText("https://tu-servidor.example")
        lay.addWidget(self.url_input)

        lay.addWidget(QLabel("Usuario:"))
        self.user_input = QLineEdit(config.username)
        self.user_input.setPlaceholderText("admin")
        lay.addWidget(self.user_input)

        lay.addWidget(QLabel("Contraseña:"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("••••••••")
        lay.addWidget(self.pass_input)

        lay.addSpacing(6)
        btns = QHBoxLayout()
        cancel = QPushButton("Cancelar")
        cancel.setObjectName("cancel")
        cancel.clicked.connect(self.reject)
        connect = QPushButton("▶  Conectar")
        connect.clicked.connect(self._try_connect)
        connect.setDefault(True)
        btns.addWidget(cancel)
        btns.addStretch()
        btns.addWidget(connect)
        lay.addLayout(btns)

    def _try_connect(self):
        url = self.url_input.text().strip()
        user = self.user_input.text().strip()
        pwd = self.pass_input.text()

        if not all([url, user, pwd]):
            QMessageBox.warning(self, "Faltan datos", "Todos los campos son requeridos.")
            return

        client = SubsonicClient(url, user, pwd)
        if client.ping():
            self.config.set_credentials(url, user, pwd)
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error de conexión",
                "No se pudo conectar al servidor Navidrome.\n"
                "Verifica la URL, usuario y contraseña."
            )


# ═══════════════════════════════════════════
#  Aplicación principal
# ═══════════════════════════════════════════

class HiFiApp:
    """Orquesta todas las partes de Tecnomata Hi-Fi."""

    def __init__(self):
        self.config = Config()
        self.client: SubsonicClient | None = None
        self.engine: PlayerEngine | None = None
        self.bar: HiFiBar | None = None
        self.expanded: ExpandedPanel | None = None
        self.lyrics: LyricsPopup | None = None
        self.tray: QSystemTrayIcon | None = None

    def start(self):
        """Punto de entrada: login → conectar → mostrar barra."""

        # Autenticación
        if not self.config.is_configured or not self._test_connection():
            if not self._show_login():
                sys.exit(0)

        # Inicializar cliente y motor
        self.client = SubsonicClient(
            self.config.server_url, self.config.username, self.config.password
        )
        self.engine = PlayerEngine(self.client)
        self.engine.volume = self.config.get("volume", 0.7)

        # Crear UI
        self.bar = HiFiBar(self.engine, self.client, self.config)
        self.expanded = ExpandedPanel(self.engine, self.client, self.config)
        self.lyrics = LyricsPopup(self.engine, self.client)

        # Conectar señales
        self.bar.expand_toggled.connect(self._toggle_expanded)
        self.bar.song_clicked.connect(self._toggle_lyrics)
        self.bar.settings_requested.connect(self._show_login)
        self.bar.orientation_changed.connect(self._on_orientation_changed)
        self.bar.bar_moved.connect(self._on_bar_moved)

        self.expanded.song_selected.connect(self.engine.play_index)
        self.expanded.playlist_selected.connect(self._load_playlist)
        self.expanded.play_direct_song.connect(self._play_direct_song)

        self.engine.track_changed.connect(self._on_track_changed)

        # System tray
        self._setup_tray()

        # Cargar datos
        self._load_initial_data()

        # Conectar limpieza en salida
        qapp = QApplication.instance()
        if qapp:
            qapp.aboutToQuit.connect(self.cleanup)

        # Mostrar barra
        self.bar.show()

    def cleanup(self):
        """Detiene completamente la reproducción y libera hilos de audio al cerrar la app."""
        if hasattr(self, "engine") and self.engine:
            try:
                self.engine.stop()
                self.engine._player.setSource(QUrl())
            except Exception:
                pass
        if hasattr(self, "lyrics") and self.lyrics:
            try:
                if self.lyrics._worker and self.lyrics._worker.isRunning():
                    self.lyrics._worker.cancel()
            except Exception:
                pass
        if hasattr(self, "tray") and self.tray:
            try:
                self.tray.hide()
            except Exception:
                pass

    # ── login ──

    def _show_login(self) -> bool:
        dlg = LoginDialog(self.config)
        return dlg.exec() == QDialog.Accepted

    def _test_connection(self) -> bool:
        try:
            c = SubsonicClient(
                self.config.server_url, self.config.username, self.config.password
            )
            return c.ping()
        except Exception:
            return False

    # ── datos ──

    def _load_initial_data(self):
        try:
            playlists = self.client.get_playlists()
            self.expanded.set_playlists(playlists)

            last = self.config.get("last_playlist_id")
            target = None
            if last:
                for pl in playlists:
                    if pl.get("id") == last:
                        target = last
                        break
            if not target and playlists:
                target = playlists[0].get("id")
            if target:
                self._load_playlist(target)
        except Exception as e:
            self.bar.show_error(str(e))

    def _load_playlist(self, playlist_id: str):
        try:
            pl = self.client.get_playlist(playlist_id)
            songs = pl.get("entry", [])
            if isinstance(songs, dict):
                songs = [songs]
            self.engine.load_playlist(songs)
            self.config.set("last_playlist_id", playlist_id)
        except Exception as e:
            self.bar.show_error(str(e))

    def _play_direct_song(self, song: dict):
        """Reproduce una canción directa seleccionada desde el buscador."""
        # Se añade a una lista temporal o se reproduce
        current_list = list(self.engine.playlist)
        current_list.insert(0, song)
        self.engine.load_playlist(current_list)
        self.engine.play_index(0)

    # ── Posicionamiento acoplado y seguro en pantalla ──

    def _on_bar_moved(self, x: int, y: int):
        """Mantiene los paneles expandido y de letras acoplados a la barra mientras se mueve."""
        self._reposition_aux_panels()

    def _reposition_aux_panels(self):
        if not self.bar:
            return

        bar_geo = self.bar.geometry()
        screen = self.bar.screen() or QApplication.primaryScreen()
        sg = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

        # 1. Reposicionar panel expandido si está visible
        if self.expanded and self.expanded.isVisible():
            if self.bar.orientation == "horizontal":
                exp_w = min(max(bar_geo.width(), 650), sg.width() - 20)
                exp_h = 390
                exp_x = bar_geo.left()
                exp_y = bar_geo.bottom() + 3

                # Si se sale por abajo de la pantalla, abrir hacia arriba
                if exp_y + exp_h > sg.bottom():
                    exp_y = bar_geo.top() - exp_h - 3

                # Clamping horizontal para no salirse de los bordes de pantalla
                if exp_x + exp_w > sg.right():
                    exp_x = sg.right() - exp_w
                if exp_x < sg.left():
                    exp_x = sg.left()

                self.expanded.resize(exp_w, exp_h)
                self.expanded.move(exp_x, exp_y)
            else:
                # Barra vertical lateral
                exp_w = min(560, sg.width() - bar_geo.width() - 30)
                exp_h = min(max(bar_geo.height(), 400), sg.height() - 40)

                # Intentar abrir a la derecha de la barra
                exp_x = bar_geo.right() + 4
                exp_y = bar_geo.top()

                # Si no cabe a la derecha, abrir a la izquierda
                if exp_x + exp_w > sg.right():
                    exp_x = bar_geo.left() - exp_w - 4

                # Si tampoco cabe a la izquierda (pantalla muy estrecha)
                if exp_x < sg.left():
                    exp_x = sg.left() + 5

                if exp_y + exp_h > sg.bottom():
                    exp_y = sg.bottom() - exp_h
                if exp_y < sg.top():
                    exp_y = sg.top()

                self.expanded.resize(exp_w, exp_h)
                self.expanded.move(exp_x, exp_y)

        # 2. Reposicionar letras si están visibles
        if self.lyrics and self.lyrics.isVisible():
            lyr_w = self.lyrics.width()
            lyr_h = self.lyrics.height()

            # Tomar como referencia el panel expandido si está abierto, sino la barra
            ref_geo = self.expanded.geometry() if (self.expanded and self.expanded.isVisible()) else bar_geo

            if self.bar.orientation == "horizontal":
                # Intentar abrir a la derecha
                lyr_x = ref_geo.right() + 8
                lyr_y = ref_geo.top()

                # Si se sale por la derecha, probar a la izquierda
                if lyr_x + lyr_w > sg.right():
                    lyr_x = ref_geo.left() - lyr_w - 8

                # Si se sale por la izquierda o no cabe
                if lyr_x < sg.left():
                    lyr_x = max(sg.left() + 10, min(ref_geo.left(), sg.right() - lyr_w - 10))
                    lyr_y = ref_geo.bottom() + 8
            else:
                # Barra lateral: intentar a la derecha de ref_geo
                lyr_x = ref_geo.right() + 6
                lyr_y = ref_geo.top()

                # Si se sale por la derecha de la pantalla, probar a la izquierda de la barra
                if lyr_x + lyr_w > sg.right():
                    lyr_x = bar_geo.left() - lyr_w - 6

                # NUNCA salirse por el borde izquierdo
                if lyr_x < sg.left():
                    lyr_x = sg.left() + 10

            # NUNCA salirse por arriba o abajo
            if lyr_y + lyr_h > sg.bottom():
                lyr_y = sg.bottom() - lyr_h - 10
            if lyr_y < sg.top():
                lyr_y = sg.top() + 10

            self.lyrics.move(lyr_x, lyr_y)

    # ── UI toggles ──

    def _toggle_expanded(self, show: bool):
        if show:
            self.expanded.show()
            self._reposition_aux_panels()
        else:
            self.expanded.hide()
            self._reposition_aux_panels()

    def _toggle_lyrics(self):
        if self.lyrics.isVisible():
            self.lyrics.hide()
            return
        song = self.engine.current_song
        if not song:
            return
        self.lyrics.load_lyrics(song)
        self.lyrics.show()
        self._reposition_aux_panels()

    def _on_orientation_changed(self, orientation: str):
        self._reposition_aux_panels()

    def _on_track_changed(self, song: dict):
        if self.lyrics.isVisible():
            self.lyrics.load_lyrics(song)

    # ── system tray ──

    def _setup_tray(self):
        self.tray = QSystemTrayIcon()
        self.tray.setToolTip("Tecnomata Hi-Fi — Sony Retro Boombox")

        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background: {styles.CHASSIS_DARK};
                color: {styles.TEXT_LIGHT};
                border: 1px solid {styles.CHASSIS_BORDER};
                font-family: {styles.FONT_UI};
            }}
            QMenu::item:selected {{
                background: {styles.CHASSIS_LIGHT};
                color: {styles.ACCENT};
            }}
        """)
        menu.addAction("🎵  Mostrar / Ocultar", self._toggle_visibility)
        menu.addAction("⚙  Configuración…", lambda: self._show_login())
        menu.addSeparator()
        menu.addAction("✕  Salir", QApplication.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_click)
        self.tray.show()

    def _toggle_visibility(self):
        if self.bar.isVisible():
            self.bar.hide()
            self.expanded.hide()
            self.lyrics.hide()
        else:
            self.bar.show()

    def _on_tray_click(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_visibility()
