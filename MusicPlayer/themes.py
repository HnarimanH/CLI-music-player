THEMES = {
    "green": {
        "accent": "lightgreen",
        "background": "black",
    },
    "purple": {
        "accent": "orchid",
        "background": "black",
    },
}

def get_theme(name="green"):
    return THEMES.get(name, THEMES["green"])