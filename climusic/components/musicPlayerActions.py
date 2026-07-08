from climusic.components.actions.appearance import AppearanceActions
from climusic.components.actions.playback import PlayBackActions
from climusic.components.actions.playlists import PlayListActions
from climusic.components.actions.commands import CommandActions
from climusic.components.miniTerminal import MiniTerminal
from climusic.components.actions.search import SearchActions

class MusicPlayerActions(PlayBackActions, PlayListActions, AppearanceActions, CommandActions, SearchActions):
  
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


    


    # ═══════════════════════════════════════════════════════════════
    # Utility
    # ═══════════════════════════════════════════════════════════════

    def print_to_terminal(self, msg: str):
        """Write message to mini terminal widget"""
        self.query_one(MiniTerminal).write(msg)