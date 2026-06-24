import os
from climusic import musicController
from climusic.audioEngine import get_position, get_length, song_finished
from climusic.components.nowPlaying import NowPlaying
from climusic.components.miniTerminal import MiniTerminal
import json
from climusic.components.songTable import SongTable
from climusic.musicController import PLAYLISTS_FILE, CONFIG_PATH
import time
class MusicPlayerActions:
    """
    Mixin for song control logic and command handling.
    Expects: self.songsList, self.visualizer, self.progress_bar
    """
    
    # ═══════════════════════════════════════════════════════════════
    # Song Playback & Navigation
    # ═══════════════════════════════════════════════════════════════
    is_paused = False
    _last_skip_time = 0
    SKIP_TIMEOUT = 1 # seconds 


    


    def load_and_play(self, index: int):
        """Load song at index and start playback"""
        song_data = musicController.load_song(index, songs=self.songsList)
        self.song = song_data["song"]
        self.visualizer_frames = song_data["visualizer_frames"]
        musicController.play_song(self.song)
        self.query_one(NowPlaying).update_song(song_data["ascii_cover"], self.song)
    def _can_skip(self) -> bool:
        """Check if enough time has passed since last skip"""
        current_time = time.time()
        if current_time - self._last_skip_time < self.SKIP_TIMEOUT:
            return False
        self._last_skip_time = current_time
        return True

    def play_next_song(self):
        """Skip to next song in playlist"""
        if not self._can_skip():
            return
        
        if not hasattr(self, "song"):
            self.print_to_terminal("[red]no song is loaded[/red]")
            return
        
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        if config.get("repeat") == True:
            self.load_and_play(self.index)
            return
        
        self.index += 1
        if self.index >= len(self.songsList):
            self.index = 0
        
        self.load_and_play(self.index)

    def play_previous_song(self):
        """Go back to previous song in playlist"""
        if not self._can_skip():
            return
        
        if not hasattr(self, "song"):
            self.print_to_terminal("[red]no song is loaded[/red]")
            return
        
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        if config.get("repeat") == True:
            self.load_and_play(self.index)
            return
        
        self.index -= 1
        if self.index < 0:
            self.index = len(self.songsList) - 1
        
        self.load_and_play(self.index)


    def action_toggle_pause(self):
        """Toggle play/pause state"""
        if  not hasattr(self, "song"):
            self.print_to_terminal("[red]no song is loaded[/red]")
            return
        if self.is_paused:
            musicController.unpause_song()
            self.print_to_terminal("resumed.")
        else:
            musicController.pause_song()
            self.print_to_terminal("paused.")
        self.is_paused = not self.is_paused

    def forward_song(self):
        if song_finished():
            self.play_next_song()
            return
        
        current = get_position()
        total = get_length()
        
        if current < 0 or not total or total <= 0:
            return
        
        new_position = min(current + 5, total)
        musicController.set_position(new_position)

    def back_song(self):
        
        current = get_position()
        total = get_length()
        if current < 0 or not total or total <= 0:
            musicController.set_position(0)
            return
        
        new_position = max(current - 5, 0)
        musicController.set_position(new_position)


    
    # ═══════════════════════════════════════════════════════════════
    # Progress & Visualization Updates
    # ═══════════════════════════════════════════════════════════════

    def update_progress(self) -> None:
        """
        Called every ~50ms to update:
        - Audio visualizer frame
        - Progress bar position
        - Auto-play next song when finished
        """
        try:
            current = get_position()
            total = get_length()
            
            if current < 0 or not total or total <= 0:
                return
            if not total or total <= 0 or not hasattr(self, "visualizer_frames"):
                return
            if song_finished():
                self.play_next_song()
            # Update visualizer if enabled
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            if config.get("visualizer", True) and hasattr(self, "visualizer"):
                frame_index = min(
                    int((current / total) * len(self.visualizer_frames) - 1),
                    len(self.visualizer_frames) - 1
                )
                frame_index = max(0, frame_index)
                self.visualizer.update_wave(self.visualizer_frames[frame_index])

            if current < 0:
                return

            # Update progress bar
            self.progress_bar.update_progress(current, total)

            # Auto-advance to next song
            

        except Exception as e:
            print(f"[red]error: {e}[/red]")

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
                "  [yellow]sort <artist,album,title>[/yellow]   sort songs alphabetically(title default)",
                "  [yellow]shuffle[/yellow]                     randomize song order",
                "  [yellow]new_dir <path>[/yellow]              change music directory",
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
            ]
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
    # ───────────────────────────────────────────────────────────────
    # Handle new directory
    # ───────────────────────────────────────────────────────────────
    def handle_new_dir(self, cmd: str):
        """Change music directory and reload library"""
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            self.print_to_terminal("[red]usage: new_dir <path>[/red]")
            return
        
        new_dir = parts[1]
        if not os.path.isdir(new_dir):
            self.print_to_terminal("[red]invalid directory[/red]")
            return
        
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        config["dir"] = new_dir
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
        
        musicController.init_library(new_dir=new_dir)
        self.songsList = musicController.return_library()
        self.index = 0
        self.query_one(SongTable).load_songs(self.songsList)
        
        
        self.load_and_play(self.index)
        self.print_to_terminal(f"[dim]music directory changed to: {new_dir}[/dim]")
    # ───────────────────────────────────────────────────────────────
    # Shuffle
    # ───────────────────────────────────────────────────────────────

    def _handle_shuffle(self):
        """Toggle shuffle mode"""
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        config["shuffle"] = not config.get("shuffle", False)
        current_songs =  musicController.filter_songs_alphabetically(self.songsList, sort_by="title")  # Preserve current order for unshuffling
        # Update the song list based on shuffle state
        if config["shuffle"]:
            self.songsList = musicController.shuffle_library(current_songs)
            msg = "shuffle: on"
        else:
            # Reload original library order
            self.songsList = current_songs
            msg = "shuffle: off"
        
        # Save config
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
        
        # Rebuild table once
        self.index = 0
        self.query_one(SongTable).load_songs(self.songsList)
            
        
        self.load_and_play(self.index)
        self.print_to_terminal(f"[dim]{msg}[/dim]")
    # ───────────────────────────────────────────────────────────────
    # Theme Management
    # ───────────────────────────────────────────────────────────────

    def _handle_theme(self, cmd: str):
        """Change app theme (live update)"""
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            self.print_to_terminal("[red]usage: theme <name>[/red]")
            return
        
        theme_name = parts[1].lower()
        valid_themes = [
            "purple", "green", "red", "cyan", "magenta", "yellow", "blue",
            "darkblue", "pink", "orange", "teal", "lime", "gold",
            "cool", "warm", "neon"
        ]
        
        if theme_name not in valid_themes:
            self.print_to_terminal(f"[red]unknown theme. available: {', '.join(valid_themes)}[/red]")
            return
        
        # Swap theme class
        for t in valid_themes:
            self.remove_class(t)
        self.add_class(theme_name)
        
        # Save preference
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        config["theme"] = theme_name
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
        
        self.print_to_terminal(f"[dim]theme set to {theme_name}[/dim]")

    # ───────────────────────────────────────────────────────────────
    # Visualizer Toggle
    # ───────────────────────────────────────────────────────────────

    def _handle_visualizer(self, cmd: str):
        """Toggle visualizer on/off (applies on next launch)"""
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            self.print_to_terminal("[dim]usage: vis <on|off>[/dim]")
            return
        
        state = parts[1].lower()
        if state not in ("on", "off"):
            self.print_to_terminal("[red]must be 'on' or 'off'[/red]")
            return
        
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        config["visualizer"] = state == "on"
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
        
        self.print_to_terminal(f"[dim]visualizer set to: {state}, changes will apply on next launch[/dim]")

    # ═══════════════════════════════════════════════════════════════
    # Playlist Management
    # ═══════════════════════════════════════════════════════════════

    def handle_playlist(self, cmd: str):
        parts = cmd.split(maxsplit=2)
        base = parts[0]

        if base == "ls":
            if len(parts) == 1:
                # list playlists
                playlists = musicController.get_playlists()
                if not playlists:
                    self.print_to_terminal("[dim]no playlists[/dim]")
                else:
                    for name in playlists:
                        self.print_to_terminal(f"  [cyan]d[/cyan]  {name}/")
            elif parts[1] == "songs":
                for i, song in enumerate(self.songsList, start=1):
                    self.print_to_terminal(f"  {i}. {song['title']} — {song['artist']}")

        elif base == "cd":
            if len(parts) < 2:
                self.print_to_terminal("[red]usage: cd <playlist> | cd ..[/red]")
                return
            if parts[1] == "..":
                if not hasattr(self, 'allSongs'):
                    
                    return  
                self.songsList = self.allSongs
                self.index = 0
                self.query_one(SongTable).load_songs(self.songsList)
                self.load_and_play(0)
                self.print_to_terminal("[dim]~ back to library[/dim]")
            else:
                songs = musicController.load_playlist(parts[1])
                if songs:
                    self.songsList = songs
                    self.index = 0
                    self.query_one(SongTable).load_songs(self.songsList)
                    self.load_and_play(0)
                    self.print_to_terminal(f"[dim]~/{parts[1]} ({len(songs)} songs)[/dim]")
                else:
                    self.print_to_terminal(f"[red]cd: {parts[1]}: no such playlist[/red]")

        elif base == "mkdir":
            if len(parts) < 2:
                self.print_to_terminal("[red]usage: mkdir <name>[/red]")
                return
            if musicController.create_playlist(parts[1]):
                self.print_to_terminal(f"[dim]created playlist '{parts[1]}'[/dim]")
            else:
                self.print_to_terminal(f"[red]mkdir: {parts[1]}: already exists[/red]")

        elif base == "cp":
            # cp . <playlist>
            
            if len(parts) < 3 or parts[1] not in (".", "rm"):
                self.print_to_terminal("[red]usage: cp . <playlist>[/red]")
                return
            if not hasattr(self, "song"):
                self.print_to_terminal("[red]cp: no song loaded[/red]")
                return

            if hasattr(self, "song"):
                if parts[1] == ".":
                    song_to_save = {k: self.song[k] for k in ("title", "artist", "album", "length", "path", "filename")}
                    if musicController.add_to_playlist(parts[2], song_to_save):
                        self.print_to_terminal(f"[dim]'{self.song['title']}' → {parts[2]}[/dim]")
                        self.print_to_terminal(f"[dim]'cd . {parts[2]}' to view {parts[2]}[/dim]")
                    else:
                        self.print_to_terminal(f"[red]cp: {parts[2]}: no such playlist[/red]")
                elif parts[1] == "rm":
                    if musicController.remove_from_playlist(parts[2], self.song):
                        self.print_to_terminal(f"[dim]removed '{self.song['title']}' from {parts[2]}[/dim]")
                    else:
                        self.print_to_terminal(f"[red]cp: {parts[2]}: no such playlist or song not in playlist[/red]")
            else:
                self.print_to_terminal("[red]cp: no song loaded[/red]")

        elif base == "rm":
            if len(parts) < 2:
                self.print_to_terminal("[red]usage: rm <playlist>[/red]")
                return
            if musicController.delete_playlist(parts[1]):
                self.print_to_terminal(f"[dim]removed '{parts[1]}'[/dim]")
            else:
                self.print_to_terminal(f"[red]rm: {parts[1]}: no such playlist[/red]")
    # ═══════════════════════════════════════════════════════════════
    # Handle Favorites
    # ═══════════════════════════════════════════════════════════════
    def handle_favorites(self, cmd: str):
        parts = cmd.split(maxsplit=1)
        if len(parts) != 1:
            self.print_to_terminal("[red]usage: fav[/red]")
            return
        if  not hasattr(self, "song"):
            self.print_to_terminal("[red]no song is loaded[/red]")
            return
        with open(PLAYLISTS_FILE, "r") as f:
            playlists = json.load(f)
        if playlists.get("favorites") is None:
           musicController.create_playlist("favorites")
        song_to_save = {k: self.song[k] for k in ("title", "artist", "album", "length", "path", "filename")}
        musicController.add_to_playlist("favorites", song_to_save)
        self.print_to_terminal(f"[dim]'{self.song['title']}' → favorites[/dim]")
        self.print_to_terminal(f"[dim]'cd . favorites' to view favorites[/dim]")
        
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
        """Sort songs alphabetically"""
        parts = cmd.split(maxsplit=1)
        sort_by = "title"  # default
        
        if len(parts) > 1:
            option = parts[1].lower()
            if option in ("artist", "album", "title"):
                sort_by = option
        
        self.songsList = musicController.filter_songs_alphabetically(self.songsList, sort_by)
        self.index = 0
        
        self.query_one(SongTable).load_songs(self.songsList)
        self.load_and_play(self.index)
        self.print_to_terminal(f"[dim]sorted by {sort_by}[/dim]")




    # ═══════════════════════════════════════════════════════════════
    # Utility
    # ═══════════════════════════════════════════════════════════════

    def print_to_terminal(self, msg: str):
        """Write message to mini terminal widget"""
        self.query_one(MiniTerminal).write(msg)