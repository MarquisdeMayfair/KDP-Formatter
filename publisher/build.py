from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter


@dataclass(frozen=True)
class PublishingConfig:
    profile: str = "general"
    mode: str = "auto"
    trim: str = "6x9"
    bleed: bool = False
    first_page: int = 1
    last_page: int | None = None
    output_format: str = "pdf"
    bleed_strategy: str = "validate"
    print_cleanup: bool = False

    def resolved_mode(self, source: Path) -> str:
        if self.profile not in {"general", "directorhelp"}:
            raise ValueError("Profile must be general or directorhelp")
        if self.mode not in {"auto", "preserve", "reflow"}:
            raise ValueError("Mode must be auto, preserve or reflow")
        if self.output_format not in {"pdf", "epub", "both"}:
            raise ValueError("Output format must be pdf, epub or both")
        if self.profile == "directorhelp":
            if source.suffix.lower() != ".md" or self.mode == "preserve":
                raise ValueError("DirectorHelp requires canonical Markdown in reflow mode")
            if self.bleed:
                raise ValueError("DirectorHelp's existing renderer supports no-bleed interiors only")
            mode = "reflow"
        else:
            mode = ("preserve" if source.suffix.lower() == ".pdf" else "reflow") if self.mode == "auto" else self.mode
        if mode == "preserve" and (source.suffix.lower() != ".pdf" or self.output_format != "pdf"):
            raise ValueError("Preserve mode requires a PDF source and PDF-only output; EPUB needs a separate conversion")
        if mode == "reflow" and (self.first_page != 1 or self.last_page is not None):
            raise ValueError("Page selection is only available in PDF preserve mode")
        if mode == "reflow" and self.bleed:
            raise ValueError("Reflow renderers do not generate full-bleed artwork")
        if self.bleed_strategy not in {"validate", "extend_edges"}:
            raise ValueError("Bleed strategy must be validate or extend_edges")
        if self.bleed_strategy == "extend_edges" and not (mode == "preserve" and self.bleed):
            raise ValueError("Edge extension requires PDF preserve mode with bleed enabled")
        if self.print_cleanup and self.bleed_strategy != "extend_edges":
            raise ValueError("Print cleanup requires explicit edge extension")
        dimensions(self.trim, self.bleed)
        return mode


def dimensions(trim: str, bleed: bool) -> tuple[float, float]:
    sizes = {"5x8": (5, 8), "5.5x8.5": (5.5, 8.5), "6x9": (6, 9), "7x10": (7, 10), "8.5x11": (8.5, 11)}
    if trim not in sizes:
        raise ValueError(f"Unsupported trim: {trim}")
    w, h = sizes[trim]
    return ((w + .125) * 72, (h + .25) * 72) if bleed else (w * 72, h * 72)


def inspect_pdf(path: Path, config: PublishingConfig) -> dict:
    """Limited draft preflight. Never certifies acceptance or alters artwork."""
    reader = PdfReader(path)
    expected = dimensions(config.trim, config.bleed)
    checks = []

    def check(name, status, message):
        checks.append({"check_name": name, "status": status, "message": message})

    wrong = [i for i, page in enumerate(reader.pages, 1) if any(abs(float(a) - b) > .5 for a, b in zip((page.mediabox.width, page.mediabox.height), expected))]
    check("page_dimensions", "fail" if wrong else "pass", f"Expected {expected[0]/72:g} x {expected[1]/72:g} inches; mismatched pages: {wrong}")
    rotated = [i for i, p in enumerate(reader.pages, 1) if p.rotation % 360]
    check("rotation", "warning" if rotated else "pass", f"Pages with rotation: {rotated}")
    count = len(reader.pages)
    check("page_count", "warning" if count < 24 or count % 2 else "pass", f"{count} pages; ink/paper/trim-specific limits still require checking")
    annotations = [i for i, p in enumerate(reader.pages, 1) if p.get("/Annots")]
    check("annotations", "warning" if annotations else "pass", f"Pages with annotations (preserved): {annotations}")
    check("file_size", "fail" if path.stat().st_size > 650_000_000 else "pass", f"{path.stat().st_size} bytes")
    diagnostics = {}
    for name, cmd in {"fonts": ["pdffonts", str(path)], "images": ["pdfimages", "-list", str(path)]}.items():
        try:
            run = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            diagnostics[name] = run.stdout if run.returncode == 0 else run.stderr
            if run.returncode:
                check(name, "warning", f"{cmd[0]} failed; inspection incomplete")
            elif name == "fonts":
                rows = run.stdout.splitlines()[2:]
                # Columns after font name/type/encoding: emb sub uni object ID.
                unembedded = [row for row in rows if len(row.split()) >= 5 and row.split()[-5] == "no"]
                check("font_resources", "warning" if unembedded else "pass", f"{len(unembedded)} unembedded font resources; visible usage must be verified")
            else:
                rows = [r.split() for r in run.stdout.splitlines()[2:]]
                low = [r for r in rows if len(r) >= 14 and r[2] == "image"
                       and min(float(r[12]), float(r[13])) < 300
                       and not (config.bleed_strategy == "extend_edges" and min(int(r[3]), int(r[4])) == 1)]
                check("image_resolution", "warning" if low else "pass", f"{len(low)} image placements below 300 PPI")
                if config.bleed_strategy == "extend_edges":
                    check("bleed_edge_images", "pass", "Single-pixel edge continuation strips excluded from artwork PPI count; inspect trim transitions")
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            check(name, "warning", f"Inspection unavailable: {type(exc).__name__}")
    check("manual_review", "warning", "Draft only: inspect safe areas, bleed artwork, transparency, pagination, colour and editorial issues; KDP Previewer and physical proof remain outstanding")
    return {"pdf_path": str(path), "overall_status": "fail" if any(c["status"] == "fail" for c in checks) else "warning", "checks": checks, "diagnostics": diagnostics, "kdp_accepted": False}


def build(source: str | Path, output_dir: str | Path, config: PublishingConfig) -> dict:
    source, output = Path(source).resolve(), Path(output_dir).resolve()
    mode = config.resolved_mode(source)
    if source.parent == output or source == output / "output.pdf":
        # Uploaded files may live beside outputs, but never overwrite the input.
        if source.name in {"output.pdf", "output.epub", "validation.json", "build.json"}:
            raise ValueError("Input would be overwritten by an output")
    output.mkdir(parents=True, exist_ok=True)
    if any((output / name).exists() for name in ("output.pdf", "output.epub", "validation.json", "build.json")):
        raise ValueError("Output files already exist; choose a new output directory")
    report = {"config": asdict(config), "resolved_mode": mode, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "draft_only": True}
    if mode == "preserve":
        reader = PdfReader(source)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF: supply an unlocked source")
        last = config.last_page if config.last_page is not None else len(reader.pages)
        if not 1 <= config.first_page <= last <= len(reader.pages):
            raise ValueError("Invalid inclusive source page range")
        writer = PdfWriter()
        for page in reader.pages[config.first_page - 1:last]:
            writer.add_page(page)
        if config.bleed_strategy == "extend_edges":
            from publisher.bleed import extend_edges
            with tempfile.TemporaryDirectory(prefix="publisher-selected-") as temp:
                selected = Path(temp) / "selected.pdf"
                with selected.open("wb") as stream:
                    writer.write(stream)
                report["bleed_preparation"] = extend_edges(selected, output / "output.pdf",
                    dimensions(config.trim, False), cleanup=config.print_cleanup)
        else:
            with (output / "output.pdf").open("wb") as stream:
                writer.write(stream)
        report["source_pages"] = [config.first_page, last]
    elif config.profile == "directorhelp":
        from directorhelp_formatter.adapter import DirectorHelpMarkdownAdapter
        from directorhelp_formatter.print_renderer import PrintConfig, PrintRenderer
        from directorhelp_formatter.epub_renderer import EPUBRenderer
        book = DirectorHelpMarkdownAdapter().convert(source)
        if config.output_format in {"pdf", "both"}:
            PrintRenderer(PrintConfig(trim_size=config.trim)).render(book, output / "output.pdf")
        if config.output_format in {"epub", "both"}:
            EPUBRenderer().render(book, output / "output.epub")
    else:
        from poc.converters import convert
        from poc.renderer import render_document_to_pdf, ReportLabPDFRenderer
        if config.trim not in ReportLabPDFRenderer.PAGE_SIZES:
            raise ValueError(f"General reflow does not support trim {config.trim}")
        book = convert(str(source), use_ai=False)
        if config.output_format in {"pdf", "both"}:
            render_document_to_pdf(book, str(output / "output.pdf"), page_size=config.trim)
        if config.output_format in {"epub", "both"}:
            from poc.epub_generator import generate_epub
            generate_epub(book, str(output / "output.epub"))
    if (output / "output.pdf").exists():
        validation = inspect_pdf(output / "output.pdf", config)
        (output / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
        report["validation"] = validation
    (output / "build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
