import threading
import pyperclip
from typing import Optional, Dict, Any, List

from climusic.components.lyricsView import LyricsView
from climusic.components.nowPlaying import NowPlaying
from climusic.components.songTable import SongTable
from climusic.components.searchResults import SearchResults
from climusic.functions.lyricsFetcher import (
    load_lyrics_for_song,
    search_lrclib,
    save_lyrics_to_cache,
)
from climusic.functions.lyricsParser import parse_lrc


class LyricsActions:
    """
    Mixin for lyrics playback synchronization, view toggling,
    online fetching, custom searching, offset adjustment, and clipboard support.
    """

    _lyrics_search_results: List[Dict[str, Any]] = []
    _lyrics_offset_ms: int = 0
    _is_lyrics_view_active: bool = False
    _current_lyrics_data: Optional[Dict[str, Any]] = None
    _current_active_line: Optional[Dict[str, Any]] = None

    # ═══════════════════════════════════════════════════════════════
    # View Navigation & Toggling
    # ═══════════════════════════════════════════════════════════════

    def action_toggle_lyrics(self) -> None:
        """Hotkey action for toggling lyrics view."""
        self.toggle_lyrics()

    def toggle_lyrics(self) -> None:
        """Toggle lyrics view on / off."""
        try:
            lyrics_view = self.query_one(LyricsView)
            song_table = self.query_one(SongTable)
            search_results = self.query_one(SearchResults)

            # If search results are currently visible, close them and open lyrics
            if not search_results.has_class("hidden"):
                search_results.add_class("hidden")
                song_table.add_class("hidden")
                lyrics_view.remove_class("hidden")
                lyrics_view.focus()
                self._is_lyrics_view_active = True
                self.print_to_terminal("[dim]lyrics view: on[/dim]")
                return

            if lyrics_view.has_class("hidden"):
                song_table.add_class("hidden")
                lyrics_view.remove_class("hidden")
                lyrics_view.focus()
                self._is_lyrics_view_active = True
                self.print_to_terminal("[dim]lyrics view: on (press 'l' or 'esc' to return)[/dim]")
            else:
                lyrics_view.add_class("hidden")
                song_table.remove_class("hidden")
                self._is_lyrics_view_active = False
                self.print_to_terminal("[dim]lyrics view: off[/dim]")
        except Exception as e:
            self.print_to_terminal(f"[red]error toggling lyrics: {e}[/red]")

    def show_lyrics_view(self) -> None:
        """Explicitly switch to lyrics view."""
        try:
            self.query_one(SongTable).add_class("hidden")
            self.query_one(SearchResults).add_class("hidden")
            lv = self.query_one(LyricsView)
            lv.remove_class("hidden")
            lv.focus()
            self._is_lyrics_view_active = True
        except Exception:
            pass

    def hide_lyrics_view(self) -> None:
        """Explicitly return to song table from lyrics view."""
        try:
            self.query_one(LyricsView).add_class("hidden")
            self.query_one(SongTable).remove_class("hidden")
            self._is_lyrics_view_active = False
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════
    # Song Lifecycle & Background Fetching
    # ═══════════════════════════════════════════════════════════════

    def load_song_lyrics(self, song: Dict[str, Any]) -> None:
        """
        Called when a new song starts playing.
        Performs fast local check, and falls back to background LRCLIB fetch.
        """
        self._lyrics_offset_ms = 0
        self._current_lyrics_data = None
        self._current_active_line = None

        try:
            now_playing = self.query_one(NowPlaying)
            now_playing.update_lyric(None)
        except Exception:
            pass

        try:
            lyrics_view = self.query_one(LyricsView)
            lyrics_view.set_status("Checking local lyrics...", song)
        except Exception:
            pass

        # 1. Fast local resolution (local file, cache, embedded tags)
        local_lyrics = load_lyrics_for_song(song, allow_network=False, extra_offset_ms=self._lyrics_offset_ms)
        if local_lyrics:
            self._current_lyrics_data = local_lyrics
            try:
                self.query_one(LyricsView).set_lyrics(song, local_lyrics)
            except Exception:
                pass
            return

        # 2. Asynchronous online fetch from LRCLIB
        try:
            self.query_one(LyricsView).set_status("Fetching lyrics from LRCLIB...", song)
        except Exception:
            pass

        threading.Thread(
            target=self._async_fetch_lyrics,
            args=(song,),
            daemon=True
        ).start()

    def _async_fetch_lyrics(self, song: Dict[str, Any]) -> None:
        """Background thread worker for fetching lyrics."""
        try:
            lyrics_data = load_lyrics_for_song(song, allow_network=True, extra_offset_ms=self._lyrics_offset_ms)
            self.call_from_thread(self._on_lyrics_loaded, song, lyrics_data)
        except Exception:
            self.call_from_thread(self._on_lyrics_loaded, song, None)

    def _on_lyrics_loaded(self, song: Dict[str, Any], lyrics_data: Optional[Dict[str, Any]]) -> None:
        """Safely updates UI from background fetch."""
        if not hasattr(self, "song") or self.song.get("path") != song.get("path"):
            return

        self._current_lyrics_data = lyrics_data
        try:
            lyrics_view = self.query_one(LyricsView)
            lyrics_view.set_lyrics(song, lyrics_data)
        except Exception:
            pass

        if lyrics_data and lyrics_data.get("source_type") == "online":
            matched_t = lyrics_data.get("matched_title") or song.get("title", "")
            matched_a = lyrics_data.get("matched_artist") or song.get("artist", "")
            score_val = lyrics_data.get("score")
            score_str = f" [{int(score_val * 100)}% match]" if score_val is not None else ""
            self.print_to_terminal(f"[green]lyrics matched & saved: '{matched_t}' by {matched_a}{score_str}[/green]")

    def update_lyrics_tick(self, current_time: float) -> None:
        """Called by the 20Hz progress loop in update_progress()."""
        if not self._current_lyrics_data:
            return

        try:
            lyrics_view = self.query_one(LyricsView)
            line = lyrics_view.sync_time(current_time)

            if line != self._current_active_line:
                self._current_active_line = line
                self.query_one(NowPlaying).update_lyric(line)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════
    # Lyrics Command Router
    # ═══════════════════════════════════════════════════════════════

    def handle_lyrics_command(self, cmd: str) -> None:
        """Main dispatcher for lyrics commands."""
        parts = cmd.strip().split(maxsplit=2)
        if len(parts) == 1:
            # 'lyrics', 'lyr', or 'l' toggles view
            self.toggle_lyrics()
            return

        sub = parts[1].lower()

        if sub in ("on", "show", "open"):
            self.show_lyrics_view()
            self.print_to_terminal("[dim]lyrics view: on[/dim]")
        elif sub in ("off", "hide", "close"):
            self.hide_lyrics_view()
            self.print_to_terminal("[dim]lyrics view: off[/dim]")
        elif sub in ("fetch", "get"):
            self._handle_manual_fetch()
        elif sub == "search":
            if len(parts) < 3:
                self.print_to_terminal("[red]usage: lyrics search <query>[/red]")
                return
            self._handle_lyrics_search(parts[2])
        elif sub in ("select", "dl"):
            if len(parts) < 3 or not parts[2].isdigit():
                self.print_to_terminal("[red]usage: lyrics select <1-5>[/red]")
                return
            self._handle_lyrics_select(int(parts[2]))
        elif sub == "offset":
            if len(parts) < 3:
                self.print_to_terminal(f"current lyrics offset: {self._lyrics_offset_ms}ms")
                self.print_to_terminal("[dim]usage: lyrics offset <+ms|-ms> (e.g. lyrics offset +500)[/dim]")
                return
            self._handle_lyrics_offset(parts[2])
        elif sub == "size":
            if len(parts) < 3:
                cur_size = "large"
                try:
                    cur_size = self.query_one(LyricsView).size_mode
                except Exception:
                    pass
                self.print_to_terminal(f"current lyrics size: [yellow]{cur_size}[/yellow]")
                self.print_to_terminal("[dim]usage: lyrics size <normal|large|huge> (or press +/- in lyrics view)[/dim]")
                return
            new_size = parts[2].lower()
            if new_size in ("normal", "large", "huge"):
                try:
                    self.query_one(LyricsView).set_size(new_size)
                except Exception:
                    pass
                self.print_to_terminal(f"[green]lyrics size set to: {new_size}[/green]")
            else:
                self.print_to_terminal("[red]invalid size. choose: normal, large, or huge[/red]")
        elif sub == "copy":
            self._handle_lyrics_copy()
        elif sub == "reload":
            if hasattr(self, "song") and self.song:
                self.load_song_lyrics(self.song)
                self.print_to_terminal("[dim]reloading lyrics for current song...[/dim]")
            else:
                self.print_to_terminal("[red]no song loaded[/red]")
        else:
            self.print_to_terminal(f"[red]unknown lyrics command: {sub}[/red]")
            self.print_to_terminal("[dim]try: lyrics, lyrics size <normal|large|huge>, lyrics on/off, lyrics fetch, lyrics search <q>, lyrics offset <ms>[/dim]")

    def _handle_manual_fetch(self) -> None:
        """Force re-fetch from LRCLIB."""
        if not hasattr(self, "song") or not self.song:
            self.print_to_terminal("[red]no song loaded[/red]")
            return

        self.print_to_terminal(f"[dim]fetching lyrics for '{self.song['title']}'...[/dim]")
        threading.Thread(
            target=self._async_fetch_lyrics,
            args=(self.song,),
            daemon=True
        ).start()

    def _handle_lyrics_search(self, query: str) -> None:
        """Search LRCLIB for candidate lyrics."""
        self.print_to_terminal(f"[dim]searching lyrics for: {query}...[/dim]")
        threading.Thread(
            target=self._async_search_lyrics,
            args=(query,),
            daemon=True
        ).start()

    def _async_search_lyrics(self, query: str) -> None:
        results = search_lrclib(query)
        self.call_from_thread(self._show_lyrics_search_results, results)

    def _show_lyrics_search_results(self, results: List[Dict[str, Any]]) -> None:
        self._lyrics_search_results = results
        if not results:
            self.print_to_terminal("[red]no lyrics matches found[/red]")
            return

        self.print_to_terminal("[bold cyan]Lyrics Results:[/bold cyan]")
        for i, item in enumerate(results, start=1):
            sync_tag = "[green]synced[/green]" if item.get("synced") else "[dim]plain[/dim]"
            inst_tag = " [cyan][instrumental][/cyan]" if item.get("instrumental") else ""
            self.print_to_terminal(f"  [yellow]{i}[/yellow]. {item['title']} — {item['artist']} ({sync_tag}){inst_tag}")
        self.print_to_terminal("[dim]type 'lyrics select <1-5>' to apply and save[/dim]")

    def _handle_lyrics_select(self, index: int) -> None:
        """Applies chosen candidate from search results."""
        if not self._lyrics_search_results:
            self.print_to_terminal("[red]no search results available. run 'lyrics search <query>' first[/red]")
            return

        idx = index - 1
        if idx < 0 or idx >= len(self._lyrics_search_results):
            self.print_to_terminal(f"[red]invalid selection. choose 1-{len(self._lyrics_search_results)}[/red]")
            return

        choice = self._lyrics_search_results[idx]
        raw_content = choice.get("content", "")

        if not raw_content:
            self.print_to_terminal("[red]selected result contains no lyrics[/red]")
            return

        # Save to cache for current song
        if hasattr(self, "song") and self.song:
            save_lyrics_to_cache(self.song["title"], self.song["artist"], raw_content, filename=self.song.get("filename"))
            parsed = parse_lrc(raw_content, extra_offset_ms=self._lyrics_offset_ms)
            parsed["source"] = f"manual select ({choice['title']})"
            parsed["instrumental"] = choice.get("instrumental", False)
            self._current_lyrics_data = parsed
            try:
                self.query_one(LyricsView).set_lyrics(self.song, parsed)
            except Exception:
                pass
            self.print_to_terminal(f"[green]lyrics applied from '{choice['title']}' and saved to cache![/green]")
        else:
            self.print_to_terminal("[yellow]lyrics saved to cache, but no active song is playing[/yellow]")

    def _handle_lyrics_offset(self, offset_arg: str) -> None:
        """Adjusts timing offset in milliseconds."""
        try:
            val = int(offset_arg.replace("ms", "").strip())
            self._lyrics_offset_ms += val
            self.print_to_terminal(f"[dim]lyrics timing offset adjusted: {self._lyrics_offset_ms:+d}ms[/dim]")

            # Re-parse existing lyrics with new offset
            if self._current_lyrics_data and self._current_lyrics_data.get("raw"):
                raw = self._current_lyrics_data["raw"]
                parsed = parse_lrc(raw, extra_offset_ms=self._lyrics_offset_ms)
                parsed["source"] = self._current_lyrics_data.get("source", "cache")
                self._current_lyrics_data = parsed
                if hasattr(self, "song") and self.song:
                    try:
                        self.query_one(LyricsView).set_lyrics(self.song, parsed)
                    except Exception:
                        pass
        except ValueError:
            self.print_to_terminal("[red]invalid offset value. Example: lyrics offset +500 or lyrics offset -300[/red]")

    def _handle_lyrics_copy(self) -> None:
        """Copies full lyrics to system clipboard."""
        if not self._current_lyrics_data or not self._current_lyrics_data.get("lines"):
            self.print_to_terminal("[red]no lyrics loaded to copy[/red]")
            return

        lines = [item.get("text", "") for item in self._current_lyrics_data["lines"] if item.get("text")]
        full_text = "\n".join(lines)
        try:
            pyperclip.copy(full_text)
            self.print_to_terminal(f"[green]copied {len(lines)} lines of lyrics to clipboard![/green]")
        except Exception as e:
            self.print_to_terminal(f"[red]failed to copy to clipboard: {e}[/red]")
