from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pdfplumber
from bs4 import BeautifulSoup
from lxml import etree
from pypdf import PdfReader

from .model import Book
from .print_renderer import PrintConfig


BANNED_OUTPUT_MARKERS = (
    "Build notes (remove before publication)",
    "[ADVERTISEMENT",
    "[TMD:",
    "Commercial disclosure. DirectorHelp",
)


class ValidationFailure(RuntimeError):
    pass


@dataclass
class Check:
    name: str
    status: str
    message: str
    details: dict[str, Any] | None = None


def _require_command(command: str) -> str:
    path = shutil.which(command)
    if not path:
        raise ValidationFailure(f"Required validation command is unavailable: {command}")
    return path


def _run(command: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    return result


def validate_pdf(pdf_path: str | Path, book: Book, config: PrintConfig) -> dict[str, Any]:
    path = Path(pdf_path)
    checks: list[Check] = []
    if not path.exists() or path.stat().st_size == 0:
        raise ValidationFailure(f"PDF was not generated: {path}")

    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    page_count_ok = 24 <= page_count <= 828 and page_count % 2 == 0
    checks.append(Check("page_count", "pass" if page_count_ok else "fail", f"{page_count} pages (must be 24-828 and even)", {"minimum": 24, "maximum": 828, "must_be_even": True}))

    expected_width, expected_height = (value * 72 for value in config.dimensions)
    wrong_pages: list[int] = []
    blank_runs: list[int] = []
    current_blank_run = 0
    extracted_text: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if abs(width - expected_width) > 0.5 or abs(height - expected_height) > 0.5:
            wrong_pages.append(index)
        text = page.extract_text() or ""
        extracted_text.append(text)
        if text.strip():
            if current_blank_run:
                blank_runs.append(current_blank_run)
            current_blank_run = 0
        else:
            current_blank_run += 1
    if current_blank_run:
        blank_runs.append(current_blank_run)
    checks.append(Check("page_dimensions", "pass" if not wrong_pages else "fail", f"All pages are {config.trim_size}" if not wrong_pages else f"Wrong page size on pages {wrong_pages}", {"wrong_pages": wrong_pages}))
    checks.append(Check("blank_pages", "pass" if max(blank_runs or [0]) <= 2 else "fail", f"Longest intentional blank run: {max(blank_runs or [0])}"))

    metadata = reader.metadata or {}
    metadata_ok = metadata.get("/Title") == book.metadata.title and metadata.get("/Author") == book.metadata.author
    checks.append(Check("metadata", "pass" if metadata_ok else "fail", f"Title={metadata.get('/Title')!r}; Author={metadata.get('/Author')!r}"))

    pdffonts = _run([_require_command("pdffonts"), str(path)])
    if pdffonts.returncode != 0:
        checks.append(Check("embedded_fonts", "error", pdffonts.stderr.strip() or "pdffonts failed"))
    else:
        font_lines = [line for line in pdffonts.stdout.splitlines()[2:] if line.strip()]
        embedded_pattern = re.compile(r"\s+yes\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$", re.IGNORECASE)
        unembedded = [line.split()[0] for line in font_lines if not embedded_pattern.search(line)]
        checks.append(Check("embedded_fonts", "pass" if font_lines and not unembedded else "fail", f"{len(font_lines) - len(unembedded)}/{len(font_lines)} fonts embedded", {"unembedded": unembedded}))

    pdfinfo = _run([_require_command("pdfinfo"), str(path)])
    checks.append(Check("pdfinfo", "pass" if pdfinfo.returncode == 0 else "error", "pdfinfo parsed the file" if pdfinfo.returncode == 0 else pdfinfo.stderr.strip()))

    images = _run([_require_command("pdfimages"), "-list", str(path)])
    low_resolution: list[dict[str, Any]] = []
    image_count = 0
    if images.returncode == 0:
        for line in images.stdout.splitlines():
            row = line.split()
            if len(row) < 16 or not row[0].isdigit():
                continue
            image_count += 1
            try:
                x_ppi, y_ppi = int(row[-4]), int(row[-3])
            except ValueError:
                continue
            if min(x_ppi, y_ppi) < 300:
                low_resolution.append({"page": int(row[0]), "x_ppi": x_ppi, "y_ppi": y_ppi})
        checks.append(Check("image_resolution", "pass" if not low_resolution else "fail", f"{image_count} images checked; {len(low_resolution)} below 300 DPI", {"low_resolution": low_resolution}))
    else:
        checks.append(Check("image_resolution", "error", images.stderr.strip() or "pdfimages failed"))

    unsafe_words: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            for word in page.extract_words():
                if word["x0"] < 17.5 or word["x1"] > page.width - 17.5 or word["top"] < 17.5 or word["bottom"] > page.height - 17.5:
                    unsafe_words.append({"page": page_index, "text": word["text"], "x0": round(word["x0"], 1), "x1": round(word["x1"], 1), "top": round(word["top"], 1), "bottom": round(word["bottom"], 1)})
                    if len(unsafe_words) >= 20:
                        break
            if len(unsafe_words) >= 20:
                break
    checks.append(Check("safe_area", "pass" if not unsafe_words else "fail", "All extracted text remains at least 0.24in from trim" if not unsafe_words else "Text approaches the trim edge", {"examples": unsafe_words}))

    full_text = "\n".join(extracted_text)
    banned = [marker for marker in BANNED_OUTPUT_MARKERS if marker.lower() in full_text.lower()]
    checks.append(Check("publication_cleanup", "pass" if not banned else "fail", "No build notes, ad directives or web disclosures remain" if not banned else f"Found banned markers: {banned}"))
    expected_chapters = [f"Chapter {chapter.number}" for chapter in book.chapters]
    missing_chapters = [chapter for chapter in expected_chapters if chapter.lower() not in full_text.lower()]
    checks.append(Check("chapter_integrity", "pass" if not missing_chapters else "fail", f"All {len(expected_chapters)} deterministic chapters are present", {"missing": missing_chapters}))

    return _finalise("pdf", str(path), checks, {"page_count": page_count, "word_count": len(full_text.split())})


def validate_epub(epub_path: str | Path, book: Book) -> dict[str, Any]:
    path = Path(epub_path)
    checks: list[Check] = []
    if not path.exists() or path.stat().st_size == 0:
        raise ValidationFailure(f"EPUB was not generated: {path}")

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        mimetype_ok = names and names[0] == "mimetype" and archive.read("mimetype") == b"application/epub+zip" and archive.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        checks.append(Check("epub_container", "pass" if mimetype_ok else "fail", "Mimetype is first and uncompressed" if mimetype_ok else "Invalid EPUB mimetype packaging"))
        required = {"META-INF/container.xml", "EPUB/package.opf", "EPUB/nav.xhtml", "EPUB/toc.ncx"}
        missing = sorted(required - set(names))
        checks.append(Check("required_files", "pass" if not missing else "fail", "Required EPUB 3 files are present", {"missing": missing}))

        xml_errors: list[str] = []
        text_chunks: list[str] = []
        for name in names:
            if not name.endswith((".xhtml", ".opf", ".ncx", ".xml")):
                continue
            try:
                root = etree.fromstring(archive.read(name))
                if name.endswith(".xhtml"):
                    text_chunks.append(" ".join(root.itertext()))
            except Exception as exc:
                xml_errors.append(f"{name}: {exc}")
        checks.append(Check("well_formed_xml", "pass" if not xml_errors else "fail", f"{len([n for n in names if n.endswith(('.xhtml','.opf','.ncx','.xml'))])} XML documents parsed", {"errors": xml_errors}))

        nav_text = archive.read("EPUB/nav.xhtml").decode("utf-8", errors="replace") if "EPUB/nav.xhtml" in names else ""
        missing_nav = [chapter.title for chapter in book.chapters if chapter.title not in nav_text]
        checks.append(Check("navigation", "pass" if not missing_nav else "fail", f"All {len(book.chapters)} chapters are in navigation", {"missing": missing_nav}))

    epubcheck = _run([_require_command("epubcheck"), str(path)], timeout=180)
    epub_output = (epubcheck.stdout + "\n" + epubcheck.stderr).strip()
    checks.append(Check("epubcheck", "pass" if epubcheck.returncode == 0 else "fail", "EPUBCheck passed with no errors" if epubcheck.returncode == 0 else "EPUBCheck failed", {"output": epub_output[-12000:]}))

    full_text = "\n".join(text_chunks)
    banned = [marker for marker in BANNED_OUTPUT_MARKERS if marker.lower() in full_text.lower()]
    checks.append(Check("publication_cleanup", "pass" if not banned else "fail", "No build notes, ad directives or web disclosures remain" if not banned else f"Found banned markers: {banned}"))
    missing_chapters = [chapter.title for chapter in book.chapters if chapter.title not in full_text]
    checks.append(Check("chapter_integrity", "pass" if not missing_chapters else "fail", f"All {len(book.chapters)} chapter titles are present", {"missing": missing_chapters}))

    return _finalise("epub", str(path), checks, {"word_count": len(full_text.split())})


def _finalise(kind: str, path: str, checks: list[Check], summary: dict[str, Any]) -> dict[str, Any]:
    blockers = [check for check in checks if check.status in {"fail", "error"}]
    report = {
        "kind": kind,
        "path": path,
        "status": "fail" if blockers else "pass",
        "summary": summary,
        "checks": [asdict(check) for check in checks],
    }
    if blockers:
        messages = "; ".join(f"{check.name}: {check.message}" for check in blockers)
        raise ValidationFailure(f"{kind.upper()} validation failed: {messages}\n{json.dumps(report, indent=2)}")
    return report
