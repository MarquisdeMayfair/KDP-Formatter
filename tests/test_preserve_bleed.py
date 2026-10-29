import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from publisher.build import PublishingConfig, build


class PreserveBleedTests(unittest.TestCase):
    def test_trim_pixels_and_outside_bleed_on_both_sides(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.pdf'
            c = canvas.Canvas(str(source), pagesize=(432, 648))
            for n in range(2):
                c.setFillColorRGB(.1, .2, .8)
                c.rect(0, 0, 432, 648, fill=1, stroke=0)
                c.setFillColorRGB(1, 0, 0)
                c.rect(0, 0, 20, 648, fill=1, stroke=0)
                c.setFillColorRGB(0, 1, 0)
                c.rect(412, 0, 20, 648, fill=1, stroke=0)
                c.setFillColorRGB(1, 1, 1)
                # Restore a font through q/Q before showing text: cleanup must
                # retain Helvetica and may discard the unused Courier setup.
                c.saveState()
                c.setFont('Courier', 9)
                c.restoreState()
                c.drawString(50, 320, f'Keep this illustration and text {n}')
                c.showPage()
            c.save()
            report = build(source, root / 'out', PublishingConfig(bleed=True, bleed_strategy='extend_edges', print_cleanup=True))
            output = root / 'out/output.pdf'
            pages = PdfReader(output).pages
            self.assertEqual(list(pages[0].mediabox), [0, 0, 441, 666])
            self.assertEqual(list(pages[0].trimbox), [0, 9, 432, 657])
            self.assertEqual(list(pages[1].trimbox), [9, 9, 441, 657])
            for n in (1, 2):
                for path, prefix in ((source, 'before'), (output, 'after')):
                    subprocess.run(['pdftoppm', '-r', '288', '-f', str(n), '-l', str(n), '-singlefile', '-png', str(path), str(root / prefix)], check=True, capture_output=True)
                with Image.open(root / 'before.png') as before, Image.open(root / 'after.png') as after:
                    x = 36 if n == 2 else 0
                    self.assertIsNone(ImageChops.difference(before, after.crop((x, 36, x+1728, 2628))).getbbox())
                    self.assertEqual(after.getpixel((0 if n == 2 else 1763, 100)), (255, 0, 0) if n == 2 else (0, 255, 0))
            self.assertEqual(report['bleed_preparation']['trim_scale'], 1)
            self.assertEqual(next(c['status'] for c in report['validation']['checks'] if c['check_name']=='page_dimensions'), 'pass')

    def test_unsafe_edge_extension_is_rejected(self):
        cases = [PublishingConfig(bleed_strategy='extend_edges'),
                 PublishingConfig(mode='reflow', bleed_strategy='extend_edges'),
                 PublishingConfig(print_cleanup=True)]
        for config in cases:
            with self.subTest(config=config), self.assertRaises(ValueError):
                config.resolved_mode(Path('book.pdf'))


if __name__ == '__main__':
    unittest.main()
