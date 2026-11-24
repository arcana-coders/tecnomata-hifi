"""Persistencia de configuración para Tecnomata Hi-Fi."""
import json
import base64
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "tecnomata-hifi"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "server_url": "",
    "username": "",
    "password_b64": "",
    "volume": 0.7,
    "orientation": "horizontal",  # "horizontal" | "vertical"
    "bar_x": -1,
    "bar_y": 20,
    "bar_width": 740,
    "vert_x": 20,
    "vert_y": 100,
    "vert_width": 200,
    "vert_height": 520,
    "last_playlist_id": None,
    "last_song_id": None,
    "shuffle": False,
    "repeat": "off",
}


class Config:
    """Lee y guarda la configuración en JSON local."""

    def __init__(self):
        self._data: dict = dict(DEFAULTS)
        self.load()

    # -- persistencia --

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._data.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # -- accesores genéricos --

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    # -- credenciales --

    @property
    def server_url(self) -> str:
        return self._data.get("server_url", DEFAULTS["server_url"]).rstrip("/")

    @property
    def username(self) -> str:
        return self._data.get("username", "")

    @property
    def password(self) -> str:
        b64 = self._data.get("password_b64", "")
        if b64:
            try:
                return base64.b64decode(b64).decode("utf-8")
            except Exception:
                return ""
        return ""

    def set_credentials(self, url: str, username: str, password: str):
        self._data["server_url"] = url
        self._data["username"] = username
        self._data["password_b64"] = base64.b64encode(password.encode()).decode()
        self.save()

    @property
    def is_configured(self) -> bool:
        return bool(self._data.get("username") and self._data.get("password_b64"))
