from io import BytesIO
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from importlib import resources

KEYBOARD_RAMP = "  .,-~:;=!*#$@"
BLOCK_RAMP = "  ░░▒▒▓▓██"
ASCII_RAMP = KEYBOARD_RAMP

QUADRANT_CHARS = [
    ' ', '▖', '▗', '▄',
    '▘', '▌', '▚', '▙',
    '▝', '▞', '▐', '▟',
    '▀', '▛', '▜', '█'
]

BRAILLE_DOTS = [
    (0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (0, 3, 0x40),
    (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (1, 3, 0x80)
]


def _open_image(cover_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(cover_bytes))
    except Exception:
        with resources.files("climusic.assets").joinpath("defaultAlbumCover.jpeg").open("rb") as f:
            image = Image.open(BytesIO(f.read()))

    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        bg = Image.new("RGB", image.size, (0, 0, 0))
        try:
            mask = image.split()[-1]
            bg.paste(image, mask=mask)
            image = bg
        except Exception:
            pass
    return image


def cover_to_ascii(cover_bytes: bytes, width: int = 64, style: str = "ascii", contrast: float = 1.25) -> str:
    """
    Converts album cover artwork into high-visibility, high-resolution terminal art.
    Supports rendering more pixels via sub-pixel character techniques or higher resolution ASCII:
      - 'ascii' / 'keyboard': Calibrated optical density ramp using keyboard symbols ("  .,-~:;=!*#$@")
      - 'pixel' / 'halfblock': True-color half-block sub-pixel rendering (2 vertical pixels per cell, 1:1 square pixels)
      - 'quadrant' / 'quad': 2x2 sub-pixel blocks (4 pixels per character cell)
      - 'braille': 2x4 sub-pixel dots (8 pixels per character cell)
      - 'blocks': Cyberpunk Unicode density block shading ("  ░░▒▒▓▓██")
    """
    image = _open_image(cover_bytes)
    aspect_ratio = image.height / max(1, image.width)
    h_chars = max(1, int(width * aspect_ratio * 0.5))

    style_clean = (style or "ascii").lower().strip()

    if style_clean in ("pixel", "halfblock", "color"):
        # 2 vertical pixels per character cell -> true square pixels in 24-bit color!
        total_pixel_rows = h_chars * 2
        img_rgb = image.convert("RGB")
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img_rgb)
            img_rgb = enhancer.enhance(max(0.2, contrast))
        img_resized = img_rgb.resize((width, total_pixel_rows), Image.Resampling.LANCZOS)
        img_resized = img_resized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140))

        lines = []
        for r in range(h_chars):
            row = []
            y_top = r * 2
            y_bot = y_top + 1
            for c in range(width):
                r1, g1, b1 = img_resized.getpixel((c, y_top))
                r2, g2, b2 = img_resized.getpixel((c, y_bot))
                row.append(f"[#{r1:02x}{g1:02x}{b1:02x} on #{r2:02x}{g2:02x}{b2:02x}]▀[/]")
            lines.append("".join(row))
        return "\n".join(lines)

    elif style_clean in ("quadrant", "quad"):
        # 2x2 subpixels per character -> 4x pixel resolution
        img_gray = image.convert("L")
        img_gray = ImageOps.autocontrast(img_gray, cutoff=1)
        if contrast != 1.0:
            img_gray = ImageEnhance.Contrast(img_gray).enhance(max(0.2, contrast))
        sub_img = img_gray.resize((width * 2, h_chars * 2), Image.Resampling.LANCZOS)
        sub_img = sub_img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140)).convert("1")

        lines = []
        for r in range(h_chars):
            row = []
            for c in range(width):
                tl = 1 if sub_img.getpixel((c * 2, r * 2)) > 0 else 0
                tr = 1 if sub_img.getpixel((c * 2 + 1, r * 2)) > 0 else 0
                bl = 1 if sub_img.getpixel((c * 2, r * 2 + 1)) > 0 else 0
                br = 1 if sub_img.getpixel((c * 2 + 1, r * 2 + 1)) > 0 else 0
                idx = (bl << 0) | (br << 1) | (tl << 2) | (tr << 3)
                row.append(QUADRANT_CHARS[idx])
            lines.append("".join(row))
        return "\n".join(lines)

    elif style_clean == "braille":
        # 2x4 subpixels per character -> 8x pixel resolution
        img_gray = image.convert("L")
        img_gray = ImageOps.autocontrast(img_gray, cutoff=1)
        if contrast != 1.0:
            img_gray = ImageEnhance.Contrast(img_gray).enhance(max(0.2, contrast))
        sub_img = img_gray.resize((width * 2, h_chars * 4), Image.Resampling.LANCZOS)
        sub_img = sub_img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140)).convert("1")

        lines = []
        for r in range(h_chars):
            row = []
            for c in range(width):
                code = 0x2800
                for dx, dy, mask in BRAILLE_DOTS:
                    if sub_img.getpixel((c * 2 + dx, r * 4 + dy)) > 0:
                        code |= mask
                row.append(chr(code))
            lines.append("".join(row))
        return "\n".join(lines)

    else:
        # Standard ASCII keyboard or block ramp
        img_gray = image.convert("L")
        img_gray = ImageOps.autocontrast(img_gray, cutoff=1)
        if contrast != 1.0:
            img_gray = ImageEnhance.Contrast(img_gray).enhance(max(0.2, contrast))
        img_resized = img_gray.resize((width, h_chars), Image.Resampling.LANCZOS)
        img_resized = img_resized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140))

        try:
            pixels = list(img_resized.get_flattened_data())
        except AttributeError:
            pixels = list(img_resized.getdata())

        ramp = BLOCK_RAMP if style_clean == "blocks" else KEYBOARD_RAMP
        num_chars = len(ramp)

        lines = []
        for r in range(h_chars):
            row = []
            for c in range(width):
                val = pixels[r * width + c]
                idx = min(num_chars - 1, max(0, int(val * num_chars / 256)))
                row.append(ramp[idx])
            lines.append("".join(row))
        return "\n".join(lines)