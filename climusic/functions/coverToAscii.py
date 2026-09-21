from io import BytesIO
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from importlib import resources

BLOCK_RAMP = "  ░░▒▒▓▓██"
ASCII_RAMP = " .:-=+*#%@"


def cover_to_ascii(cover_bytes, width=64, style="blocks"):
    """
    Converts album cover artwork into high-visibility, crisp terminal ASCII/block art.
    Features:
    - Autocontrast normalization to prevent dark/washed-out covers
    - Balanced contrast enhancement for terminal readability
    - Lanczos resampling with 0.5 terminal aspect ratio correction
    - Unsharp mask edge sharpening so details, logos, and features pop
    - Cyberpunk block shading (░▒▓█) matching the audio visualizer
    """
    try:
        image = Image.open(BytesIO(cover_bytes))
    except Exception as e:
        with resources.files("climusic.assets").joinpath("defaultAlbumCover.jpeg").open("rb") as f:
            image = Image.open(BytesIO(f.read()))

    # Handle transparent PNG/M4A images cleanly over a dark background
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        bg = Image.new("RGB", image.size, (0, 0, 0))
        try:
            mask = image.split()[-1]
            bg.paste(image, mask=mask)
            image = bg
        except Exception:
            pass

    # Convert to grayscale
    image = image.convert("L")

    # Autocontrast maximizes dynamic range so dark albums aren't lost
    image = ImageOps.autocontrast(image, cutoff=1)

    # Balanced contrast boost for punchy terminal clarity
    contrast = ImageEnhance.Contrast(image)
    image = contrast.enhance(1.25)

    # Maintain aspect ratio with 0.5 height factor for standard terminal character cells
    aspect_ratio = image.height / image.width
    height = max(1, int(width * aspect_ratio * 0.5))
    image = image.resize((width, height), Image.Resampling.LANCZOS)

    # Unsharp mask sharpens lines, borders, faces, and text
    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140))

    try:
        pixels = list(image.get_flattened_data())
    except AttributeError:
        pixels = list(image.getdata())

    ramp = ASCII_RAMP if style == "ascii" else BLOCK_RAMP
    num_chars = len(ramp)

    lines = []
    for r in range(height):
        row = []
        for c in range(width):
            val = pixels[r * width + c]
            idx = min(num_chars - 1, max(0, int(val * num_chars / 256)))
            row.append(ramp[idx])
        lines.append("".join(row))

    return "\n".join(lines)