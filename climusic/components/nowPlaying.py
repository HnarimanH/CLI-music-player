import json
from pathlib import Path
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
        self.cover_style: str = "ascii"
        self.cover_contrast: float = 1.25
        self._rendered_width: int = 0
        self._rendered_style: str = "ascii"
        self._load_cover_config()

    def _load_cover_config(self) -> None:
        try:
            from climusic.musicController import CONFIG_PATH
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if "cover_width" in cfg:
                    self.cover_width = cfg["cover_width"]
                if "cover_style" in cfg:
                    self.cover_style = str(cfg["cover_style"])
                if "cover_contrast" in cfg:
                    self.cover_contrast = float(cfg["cover_contrast"])
        except Exception:
            pass

    def _save_cover_config(self) -> None:
        try:
            from climusic.musicController import CONFIG_PATH
            cfg = {}
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            cfg["cover_width"] = self.cover_width
            cfg["cover_style"] = self.cover_style
            cfg["cover_contrast"] = self.cover_contrast
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4)
        except Exception:
            pass

    def _get_target_width(self) -> int:
        if isinstance(self.cover_width, int):
            return self.cover_width
        if self.size and self.size.width > 20:
            avail_w = max(24, self.size.width - 4)
            return max(32, min(avail_w, 88))
        return 64

    def _render_cover(self, width: Optional[int] = None, style: Optional[str] = None) -> None:
        if not self.current_cover_bytes:
            return
        target_w = width if width is not None else self._get_target_width()
        target_style = style if style is not None else self.cover_style
        ascii_cover = cover_to_ascii(
            self.current_cover_bytes,
            width=target_w,
            style=target_style,
            contrast=self.cover_contrast
        )
        self._rendered_width = target_w
        self._rendered_style = target_style
        try:
            self.query_one("#AlbumAsciiCover", Static).update(ascii_cover)
        except Exception:
            pass

    def set_cover_width(self, width: Union[str, int]) -> None:
        self.cover_width = width
        self._save_cover_config()
        if self.current_cover_bytes:
            self._render_cover(self._get_target_width())

    def adjust_cover_width(self, delta: int) -> int:
        current = self._get_target_width()
        new_val = max(20, min(120, current + delta))
        self.cover_width = new_val
        self._save_cover_config()
        if self.current_cover_bytes:
            self._render_cover(new_val)
        return new_val

    def set_cover_style(self, style: str) -> None:
        self.cover_style = style
        self._save_cover_config()
        if self.current_cover_bytes:
            self._render_cover(self._get_target_width(), style=style)

    def set_cover_contrast(self, contrast: float) -> None:
        self.cover_contrast = max(0.2, min(3.0, contrast))
        self._save_cover_config()
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
        self._rendered_style = self.cover_style
        yield Static(
            cover_to_ascii(cover_data, width=target_w, style=self.cover_style, contrast=self.cover_contrast),
            id="AlbumAsciiCover"
        )
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
            self._rendered_style = self.cover_style
            ascii_cover = cover_to_ascii(
                self.current_cover_bytes,
                width=target_w,
                style=self.cover_style,
                contrast=self.cover_contrast
            )
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

