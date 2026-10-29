"""Opt-in edge-extension for illustrated print PDFs; never scale live content."""
from io import BytesIO
from pathlib import Path
import subprocess
import tempfile

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject, RectangleObject, DecodedStreamObject, NumberObject, ArrayObject
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def _font_key(font):
    ref = getattr(font, 'indirect_reference', None)
    return (ref.idnum, ref.generation) if ref else id(font)


def _embedded(font):
    font = font.get_object()
    if font.get('/Subtype') == '/Type3':
        return True
    children = font.get('/DescendantFonts')
    if children:
        return all(_embedded(f) for f in children)
    descriptor = font.get('/FontDescriptor')
    return bool(descriptor and any(descriptor.get_object().get(k)
                                   for k in ('/FontFile', '/FontFile2', '/FontFile3')))


def remove_unused_unembedded_fonts(reader):
    """Remove only fonts never used to show text, including shared form resources."""
    scopes, used, visited = [], set(), set()

    def scan(owner, resources, contents, initial=None, page=False):
        resources = resources.get_object()
        key = (id(owner), id(resources), initial)
        if key in visited:
            return
        visited.add(key)
        stream = ContentStream(contents, reader)
        fonts = resources.get('/Font', {})
        fonts = fonts.get_object() if hasattr(fonts, 'get_object') else fonts
        refs = {name: ref.get_object() for name, ref in fonts.items()}
        current = initial
        stack = []
        scopes.append((owner, resources, stream, refs, page))
        for args, op in stream.operations:
            if op == b'q':
                stack.append(current)
            elif op == b'Q' and stack:
                current = stack.pop()
            elif op == b'Tf':
                font = refs.get(args[0])
                current = _font_key(font) if font is not None else None
            elif op in (b'Tj', b'TJ', b"'", b'"'):
                values = args[0] if op == b'TJ' else [args[-1]]
                if any(isinstance(v, (str, bytes)) and len(v) for v in values) and current is not None:
                    used.add(current)
            elif op == b'Do':
                objects = resources.get('/XObject', {})
                objects = objects.get_object() if hasattr(objects, 'get_object') else objects
                form = objects.get(args[0])
                if form is not None:
                    form = form.get_object()
                    if form.get('/Subtype') == '/Form':
                        scan(form, form.get('/Resources', resources), form, current)

    for page in reader.pages:
        scan(page, page['/Resources'], page.get_contents(), page=True)
    removable = {_font_key(f) for _, _, _, fonts, _ in scopes
                 for f in fonts.values() if not _embedded(f) and _font_key(f) not in used}
    for owner, resources, stream, refs, page in scopes:
        names = {n for n, f in refs.items() if _font_key(f) in removable}
        if not names:
            continue
        stream.operations = [(args, op) for args, op in stream.operations
                             if not (op == b'Tf' and args[0] in names)]
        if page:
            owner[NameObject('/Contents')] = stream
        else:
            owner.set_data(stream.get_data())
        fonts = resources['/Font']
        for name in names:
            fonts.pop(name, None)
    return len(removable)


def extend_edges(source: Path, destination: Path, trim_points, *, cleanup=False):
    """Add 9pt outside/top/bottom bleed, retain original trim at 1:1 scale.

    First selected page is recto. Even output pages have bleed at the left.
    Raster strips duplicate only edge colours outside the trim; the interior
    remains the original PDF artwork/text with its fonts and vector graphics.
    """
    reader = PdfReader(source)
    width, height = trim_points
    bleed = 9.0
    for page in reader.pages:
        if page.rotation % 360 or list(map(float, page.mediabox)) != [0, 0, width, height]:
            raise ValueError('Edge extension requires unrotated, trim-sized pages at origin; no scaling is performed')
    removed_fonts = remove_unused_unembedded_fonts(reader) if cleanup else 0
    removed_links = 0
    writer = PdfWriter()
    with tempfile.TemporaryDirectory(prefix='publisher-bleed-') as tmp:
        tmp = Path(tmp)
        for n, page in enumerate(reader.pages, 1):
            subprocess.run(['pdftoppm', '-f', str(n), '-l', str(n), '-singlefile',
                            '-r', '288', '-png', str(source), str(tmp / 'page')],
                           check=True, capture_output=True)
            with Image.open(tmp / 'page.png') as source_image:
                image = source_image.convert('RGB')
            iw, ih = image.size
            left = n % 2 == 0
            x = bleed if left else 0
            data = BytesIO()
            c = canvas.Canvas(data, pagesize=(width + bleed, height + 2 * bleed), pageCompression=1)
            # Single-pixel strips stretch solely into the new exterior area.
            top = image.crop((0, 0, iw, 1))
            bottom = image.crop((0, ih-1, iw, ih))
            side = image.crop((0, 0, 1, ih) if left else (iw-1, 0, iw, ih))
            c.drawImage(ImageReader(top), x, height + bleed, width=width, height=bleed)
            c.drawImage(ImageReader(bottom), x, 0, width=width, height=bleed)
            side_x = 0 if left else width
            c.drawImage(ImageReader(side), side_x, bleed, width=bleed, height=height)
            for y, rgb in [(0, image.getpixel((0 if left else iw-1, ih-1))),
                           (height + bleed, image.getpixel((0 if left else iw-1, 0)))]:
                c.setFillColorRGB(*(v / 255 for v in rgb))
                c.rect(side_x, y, bleed, bleed, stroke=0, fill=1)
            c.showPage()
            c.save()
            data.seek(0)
            edge_reader = PdfReader(data)
            base = edge_reader.pages[0]
            # ReportLab's image-only page registers an unused default font.
            edge_stream = ContentStream(base.get_contents(), edge_reader)
            assert not any(op in (b'Tj', b'TJ', b"'", b'"') for _, op in edge_stream.operations)
            edge_stream.operations = [(a, op) for a, op in edge_stream.operations
                                      if op not in (b'BT', b'ET', b'Tf', b'TL')]
            base[NameObject('/Contents')] = edge_stream
            base['/Resources'].pop('/Font', None)
            if cleanup:
                annotations = page.get('/Annots', [])
                # Links have no visible appearance in these print inputs. Keep
                # other annotation types so no visible content is silently lost.
                kept = [a for a in annotations
                        if a.get_object().get('/Subtype') != '/Link'
                        or a.get_object().get('/AP')
                        or int(a.get_object().get('/F', 0)) & 4]
                removed_links += len(annotations) - len(kept)
                if annotations:
                    page[NameObject('/Annots')] = ArrayObject(kept)
            # Wrap native bytes in a Form instead of rewriting every numeric
            # drawing operand during merge. Its BBox clips at the original
            # trim; only an integer translation moves it onto the new canvas.
            if page.get('/Annots'):
                raise ValueError('Annotations require print cleanup for nonprinting links, or a separately flattened print source for visible appearances')
            base = writer.add_page(base)
            form = DecodedStreamObject()
            form.set_data(page.get_contents().get_data())
            form[NameObject('/Type')] = NameObject('/XObject')
            form[NameObject('/Subtype')] = NameObject('/Form')
            form[NameObject('/FormType')] = NumberObject(1)
            form[NameObject('/BBox')] = RectangleObject((0, 0, width, height))
            form[NameObject('/Resources')] = page['/Resources'].clone(writer)
            if page.get('/Group'):
                form[NameObject('/Group')] = page['/Group'].clone(writer)
            base['/Resources']['/XObject'][NameObject('/PreservedTrim')] = writer._add_object(form)
            contents = DecodedStreamObject()
            contents.set_data(base.get_contents().get_data() + f'\nq 1 0 0 1 {x:g} {bleed:g} cm /PreservedTrim Do Q\n'.encode())
            base[NameObject('/Contents')] = writer._add_object(contents)
            base.trimbox = RectangleObject((x, bleed, x + width, bleed + height))
            base.bleedbox = RectangleObject((0, 0, width + bleed, height + 2 * bleed))
            base.cropbox = RectangleObject(base.bleedbox)
        writer.add_metadata({'/Title': 'Layout-preserving print PDF',
                             '/Producer': 'KDP Formatter general preserve / edge extension'})
        with destination.open('wb') as output:
            writer.write(output)
    return {'strategy': 'extend_edges', 'trim_scale': 1, 'bleed_points': bleed,
            'first_output_page': 'recto', 'edge_sampling_dpi': 288,
            'unused_unembedded_fonts_removed': removed_fonts,
            'nonprinting_links_removed': removed_links,
            'limitations': ['Edge continuation is reconstructed from source edge pixels',
                            'Source image resolution is unchanged',
                            'KDP preview and physical proof still required']}
