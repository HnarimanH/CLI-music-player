from typing import Union, Optional
from textual.containers import Vertical
from textual.widgets import Static
from climusic.components.songProgress import SongProgress
from climusic.functions.timeConvert import convertToSeconds
from climusic.functions.coverToAscii import cover_to_ascii
from importlib import resources
from rich.markup import escape


class NowPlaying(Vertical):
    def __init__(self, **kwargs):
        super().__init__(id="now-playing", **kwargs)
        self.current_cover_bytes: Optional[bytes] = None
        self.cover_width: Union[str, int] = "auto"
        self._rendered_width: int = 0

    def _get_target_width(self) -> int:
        if isinstance(self.cover_width, int):
            return self.cover_width
        if self.size and self.size.width > 20:
            return max(48, min(self.size.width - 4, 80))
        return 64

    def _render_cover(self, width: int) -> None:
        if not self.current_cover_bytes:
            return
        ascii_cover = cover_to_ascii(self.current_cover_bytes, width=width)
        self._rendered_width = width
        try:
            self.query_one("#AlbumAsciiCover", Static).update(ascii_cover)
        except Exception:
            pass

    def set_cover_width(self, width: Union[str, int]) -> None:
        self.cover_width = width
        if self.current_cover_bytes:
            self._render_cover(self._get_target_width())

    def on_resize(self, event) -> None:
        if self.cover_width == "auto" and self.current_cover_bytes:
            target = self._get_target_width()
            if abs(target - self._rendered_width) >= 2:
                self._render_cover(target)

    def compose(self):
        with resources.files("climusic.assets").joinpath("defaultAlbumCover.jpeg").open("rb") as f:
            cover_data = f.read()
        self.current_cover_bytes = cover_data
        target_w = self._get_target_width()
        self._rendered_width = target_w
        yield Static(cover_to_ascii(cover_data, width=target_w), id="AlbumAsciiCover")
        yield Static("Nothing is playing", id="SongDetails")
        yield SongProgress()
        yield Static("[dim]♪ ... ♪[/dim]", id="NowPlayingLyric")

    def update_song(self, cover, song: dict):
        cover_widget = self.query_one("#AlbumAsciiCover", Static)
        details_widget = self.query_one("#SongDetails", Static)
        progress_bar = self.query_one(SongProgress)
        lyric_widget = self.query_one("#NowPlayingLyric", Static)

        if isinstance(cover, (bytes, bytearray)):
            self.current_cover_bytes = bytes(cover)
            target_w = self._get_target_width()
            self._rendered_width = target_w
            ascii_cover = cover_to_ascii(self.current_cover_bytes, width=target_w)
            cover_widget.update(ascii_cover)
        elif isinstance(cover, str):
            cover_widget.update(cover)

        lyric_widget.update("[dim]♪ ... ♪[/dim]")

        details_widget.update(
            f"""
Title: {song['title']}
Artist: {song['artist']}
Album: {song['album']}
Length: {song['length']}
            """
        )

        progress_bar.update_progress(
            current=0,
            total=convertToSeconds(song["length"])
        )

    def update_lyric(self, line) -> None:
        lyric_widget = self.query_one("#NowPlayingLyric", Static)
        if not line:
            lyric_widget.update("[dim]♪ ... ♪[/dim]")
            return
        text = line.get("text", "").strip()
        if text:
            lyric_widget.update(f"[bold reverse]  ▶  {escape(text)}  ◀  [/bold reverse]")
        else:
            lyric_widget.update("[dim italic]♪ Instrumental ♪[/dim italic]")

