import os
import re
import json
import time
import requests
import threading
import yt_dlp
from mutagen.mp4 import MP4, MP4Cover
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC
from climusic.components.searchResults import SearchResults
from climusic.components.songTable import SongTable
from climusic import musicController
from climusic.functions.spotifyClient import search_tracks
from climusic.functions.lyricsFetcher import load_lyrics_for_song


def sanitize_filename(filename: str) -> str:
    return re.sub(r'[/\\:*?"<>|]', '_', filename).strip()


class SearchActions:
    _search_results = []  # store results for dl command

    def _handle_search(self, cmd: str):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            self.print_to_terminal("[red]usage: search <query>[/red]")
            return

        query = parts[1]
        self.print_to_terminal(f"[dim]searching Spotify: {query}...[/dim]")

        # run in thread so UI doesn't freeze
        threading.Thread(
            target=self._do_search,
            args=(query,),
            daemon=True
        ).start()

    def _do_search(self, query: str):
        try:
            results = search_tracks(query, limit=5)
            self._search_results = results
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
        source = self._search_results[0].get("source", "spotify") if self._search_results else "spotify"
        count = len(self._search_results)
        self.print_to_terminal(f"[dim]found {count} tracks ({source}) | dl <1-{count}> to download | esc to return[/dim]")

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
        self.print_to_terminal(f"[dim]downloading '{song['title']}' by {song['artist']}...[/dim]")

        threading.Thread(
            target=self._do_download,
            args=(song,),
            daemon=True
        ).start()

    def _do_download(self, song: dict):
        try:
            with open(musicController.CONFIG_PATH, "r") as f:
                config = json.load(f)

            music_dir = config.get("dir", ".")
            safe_name = sanitize_filename(f"{song['artist']} - {song['title']}")

            # 1. Download best quality audio stream matching the Spotify track
            download_query = f"ytsearch1:{song['artist']} - {song['title']} audio"
            out_template = os.path.join(music_dir, f"{safe_name}.%(ext)s")

            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': out_template,
                'quiet': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(download_query, download=True)
                filepath = ydl.prepare_filename(info)

            # In case the downloader merged or converted extension
            if not os.path.exists(filepath):
                base_without_ext = os.path.splitext(filepath)[0]
                for ext in (".m4a", ".mp3", ".webm", ".opus"):
                    candidate = base_without_ext + ext
                    if os.path.exists(candidate):
                        filepath = candidate
                        break

            # 2. Download high-resolution Spotify album cover art
            cover_bytes = None
            if song.get("cover_url"):
                try:
                    c_res = requests.get(song["cover_url"], timeout=10)
                    if c_res.status_code == 200:
                        cover_bytes = c_res.content
                except Exception:
                    pass

            # 3. Embed metadata (Title, Artist, Album, Year) and Cover Art
            ext = os.path.splitext(filepath)[1].lower()
            if ext in (".m4a", ".mp4"):
                try:
                    audio = MP4(filepath)
                    audio['\xa9nam'] = [song["title"]]
                    audio['\xa9ART'] = [song["artist"]]
                    audio['\xa9alb'] = [song.get("album", "Unknown Album")]
                    if song.get("year"):
                        audio['\xa9day'] = [str(song["year"])]
                    if cover_bytes:
                        img_fmt = MP4Cover.FORMAT_PNG if cover_bytes.startswith(b'\x89PNG') else MP4Cover.FORMAT_JPEG
                        audio['covr'] = [MP4Cover(cover_bytes, imageformat=img_fmt)]
                    audio.save()
                except Exception as e:
                    print(f"MP4 tagging error: {e}")
            elif ext == ".mp3":
                try:
                    audio = MP3(filepath, ID3=ID3)
                    try:
                        audio.add_tags()
                    except Exception:
                        pass
                    audio.tags.add(TIT2(encoding=3, text=song["title"]))
                    audio.tags.add(TPE1(encoding=3, text=song["artist"]))
                    audio.tags.add(TALB(encoding=3, text=song.get("album", "Unknown Album")))
                    if song.get("year"):
                        audio.tags.add(TDRC(encoding=3, text=str(song["year"])))
                    if cover_bytes:
                        mime = "image/png" if cover_bytes.startswith(b'\x89PNG') else "image/jpeg"
                        audio.tags.add(APIC(
                            encoding=3,
                            mime=mime,
                            type=3,
                            desc="Cover",
                            data=cover_bytes
                        ))
                    audio.save()
                except Exception as e:
                    print(f"MP3 tagging error: {e}")

            # 4. Automatically pre-fetch & cache synchronized lyrics
            try:
                load_lyrics_for_song({
                    "title": song["title"],
                    "artist": song["artist"],
                    "path": filepath,
                    "filename": os.path.basename(filepath)
                }, allow_network=True)
            except Exception:
                pass

            self.call_from_thread(
                self.print_to_terminal,
                f"[green]downloaded '{song['title']}' with album '{song.get('album', '')}' and artwork![/green]"
            )
            self.call_from_thread(self._reload_library)

        except Exception as e:
            self.call_from_thread(self.print_to_terminal, f"[red]download failed: {e}[/red]")

    def _reload_library(self):
        time.sleep(0.5)  # wait for file to actually land on disk
        musicController.init_library()
        self.allSongs = musicController.return_library()
        self.songsList = musicController.filter_songs_alphabetically(self.allSongs)
        self.query_one(SongTable).load_songs(self.songsList)

    def _handle_close_search(self):
        self.query_one(SearchResults).add_class("hidden")
        self.query_one(SongTable).remove_class("hidden")
        self.print_to_terminal("[dim]back to library[/dim]")