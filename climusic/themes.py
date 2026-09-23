def build_css():
    themes = {
        "purple": {"accent": "orchid", "bg": "black"},
        "green": {"accent": "lightgreen", "bg": "black"},
        "red": {"accent": "red", "bg": "black"},
        "cyan": {"accent": "cyan", "bg": "black"},
        "magenta": {"accent": "magenta", "bg": "black"},
        "yellow": {"accent": "yellow", "bg": "black"},
        "blue": {"accent": "dodgerblue", "bg": "black"},
        "darkblue": {"accent": "steelblue", "bg": "black"},
        "pink": {"accent": "hotpink", "bg": "black"},
        "orange": {"accent": "orange", "bg": "black"},  # was orange1
        "teal": {"accent": "turquoise", "bg": "black"},
        "lime": {"accent": "chartreuse", "bg": "black"},  # was chartreuse1
        "gold": {"accent": "gold", "bg": "black"},  # was gold1
        "cool": {"accent": "lightcyan", "bg": "#1a1a2e"},
        "warm": {"accent": "lightyellow", "bg": "#2a1a0a"},
        "neon": {"accent": "lime", "bg": "#0a0a0a"},
    }
    
    # Base CSS (layout, no colors)
    base_css = """
    #left_panel {
        width: 55%;
    }

    #right_panel {
        width: 45%;
    }

    #song-table {
    
        height: 1fr;
        border: round;
        padding: 1;
    }
    #search-table {
        height: 1fr;
        border: round;
        padding: 1;
    }
    #lyrics-view {
        height: 1fr;
        border: round;
        padding: 1 2;
        content-align: center middle;
        text-align: center;
    }

    #table-container {
        height: 1fr;
    }

    #now-playing {
        padding: 1;
        text-align: center;
        width: 1fr;
        height: 1fr;
        border: round;
        align: center middle;
        text-align: center;
        overflow-y: auto;
        scrollbar-size: 1 1;
    }

    #AlbumAsciiCover {
        content-align: center middle;
        text-align: center;
        overflow-x: hidden;
    }

    #SongDetails, #SongProgress, #SongTime {
        content-align: center middle;
        text-align: center;
    }
    #NowPlayingLyric {
        height: 3;
        margin-top: 1;
        border: round;
        content-align: center middle;
        text-align: center;
    }
    .hidden {
        display: none;}
    #audio-visualizer {
        height: 15%;
        border: round;
        content-align: center middle;
    }

    #terminal {
        height: 35%;
        border: round;
        content-align: center middle;
    }

    #terminal-header {
        text-style: bold;
        padding: 0 1;
        height: 1;
    }

    #terminal-log {
        height: 1fr;
        scrollbar-size: 1 1;
        background: transparent;
    }

    #terminal-input {
       
        height: 3;
        margin-top: 1;
    }

    #terminal-input:focus {
        
    }
    """
    
    # Theme-specific CSS
    theme_css = ""
    for name, colors in themes.items():
        theme_css += f"""
        .{name} #song-table, .{name} #search-table, .{name} #lyrics-view {{
            color: {colors['accent']};
            border: round {colors['accent']};
            background: {colors['bg']};
        }}

        .{name} #now-playing {{
            color: {colors['accent']};
            background: {colors['bg']};
            border: round {colors['accent']};
        }}

        .{name} #AlbumAsciiCover {{
            color: {colors['accent']};
        }}

        .{name} #SongDetails, .{name} #SongProgress, .{name} #SongTime {{
            color: {colors['accent']};
        }}

        .{name} #NowPlayingLyric {{
            color: {colors['accent']};
            border: round {colors['accent']};
        }}

        .{name} #audio-visualizer {{
            color: {colors['accent']};
            border: round {colors['accent']};
            background: {colors['bg']};
        }}

        .{name} #terminal {{
            border: round {colors['accent']};
            background: {colors['bg']};
        }}

        .{name} #terminal-header {{
            color: {colors['accent']};
        }}

        .{name} #terminal-log {{
            color: {colors['accent']};
        }}

        .{name} #terminal-input {{
            border: tall {colors['accent']};
            background: {colors['bg']};
            color: {colors['accent']};
        }}

        .{name} #terminal-input:focus {{
            border: tall {colors['accent']};
        }}
        """
    
    return base_css + theme_css