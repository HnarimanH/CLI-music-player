from climusic.musicController import CONFIG_PATH
import json
from climusic import musicController
from climusic.components.songTable import SongTable
import os

class AppearanceActions:

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
