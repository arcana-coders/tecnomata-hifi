"""Cliente Subsonic / OpenSubsonic para Navidrome."""
import hashlib
import secrets
from urllib.parse import urlencode
import requests

API_VERSION = "1.16.1"
CLIENT_NAME = "TecnomataHiFi"


class SubsonicClient:
    """Interfaz HTTP contra la API Subsonic de Navidrome."""

    def __init__(self, server_url: str, username: str, password: str):
        self.server_url = server_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers["User-Agent"] = CLIENT_NAME

    # ── autenticación ──

    def _auth_params(self) -> dict:
        salt = secrets.token_hex(8)
        token = hashlib.md5((self.password + salt).encode()).hexdigest()
        return {
            "u": self.username,
            "t": token,
            "s": salt,
            "v": API_VERSION,
            "c": CLIENT_NAME,
            "f": "json",
        }

    # ── transporte ──

    def _url(self, endpoint: str) -> str:
        return f"{self.server_url}/rest/{endpoint}"

    def _get(self, endpoint: str, **params) -> dict:
        all_params = {**self._auth_params(), **params}
        resp = self.session.get(self._url(endpoint), params=all_params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        sr = data.get("subsonic-response", {})
        if sr.get("status") != "ok":
            err = sr.get("error", {})
            raise RuntimeError(
                f"Subsonic API error {err.get('code', '?')}: {err.get('message', 'desconocido')}"
            )
        return sr

    # ── endpoints ──

    def ping(self) -> bool:
        try:
            self._get("ping")
            return True
        except Exception:
            return False

    def get_playlists(self) -> list:
        resp = self._get("getPlaylists")
        pls = resp.get("playlists", {}).get("playlist", [])
        return pls if isinstance(pls, list) else [pls]

    def get_playlist(self, playlist_id: str) -> dict:
        resp = self._get("getPlaylist", id=playlist_id)
        return resp.get("playlist", {})

    def get_random_songs(self, count: int = 50) -> list:
        resp = self._get("getRandomSongs", size=count)
        songs = resp.get("randomSongs", {}).get("song", [])
        return songs if isinstance(songs, list) else [songs]

    def search(self, query: str, song_count: int = 30) -> list:
        resp = self._get(
            "search3", query=query, songCount=song_count, albumCount=0, artistCount=0
        )
        songs = resp.get("searchResult3", {}).get("song", [])
        return songs if isinstance(songs, list) else [songs]

    def search3_full(self, query: str, song_count: int = 40, album_count: int = 8, artist_count: int = 8) -> dict:
        """Búsqueda integral en todo el servidor Navidrome: canciones, álbumes y artistas."""
        resp = self._get(
            "search3",
            query=query,
            songCount=song_count,
            albumCount=album_count,
            artistCount=artist_count,
        )
        res = resp.get("searchResult3", {})
        songs = res.get("song", [])
        if isinstance(songs, dict):
            songs = [songs]
        albums = res.get("album", [])
        if isinstance(albums, dict):
            albums = [albums]
        artists = res.get("artist", [])
        if isinstance(artists, dict):
            artists = [artists]
        return {
            "songs": songs,
            "albums": albums,
            "artists": artists,
        }

    def get_artist(self, artist_id: str) -> dict:
        """Obtiene detalles y álbumes de un artista."""
        resp = self._get("getArtist", id=artist_id)
        return resp.get("artist", {})

    def get_album(self, album_id: str) -> dict:
        """Obtiene canciones de un álbum."""
        resp = self._get("getAlbum", id=album_id)
        return resp.get("album", {})

    def scrobble(self, song_id: str):
        try:
            self._get("scrobble", id=song_id)
        except Exception:
            pass

    # ── URLs de streaming / recursos ──

    def stream_url(self, song_id: str, fmt: str = "raw") -> str:
        params = {**self._auth_params(), "id": song_id, "format": fmt}
        return f"{self._url('stream')}?{urlencode(params)}"

    def cover_art_url(self, cover_id: str, size: int = 300) -> str:
        params = {**self._auth_params(), "id": cover_id, "size": size}
        return f"{self._url('getCoverArt')}?{urlencode(params)}"

    def get_cover_art_bytes(self, cover_id: str, size: int = 300) -> bytes:
        url = self.cover_art_url(cover_id, size)
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.content
        except Exception:
            return b""

    # ── letras (OpenSubsonic & Subsonic estándar) ──

    def get_lyrics(self, song_id: str, artist: str = "", title: str = "") -> dict:
        """Obtiene letras sincronizadas vía getLyricsBySongId con fallback a getLyrics."""
        # 1. Intentar OpenSubsonic getLyricsBySongId
        try:
            resp = self._get("getLyricsBySongId", id=song_id)
            lyrics_list = resp.get("lyricsList", {})
            if lyrics_list.get("structuredLyrics"):
                return lyrics_list
        except Exception:
            pass

        # 2. Fallback a getLyrics tradicional
        try:
            params = {}
            if artist and title:
                params["artist"] = artist
                params["title"] = title
            else:
                params["id"] = song_id
            resp = self._get("getLyrics", **params)
            return resp.get("lyrics", {})
        except Exception:
            return {}
