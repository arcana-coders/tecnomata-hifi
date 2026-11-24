"""Proveedor y buscador automático de letras: caché local, Navidrome, LRCLIB y fallback online."""
import json
import re
from pathlib import Path
from urllib.parse import quote
import requests

LRCLIB_BASE = "https://lrclib.net/api"
LYRICS_OVH_BASE = "https://api.lyrics.ovh/v1"
USER_AGENT = "TecnomataHiFi/1.0 (https://github.com/arcana-coders/tecnomata-hifi)"


def parse_lrc(lrc_text: str) -> list[dict]:
    """Convierte texto en formato .lrc ([mm:ss.xx] texto) a lista estructurada con milisegundos."""
    lines = []
    pattern = re.compile(r'\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\]')

    for raw_line in lrc_text.splitlines():
        matches = list(pattern.finditer(raw_line))
        if not matches:
            continue
        last_match = matches[-1]
        text = raw_line[last_match.end():].strip()

        for m in matches:
            mins = int(m.group(1))
            secs = int(m.group(2))
            millis_str = m.group(3)
            if millis_str:
                if len(millis_str) == 2:
                    millis = int(millis_str) * 10
                elif len(millis_str) == 1:
                    millis = int(millis_str) * 100
                else:
                    millis = int(millis_str[:3])
            else:
                millis = 0
            start_ms = mins * 60000 + secs * 1000 + millis
            lines.append({"start": start_ms, "value": text})

    lines.sort(key=lambda x: x["start"])
    return lines


def clean_search_title(title: str) -> str:
    """Remueve sufijos y anotaciones que entorpecen la búsqueda exacta en APIs de letras."""
    t = title
    # Quitar paréntesis con anotaciones comunes: (Remastered...), (Live...), (2011 Remaster), etc.
    t = re.sub(r'\s*\([^)]*(?:remaster|live|version|edit|mono|stereo|bonus|deluxe|mix|anniversary|radio)[^)]*\)', '', t, flags=re.I)
    # Quitar corchetes: [Remastered], [Live], etc.
    t = re.sub(r'\s*\[[^\]]*(?:remaster|live|version|edit|mono|stereo|bonus|deluxe|mix|anniversary|radio)[^\]]*\]', '', t, flags=re.I)
    # Quitar " - Remastered 2011", " - Live", etc.
    t = re.sub(r'\s*-\s*(?:remastered|live|mono|stereo|single version|radio edit).*$', '', t, flags=re.I)
    # Quitar "feat. ..." o "ft. ..."
    t = re.sub(r'\s*(?:feat\.|ft\.).*$', '', t, flags=re.I)
    return t.strip()


def clean_search_artist(artist: str) -> str:
    """Extrae el artista principal si incluye colaboradores."""
    a = re.sub(r'\s*(?:feat\.|ft\.).*$', '', artist, flags=re.I)
    if " / " in a:
        a = a.split(" / ")[0]
    if " & " in a:
        a = a.split(" & ")[0]
    return a.strip()


class LyricsProvider:
    """Gestor de letras con caché en disco y resolución multinivel."""

    def __init__(self, cache_dir: Path = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".config" / "tecnomata-hifi" / "lyrics"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def _cache_path(self, artist: str, title: str) -> Path:
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', f"{artist} - {title}".lower().strip())[:120]
        return self.cache_dir / f"{safe_name}.json"

    def get_cached(self, artist: str, title: str) -> dict | None:
        """Recupera letras de la caché local si existen."""
        path = self._cache_path(artist, title)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def save_cached(self, artist: str, title: str, data: dict):
        """Guarda letras en la caché local para acceso offline instantáneo."""
        path = self._cache_path(artist, title)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def fetch_lrclib(
        self, artist: str, title: str, album: str = "", duration: int = 0
    ) -> dict | None:
        """Busca letras sincronizadas en LRCLIB con estrategias exacta, limpia y difusa."""
        # 1. Búsqueda exacta
        params = {"artist_name": artist, "track_name": title}
        if album:
            params["album_name"] = album
        if duration > 0:
            params["duration"] = int(duration)

        try:
            resp = self.session.get(f"{LRCLIB_BASE}/get", params=params, timeout=7)
            if resp.status_code == 200:
                data = resp.json()
                return self._format_lrclib_result(data)
        except Exception:
            pass

        # 2. Búsqueda con título y artista normalizados
        clean_t = clean_search_title(title)
        clean_a = clean_search_artist(artist)
        if clean_t != title or clean_a != artist:
            try:
                resp = self.session.get(
                    f"{LRCLIB_BASE}/get",
                    params={"artist_name": clean_a, "track_name": clean_t},
                    timeout=7,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return self._format_lrclib_result(data)
            except Exception:
                pass

        # 3. Búsqueda difusa en el catálogo de LRCLIB
        try:
            q = f"{clean_a} {clean_t}".strip()
            resp = self.session.get(f"{LRCLIB_BASE}/search", params={"q": q}, timeout=7)
            if resp.status_code == 200:
                results = resp.json()
                if isinstance(results, list) and results:
                    best = None
                    # Priorizar aquel con syncedLyrics y duración cercana
                    for item in results:
                        has_synced = bool(item.get("syncedLyrics"))
                        dur_diff = abs(item.get("duration", 0) - duration) if duration > 0 else 0
                        if has_synced and (duration == 0 or dur_diff <= 12):
                            best = item
                            break
                        if not best and (has_synced or item.get("plainLyrics")):
                            best = item

                    if best:
                        return self._format_lrclib_result(best)
        except Exception:
            pass

        return None

    def fetch_lyrics_ovh(self, artist: str, title: str) -> dict | None:
        """Fallback para letras planas no sincronizadas vía Lyrics.ovh."""
        clean_a = clean_search_artist(artist)
        clean_t = clean_search_title(title)
        try:
            url = f"{LYRICS_OVH_BASE}/{quote(clean_a)}/{quote(clean_t)}"
            resp = self.session.get(url, timeout=6)
            if resp.status_code == 200:
                lyrics_text = resp.json().get("lyrics", "").strip()
                if lyrics_text:
                    return {
                        "synced": False,
                        "structuredLyrics": [],
                        "plainLyrics": lyrics_text,
                        "source": "lyrics.ovh",
                        "instrumental": False,
                    }
        except Exception:
            pass
        return None

    def _format_lrclib_result(self, data: dict) -> dict:
        synced_lrc = data.get("syncedLyrics") or ""
        plain = data.get("plainLyrics") or ""
        instrumental = data.get("instrumental", False)

        structured_lines = parse_lrc(synced_lrc) if synced_lrc else []
        has_synced = bool(structured_lines)

        structured_entry = [{"synced": has_synced, "line": structured_lines}] if has_synced else []

        return {
            "synced": has_synced,
            "structuredLyrics": structured_entry,
            "plainLyrics": plain,
            "raw_lrc": synced_lrc,
            "source": "LRCLIB",
            "instrumental": instrumental,
        }

    def resolve_lyrics(self, song: dict, subsonic_client=None) -> dict | None:
        """Resuelve letras consultando en orden: Caché local → Navidrome → LRCLIB → lyrics.ovh."""
        artist = song.get("artist", "").strip()
        title = song.get("title", song.get("path", "")).strip()
        album = song.get("album", "").strip()
        duration = song.get("duration", 0)
        song_id = song.get("id", "")

        # 1. Caché local
        cached = self.get_cached(artist, title)
        if cached:
            return cached

        # 2. Servidor Navidrome
        if subsonic_client and song_id:
            try:
                nav_data = subsonic_client.get_lyrics(song_id, artist=artist, title=title)
                structured = nav_data.get("structuredLyrics", [])
                plain = nav_data.get("value") or nav_data.get("content")
                if structured or plain:
                    res = {
                        "synced": any(s.get("synced") for s in structured) if structured else False,
                        "structuredLyrics": structured,
                        "plainLyrics": plain or "",
                        "source": "Navidrome",
                        "instrumental": False,
                    }
                    self.save_cached(artist, title, res)
                    return res
            except Exception:
                pass

        # 3. LRCLIB (online con soporte .lrc)
        lrclib_res = self.fetch_lrclib(artist, title, album=album, duration=duration)
        if lrclib_res:
            self.save_cached(artist, title, lrclib_res)
            return lrclib_res

        # 4. Fallback lyrics.ovh (texto plano)
        ovh_res = self.fetch_lyrics_ovh(artist, title)
        if ovh_res:
            self.save_cached(artist, title, ovh_res)
            return ovh_res

        return None
