
import json
import os
from climusic.musicController import CONFIG_PATH
from climusic import musicController
from climusic.components.songTable import SongTable
class CommandActions:

    # ═══════════════════════════════════════════════════════════════
    # Command Routing & Handling
    # ═══════════════════════════════════════════════════════════════

    def handle_command(self, cmd: str):
        """Main command dispatcher"""
        cmd = cmd.strip().lower()
        parts = cmd.split()

        if not parts:
            return

        base = parts[0]

        if base in ("man", "help", "?"):
            self._handle_help(cmd)
        elif base == "prev" or base == "previous":
            self.print_to_terminal("loading previous song.")
            self.play_previous_song()
        elif base == "next" or base == "n":
            self.print_to_terminal("loading next song.")
            self.play_next_song()
        elif base == "pause" or base == "p":
            musicController.pause_song()
            self.print_to_terminal("paused.")
        elif base == "resume" or base == "r":
            musicController.unpause_song()
            self.print_to_terminal("resumed.")
        elif base == "repeat" or base == "rep":
            self._handle_repeat()
        elif base == "vol" or base == "volume":
            self.handle_volume(cmd)
        elif base == "shuffle" or base == "shuf":
            self._handle_shuffle()
        elif base == "theme" or base == "t":
            self._handle_theme(cmd)
        elif base == "vis" or base == "visualizer":
            self._handle_visualizer(cmd)
        elif base == "new_dir":
            self.handle_new_dir(cmd)
        elif base == "ls" or base == "list":
            self.handle_playlist(cmd)
        elif base == "fav" or base == "favorites":
            self.handle_favorites(cmd)
        elif base == "sort" or base == "a2z":
            self._handle_sort(cmd)
        elif base == "cd":
            self.handle_playlist(cmd)
        elif base == "mkdir":
            self.handle_playlist(cmd)
        elif base == "cp":
            self.handle_playlist(cmd)
        elif base == "rm":
            self.handle_playlist(cmd)
        elif base == "search" or base == "s":
            self._handle_search(cmd)
        elif base == "dl":
            self._handle_download(cmd)
        elif base in ("lyrics", "lyr", "l"):
            self.handle_lyrics_command(cmd)
        elif base in ("spotify", "sp"):
            self._handle_spotify_command(cmd)
        elif base in ("cover", "art"):
            self._handle_cover_size(cmd)
        elif base == "esc":
            self._handle_esc()
        else:
            self.print_to_terminal(f"[dim]command not found: {base}[/dim]")

    # ═══════════════════════════════════════════════════════════════
    # Help & Documentation
    # ═══════════════════════════════════════════════════════════════

    def _handle_help(self, cmd: str):
        """Display help for commands"""
        parts = cmd.split(maxsplit=1)
        topic = parts[1].lower() if len(parts) > 1 else None

        help_text = {
            
            "playback": [
                "[bold cyan]Playback[/bold cyan]",
                "  [yellow]next, n[/yellow]           play next song",
                "  [yellow]prev, previous[/yellow]    play previous song",
                "  [yellow]pause, p[/yellow]          pause playback",
                "  [yellow]resume, r[/yellow]         resume playback",
                "  [yellow]repeat, rep[/yellow]       toggle repeat mode",
                "[bold cyan]Playback hotKeys[/bold cyan]",
                "  [yellow]space[/yellow]             pause/resume",
                "  [yellow]d[/yellow]                 next song",
                "  [yellow]a[/yellow]                 previous song",
                "  [yellow]q[/yellow]                 skip forward 5s",
                "  [yellow]e[/yellow]                 skip back 5s",
                "  [yellow]l[/yellow]                 toggle lyrics view",
            ],
            "volume": [
                "[bold cyan]Volume[/bold cyan]",
                "  [yellow]vol[/yellow]               show current volume",
                "  [yellow]vol up[/yellow]            increase by 10%",
                "  [yellow]vol down[/yellow]          decrease by 10%",
                "  [yellow]vol 50[/yellow]            set to 50%",
                "[bold cyan]Volume hotkeys[/bold cyan]",
                "  [yellow]w[/yellow]                 volume up",
                "  [yellow]s[/yellow]                 volume down",
            ],
            "playlists": [
                "[bold cyan]Playlists[/bold cyan]",
                "  [yellow]ls, list[/yellow]          list all playlists",
                "  [yellow]ls songs[/yellow]          list all songs in library",
                "  [yellow]mkdir <name>[/yellow]      create new playlist",
                "  [yellow]cd <name>[/yellow]         load playlist",
                "  [yellow]cd ..[/yellow]             back to full library",
                "  [yellow]cp . <name>[/yellow]       add current song to playlist",
                "  [yellow]cp rm <name>[/yellow]      remove current song from playlist",
                "  [yellow]fav/favorites[/yellow]     add current song to 'favorites' playlist",
                "  [yellow]rm <name>[/yellow]         delete playlist",
            ],
            "library": [
            "[bold cyan]Library[/bold cyan]",
            "  [yellow]sort title[/yellow]           sort by title",
            "  [yellow]sort artist[/yellow]          sort by artist",
            "  [yellow]sort album[/yellow]           sort by album",
            "  [yellow]sort date[/yellow]            sort by date added (default)",
            "  [yellow]shuffle[/yellow]              randomize song order",
            "  [yellow]new_dir <path>[/yellow]       change music directory",
        ],
            "appearance": [
                "[bold cyan]Appearance[/bold cyan]",
                "  [yellow]theme <name>[/yellow]      change theme (live)",
                "  [yellow]vis on/off[/yellow]        toggle visualizer",
                "  [yellow]cover <width>[/yellow]     set cover size (20-120, auto, big, small)",
                "  [yellow]cover +/-[/yellow]         increase / decrease cover size by 4",
                "  [yellow]cover <style>[/yellow]     pixel, ascii, braille, quadrant, blocks",
                "  [yellow]cover contrast <x>[/yellow] adjust contrast boost (0.5 to 3.0)",
            ],
            "themes": [
                "[bold cyan]Available Themes[/bold cyan]",
                "  purple  green  red  cyan  magenta  yellow  blue",
                "  darkblue  pink  orange  teal  lime  gold",
                "  cool  warm  neon",
            ],
            "search": [
                "[bold cyan]Search & Download[/bold cyan]",
                "  [yellow]search, s <query>[/yellow]    search Spotify for songs with album art",
                "  [yellow]dl <1-5>[/yellow]             download track with album & cover art",
                "  [yellow]esc[/yellow]                  close search results",
            ],
            "spotify": [
                "[bold cyan]Spotify Integration[/bold cyan]",
                "  [yellow]spotify token <tok>[/yellow]   save Spotify bearer access token",
                "  [yellow]spotify config <id> <sec>[/yellow] save Spotify API client credentials",
                "  [yellow]spotify status[/yellow]        check active Spotify API status",
            ],
            "lyrics": [
                "[bold cyan]Lyrics[/bold cyan]",
                "  [yellow]lyrics, lyr, l[/yellow]         toggle lyrics view",
                "  [yellow]lyrics size <mode>[/yellow]  change size (normal/large/huge)",
                "  [yellow]lyrics on / off[/yellow]       explicitly show/hide lyrics",
                "  [yellow]lyrics fetch[/yellow]          retry fetching online lyrics",
                "  [yellow]lyrics search <query>[/yellow] search LRCLIB for lyrics",
                "  [yellow]lyrics select <1-5>[/yellow]  apply search result and save",
                "  [yellow]lyrics offset <+ms>[/yellow]   adjust timing offset (e.g. +500)",
                "  [yellow]lyrics copy[/yellow]           copy lyrics to clipboard",
                "  [yellow]lyrics reload[/yellow]         reload lyrics from disk",
                "[bold cyan]Lyrics hotkeys[/bold cyan]",
                "  [yellow]l[/yellow]                     toggle lyrics view",
                "  [yellow]+ / -[/yellow]                 increase / decrease lyrics size",
                "  [yellow]up / down / j / k[/yellow]     scroll lyrics manually",
                "  [yellow]esc[/yellow]                   return to library table",
            ],
        }

        if topic is None:
            self.print_to_terminal("[bold]help/man <topic> for details[/bold]")
            for section in help_text.keys():
                self.print_to_terminal(f"  • {section}")
        elif topic in help_text:
            for line in help_text[topic]:
                self.print_to_terminal(line)
        else:
            self.print_to_terminal(f"[red]no manual entry for: {topic}[/red]")
            self.print_to_terminal("[dim]topics: " + ", ".join(help_text.keys()) + "[/dim]")

    def _handle_esc(self):
        """Close search results or lyrics view and return to song table."""
        from climusic.components.lyricsView import LyricsView
        from climusic.components.searchResults import SearchResults
        from climusic.components.songTable import SongTable

        try:
            lv = self.query_one(LyricsView)
            if not lv.has_class("hidden"):
                lv.add_class("hidden")
                self.query_one(SongTable).remove_class("hidden")
                self._is_lyrics_view_active = False
                self.print_to_terminal("[dim]back to library[/dim]")
                return
        except Exception:
            pass

        try:
            sr = self.query_one(SearchResults)
            if not sr.has_class("hidden"):
                sr.add_class("hidden")
                self.query_one(SongTable).remove_class("hidden")
                self.print_to_terminal("[dim]back to library[/dim]")
                return
        except Exception:
            pass

    def _handle_cover_size(self, cmd: str):
        """Adjust or query the album ASCII/pixel cover rendering."""
        from climusic.components.nowPlaying import NowPlaying
        parts = cmd.strip().split()
        try:
            now_playing = self.query_one(NowPlaying)
        except Exception:
            self.print_to_terminal("[red]NowPlaying widget not found[/red]")
            return

        if len(parts) < 2 or parts[1].lower() in ("help", "status", "info"):
            cur_w = getattr(now_playing, "cover_width", "auto")
            cur_style = getattr(now_playing, "cover_style", "ascii")
            cur_contrast = getattr(now_playing, "cover_contrast", 1.25)
            rendered_w = getattr(now_playing, "_rendered_width", 64)
            rendered_h = max(1, int(rendered_w * 0.5))

            if cur_style in ("pixel", "halfblock", "color"):
                pixel_info = f"{rendered_w}x{rendered_w} ({rendered_w * rendered_w:,} true-color square pixels, 2x vertical)"
            elif cur_style in ("quadrant", "quad"):
                pixel_info = f"{rendered_w * 2}x{rendered_h * 2} ({rendered_w * 2 * rendered_h * 2:,} sub-pixels, 4x)"
            elif cur_style == "braille":
                pixel_info = f"{rendered_w * 2}x{rendered_h * 4} ({rendered_w * 2 * rendered_h * 4:,} sub-pixels, 8x)"
            else:
                pixel_info = f"{rendered_w}x{rendered_h} ({rendered_w * rendered_h:,} keyboard characters)"

            self.print_to_terminal("[bold cyan]Cover Settings & Status[/bold cyan]")
            self.print_to_terminal(f"  Width:      [yellow]{cur_w}[/yellow] (active: {rendered_w} cols)")
            self.print_to_terminal(f"  Style:      [yellow]{cur_style}[/yellow]")
            self.print_to_terminal(f"  Resolution: [green]{pixel_info}[/green]")
            self.print_to_terminal(f"  Contrast:   [yellow]{cur_contrast:.2f}x[/yellow]")
            self.print_to_terminal("[dim]Commands: cover <20-120> | cover +/- | cover <pixel|ascii|braille|quadrant|blocks> | cover contrast <0.5-3.0>[/dim]")
            return

        arg = parts[1].lower()

        # Incremental adjustments
        if arg in ("+", "bigger", "up", "zoomin"):
            new_w = now_playing.adjust_cover_width(4)
            self.print_to_terminal(f"[green]cover size increased to: {new_w} cols[/green]")
            return
        elif arg in ("-", "smaller", "down", "zoomout"):
            new_w = now_playing.adjust_cover_width(-4)
            self.print_to_terminal(f"[green]cover size decreased to: {new_w} cols[/green]")
            return

        # Sizing presets
        if arg == "auto":
            now_playing.set_cover_width("auto")
            self.print_to_terminal("[green]cover size set to: auto (responsive)[/green]")
            return
        elif arg in ("small", "sm"):
            now_playing.set_cover_width(40)
            self.print_to_terminal("[green]cover size set to: 40 (small)[/green]")
            return
        elif arg in ("medium", "med"):
            now_playing.set_cover_width(56)
            self.print_to_terminal("[green]cover size set to: 56 (medium)[/green]")
            return
        elif arg in ("big", "large", "lg"):
            now_playing.set_cover_width(72)
            self.print_to_terminal("[green]cover size set to: 72 (big)[/green]")
            return
        elif arg in ("huge", "xl"):
            now_playing.set_cover_width(88)
            self.print_to_terminal("[green]cover size set to: 88 (huge)[/green]")
            return
        elif arg in ("max", "xxl"):
            now_playing.set_cover_width(104)
            self.print_to_terminal("[green]cover size set to: 104 (max)[/green]")
            return

        # Explicit numeric width
        if arg.isdigit():
            val = max(20, min(int(arg), 120))
            now_playing.set_cover_width(val)
            self.print_to_terminal(f"[green]cover size set to: {val} cols[/green]")
            return

        # Contrast adjustment: cover contrast 1.5
        if arg == "contrast":
            if len(parts) >= 3:
                try:
                    cval = float(parts[2])
                    now_playing.set_cover_contrast(cval)
                    self.print_to_terminal(f"[green]cover contrast set to: {cval:.2f}x[/green]")
                    return
                except ValueError:
                    self.print_to_terminal("[red]usage: cover contrast <0.5-3.0>[/red]")
                    return
            else:
                cur_c = getattr(now_playing, "cover_contrast", 1.25)
                self.print_to_terminal(f"current contrast: [yellow]{cur_c:.2f}x[/yellow] (usage: cover contrast <0.5-3.0>)")
                return

        # Style / Mode adjustments: cover style <mode> or cover <mode>
        style_arg = parts[2].lower() if (arg in ("style", "mode") and len(parts) >= 3) else arg
        if style_arg in ("pixel", "halfblock", "color"):
            now_playing.set_cover_style("pixel")
            self.print_to_terminal("[green]cover style set to: pixel (2x true-color half-blocks, 1:1 square pixels)[/green]")
        elif style_arg in ("ascii", "keyboard"):
            now_playing.set_cover_style("ascii")
            self.print_to_terminal("[green]cover style set to: ascii (keyboard symbols:  .,-~:;=!*#$@)[/green]")
        elif style_arg == "braille":
            now_playing.set_cover_style("braille")
            self.print_to_terminal("[green]cover style set to: braille (8x sub-pixel dot matrix)[/green]")
        elif style_arg in ("quadrant", "quad"):
            now_playing.set_cover_style("quadrant")
            self.print_to_terminal("[green]cover style set to: quadrant (4x sub-pixel 2x2 blocks)[/green]")
        elif style_arg in ("blocks", "block"):
            now_playing.set_cover_style("blocks")
            self.print_to_terminal("[green]cover style set to: blocks (Unicode block shading ░▒▓█)[/green]")
        else:
            self.print_to_terminal("[red]unknown cover option. Use: cover <20-120|auto|+/-|pixel|ascii|braille|quadrant|blocks>[/red]")

    def _handle_spotify_command(self, cmd: str):
        """Manage Spotify authentication token and credentials."""
        from climusic.functions.spotifyClient import (
            save_spotify_token,
            save_spotify_credentials,
            load_config
        )
        parts = cmd.split()
        if len(parts) < 2:
            cfg = load_config()
            has_token = bool(cfg.get("spotify_token"))
            has_creds = bool(cfg.get("spotify_client_id") and cfg.get("spotify_client_secret"))
            status = "[green]active[/green]" if (has_token or has_creds) else "[yellow]fallback (iTunes/zero-config)[/yellow]"
            self.print_to_terminal(f"Spotify mode: {status}")
            self.print_to_terminal("[dim]usage: spotify token <access_token>[/dim]")
            self.print_to_terminal("[dim]       spotify config <client_id> <client_secret>[/dim]")
            self.print_to_terminal("[dim]       spotify status[/dim]")
            return

        sub = parts[1].lower()
        if sub == "token":
            if len(parts) < 3:
                self.print_to_terminal("[red]usage: spotify token <access_token>[/red]")
                return
            token = parts[2].strip()
            save_spotify_token(token)
            self.print_to_terminal("[green]Spotify token saved successfully![/green]")
        elif sub in ("config", "auth"):
            if len(parts) < 4:
                self.print_to_terminal("[red]usage: spotify config <client_id> <client_secret>[/red]")
                return
            cid = parts[2].strip()
            csec = parts[3].strip()
            save_spotify_credentials(cid, csec)
            self.print_to_terminal("[green]Spotify credentials saved successfully![/green]")
        elif sub == "status":
            cfg = load_config()
            has_token = bool(cfg.get("spotify_token"))
            has_creds = bool(cfg.get("spotify_client_id") and cfg.get("spotify_client_secret"))
            status = "[green]active[/green]" if (has_token or has_creds) else "[yellow]fallback (iTunes)[/yellow]"
            self.print_to_terminal(f"Spotify mode: {status}")
        else:
            self.print_to_terminal(f"[red]unknown spotify command: {sub}[/red]")
            self.print_to_terminal("[dim]try: spotify token <token> or spotify config <id> <sec>[/dim]")

    # ───────────────────────────────────────────────────────────────
    # Handle repeat
    # ───────────────────────────────────────────────────────────────
    def _handle_repeat(self):
        """Restart current song from the beginning"""
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        if config["repeat"] == True:

            config["repeat"] = False
            with open(CONFIG_PATH, "w") as f:                
                json.dump(config, f)
            
        else:

            config["repeat"] = True
            with open(CONFIG_PATH, "w") as f:                
                json.dump(config, f)
        self.print_to_terminal(f"[dim]repeat :{config['repeat']}.[/dim]")
    # ═══════════════════════════════════════════════════════════════
    # Volume Control
    # ═══════════════════════════════════════════════════════════════
        """
        Handle volume adjustments
        Usage: vol [up|down|0-100]
        """
    def handle_volume(self, cmd: str):    
        parts = cmd.split(maxsplit=1)
        
        if len(parts) == 1:
            # Show current volume
            current = musicController.get_volume()
            self.print_to_terminal(f"volume: {current}%")
        elif len(parts) == 2:
            action = parts[1].lower()
            current = musicController.get_volume()
            
            if action == "up":
                new_vol = min(100, current + 10)
                musicController.set_volume(new_vol)
                self.print_to_terminal(f"volume: {new_vol}%")
            elif action == "down":
                new_vol = max(0, current - 10)
                musicController.set_volume(new_vol)
                self.print_to_terminal(f"volume: {new_vol}%")
            else:
                try:
                    level = int(action)
                    if 0 <= level <= 100:
                        musicController.set_volume(level)
                        self.print_to_terminal(f"volume: {level}%")
                    else:
                        self.print_to_terminal("[red]volume must be 0-100[/red]")
                except ValueError:
                    self.print_to_terminal("[red]usage: vol [up|down|0-100][/red]")
    # ═══════════════════════════════════════════════════════════════
    # Handle Sorting
    # ═══════════════════════════════════════════════════════════════
    def _handle_sort(self, cmd: str):
        parts = cmd.split(maxsplit=1)
        sort_by = "date"  
        
        if len(parts) > 1:
            option = parts[1].lower()
            if option in ("artist", "album", "title"):
                sort_by = option
            elif option in ("date", "added", "new"):
                # sort by file modification time, newest first
                self.songsList = sorted(
                    self.songsList,
                    key=lambda s: os.path.getmtime(s["path"]),
                    reverse=True
                )
                self.index = 0
                self.query_one(SongTable).load_songs(self.songsList)
        
                self.print_to_terminal("[dim]sorted by date added[/dim]")
                return
        
        self.songsList = musicController.filter_songs_alphabetically(self.songsList, sort_by)
        self.index = 0
        self.query_one(SongTable).load_songs(self.songsList)

        self.print_to_terminal(f"[dim]sorted by {sort_by}[/dim]")


