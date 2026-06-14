from io import BytesIO
from PIL import Image, ImageEnhance

ASCII_CHARS = " .:-=+*#%@"


def cover_to_ascii(cover_bytes, width=30):
    if cover_bytes is None:
        return "No Cover Art"

    image = Image.open(BytesIO(cover_bytes))

    # Convert to grayscale
    image = image.convert("L")

    # Resize while preserving aspect ratio
    aspect_ratio = image.height / image.width
    height = max(1, int(width * aspect_ratio * 0.5))
    image = image.resize((width, height))

    # Improve visibility of details
    brightness = ImageEnhance.Brightness(image)
    image = brightness.enhance(0.4)

    contrast = ImageEnhance.Contrast(image)
    image = contrast.enhance(5.0)

    pixels = list(image.getdata())

    ascii_str = ""

    for i, pixel in enumerate(pixels):
        char_index = pixel * (len(ASCII_CHARS) - 1) // 255
        ascii_str += ASCII_CHARS[char_index]

        if (i + 1) % width == 0:
            ascii_str += "\n"

    return ascii_str