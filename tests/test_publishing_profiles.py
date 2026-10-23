import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from publisher.build import PublishingConfig, build


class PublishingProfilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'illustrated.pdf'
        c = canvas.Canvas(str(self.source), pagesize=(432, 648))
        for n in range(4):
            c.setFillColorRGB(n/4, .2, .8)
            c.rect(0, 0, 432, 648, fill=1)
            c.drawString(40, 300, f'Illustrated page {n+1}')
            c.showPage()
        c.save()

    def tearDown(self):
        self.temp.cleanup()

    def test_default_pdf_preserves_selected_content_and_geometry_without_reflow(self):
        with patch('poc.converters.convert', side_effect=AssertionError('must never reflow PDF')):
            result = build(self.source, self.root/'draft', PublishingConfig(first_page=2, last_page=3))
        before, after = PdfReader(self.source), PdfReader(self.root/'draft/output.pdf')
        self.assertEqual(len(after.pages), 2)
        for original, restored in zip(before.pages[1:3], after.pages):
            self.assertEqual(original.get_contents().get_data(), restored.get_contents().get_data())
            self.assertEqual(original.mediabox, restored.mediabox)
            self.assertEqual(original.extract_text(), restored.extract_text())
        self.assertFalse(result['validation']['kdp_accepted'])
        fonts = next(c for c in result['validation']['checks'] if c['check_name'] == 'font_resources')
        self.assertEqual(fonts['status'], 'warning')
        self.assertEqual(result['resolved_mode'], 'preserve')

    def test_missing_bleed_is_reported_without_resizing(self):
        result = build(self.source, self.root/'bleed', PublishingConfig(bleed=True))
        self.assertEqual(result['validation']['overall_status'], 'fail')
        self.assertEqual(float(PdfReader(self.root/'bleed/output.pdf').pages[0].mediabox.width), 432)

    def test_unsafe_combinations_and_ranges_rejected(self):
        cases = [PublishingConfig(profile='directorhelp'), PublishingConfig(output_format='both'),
                 PublishingConfig(first_page=0), PublishingConfig(last_page=9), PublishingConfig(mode='invalid')]
        for i, config in enumerate(cases):
            with self.subTest(config=config), self.assertRaises(ValueError):
                build(self.source, self.root/f'bad-{i}', config)
        with self.assertRaises(ValueError):
            PublishingConfig(mode='reflow', last_page=2).resolved_mode(Path('book.md'))

    def test_existing_outputs_are_not_overwritten(self):
        destination = self.root/'existing'
        build(self.source, destination, PublishingConfig())
        original = (destination/'output.pdf').read_bytes()
        with self.assertRaises(ValueError):
            build(self.source, destination, PublishingConfig())
        self.assertEqual((destination/'output.pdf').read_bytes(), original)

    def test_directorhelp_route_matches_existing_renderer(self):
        from directorhelp_formatter.adapter import DirectorHelpMarkdownAdapter
        from directorhelp_formatter.print_renderer import PrintRenderer
        source = self.root/'guide.md'
        source.write_text("# A Test Guide\n\n# PART ONE\n# Decisions\n\n## 1. First\n\nKeep this guide style.\n")
        expected = self.root/'expected.pdf'
        PrintRenderer().render(DirectorHelpMarkdownAdapter().convert(source), expected)
        build(source, self.root/'guide', PublishingConfig(profile='directorhelp'))
        actual = PdfReader(self.root/'guide/output.pdf')
        self.assertEqual([p.extract_text() for p in actual.pages], [p.extract_text() for p in PdfReader(expected).pages])
        self.assertIn("directorhelp", actual.pages[0].extract_text())

    def test_general_text_does_not_inherit_directorhelp_brand(self):
        source = self.root/'novel.txt'
        source.write_text('A General Book\n\nChapter 1\n\nA long journey begins with this paragraph.\n')
        build(source, self.root/'general', PublishingConfig())
        text = '\n'.join(p.extract_text() for p in PdfReader(self.root/'general/output.pdf').pages)
        self.assertNotIn('DirectorHelp', text)
        self.assertNotIn("A Director's Guide", text)

    def test_upload_profile_and_cached_validation(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with patch('app.main.OUTPUT_DIR', self.root/'web'):
            (self.root/'web').mkdir()
            client = TestClient(app)
            reply = client.post('/convert', files={'file': ('book.pdf', self.source.read_bytes(), 'application/pdf')},
                                data={'publishing_profile': 'general', 'first_page': '2', 'last_page': '3'})
            self.assertEqual(reply.status_code, 200, reply.text)
            session = reply.json()['session_id']
            validation = client.get(f'/validate/{session}')
            self.assertEqual(validation.status_code, 200)
            self.assertFalse(validation.json()['kdp_accepted'])
            self.assertEqual(client.get(f'/download/{session}/report').status_code, 200)
            preview = client.get(f'/preview/{session}')
            self.assertEqual(preview.status_code, 200, preview.text)
            self.assertIn('Preserved from source', preview.text)
            self.assertEqual(client.get('/').status_code, 200)
            invalid = client.post('/convert', files={'file': ('book.pdf', self.source.read_bytes(), 'application/pdf')},
                                  data={'publishing_profile': 'directorhelp'})
            self.assertEqual(invalid.status_code, 400)


if __name__ == '__main__':
    unittest.main()
