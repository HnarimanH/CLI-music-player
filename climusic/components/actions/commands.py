
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
        elif base == "esc":
            self._handle_close_search()
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
            ],
            "themes": [
                "[bold cyan]Available Themes[/bold cyan]",
                "  purple  green  red  cyan  magenta  yellow  blue",
                "  darkblue  pink  orange  teal  lime  gold",
                "  cool  warm  neon",
            ],
            "search": [
                "[bold cyan]Search & Download[/bold cyan]",
                "  [yellow]search, s <query>[/yellow]    search YouTube for songs",
                "  [yellow]dl <1-5>[/yellow]             download result to music dir",
                "  [yellow]esc[/yellow]                  close search results",
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


