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
        self.assertTrue(all(ch in "  .,-~:;=!*#$@" for line in lines for ch in line))

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

    def test_pixel_style(self):
        img = Image.new("RGB", (40, 40), color=(255, 0, 128))
        bio = BytesIO()
        img.save(bio, format="PNG")
        art = cover_to_ascii(bio.getvalue(), width=20, style="pixel", contrast=1.0)
        lines = art.split("\n")
        self.assertEqual(len(lines), 10)
        self.assertIn("▀", lines[0])
        self.assertIn("#ff0080", lines[0])

    def test_braille_style(self):
        img = Image.new("RGB", (40, 40), color=(200, 200, 200))
        bio = BytesIO()
        img.save(bio, format="PNG")
        art = cover_to_ascii(bio.getvalue(), width=20, style="braille")
        lines = art.split("\n")
        self.assertEqual(len(lines), 10)
        self.assertEqual(len(lines[0]), 20)
        self.assertTrue(any(ord(ch) >= 0x2800 for ch in lines[0]))

    def test_quadrant_style(self):
        img = Image.new("RGB", (40, 40), color=(180, 180, 180))
        bio = BytesIO()
        img.save(bio, format="PNG")
        art = cover_to_ascii(bio.getvalue(), width=20, style="quadrant")
        lines = art.split("\n")
        self.assertEqual(len(lines), 10)
        self.assertEqual(len(lines[0]), 20)

    def test_now_playing_cover_width(self):
        from climusic.components.nowPlaying import NowPlaying
        np = NowPlaying()
        np.cover_width = "auto"
        self.assertEqual(np._get_target_width(), 64)
        np.set_cover_width(72)
        self.assertEqual(np._get_target_width(), 72)
        np.set_cover_width("auto")
        self.assertEqual(np.cover_width, "auto")

    def test_now_playing_adjust_width(self):
        from climusic.components.nowPlaying import NowPlaying
        np = NowPlaying()
        np.set_cover_width(60)
        new_w = np.adjust_cover_width(4)
        self.assertEqual(new_w, 64)
        new_w = np.adjust_cover_width(-8)
        self.assertEqual(new_w, 56)

    def test_now_playing_set_style_and_contrast(self):
        from climusic.components.nowPlaying import NowPlaying
        np = NowPlaying()
        np.set_cover_style("pixel")
        self.assertEqual(np.cover_style, "pixel")
        np.set_cover_contrast(1.75)
        self.assertEqual(np.cover_contrast, 1.75)


class TestCoverCommands(unittest.TestCase):
    def setUp(self):
        from climusic.components.actions.commands import CommandActions
        from climusic.components.nowPlaying import NowPlaying
        self.cmd_actions = CommandActions()
        self.np = NowPlaying()
        self.messages = []
        self.cmd_actions.query_one = lambda widget_type: self.np
        self.cmd_actions.print_to_terminal = lambda msg: self.messages.append(msg)

    def test_cover_commands_width(self):
        self.cmd_actions._handle_cover_size("cover 76")
        self.assertEqual(self.np.cover_width, 76)
        self.cmd_actions._handle_cover_size("cover +")
        self.assertEqual(self.np.cover_width, 80)
        self.cmd_actions._handle_cover_size("cover -")
        self.assertEqual(self.np.cover_width, 76)
        self.cmd_actions._handle_cover_size("cover auto")
        self.assertEqual(self.np.cover_width, "auto")

    def test_cover_commands_styles(self):
        self.cmd_actions._handle_cover_size("cover pixel")
        self.assertEqual(self.np.cover_style, "pixel")
        self.cmd_actions._handle_cover_size("cover braille")
        self.assertEqual(self.np.cover_style, "braille")
        self.cmd_actions._handle_cover_size("cover quadrant")
        self.assertEqual(self.np.cover_style, "quadrant")
        self.cmd_actions._handle_cover_size("cover blocks")
        self.assertEqual(self.np.cover_style, "blocks")
        self.cmd_actions._handle_cover_size("cover ascii")
        self.assertEqual(self.np.cover_style, "ascii")

    def test_cover_commands_contrast(self):
        self.cmd_actions._handle_cover_size("cover contrast 1.8")
        self.assertEqual(self.np.cover_contrast, 1.8)

    def test_cover_status_display(self):
        self.cmd_actions._handle_cover_size("cover")
        self.assertTrue(any("Cover Settings & Status" in m for m in self.messages))


if __name__ == "__main__":
    unittest.main()
