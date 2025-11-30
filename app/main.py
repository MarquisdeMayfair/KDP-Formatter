"""
KDP Formatter - Local Testing Web UI
FastAPI application for manual testing and validation of KDP formatting.
"""

import logging
import os
import tempfile
import shutil
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.background import BackgroundTasks

# Add poc directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from poc.converters import convert
    from poc.renderer import render_document_to_pdf
    from poc.validator import validate_pdf_file, ValidationConfig
    from poc.epub_generator import generate_epub
except ImportError:
    # Fallback for direct script execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'poc'))
    from converters import convert
    from renderer import render_document_to_pdf
    from validator import validate_pdf_file, ValidationConfig
    from epub_generator import generate_epub

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Derive base directory for absolute paths
BASE_DIR = Path(__file__).parent

# Initialize FastAPI app
app = FastAPI(
    title="KDP Formatter",
    version="1.0.0",
    description="Local testing interface for KDP formatting"
)

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Setup templates
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Create output directory for generated files
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# In-memory session storage (use Redis for production)
sessions: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting KDP Formatter Web UI...")

    try:
        # Verify directories exist
        OUTPUT_DIR.mkdir(exist_ok=True)
        logger.info(f"Output directory: {OUTPUT_DIR}")

        # Cleanup old files on startup
        await cleanup_old_files()

        # Check for critical dependencies
        missing_deps = []
        try:
            from pdfminer.high_level import extract_text
        except ImportError:
            missing_deps.append("pdfminer.six")

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            missing_deps.append("beautifulsoup4")

        try:
            from weasyprint import HTML
        except ImportError:
            missing_deps.append("weasyprint")

        if missing_deps:
            logger.warning(f"Missing dependencies: {', '.join(missing_deps)}")
            logger.warning("Some features may not work. Run: pip install -r requirements.txt")

        logger.info("KDP Formatter Web UI started successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down KDP Formatter Web UI...")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main HTML page with file upload form."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/convert")
async def convert_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_format: str = Form("pdf"),
    use_ai: bool = Form(False),
    use_drop_caps: bool = Form(False),
    page_size: str = Form("6x9"),
    margins: str = Form("0.75"),
    use_paragraph_spacing: bool = Form(False),
    disable_indentation: bool = Form(False)
):
    """Handle file upload and conversion."""
    try:
        # Validate file type
        allowed_extensions = {'.txt', '.pdf', '.docx', '.md'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}")

        # Validate file size (50MB limit)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        if file_size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(status_code=400, detail="File too large. Maximum size: 50MB")

        # Validate page_size
        valid_page_sizes = {'6x9', '8.5x11'}
        if page_size not in valid_page_sizes:
            raise HTTPException(status_code=400, detail=f"Invalid page_size '{page_size}'. Must be one of: {', '.join(valid_page_sizes)}")

        # Validate margins
        try:
            margins_val = float(margins)
            if not (0.5 <= margins_val <= 1.5):
                raise HTTPException(status_code=400, detail="Margins must be between 0.5 and 1.5 inches inclusive")
        except ValueError:
            raise HTTPException(status_code=400, detail="Margins must be a valid number")

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create session directory
        session_dir = OUTPUT_DIR / session_id
        session_dir.mkdir(exist_ok=True)

        # Save uploaded file
        input_path = session_dir / f"input{file_ext}"
        with open(input_path, 'wb') as f:
            f.write(content)

        # Convert to IDM
        logger.info(f"Converting {file.filename} to IDM...")
        document = convert(str(input_path), use_ai=use_ai)

        # Save IDM
        idm_path = session_dir / "output_idm.json"
        with open(idm_path, 'w', encoding='utf-8') as f:
            json.dump(document.to_dict(), f, indent=2, ensure_ascii=False)

        result = {
            "session_id": session_id,
            "validation_summary": {"pass": 0, "warning": 0, "fail": 0, "error": 0}
        }

        # Generate PDF if requested
        if output_format in ["pdf", "both"]:
            logger.info("Rendering PDF...")
            pdf_path = session_dir / "output.pdf"
            # Parse configuration values
            page_size_val = page_size
            margins_val = margins_val
            render_document_to_pdf(document, str(pdf_path), use_drop_caps=use_drop_caps, page_size=page_size_val, margins=margins_val,
                                   use_paragraph_spacing=use_paragraph_spacing, disable_indentation=disable_indentation)
            result["pdf_url"] = f"/download/{session_id}/pdf"

            # Validate PDF
            logger.info("Validating PDF...")
            validation_config = ValidationConfig(
                use_drop_caps=use_drop_caps,
                page_size=page_size_val,
                margins=margins_val,
                css_path=None,  # Will use default poc/styles.css
                use_paragraph_spacing=use_paragraph_spacing,
                disable_indentation=disable_indentation
            )
            pdf_report = validate_pdf_file(str(pdf_path), config=validation_config)

            # Count validation results
            for check in pdf_report.checks:
                result["validation_summary"][check.status] = result["validation_summary"].get(check.status, 0) + 1

        # Generate EPUB if requested
        if output_format in ["epub", "both"]:
            logger.info("Generating EPUB...")
            epub_path = session_dir / "output.epub"
            generate_epub(document, str(epub_path), use_paragraph_spacing=use_paragraph_spacing, disable_indentation=disable_indentation)
            result["epub_url"] = f"/download/{session_id}/epub"

        # Store session data
        sessions[session_id] = {
            "filename": file.filename,
            "timestamp": os.path.getctime(session_dir),
            "config": {
                "output_format": output_format,
                "use_ai": use_ai,
                "use_drop_caps": use_drop_caps,
                "page_size": page_size,
                "margins": margins,
                "use_paragraph_spacing": use_paragraph_spacing,
                "disable_indentation": disable_indentation
            },
            "ai_cost": document.metadata.ai_cost if hasattr(document.metadata, 'ai_cost') else 0
        }

        # Schedule cleanup
        background_tasks.add_task(cleanup_old_sessions)

        result["preview_url"] = f"/preview/{session_id}"
        return result

    except ImportError as e:
        error_msg = str(e)
        if "pdfminer.six" in error_msg:
            error_msg = "PDF conversion requires pdfminer.six. Install it with: pip install pdfminer.six"
        elif "beautifulsoup4" in error_msg:
            error_msg = "DOCX/MD conversion requires beautifulsoup4. Install it with: pip install beautifulsoup4"
        elif "weasyprint" in error_msg:
            error_msg = "PDF rendering requires WeasyPrint. Install it with: pip install weasyprint"
        logger.error(f"Missing dependency: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/preview/{session_id}", response_class=HTMLResponse)
async def preview_page(request: Request, session_id: str):
    """Serve PDF preview page."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = sessions[session_id]
    import time
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session_data["timestamp"])) if session_data["timestamp"] else 'Unknown'
    return templates.TemplateResponse("preview.html", {
        "request": request,
        "session_id": session_id,
        "config": session_data["config"],
        "filename": session_data["filename"],
        "timestamp": timestamp,
        "ai_cost": session_data["ai_cost"],
        "config_json": json.dumps(session_data["config"])
    })


@app.get("/download/{session_id}/{file_type}")
async def download_file(session_id: str, file_type: str):
    """Serve generated files for download."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_dir = OUTPUT_DIR / session_id

    if file_type == "pdf":
        file_path = session_dir / "output.pdf"
        media_type = "application/pdf"
        filename = f"{Path(sessions[session_id]['filename']).stem}_formatted.pdf"
    elif file_type == "epub":
        file_path = session_dir / "output.epub"
        media_type = "application/epub+zip"
        filename = f"{Path(sessions[session_id]['filename']).stem}_formatted.epub"
    elif file_type == "report":
        # Generate validation report
        pdf_path = session_dir / "output.pdf"
        if pdf_path.exists():
            # Get configuration from session
            config_data = sessions[session_id].get('config', {})
            validation_config = ValidationConfig(
                use_drop_caps=config_data.get('use_drop_caps', False),
                page_size=config_data.get('page_size', '6x9'),
                margins=float(config_data.get('margins', 0.75)),
                css_path=None,
                use_paragraph_spacing=config_data.get('use_paragraph_spacing', False),
                disable_indentation=config_data.get('disable_indentation', False)
            )
            report = validate_pdf_file(str(pdf_path), config=validation_config)
            report_content = f"PDF Validation Report\n{'='*50}\n\n"
            report_content += f"File: {sessions[session_id]['filename']}\n"
            report_content += f"Overall Status: {report.overall_status.upper()}\n\n"

            for check in report.checks:
                status_icon = {'pass': '✓', 'fail': '✗', 'warning': '⚠', 'error': '✗'}.get(check.status, '?')
                report_content += f"{status_icon} {check.check_name}: {check.status.upper()}\n"
                report_content += f"   {check.message}\n\n"

            filename = f"{Path(sessions[session_id]['filename']).stem}_validation_report.txt"
            return PlainTextResponse(
                content=report_content,
                media_type='text/plain',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            raise HTTPException(status_code=404, detail="PDF not found for validation")
    elif file_type == "idm":
        file_path = session_dir / "output_idm.json"
        media_type = "application/json"
        filename = f"{Path(sessions[session_id]['filename']).stem}_idm.json"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


@app.get("/validate/{session_id}")
async def get_validation(session_id: str):
    """Return validation results as JSON."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_dir = OUTPUT_DIR / session_id
    pdf_path = session_dir / "output.pdf"

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    # Get configuration from session
    config_data = sessions[session_id].get('config', {})
    validation_config = ValidationConfig(
        use_drop_caps=config_data.get('use_drop_caps', False),
        page_size=config_data.get('page_size', '6x9'),
        margins=float(config_data.get('margins', 0.75)),
        css_path=None,
        use_paragraph_spacing=config_data.get('use_paragraph_spacing', False),
        disable_indentation=config_data.get('disable_indentation', False)
    )
    report = validate_pdf_file(str(pdf_path), config=validation_config)
    return report.to_dict()


@app.get("/formatting-test")
async def formatting_test(
    background_tasks: BackgroundTasks = None,
    use_drop_caps: bool = False,
    page_size: str = "6x9",
    margins: str = "0.75",
    use_paragraph_spacing: bool = False,
    disable_indentation: bool = False
):
    """Generate a test PDF with known formatting patterns for verification."""
    try:
        # Validate page_size
        valid_page_sizes = {'6x9', '8.5x11'}
        if page_size not in valid_page_sizes:
            raise HTTPException(status_code=400, detail=f"Invalid page_size '{page_size}'. Must be one of: {', '.join(valid_page_sizes)}")

        # Validate margins
        try:
            margins_val = float(margins)
            if not (0.5 <= margins_val <= 1.5):
                raise HTTPException(status_code=400, detail="Margins must be between 0.5 and 1.5 inches inclusive")
        except ValueError:
            raise HTTPException(status_code=400, detail="Margins must be a valid number")

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create session directory
        session_dir = OUTPUT_DIR / session_id
        session_dir.mkdir(exist_ok=True)

        # Create test IDM document with known formatting patterns
        from poc.idm_schema import IDMDocument, IDMChapter, IDMParagraph, IDMHeading

        # Create test document
        test_doc = IDMDocument(
            metadata={
                "title": "KDP Formatting Test Document",
                "author": "KDP Formatter Test Suite",
                "language": "en"
            }
        )

        # Chapter 1: Basic paragraph indentation test
        chapter1 = IDMChapter(title="Chapter 1: Basic Formatting")
        chapter1.blocks = [
            IDMParagraph(text="This is the first paragraph after a chapter heading. It should have NO indentation.", style="normal"),
            IDMParagraph(text="This is a subsequent paragraph in the same chapter. It should have proper indentation (0.2-0.25 inches) to create a professional appearance.", style="normal"),
            IDMParagraph(text="Another paragraph to test consistent indentation patterns. The first line should be indented while maintaining proper text flow.", style="normal"),
            IDMParagraph(text="A short paragraph that tests widow/orphan control. This line should not appear alone at the bottom or top of a page.", style="normal")
        ]

        # Chapter 2: Drop caps test (if enabled)
        chapter2 = IDMChapter(title="Chapter 2: Drop Caps Test")
        drop_cap_text = "This chapter tests drop caps functionality. The first letter should be enlarged and possibly styled differently, but must not overlap with adjacent text. The drop cap should be positioned properly within the margin boundaries and not interfere with the paragraph's indentation rules."
        chapter2.blocks = [
            IDMParagraph(text=drop_cap_text, style="normal")
        ]

        # Chapter 3: Heading levels test
        chapter3 = IDMChapter(title="Chapter 3: Heading Levels")
        chapter3.blocks = [
            IDMParagraph(text="First paragraph after main chapter heading - no indent.", style="normal"),
            IDMHeading(text="Section Heading", level=2),
            IDMParagraph(text="First paragraph after section heading - no indent.", style="normal"),
            IDMParagraph(text="Subsequent paragraph with proper indentation.", style="normal"),
            IDMHeading(text="Subsection", level=3),
            IDMParagraph(text="Another first paragraph - no indent.", style="normal")
        ]

        # Chapter 4: Long content for page break testing
        chapter4 = IDMChapter(title="Chapter 4: Page Break and Flow")
        long_text = "This chapter contains longer content to test page breaks and text flow. " * 50
        chapter4.blocks = [
            IDMParagraph(text=long_text, style="normal"),
            IDMParagraph(text="A new paragraph after the long text block.", style="normal")
        ]

        test_doc.chapters = [chapter1, chapter2, chapter3, chapter4]

        # Save test IDM
        idm_path = session_dir / "test_idm.json"
        with open(idm_path, 'w', encoding='utf-8') as f:
            json.dump(test_doc.to_dict(), f, indent=2, ensure_ascii=False)

        # Generate PDF
        pdf_path = session_dir / "test_formatting.pdf"
        render_document_to_pdf(test_doc, str(pdf_path), use_drop_caps=use_drop_caps, page_size=page_size, margins=margins_val,
                               use_paragraph_spacing=use_paragraph_spacing, disable_indentation=disable_indentation)

        # Validate the test PDF
        validation_config = ValidationConfig(
            use_drop_caps=use_drop_caps,
            page_size=page_size,
            margins=margins_val,
            css_path=None,
            use_paragraph_spacing=use_paragraph_spacing,
            disable_indentation=disable_indentation
        )
        test_report = validate_pdf_file(str(pdf_path), config=validation_config)
        logger.info(f"Test PDF validation: {test_report.overall_status}")

        # Store session data
        sessions[session_id] = {
            "filename": "formatting_test.txt",
            "timestamp": os.path.getctime(session_dir),
            "config": {
                "output_format": "pdf",
                "use_ai": False,
                "use_drop_caps": use_drop_caps,
                "page_size": page_size,
                "margins": margins,
                "use_paragraph_spacing": use_paragraph_spacing,
                "disable_indentation": disable_indentation
            },
            "ai_cost": 0,
            "is_test": True
        }

        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_old_sessions)

        # Return session data for recent conversions
        return {
            "session_id": session_id,
            "filename": "formatting_test.txt",
            "validation_summary": test_report.to_dict(),
            "redirect": f"/preview/{session_id}"
        }

    except Exception as e:
        logger.error(f"Error generating formatting test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """Return available configuration options."""
    return {
        "page_sizes": [
            {"value": "6x9", "label": "6\" x 9\" (Standard KDP)"},
            {"value": "8.5x11", "label": "8.5\" x 11\" (Letter)"}
        ],
        "margin_options": [
            {"value": "0.5", "label": "0.5 inches"},
            {"value": "0.75", "label": "0.75 inches (Standard)"},
            {"value": "1.0", "label": "1.0 inches"},
            {"value": "1.25", "label": "1.25 inches"},
            {"value": "1.5", "label": "1.5 inches"}
        ],
        "ai_models": [
            {"value": "gpt-4", "label": "GPT-4 (High accuracy)"},
            {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo (Fast)"}
        ],
        "format_options": [
            {"value": "pdf", "label": "PDF only"},
            {"value": "epub", "label": "EPUB only"},
            {"value": "both", "label": "PDF and EPUB"}
        ],
        "formatting_options": [
            {"value": "kdp_standard", "label": "KDP Standard (indent, no spacing)"},
            {"value": "modern", "label": "Modern (indent + spacing)"},
            {"value": "no_indent", "label": "No Indentation (spacing only)"}
        ]
    }


@app.post("/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up a specific session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        session_dir = OUTPUT_DIR / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)

        # Remove from memory
        del sessions[session_id]

        return {"message": "Session cleaned up successfully"}

    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if required dependencies are available
        missing_deps = []

        try:
            from pdfminer.high_level import extract_text
        except ImportError:
            missing_deps.append("pdfminer.six")

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            missing_deps.append("beautifulsoup4")

        try:
            from weasyprint import HTML
        except ImportError:
            missing_deps.append("weasyprint")

        try:
            import pypdf
        except ImportError:
            missing_deps.append("pypdf")

        try:
            import subprocess
            subprocess.run(['pandoc', '--version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_deps.append("pandoc")

        status = "degraded" if missing_deps else "healthy"

        return {
            "status": status,
            "version": "1.0.0",
            "missing_dependencies": missing_deps if missing_deps else None,
            "installation_command": "pip install -r requirements.txt" if missing_deps else None
        }

    except Exception as e:
        return {
            "status": "error",
            "version": "1.0.0",
            "error": str(e)
        }


def cleanup_old_sessions():
    """Clean up sessions older than 1 hour."""
    try:
        import time
        current_time = time.time()
        one_hour_ago = current_time - 3600

        to_remove = []
        for session_id, session_data in sessions.items():
            if session_data["timestamp"] < one_hour_ago:
                session_dir = OUTPUT_DIR / session_id
                if session_dir.exists():
                    shutil.rmtree(session_dir)
                to_remove.append(session_id)

        for session_id in to_remove:
            del sessions[session_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old sessions")

    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")


async def cleanup_old_files():
    """Clean up old files on startup."""
    try:
        import time
        current_time = time.time()
        one_hour_ago = current_time - 3600

        for session_dir in OUTPUT_DIR.glob("*"):
            if session_dir.is_dir() and session_dir.stat().st_mtime < one_hour_ago:
                shutil.rmtree(session_dir)
                logger.info(f"Cleaned up old session directory: {session_dir}")

    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8001,
        reload=True
    )
