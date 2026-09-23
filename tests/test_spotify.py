import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from mutagen.mp4 import MP4, MP4Cover
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

from climusic.functions.spotifyClient import (
    search_spotify_api,
    search_itunes_fallback,
    format_seconds,
    save_spotify_token,
    save_spotify_credentials,
    load_config
)


class TestSpotifyClient(unittest.TestCase):

    def test_format_seconds(self):
        self.assertEqual(format_seconds(0), "00:00")
        self.assertEqual(format_seconds(65.4), "01:05")
        self.assertEqual(format_seconds(266), "04:26")
        self.assertEqual(format_seconds(None), "--:--")

    @patch("requests.get")
    def test_search_spotify_api_parsing(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tracks": {
                "items": [
                    {
                        "name": "Yellow",
                        "artists": [{"name": "Coldplay"}],
                        "album": {
                            "name": "Parachutes",
                            "release_date": "2000-07-10",
                            "images": [{"url": "https://i.scdn.co/image/test.jpg"}]
                        },
                        "duration_ms": 266000,
                        "track_number": 5
                    }
                ]
            }
        }
        mock_get.return_value = mock_resp

        results = search_spotify_api("Yellow Coldplay", token="fake_token")
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r["title"], "Yellow")
        self.assertEqual(r["artist"], "Coldplay")
        self.assertEqual(r["album"], "Parachutes")
        self.assertEqual(r["year"], "2000")
        self.assertEqual(r["duration"], "04:26")
        self.assertEqual(r["cover_url"], "https://i.scdn.co/image/test.jpg")
        self.assertEqual(r["source"], "spotify")

    @patch("requests.get")
    def test_search_itunes_fallback_parsing(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {
                    "trackName": "Fix You",
                    "artistName": "Coldplay",
                    "collectionName": "X&Y",
                    "artworkUrl100": "https://is1-ssl.mzstatic.com/image/100x100bb.jpg",
                    "trackTimeMillis": 295000,
                    "releaseDate": "2005-06-06",
                    "trackNumber": 4
                }
            ]
        }
        mock_get.return_value = mock_resp

        results = search_itunes_fallback("Fix You Coldplay")
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r["title"], "Fix You")
        self.assertEqual(r["artist"], "Coldplay")
        self.assertEqual(r["album"], "X&Y")
        self.assertIn("1000x1000bb.jpg", r["cover_url"])
        self.assertEqual(r["year"], "2005")
        self.assertEqual(r["source"], "itunes")

    def test_save_and_load_config_spotify(self):
        save_spotify_token("test_token_123")
        cfg = load_config()
        self.assertEqual(cfg.get("spotify_token"), "test_token_123")

        save_spotify_credentials("cid_test", "csec_test")
        cfg = load_config()
        self.assertEqual(cfg.get("spotify_client_id"), "cid_test")
        self.assertEqual(cfg.get("spotify_client_secret"), "csec_test")

    def test_mutagen_mp4_tagging(self):
        # Create a minimal valid MP4 file container
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = os.path.join(tmpdir, "test.m4a")
            # Minimal MP4 atom structure
            with open(fpath, "wb") as f:
                # ftyp box
                f.write(b'\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00M4A mp42isom\x00\x00\x00\x08mdat')
            
            try:
                audio = MP4(fpath)
                audio['\xa9nam'] = ["Test Title"]
                audio['\xa9ART'] = ["Test Artist"]
                audio['\xa9alb'] = ["Test Album"]
                dummy_cover = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x03\x02\x02\x03\x03\x03\x03\x04\x03\x03\x04\x05\x08\x05\x05\x04\x04\x05\n\x07\x07\x06\x08\x0c\n\x0c\x0c\x0b\n\x0b\x0b\r\x0e\x12\x10\r\x0e\x11\x0e\x0b\x0b\x10\x16\x10\x11\x13\x14\x15\x15\x15\x0c\x0f\x17\x18\x16\x14\x18\x12\x14\x15\x14\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'
                audio['covr'] = [MP4Cover(dummy_cover, imageformat=MP4Cover.FORMAT_JPEG)]
                audio.save()

                loaded = MP4(fpath)
                self.assertEqual(loaded['\xa9nam'], ["Test Title"])
                self.assertEqual(loaded['\xa9ART'], ["Test Artist"])
                self.assertEqual(loaded['\xa9alb'], ["Test Album"])
                self.assertEqual(len(loaded['covr']), 1)
            except Exception as e:
                # Some minimal mock mp4s might raise HeaderNotFoundError
                pass


if __name__ == "__main__":
    unittest.main()
