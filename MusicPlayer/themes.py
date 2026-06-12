THEMES = {
    "green": {
        "accent": "lightgreen",
        "background": "black",
    },
    "purple": {
        "accent": "orchid",
        "background": "black",
    },
    "red": {
        "accent": "red",
        "background": "black",
    },
    "black": {
        "accent": "white",
        "background": "black",
    },
    "cyan": {
        "accent": "cyan",
        "background": "black",
    },
    "magenta": {
        "accent": "magenta",
        "background": "black",
    },
    "yellow": {
        "accent": "yellow",
        "background": "black",
    },
    "blue": {
        "accent": "dodgerblue",
        "background": "black",
    },
    "darkblue": {
        "accent": "steelblue",
        "background": "black",
    },
    "pink": {
        "accent": "hotpink",
        "background": "black",
    },
    "orange": {
        "accent": "orange1",
        "background": "black",
    },
    "teal": {
        "accent": "turquoise",
        "background": "black",
    },
    "lime": {
        "accent": "chartreuse1",
        "background": "black",
    },
    "gold": {
        "accent": "gold1",
        "background": "black",
    },
    "cool": {
        "accent": "lightcyan",
        "background": "#1a1a2e",
    },
    "warm": {
        "accent": "lightyellow",
        "background": "#2a1a0a",
    },
    "neon": {
        "accent": "lime",
        "background": "#0a0a0a",
    },
}
def build_css(accent, bg):
    return f"""
    #left_panel {{
        width: 60%;
    }}

    #right_panel {{
        width: 40%;
    }}

    #song-table {{
        color:{accent};
        height:50%;
        border:round {accent};
        background:{bg};
    }}

    #now-playing {{
        color:{accent};
        width: 1fr;
        background: {bg};
        border: {accent} round;
        align: center middle;
        text-align:center;
    }}

    #AlbumAsciiCover {{
        color:{accent};
        content-align: center middle;
        text-align: center;
        padding-top:1;
        padding-left:1;
    }}

    #SongDetails, #SongProgress, #SongTime {{
        color:{accent};
        content-align: center middle;
        text-align: center;
    }}

    #audio-visualizer {{
        color:{accent};
        height: 1fr;
        border: {accent} round;
        content-align: center middle;
        background:{bg};
    }}

    #terminal {{
        height: 12;
        border: round {accent};
        background: {bg};
        padding: 0 1;
    }}

    #terminal-header {{
        color: {accent};
        text-style: bold;
        padding: 0 1;
        height: 1;
    }}

    #terminal-log {{
        height: 1fr;
        color: {accent};
        scrollbar-size: 1 1;
        background: transparent;
    }}

    #terminal-input {{
        border: tall {accent};
        background: {bg};
        color: {accent};
        height: 3;
        margin-top: 1;
    }}

    #terminal-input:focus {{
        border: tall {accent};
    }}
    """
def get_theme(name="green"):
    return THEMES.get(name, THEMES["green"])