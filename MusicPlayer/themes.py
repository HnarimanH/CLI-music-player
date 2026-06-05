from themes import get_theme

theme = get_theme("green")
accent = theme["accent"]
bg = theme["background"]

CSS = f"""
    #song-table {{
        color:{accent};
        height:50%;
        border:round;
        background:{bg};
    }}

    #now-playing {{
        color:{accent};
        width: 1fr;
        height: 100%;
        background: {bg};
        border: round;
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

    #SongDetails {{
        color:{accent};
        content-align: center middle;
        text-align: center;
    }}
    
    #SongProgress {{
        color:{accent};
        content-align: center middle;
        text-align: center;
    }}

    #SongTime {{
        color:{accent};
        content-align: center middle;
        text-align: center;
    }}

    #audio-visualizer {{
        color:{accent};
        height: 1fr;
        border: round;
        content-align: center middle;
        background:{bg};
    }}
    
    #left_panel {{
        width:60%;
    }}
    """