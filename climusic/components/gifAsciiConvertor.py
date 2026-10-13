from climusic.functions.coverToAscii import cover_to_ascii
import json
from pathlib import Path
from PIL import Image
from importlib import resources
from io import BytesIO
APP_DIR = Path.home() / ".climusic"
APP_DIR.mkdir(exist_ok=True)
ASCII_ANIMATION_DIR = APP_DIR / "cache" / "ascii_animations"
ASCII_ANIMATION_DIR.mkdir(parents=True, exist_ok=True)

def gif_to_ascii(gif_path=None,
                output_path=ASCII_ANIMATION_DIR / "defaultGif.json", 
                width=80
                ):
    if gif_path is None:
        with resources.files("climusic.assets").joinpath("defaultGif.gif").open("rb") as f:
            gif = Image.open(BytesIO(f.read()))
    else:
        gif = Image.open(gif_path)
        
    output_path = Path(output_path)

    frames = []

    for frame in range(gif.n_frames):
        gif.seek(frame)
    
        # Copy the current composited frame
        image = gif.convert("RGB").copy()
    
        # Resize while accounting for terminal character proportions
        height = max(1, int(image.height / image.width * width * 0.5))
        image = image.resize((width, height))
    
        # Use your existing conversion function here
        ascii_frame = cover_to_ascii(image)
    
        frames.append({
            "ascii": ascii_frame,
                    "duration": gif.info.get("duration", 100)
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(frames, file, ensure_ascii=False)

    return len(frames)