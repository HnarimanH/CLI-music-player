import time
import textwrap
from typing import Optional, Dict, Any, List
from textual.widgets import Static
from textual.events import Key
from climusic.functions.lyricsParser import get_active_line_index, format_time
from climusic.functions.turnicateText import truncate
from rich.markup import escape


def format_active_banner(text: str, max_width: int = 60, fullwidth: bool = False) -> str:
    """Formats the singing lyric into a prominent, multi-line framed marquee card."""
    text = text.strip()
    if not text:
        content_lines = ["♪  Instrumental  ♪"]
    else:
        if fullwidth and len(text) <= 22:
            # Fullwidth character expansion for massive letter presence
            fw = "".join(chr(ord(c) + 0xFEE0) if 33 <= ord(c) <= 126 else ("  " if c == " " else c) for c in text)
            content_lines = [f"✦ ▶  {fw}  ◀ ✦"]
        else:
            wrap_target = max(20, max_width - 14)
            wrapped = textwrap.wrap(text, width=wrap_target) or [text]
            if len(wrapped) == 1:
                content_lines = [f"✦  ▶  {wrapped[0]}  ◀  ✦"]
            else:
                content_lines = [f"▶▶  {w}  ◀◀" if i == 0 else f"    {w}    " for i, w in enumerate(wrapped)]

    max_line_len = max(len(cl) for cl in content_lines)
    box_w = min(max_width, max(max_line_len + 6, 36))

    top = "┏" + "━" * (box_w - 2) + "┓"
    bot = "┗" + "━" * (box_w - 2) + "┛"
    empty = "┃" + " " * (box_w - 2) + "┃"

    rows = [top, empty]
    for cl in content_lines:
        pad = (box_w - 2 - len(cl)) // 2
        pad_l = " " * max(0, pad)
        pad_r = " " * max(0, box_w - 2 - len(cl) - pad)
        rows.append("┃" + pad_l + cl + pad_r + "┃")
    rows.append(empty)
    rows.append(bot)
    return "\n".join(rows)


class LyricsView(Static):
    """
    Textual widget for displaying synchronized karaoke-style lyrics or plain lyrics.
    Features:
    - Large, high-visibility framed marquee for the active singing line
    - Spacious layout (large/huge/normal size modes)
    - Full centering and double vertical spacing
    - Interactive hotkeys (+/-) and manual scrolling
    """

    def __init__(self, **kwargs):
        super().__init__(id="lyrics-view", **kwargs)
        self.can_focus = True
        self.song: Optional[Dict[str, Any]] = None
        self.lyrics_data: Optional[Dict[str, Any]] = None
        self.status_message: Optional[str] = None
        self.active_index: int = -1
        self.last_rendered_index: int = -999
        self.manual_scroll_offset: int = 0
        self.last_manual_scroll_time: float = 0.0
        self.size_mode: str = "large"  # 'normal', 'large', 'huge'

    def on_mount(self) -> None:
        self.update("[dim]no lyrics loaded. play a song and press 'l' or type 'lyrics'.[/dim]")

    def set_size(self, mode: str) -> None:
        """Sets size mode: 'normal', 'large', or 'huge'."""
        if mode in ("normal", "large", "huge"):
            self.size_mode = mode
            self._render_view(force=True)

    def set_status(self, message: str, song: Optional[Dict[str, Any]] = None) -> None:
        """Displays a status or progress message."""
        if song:
            self.song = song
        self.status_message = message
        self.lyrics_data = None
        self._render_status()

    def set_lyrics(self, song: Dict[str, Any], lyrics_data: Optional[Dict[str, Any]]) -> None:
        """Updates the active lyrics data for the currently playing song."""
        self.song = song
        self.lyrics_data = lyrics_data
        self.status_message = None
        self.active_index = -1
        self.last_rendered_index = -999
        self.manual_scroll_offset = 0
        self.last_manual_scroll_time = 0.0
        self._render_view(force=True)

    def clear_lyrics(self) -> None:
        """Clears the lyrics display."""
        self.song = None
        self.lyrics_data = None
        self.status_message = None
        self.active_index = -1
        self.last_rendered_index = -999
        self.manual_scroll_offset = 0
        self.update("[dim]no song playing[/dim]")

    def sync_time(self, current_time: float) -> Optional[Dict[str, Any]]:
        """
        Called on playback clock ticks.
        Returns the active line dict (or None) and updates the widget if the line changed.
        """
        if not self.lyrics_data or not self.lyrics_data.get("lines"):
            return None

        lines = self.lyrics_data["lines"]
        is_synced = self.lyrics_data.get("synced", False)

        if is_synced:
            new_idx = get_active_line_index(lines, current_time, is_synced=True)
            
            # Reset manual scroll after 5 seconds of inactivity
            if self.manual_scroll_offset != 0 and (time.time() - self.last_manual_scroll_time > 5.0):
                self.manual_scroll_offset = 0

            if new_idx != self.active_index or self.manual_scroll_offset != 0:
                self.active_index = new_idx
                self._render_view()

            if 0 <= new_idx < len(lines):
                return lines[new_idx]
            return None
        else:
            return None

    def _render_status(self) -> None:
        title = self.song.get("title", "Unknown") if self.song else "No Song"
        artist = self.song.get("artist", "Unknown") if self.song else ""
        msg = self.status_message or "Loading..."

        lines = [
            f"[bold]{escape(title)}[/bold]" + (f" — [dim]{escape(artist)}[/dim]" if artist else ""),
            f"[dim cyan]• {escape(msg)} •[/dim cyan]",
            "[dim]" + "─" * 40 + "[/dim]",
            "",
            f"[yellow]{escape(msg)}[/yellow]",
            "",
            "[dim]• Press 'l' or 'esc' to return to song list[/dim]",
            "[dim]• Type 'lyrics search <query>' to find lyrics[/dim]"
        ]
        self.update("\n".join(lines))

    def _render_view(self, force: bool = False) -> None:
        if not force and self.active_index == self.last_rendered_index and self.manual_scroll_offset == 0:
            return

        self.last_rendered_index = self.active_index

        if not self.song:
            self.update("[dim]no song loaded[/dim]")
            return

        if not self.lyrics_data or not self.lyrics_data.get("lines"):
            title = self.song.get("title", "Unknown")
            artist = self.song.get("artist", "Unknown")
            lines = [
                f"[bold cyan]Lyrics[/bold cyan]: [bold]{escape(title)}[/bold] — [dim]{escape(artist)}[/dim]",
                "[dim]" + "─" * 45 + "[/dim]",
                "",
                "[bold red]No lyrics found for this song.[/bold red]",
                "",
                "[dim]Options:[/dim]",
                "  [yellow]lyrics search <song>[/yellow]    search online lyrics",
                "  [yellow]lyrics fetch[/yellow]            retry fetching online",
                "  [yellow]esc[/yellow]                     return to library",
                "",
                "[dim]Or add a .lrc file in the same folder as your song.[/dim]"
            ]
            self.update("\n".join(lines))
            return

        lines: List[Dict[str, Any]] = self.lyrics_data["lines"]
        is_synced = self.lyrics_data.get("synced", False)
        source = self.lyrics_data.get("source", "unknown")
        title = self.song.get("title", "Unknown")
        artist = self.song.get("artist", "Unknown")

        # Header with size indicator
        badge = f"[bold green]Synced[/bold green] • {escape(source)}" if is_synced else f"[yellow]Unsynced[/yellow] • {escape(source)}"
        size_tag = f"[dim]size: {self.size_mode} (+/-)[/dim]"
        header = [
            f"[bold]{escape(truncate(title, 35))}[/bold] — [dim]{escape(truncate(artist, 25))}[/dim]  ({badge})  {size_tag}",
            "[dim]" + "─" * 50 + "[/dim]"
        ]

        widget_height = self.size.height if self.size and self.size.height > 6 else 22
        widget_width = self.size.width if self.size and self.size.width > 30 else 70

        # Center on active line + manual scroll
        center_idx = max(0, self.active_index if self.active_index >= 0 else 0)
        center_idx += self.manual_scroll_offset
        center_idx = max(0, min(center_idx, len(lines) - 1))

        body: List[str] = []

        if self.size_mode == "normal":
            # Compact view (single-spaced)
            available_rows = max(5, widget_height - len(header) - 2)
            half = available_rows // 2
            start = max(0, center_idx - half)
            end = min(len(lines), start + available_rows)
            if end - start < available_rows and start > 0:
                start = max(0, end - available_rows)

            if is_synced and self.active_index == -1:
                body.append("[bold cyan]▶  ♪  Intro  ♪  ◀[/bold cyan]")

            for i in range(start, end):
                item = lines[i]
                text = escape(item.get("text", ""))
                t_str = f"[{format_time(item.get('time'))}] " if is_synced and item.get("time") is not None else ""

                if is_synced:
                    if i < self.active_index:
                        body.append(f"[dim]{t_str}{text}[/dim]")
                    elif i == self.active_index:
                        if not text.strip():
                            body.append(f"[bold cyan]▶  ♪  Instrumental  ♪  ◀[/bold cyan]")
                        else:
                            body.append(f"[bold reverse] ▶ {text} ◀ [/bold reverse]")
                    else:
                        body.append(f"[white]{t_str}{text}[/white]")
                else:
                    if i == center_idx:
                        body.append(f"[bold reverse] {text} [/bold reverse]")
                    else:
                        body.append(f"[white]{text}[/white]")
        else:
            # Large or Huge mode: Spacious layout with prominent active marquee card
            surrounding_rows = max(4, widget_height - len(header) - 8)
            visible_items = max(3, surrounding_rows // 2)
            half = visible_items // 2
            start = max(0, center_idx - half)
            end = min(len(lines), start + visible_items)
            if end - start < visible_items and start > 0:
                start = max(0, end - visible_items)

            if is_synced and self.active_index == -1:
                body.append("[bold cyan]┏━ ♪  Intro  ♪ ━┓[/bold cyan]")
                body.append("")

            for i in range(start, end):
                item = lines[i]
                raw_text = item.get("text", "")
                text = escape(raw_text)
                t_str = f"[{format_time(item.get('time'))}] " if is_synced and item.get("time") is not None else ""

                if is_synced:
                    if i < self.active_index:
                        body.append(f"[dim]{t_str}{text}[/dim]")
                        body.append("")
                    elif i == self.active_index:
                        is_huge = (self.size_mode == "huge")
                        banner = format_active_banner(
                            raw_text,
                            max_width=min(widget_width - 6, 68),
                            fullwidth=is_huge
                        )
                        body.append(f"[bold reverse]{banner}[/bold reverse]")
                        body.append("")
                    else:
                        body.append(f"[white]{t_str}{text}[/white]")
                        body.append("")
                else:
                    if i == center_idx:
                        is_huge = (self.size_mode == "huge")
                        banner = format_active_banner(
                            raw_text,
                            max_width=min(widget_width - 6, 68),
                            fullwidth=is_huge
                        )
                        body.append(f"[bold reverse]{banner}[/bold reverse]")
                        body.append("")
                    else:
                        body.append(f"[white]{text}[/white]")
                        body.append("")

        full_content = "\n".join(header + [""] + body)
        self.update(full_content)

    def scroll_up(self, delta: int = 1) -> None:
        """Manual scroll up."""
        self.manual_scroll_offset -= delta
        self.last_manual_scroll_time = time.time()
        self._render_view(force=True)

    def scroll_down(self, delta: int = 1) -> None:
        """Manual scroll down."""
        self.manual_scroll_offset += delta
        self.last_manual_scroll_time = time.time()
        self._render_view(force=True)

    def on_key(self, event: Key) -> None:
        """Handles keypresses when LyricsView is focused."""
        if event.key in ("up", "k"):
            self.scroll_up(1)
            event.stop()
        elif event.key in ("down", "j"):
            self.scroll_down(1)
            event.stop()
        elif event.key == "pageup":
            self.scroll_up(5)
            event.stop()
        elif event.key == "pagedown":
            self.scroll_down(5)
            event.stop()
        elif event.key in ("plus", "equals", "="):
            # Increase font size
            modes = ["normal", "large", "huge"]
            cur_idx = modes.index(self.size_mode) if self.size_mode in modes else 1
            new_idx = min(len(modes) - 1, cur_idx + 1)
            self.set_size(modes[new_idx])
            event.stop()
        elif event.key in ("minus", "-"):
            # Decrease font size
            modes = ["normal", "large", "huge"]
            cur_idx = modes.index(self.size_mode) if self.size_mode in modes else 1
            new_idx = max(0, cur_idx - 1)
            self.set_size(modes[new_idx])
            event.stop()
        elif event.key in ("escape", "l"):
            if hasattr(self.app, "action_toggle_lyrics"):
                self.app.action_toggle_lyrics()
            event.stop()

