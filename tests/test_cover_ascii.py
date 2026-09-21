import unittest
from io import BytesIO
from PIL import Image
from climusic.functions.coverToAscii import cover_to_ascii


class TestCoverToAscii(unittest.TestCase):
    def test_default_fallback_on_invalid_bytes(self):
        ascii_art = cover_to_ascii(b"invalid data", width=36)
        lines = ascii_art.split("\n")
        self.assertGreater(len(lines), 0)
        self.assertEqual(len(lines[0]), 36)

    def test_custom_dimensions(self):
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        bio = BytesIO()
        img.save(bio, format="PNG")
        art = cover_to_ascii(bio.getvalue(), width=30)
        lines = art.split("\n")
        self.assertEqual(len(lines[0]), 30)
        # 30 * 1.0 * 0.5 = 15
        self.assertEqual(len(lines), 15)

    def test_ascii_style(self):
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        bio = BytesIO()
        img.save(bio, format="PNG")
        art = cover_to_ascii(bio.getvalue(), width=20, style="ascii")
        lines = art.split("\n")
        self.assertEqual(len(lines[0]), 20)
        self.assertTrue(all(ch in " .:-=+*#%@" for line in lines for ch in line))

    def test_blocks_style(self):
        img = Image.new("RGB", (100, 100), color=(0, 0, 0))
        bio = BytesIO()
        img.save(bio, format="PNG")
        art = cover_to_ascii(bio.getvalue(), width=20, style="blocks")
        lines = art.split("\n")
        self.assertEqual(len(lines[0]), 20)
        self.assertTrue(all(ch in "  ░░▒▒▓▓██" for line in lines for ch in line))

    def test_rgba_transparency_handling(self):
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        bio = BytesIO()
        img.save(bio, format="PNG")
        art = cover_to_ascii(bio.getvalue(), width=24)
        lines = art.split("\n")
        self.assertEqual(len(lines[0]), 24)


    def test_default_width_is_64(self):
        art = cover_to_ascii(b"invalid data")
        lines = art.split("\n")
        self.assertEqual(len(lines[0]), 64)

    def test_now_playing_cover_width(self):
        from climusic.components.nowPlaying import NowPlaying
        np = NowPlaying()
        self.assertEqual(np._get_target_width(), 64)
        np.set_cover_width(72)
        self.assertEqual(np._get_target_width(), 72)
        np.set_cover_width("auto")
        self.assertEqual(np.cover_width, "auto")


if __name__ == "__main__":
    unittest.main()
