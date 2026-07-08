from climusic import musicController
import json
from climusic.components.songTable import SongTable
# add this at the top of playlists.py
from climusic.musicController import PLAYLISTS_FILE


class PlayListActions:
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
        