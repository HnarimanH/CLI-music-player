import json
import base64
import requests
from typing import Optional, Dict, Any, List
def format_seconds(seconds: Optional[float]) -> str:
    if seconds is None or seconds < 0:
        return "--:--"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


from climusic.musicController import CONFIG_PATH

DEFAULT_INITIAL_TOKEN = "BQDFhwcsNYbXWdsdSchLg6Vrvj83Esyb5j-UPCBTgEzhfmwK52DcJ8FSgavWmTiblP1CEGmd8esZq0U4KmZOw2T9keDga-YEwxMZaWVHEpogrsTqI_teOrtO2PCtWGY4tC_7KQer9C93F_DejfpV2HlrA4BXqvUMptE20IVq1k_kT4NT-4XR_ojHrPNJY9W-B-xjA8-8oMWdBnT7m-dMWDRSskb9jPOVodgmYXyq7U67AeYACl1VAPlCYJLm5cKaxKFwoV7llB4lTmhnizoB31TEf33uvcBWy5ucSMTekAX1RtWoKjaDVWcfNU33_Ny_aYu3C1A"


def load_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Failed to save config: {e}")


def save_spotify_token(token: str) -> None:
    cfg = load_config()
    cfg["spotify_token"] = token.strip()
    save_config(cfg)


def save_spotify_credentials(client_id: str, client_secret: str) -> None:
    cfg = load_config()
    cfg["spotify_client_id"] = client_id.strip()
    cfg["spotify_client_secret"] = client_secret.strip()
    save_config(cfg)


def get_spotify_token() -> Optional[str]:
    cfg = load_config()
    token = cfg.get("spotify_token")
    if token:
        return token

    # Check client credentials flow
    client_id = cfg.get("spotify_client_id")
    client_secret = cfg.get("spotify_client_secret")
    if client_id and client_secret:
        refreshed = refresh_token_with_credentials(client_id, client_secret)
        if refreshed:
            save_spotify_token(refreshed)
            return refreshed

    # Fallback to default user-provided initial token
    return DEFAULT_INITIAL_TOKEN


def refresh_token_with_credentials(client_id: str, client_secret: str) -> Optional[str]:
    try:
        auth_str = f"{client_id}:{client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        r = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data, timeout=8)
        if r.status_code == 200:
            return r.json().get("access_token")
    except Exception:
        pass
    return None


def search_spotify_api(query: str, token: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
    """Queries Spotify Web API search endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query, "type": "track", "limit": limit}
    r = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params, timeout=7)
    if r.status_code == 200:
        data = r.json()
        items = data.get("tracks", {}).get("items", [])
        results = []
        for it in items:
            title = it.get("name", "Unknown Title")
            artists = ", ".join(a["name"] for a in it.get("artists", [])) or "Unknown Artist"
            album = it.get("album", {}).get("name", "Unknown Album")
            images = it.get("album", {}).get("images", [])
            cover_url = images[0]["url"] if images else ""
            release_date = it.get("album", {}).get("release_date", "")
            year = release_date[:4] if release_date else ""
            duration_s = it.get("duration_ms", 0) / 1000.0
            results.append({
                "title": title,
                "artist": artists,
                "album": album,
                "duration": format_seconds(duration_s),
                "duration_seconds": duration_s,
                "cover_url": cover_url,
                "year": year,
                "track_num": it.get("track_number", 1),
                "source": "spotify"
            })
        return results
    return None


def search_itunes_fallback(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fallback search using iTunes Search API for zero-config metadata and artwork."""
    try:
        params = {"term": query, "entity": "song", "limit": limit}
        r = requests.get("https://itunes.apple.com/search", params=params, timeout=7)
        if r.status_code == 200:
            items = r.json().get("results", [])
            results = []
            for it in items:
                title = it.get("trackName", "Unknown Title")
                artist = it.get("artistName", "Unknown Artist")
                album = it.get("collectionName", "Unknown Album")
                art100 = it.get("artworkUrl100", "")
                cover_url = art100.replace("100x100bb.jpg", "1000x1000bb.jpg") if art100 else ""
                duration_s = it.get("trackTimeMillis", 0) / 1000.0
                rel_date = it.get("releaseDate", "")
                year = rel_date[:4] if rel_date else ""
                results.append({
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "duration": format_seconds(duration_s),
                    "duration_seconds": duration_s,
                    "cover_url": cover_url,
                    "year": year,
                    "track_num": it.get("trackNumber", 1),
                    "source": "itunes"
                })
            return results
    except Exception:
        pass
    return []


def search_tracks(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Searches for tracks using Spotify Web API.
    Falls back to iTunes search if Spotify token is expired or unauthorized.
    """
    token = get_spotify_token()
    if token:
        try:
            results = search_spotify_api(query, token, limit=limit)
            if results is not None:
                return results
        except Exception:
            pass

    # If Spotify fails (e.g. 401 token expired or rate limit), use iTunes fallback
    return search_itunes_fallback(query, limit=limit)
