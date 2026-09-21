from mutagen.mp4 import MP4
import yt_dlp
import threading
from climusic.components.searchResults import SearchResults
from climusic.components.songTable import SongTable
from climusic import musicController
import time
import json 
class SearchActions:
    _search_results = []  # store results for dl command

    def _handle_search(self, cmd: str):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            self.print_to_terminal("[red]usage: search <query>[/red]")
            return

        query = parts[1]
        self.print_to_terminal(f"[dim]searching: {query}...[/dim]")

        # run in thread so UI doesn't freeze
        threading.Thread(
            target=self._do_search, 
            args=(query,), 
            daemon=True
        ).start()

    def _do_search(self, query: str):
        try:
            ydl_opts = {
                'quiet': True,
                'noplaylist': True,
                'extract_flat': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch5:{query}", download=False)
                self._search_results = [
                    {
                        "title": e["title"],
                        "url": e["url"],
                        "duration": str(e.get("duration", "?")),
                        "channel": e.get("channel", "?"),
                    }
                    for e in info["entries"]
                ]

            # update UI from thread safely
            self.call_from_thread(self._show_search_results)

        except Exception as e:
            self.call_from_thread(
                self.print_to_terminal, f"[red]search failed: {e}[/red]"
            )

    def _show_search_results(self):
        # swap song table for results panel
        self.query_one(SongTable).add_class("hidden")
        results_widget = self.query_one(SearchResults)
        results_widget.remove_class("hidden")
        results_widget.load_results(self._search_results)
        self.print_to_terminal("[dim]dl <1-5> to download | esc to go back[/dim]")

    def _handle_download(self, cmd: str):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].isdigit():
            self.print_to_terminal("[red]usage: dl <1-5>[/red]")
            return

        idx = int(parts[1]) - 1
        if idx < 0 or idx >= len(self._search_results):
            self.print_to_terminal("[red]invalid number[/red]")
            return

        song = self._search_results[idx]
        self.print_to_terminal(f"[dim]downloading: {song['title']}...[/dim]")

        threading.Thread(
            target=self._do_download,
            args=(song,),
            daemon=True
        ).start()

    def _do_download(self, song: dict):
        try:
            with open(musicController.CONFIG_PATH, "r") as f:
                config = json.load(f)

            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'outtmpl': f'{config["dir"]}/%(title)s.%(ext)s',
                'quiet': True,
                
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(song["url"], download=True)
                filepath = ydl.prepare_filename(info)

            # tag it right after download
            audio = MP4(filepath)
            audio['\xa9nam'] = [song["title"]]
            audio['\xa9ART'] = [song.get("channel", "Unknown")]
            audio['\xa9alb'] = ["YouTube"]
            audio.save()

            self.call_from_thread(self.print_to_terminal, f"[green]downloaded: {song['title']}[/green]")
            self.call_from_thread(self._reload_library)

        except Exception as e:
            self.call_from_thread(self.print_to_terminal, f"[red]download failed: {e}[/red]")
    def _reload_library(self):
        
        time.sleep(0.5)  # wait for file to actually land on disk
        musicController.init_library()
        self.allSongs = musicController.return_library()
        print(f"songs: {len(self.allSongs)}")  # debug
        self.songsList = musicController.filter_songs_alphabetically(self.allSongs)
        self.query_one(SongTable).load_songs(self.songsList)
    def _handle_close_search(self):
        self.query_one(SearchResults).add_class("hidden")
        self.query_one(SongTable).remove_class("hidden")
        self.print_to_terminal("[dim]back to library[/dim]")