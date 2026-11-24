"""Motor de reproducción: envuelve QMediaPlayer con gestión de playlist."""
import random
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class PlayerEngine(QObject):
    """Reproduce canciones vía streaming Subsonic y gestiona la cola."""

    # ── señales ──
    track_changed = Signal(dict)       # canción actual (dict Subsonic)
    position_changed = Signal(int)     # ms
    duration_changed = Signal(int)     # ms
    state_changed = Signal(str)        # "playing" | "paused" | "stopped"
    playlist_loaded = Signal(list)     # lista de dicts
    shuffle_changed = Signal(bool)     # True | False
    repeat_changed = Signal(str)       # "off" | "all" | "one"
    error_occurred = Signal(str)

    def __init__(self, subsonic_client, parent=None):
        super().__init__(parent)
        self.client = subsonic_client

        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)

        self._playlist: list[dict] = []
        self._current_index: int = -1
        self._shuffle: bool = False
        self._repeat: str = "off"       # off | all | one
        self._shuffle_history: list[int] = []

        # conectar señales internas
        self._player.positionChanged.connect(self.position_changed.emit)
        self._player.durationChanged.connect(self.duration_changed.emit)
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(self._on_error)

    # ── propiedades ──

    @property
    def volume(self) -> float:
        return self._audio.volume()

    @volume.setter
    def volume(self, v: float):
        self._audio.setVolume(max(0.0, min(1.0, v)))

    @property
    def current_song(self) -> dict:
        if 0 <= self._current_index < len(self._playlist):
            return self._playlist[self._current_index]
        return {}

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def is_playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlayingState

    @property
    def is_paused(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PausedState

    @property
    def playlist(self) -> list:
        return self._playlist

    @property
    def shuffle(self) -> bool:
        return self._shuffle

    @property
    def repeat(self) -> str:
        return self._repeat

    @property
    def position(self) -> int:
        return self._player.position()

    @property
    def duration(self) -> int:
        return self._player.duration()

    # ── playlist ──

    def load_playlist(self, songs: list):
        self._playlist = songs if isinstance(songs, list) else [songs]
        self._current_index = -1
        self._shuffle_history.clear()
        self.playlist_loaded.emit(self._playlist)

    # ── reproducción ──

    def play_index(self, index: int):
        if 0 <= index < len(self._playlist):
            self._current_index = index
            song = self._playlist[index]
            url = self.client.stream_url(song["id"])
            self._player.setSource(QUrl(url))
            self._player.play()
            self.track_changed.emit(song)
            self.state_changed.emit("playing")
            # scrobble en hilo de fondo sería ideal, pero OK síncrono
            self.client.scrobble(song["id"])

    def play(self):
        if self._current_index < 0 and self._playlist:
            self.play_index(0)
        elif self._current_index >= 0:
            self._player.play()
            self.state_changed.emit("playing")

    def pause(self):
        self._player.pause()
        self.state_changed.emit("paused")

    def toggle(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def stop(self):
        self._player.stop()
        self.state_changed.emit("stopped")

    def next_track(self):
        if not self._playlist:
            return
        if self._shuffle:
            pool = [i for i in range(len(self._playlist)) if i != self._current_index]
            if pool:
                self._shuffle_history.append(self._current_index)
                self.play_index(random.choice(pool))
        else:
            nxt = self._current_index + 1
            if nxt >= len(self._playlist):
                if self._repeat == "all":
                    nxt = 0
                else:
                    self.stop()
                    return
            self.play_index(nxt)

    def prev_track(self):
        if not self._playlist:
            return
        if self._shuffle and self._shuffle_history:
            self.play_index(self._shuffle_history.pop())
            return
        if self._player.position() > 3000:
            self._player.setPosition(0)
        else:
            prv = self._current_index - 1
            if prv < 0:
                prv = len(self._playlist) - 1 if self._repeat == "all" else 0
            self.play_index(prv)

    def seek(self, position_ms: int):
        self._player.setPosition(position_ms)

    def set_shuffle(self, enabled: bool):
        self._shuffle = enabled
        self._shuffle_history.clear()
        self.shuffle_changed.emit(enabled)

    def set_repeat(self, mode: str):
        self._repeat = mode
        self.repeat_changed.emit(mode)

    # ── callbacks internos ──

    def _on_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            if self._repeat == "one":
                self.play_index(self._current_index)
            else:
                self.next_track()

    def _on_error(self, error, message=""):
        err_msg = str(message) or str(error)
        self.error_occurred.emit(f"Error de reproducción: {err_msg}")
        self.state_changed.emit("stopped")
