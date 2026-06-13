import musicController
from audioEngine import get_position, get_length, song_finished
from components.nowPlaying import NowPlaying
from components.miniTerminal import MiniTerminal
import json

class MusicPlayerActions:
    """Mixin for song control logic. Expects self.songsList, self.visualizer, self.progress_bar."""

    def load_and_play(self, index: int):
        song_data = musicController.load_song(index, songs=self.songsList)
        self.song = song_data["song"]
        self.visualizer_frames = song_data["visualizer_frames"]
        musicController.play_song(index + 1)
        self.query_one(NowPlaying).update_song(song_data["ascii_cover"], self.song)

    def play_next_song(self):
        self.index += 1
        if self.index >= len(self.songsList):
            return
        self.load_and_play(self.index)
    def play_previous_song(self):
        self.index -= 1
        if self.index >= len(self.songsList):
            return
        self.load_and_play(self.index)

    def update_progress(self) -> None:
        try:
            current = get_position()
            total = get_length()
            if current < 0 or not total or total <= 0:
                return
            if not total or total <= 0 or not hasattr(self, "visualizer_frames"):
                return
            with open("config.json", "r") as f:
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

            self.progress_bar.update_progress(current, total)

            if song_finished():
                self.play_next_song()

        except Exception as e:
            print(f"[red]error: {e}[/red]")

    def handle_command(self, cmd: str):
        if cmd == "p" or cmd == "previouse" or cmd == "pre":
            self.print_to_terminal("loading previous song.")
            self.play_previous_song()
        elif cmd == "n" or cmd == "next":
            self.print_to_terminal("loading next song.")
            self.play_next_song()
        elif cmd == "s" or cmd == "stop":
            musicController.pause_song()
            self.print_to_terminal("stopped.")
        elif cmd == "r" or cmd == "resume":
            musicController.unpause_song()
            self.print_to_terminal("resumed.")
        elif cmd.startswith("volume") or cmd.startswith("vol"):
            self.handle_volume(cmd)
        elif cmd.startswith("theme"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                self.print_to_terminal("[red]usage: theme <name>[/red]")
            else:
                theme_name = parts[1].lower()
                valid_themes = [
                    "purple", "green", "red", "cyan", "magenta", "yellow", "blue",
                    "darkblue", "pink", "orange", "teal", "lime", "gold",
                    "cool", "warm", "neon"
                ]
                
                if theme_name not in valid_themes:
                    self.print_to_terminal(f"[red]unknown theme. available: {', '.join(valid_themes)}[/red]")
                else:
                    
                    for t in valid_themes:
                        self.remove_class(t)
                    self.add_class(theme_name)
                    
                    
                    with open("config.json", "r") as f:
                        config = json.load(f)
                    config["theme"] = theme_name
                    with open("config.json", "w") as f:
                        json.dump(config, f)
                    
                    self.print_to_terminal(f"[dim]theme set to {theme_name}[/dim]")
        elif cmd.startswith("vis") or cmd.startswith("visualizer"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                self.print_to_terminal("[dim]usage: vis <on|off>[/dim]")
            else:
                state = parts[1].lower()
                if state not in ("on", "off"):
                    self.print_to_terminal("[red]must be 'on' or 'off'[/red]")
                else:
                    with open("config.json", "r") as f:
                        config = json.load(f)
                    config["visualizer"] = state == "on"  
                    with open("config.json", "w") as f:
                        json.dump(config, f)
                    self.print_to_terminal(f"[dim]visualizer set to: {state}, changes will apply on next launch[/dim]")
        else:
            self.print_to_terminal(f"[dim]unknown command: {cmd}[/dim]")

    def handle_volume(self, cmd: str):
        """Handle volume commands: vol, vol up, vol down, vol <0-100>"""
        parts = cmd.split(maxsplit=1)
        
        if len(parts) == 1:
            # just "vol" or "volume"
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

    def print_to_terminal(self, msg: str):
        self.query_one(MiniTerminal).write(msg)