import os
import tempfile
import unittest
from pathlib import Path

from climusic.functions.lyricsParser import (
    clean_title_and_artist,
    parse_lrc,
    get_active_line_index,
    format_time,
)
from climusic.functions.lyricsFetcher import (
    sanitize_filename,
    get_local_file_lyrics,
    get_cached_lyrics,
    save_lyrics_to_cache,
    load_lyrics_for_song,
    LYRICS_DIR,
)


class TestLyricsParser(unittest.TestCase):

    def test_clean_title_and_artist(self):
        # 1. YouTube video artifacts
        title, artist = clean_title_and_artist("Yellow (Official Music Video) [4K]", "Coldplay")
        self.assertEqual(title, "Yellow")
        self.assertEqual(artist, "Coldplay")

        # 2. Leading track numbers and lyric video
        title, artist = clean_title_and_artist("01. Viva La Vida (Lyrics)", "Coldplay")
        self.assertEqual(title, "Viva La Vida")
        self.assertEqual(artist, "Coldplay")

        # 3. Fallback to filename when title is Unknown
        title, artist = clean_title_and_artist("Unknown Title", "Unknown Artist", filename="Queen - Bohemian Rhapsody.mp3")
        self.assertEqual(title, "Bohemian Rhapsody")
        self.assertEqual(artist, "Queen")

        # 4. Remastered and audio tags
        title, artist = clean_title_and_artist("Hotel California (Remastered 2013) (Official Audio)", "Eagles")
        self.assertEqual(title, "Hotel California")
        self.assertEqual(artist, "Eagles")

        # 5. Packed 'Artist - Title' in title when artist is unknown or YouTube
        title, artist = clean_title_and_artist("Nirvana - Smells Like Teen Spirit (Official Video)", "YouTube")
        self.assertEqual(title, "Smells Like Teen Spirit")
        self.assertEqual(artist, "Nirvana")

        # 6. Channel suffix ' - Topic'
        title, artist = clean_title_and_artist("Yellow", "Coldplay - Topic")
        self.assertEqual(title, "Yellow")
        self.assertEqual(artist, "Coldplay")

    def test_parse_lrc_standard(self):
        sample = """[ti:Test Song]
[ar:Tester]
[00:05.50]Line one
[00:10.00]Line two
[00:15.250]Line three
"""
        res = parse_lrc(sample)
        self.assertTrue(res["synced"])
        self.assertEqual(len(res["lines"]), 3)
        self.assertAlmostEqual(res["lines"][0]["time"], 5.5)
        self.assertEqual(res["lines"][0]["text"], "Line one")
        self.assertAlmostEqual(res["lines"][1]["time"], 10.0)
        self.assertAlmostEqual(res["lines"][2]["time"], 15.25)

    def test_parse_lrc_multiple_timestamps_and_offset(self):
        sample = """[offset:500]
[00:02.00][00:08.00]Chorus line
[00:05.00]Verse line
"""
        # offset is +500ms -> +0.5s
        res = parse_lrc(sample)
        self.assertTrue(res["synced"])
        self.assertEqual(len(res["lines"]), 3)
        # Should be sorted chronologically
        self.assertAlmostEqual(res["lines"][0]["time"], 2.5)
        self.assertEqual(res["lines"][0]["text"], "Chorus line")
        self.assertAlmostEqual(res["lines"][1]["time"], 5.5)
        self.assertEqual(res["lines"][1]["text"], "Verse line")
        self.assertAlmostEqual(res["lines"][2]["time"], 8.5)
        self.assertEqual(res["lines"][2]["text"], "Chorus line")

    def test_parse_lrc_unsynced(self):
        sample = """Just a plain text lyric line
Another line without timestamps
And a third one
"""
        res = parse_lrc(sample)
        self.assertFalse(res["synced"])
        self.assertEqual(len(res["lines"]), 3)
        self.assertIsNone(res["lines"][0]["time"])
        self.assertEqual(res["lines"][0]["text"], "Just a plain text lyric line")

    def test_get_active_line_index(self):
        lines = [
            {"time": 5.0, "text": "Intro done"},
            {"time": 10.0, "text": "Verse 1"},
            {"time": 15.0, "text": ""},  # instrumental break
            {"time": 20.0, "text": "Chorus"},
        ]

        # Before first line -> -1 (intro)
        self.assertEqual(get_active_line_index(lines, 0.0, is_synced=True), -1)
        self.assertEqual(get_active_line_index(lines, 4.9, is_synced=True), -1)

        # Exactly at first line
        self.assertEqual(get_active_line_index(lines, 5.0, is_synced=True), 0)
        self.assertEqual(get_active_line_index(lines, 7.5, is_synced=True), 0)

        # Second line
        self.assertEqual(get_active_line_index(lines, 10.0, is_synced=True), 1)
        self.assertEqual(get_active_line_index(lines, 14.9, is_synced=True), 1)

        # Instrumental break
        self.assertEqual(get_active_line_index(lines, 15.0, is_synced=True), 2)

        # Chorus
        self.assertEqual(get_active_line_index(lines, 20.0, is_synced=True), 3)
        self.assertEqual(get_active_line_index(lines, 100.0, is_synced=True), 3)

    def test_format_time(self):
        self.assertEqual(format_time(0), "00:00")
        self.assertEqual(format_time(65.4), "01:05")
        self.assertEqual(format_time(215), "03:35")
        self.assertEqual(format_time(None), "--:--")


class TestLyricsFetcher(unittest.TestCase):

    def test_sanitize_filename(self):
        dirty = 'AC/DC: Back in "Black" *Rock?*'
        clean = sanitize_filename(dirty)
        self.assertNotIn('/', clean)
        self.assertNotIn(':', clean)
        self.assertNotIn('"', clean)
        self.assertNotIn('*', clean)
        self.assertNotIn('?', clean)

    def test_local_file_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            song_file = os.path.join(tmpdir, "test_track.mp3")
            lrc_file = os.path.join(tmpdir, "test_track.lrc")
            Path(song_file).touch()
            with open(lrc_file, "w", encoding="utf-8") as f:
                f.write("[00:01.00]Local line\n")

            res = get_local_file_lyrics(song_file)
            self.assertIsNotNone(res)
            self.assertEqual(res["source"], "local_file")
            self.assertIn("Local line", res["content"])

    def test_compute_lyrics_relevance(self):
        from climusic.functions.lyricsFetcher import compute_lyrics_relevance

        # 1. Exact match with synced lyrics and close duration -> near 1.0
        cand_exact = {
            "trackName": "Yellow",
            "artistName": "Coldplay",
            "duration": 268.0,
            "syncedLyrics": "[00:10.00]Look at the stars",
        }
        score = compute_lyrics_relevance(cand_exact, "Yellow", "Coldplay", target_duration=268.0)
        self.assertGreaterEqual(score, 0.95)

        # 2. Same title, completely different artist -> heavily penalized
        cand_wrong_artist = {
            "trackName": "Yellow",
            "artistName": "Completely Different Band",
            "duration": 268.0,
            "syncedLyrics": "[00:10.00]Different lyrics",
        }
        score_wrong = compute_lyrics_relevance(cand_wrong_artist, "Yellow", "Coldplay", target_duration=268.0)
        self.assertLess(score_wrong, 0.20)

        # 3. Live version with duration discrepancy
        cand_live = {
            "trackName": "Yellow (Live)",
            "artistName": "Coldplay",
            "duration": 340.0,  # +72s difference
            "syncedLyrics": "[00:10.00]Look at the stars",
        }
        score_live = compute_lyrics_relevance(cand_live, "Yellow", "Coldplay", target_duration=268.0)
        # Studio version should strictly beat live version
        self.assertGreater(score, score_live)

        # 4. Candidate with no lyrics content -> 0.0
        cand_empty = {
            "trackName": "Yellow",
            "artistName": "Coldplay",
            "syncedLyrics": None,
            "plainLyrics": None,
        }
        self.assertEqual(compute_lyrics_relevance(cand_empty, "Yellow", "Coldplay"), 0.0)

    def test_cache_save_with_filename(self):
        title = "FileTrackTest"
        artist = "FileArtistTest"
        filename = "01 - UniqueFilename_Song.mp3"
        content = "[00:05.00]Filename cached line\n"

        saved_path = save_lyrics_to_cache(title, artist, content, filename=filename)
        self.assertIsNotNone(saved_path)

        # Lookup by filename
        cached = get_cached_lyrics(title, artist, filename=filename)
        self.assertIsNotNone(cached)
        self.assertIn("Filename cached line", cached["content"])

        # Clean up
        try:
            os.remove(saved_path)
            alt_path = LYRICS_DIR / "01 - UniqueFilename_Song.lrc"
            if alt_path.exists():
                os.remove(alt_path)
        except OSError:
            pass


class TestLyricsUI(unittest.TestCase):

    def test_lyrics_view_widget_lifecycle(self):
        from climusic.components.lyricsView import LyricsView

        view = LyricsView()
        self.assertEqual(view.id, "lyrics-view")
        self.assertTrue(view.can_focus)

        song = {"title": "Test Song", "artist": "Test Artist", "path": "/test/song.mp3"}
        lrc_data = parse_lrc("[00:05.00]First line\n[00:10.00]Second line\n")

        # 1. Set lyrics
        view.set_lyrics(song, lrc_data)
        self.assertEqual(view.song, song)
        self.assertEqual(len(view.lyrics_data["lines"]), 2)

        # 2. Time sync before first line
        active = view.sync_time(2.0)
        self.assertIsNone(active)
        self.assertEqual(view.active_index, -1)

        # 3. Time sync at first line
        active = view.sync_time(6.0)
        self.assertIsNotNone(active)
        self.assertEqual(active["text"], "First line")
        self.assertEqual(view.active_index, 0)

        # 4. Time sync at second line
        active = view.sync_time(12.0)
        self.assertIsNotNone(active)
        self.assertEqual(active["text"], "Second line")
        self.assertEqual(view.active_index, 1)

        # 5. Manual scroll
        view.scroll_down(2)
        self.assertEqual(view.manual_scroll_offset, 2)
        view.scroll_up(1)
        self.assertEqual(view.manual_scroll_offset, 1)

        # 6. Set status and clear
        view.set_status("Fetching online...", song)
        self.assertEqual(view.status_message, "Fetching online...")
        view.clear_lyrics()
        self.assertIsNone(view.song)
        self.assertIsNone(view.lyrics_data)

    def test_now_playing_lyric_subtitle(self):
        from climusic.components.nowPlaying import NowPlaying

        np = NowPlaying()
        # Ensure compose works
        widgets = list(np.compose())
        lyric_widget = [w for w in widgets if getattr(w, "id", "") == "NowPlayingLyric"]
        self.assertEqual(len(lyric_widget), 1)

    def test_interface_css_compilation(self):
        from climusic.themes import build_css
        css = build_css()
        self.assertIn("#lyrics-view", css)
        self.assertIn("#NowPlayingLyric", css)
        self.assertIn("purple", css)
        self.assertIn("neon", css)


class TestLyricsCommands(unittest.TestCase):

    class MockApp:
        def __init__(self):
            self.printed = []
            self._lyrics_offset_ms = 0
            self._current_lyrics_data = parse_lrc("[00:01.00]Line A\n[00:02.00]Line B\n")
            self.song = {"title": "Mock Title", "artist": "Mock Artist"}

        def print_to_terminal(self, msg):
            self.printed.append(msg)

    def test_lyrics_offset_command(self):
        from climusic.components.actions.lyrics import LyricsActions

        app = self.MockApp()
        # Bind method to mock instance
        handle_offset = LyricsActions._handle_lyrics_offset.__get__(app, self.MockApp)

        handle_offset("+500")
        self.assertEqual(app._lyrics_offset_ms, 500)
        self.assertIn("+500ms", app.printed[-1])

        handle_offset("-200")
        self.assertEqual(app._lyrics_offset_ms, 300)
        self.assertIn("+300ms", app.printed[-1])

    def test_lyrics_copy_command(self):
        from climusic.components.actions.lyrics import LyricsActions
        import pyperclip

        app = self.MockApp()
        handle_copy = LyricsActions._handle_lyrics_copy.__get__(app, self.MockApp)
        handle_copy()
        self.assertIn("copied 2 lines", app.printed[-1])

    def test_lyrics_size_and_banner(self):
        from climusic.components.lyricsView import LyricsView, format_active_banner
        view = LyricsView()
        self.assertEqual(view.size_mode, "large")
        view.set_size("huge")
        self.assertEqual(view.size_mode, "huge")
        view.set_size("normal")
        self.assertEqual(view.size_mode, "normal")

        # Test active banner creation
        banner = format_active_banner("Singing loud", max_width=50)
        self.assertIn("┏", banner)
        self.assertIn("Singing loud", banner)
        self.assertIn("┛", banner)

        # Fullwidth banner in huge mode
        fw_banner = format_active_banner("Hey", max_width=50, fullwidth=True)
        self.assertIn("┏", fw_banner)
        self.assertIn("Ｈｅｙ", fw_banner)


if __name__ == "__main__":
    unittest.main()
