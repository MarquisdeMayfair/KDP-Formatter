"""
EPUB Validator for KDP Formatter POC

This module validates generated EPUB files for KDP compatibility using epubcheck
and custom validation checks.
"""

import os
import subprocess
import zipfile
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from xml.etree import ElementTree as ET

try:
    from lxml import etree
except ImportError:
    etree = None


@dataclass
class ValidationCheck:
    """Result of a validation check"""
    check_name: str
    status: str  # 'pass', 'fail', 'warning', 'error'
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class EPUBValidationReport:
    """Complete EPUB validation report"""
    epub_path: str
    overall_status: str  # 'pass', 'fail', 'warning'
    checks: List[ValidationCheck]
    epubcheck_output: str
    kdp_blockers: List[str]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "epub_path": self.epub_path,
            "overall_status": self.overall_status,
            "checks": [
                {
                    "check_name": check.check_name,
                    "status": check.status,
                    "message": check.message,
                    "details": check.details
                }
                for check in self.checks
            ],
            "epubcheck_output": self.epubcheck_output,
            "kdp_blockers": self.kdp_blockers,
            "warnings": self.warnings
        }


def validate_epub_file(epub_path: str) -> EPUBValidationReport:
    """
    Validate an EPUB file for KDP compatibility

    Args:
        epub_path: Path to the EPUB file to validate

    Returns:
        EPUBValidationReport with comprehensive validation results
    """
    if not os.path.exists(epub_path):
        return EPUBValidationReport(
            epub_path=epub_path,
            overall_status="error",
            checks=[ValidationCheck(
                "file_exists",
                "error",
                f"EPUB file not found: {epub_path}"
            )],
            epubcheck_output="",
            kdp_blockers=["File not found"],
            warnings=[]
        )

    checks = []
    kdp_blockers = []
    warnings = []

    # Run epubcheck
    epubcheck_result = _run_epubcheck(epub_path)
    checks.extend(epubcheck_result["checks"])

    # Add epubcheck output to report
    epubcheck_output = epubcheck_result["output"]

    # Update KDP blockers and warnings from epubcheck
    for check in epubcheck_result["checks"]:
        if check.status == "fail":
            kdp_blockers.append(f"{check.check_name}: {check.message}")
        elif check.status == "warning":
            warnings.append(f"{check.check_name}: {check.message}")

    # Run custom KDP checks
    custom_checks = _run_kdp_checks(epub_path)
    checks.extend(custom_checks)

    # Update blockers and warnings from custom checks
    for check in custom_checks:
        if check.status == "fail":
            kdp_blockers.append(f"{check.check_name}: {check.message}")
        elif check.status == "warning":
            warnings.append(f"{check.check_name}: {check.message}")

    # Determine overall status
    statuses = [check.status for check in checks]
    if 'error' in statuses:
        overall_status = 'error'
    elif 'fail' in statuses:
        overall_status = 'fail'
    elif 'warning' in statuses:
        overall_status = 'warning'
    else:
        overall_status = 'pass'

    return EPUBValidationReport(
        epub_path=epub_path,
        overall_status=overall_status,
        checks=checks,
        epubcheck_output=epubcheck_output,
        kdp_blockers=kdp_blockers,
        warnings=warnings
    )


def _run_epubcheck(epub_path: str) -> Dict[str, Any]:
    """Run epubcheck and parse results"""
    if not _check_epubcheck_installed():
        return {
            "checks": [ValidationCheck(
                "epubcheck",
                "error",
                "epubcheck not installed. Install Java and epubcheck for full validation."
            )],
            "output": "epubcheck not available"
        }

    # Try wrapper script first, then fallback to JAR
    epubcheck_cmds = [
        ['epubcheck', epub_path],
        ['java', '-jar', '/opt/epubcheck/epubcheck.jar', epub_path]
    ]

    for cmd in epubcheck_cmds:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse epubcheck output
            checks = _parse_epubcheck_output(result.stdout + result.stderr)

            return {
                "checks": checks,
                "output": result.stdout + result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "checks": [ValidationCheck(
                    "epubcheck",
                    "error",
                    "epubcheck timed out after 60 seconds"
                )],
                "output": "timeout"
            }
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue  # Try next command

    # If all commands failed
    return {
        "checks": [ValidationCheck(
            "epubcheck",
            "error",
            "Failed to run epubcheck with any available method"
        )],
        "output": "all methods failed"
    }


def _parse_epubcheck_output(output: str) -> List[ValidationCheck]:
    """Parse epubcheck output into validation checks"""
    checks = []

    if "No errors or warnings detected" in output:
        checks.append(ValidationCheck(
            "epubcheck_validation",
            "pass",
            "EPUB passed epubcheck validation with no errors or warnings"
        ))
        return checks

    # Parse errors and warnings
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('ERROR'):
            # Extract error message
            message = line[6:].strip()  # Remove "ERROR:" prefix
            checks.append(ValidationCheck(
                "epubcheck_error",
                "fail",
                message
            ))
        elif line.startswith('WARNING'):
            # Extract warning message
            message = line[8:].strip()  # Remove "WARNING:" prefix
            checks.append(ValidationCheck(
                "epubcheck_warning",
                "warning",
                message
            ))

    if not checks:
        # If we couldn't parse specific errors but there was output, assume failure
        checks.append(ValidationCheck(
            "epubcheck_validation",
            "fail",
            "EPUB failed epubcheck validation (could not parse details)"
        ))

    return checks


def _run_kdp_checks(epub_path: str) -> List[ValidationCheck]:
    """Run custom KDP-specific validation checks"""
    checks = []

    # Check file count
    checks.append(_check_file_count(epub_path))

    # Check file sizes
    checks.append(_check_file_sizes(epub_path))

    # Check metadata
    checks.append(_check_metadata(epub_path))

    # Check nav.xhtml
    checks.append(_check_nav_xhtml(epub_path))

    # Check fonts
    checks.append(_check_fonts(epub_path))

    # Check structure
    checks.append(_check_structure(epub_path))

    return checks


def _check_file_count(epub_path: str) -> ValidationCheck:
    """Check that EPUB has reasonable file count (< 300 HTML files)"""
    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            files = epub_zip.namelist()
            html_files = [f for f in files if f.endswith(('.xhtml', '.html'))]

            if len(html_files) > 300:
                return ValidationCheck(
                    "file_count",
                    "fail",
                    f"Too many HTML files: {len(html_files)} (KDP limit: 300)",
                    {"html_files": len(html_files), "limit": 300}
                )
            elif len(html_files) == 0:
                return ValidationCheck(
                    "file_count",
                    "fail",
                    "No HTML files found in EPUB"
                )
            else:
                return ValidationCheck(
                    "file_count",
                    "pass",
                    f"HTML file count: {len(html_files)} (within KDP limit of 300)"
                )
    except Exception as e:
        return ValidationCheck(
            "file_count",
            "error",
            f"Failed to check file count: {str(e)}"
        )


def _check_file_sizes(epub_path: str) -> ValidationCheck:
    """Check that individual files are under 30MB"""
    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            oversized_files = []

            for file_info in epub_zip.filelist:
                if file_info.file_size > 30 * 1024 * 1024:  # 30MB
                    oversized_files.append(file_info.filename)

            if oversized_files:
                return ValidationCheck(
                    "file_sizes",
                    "fail",
                    f"Files exceed 30MB limit: {', '.join(oversized_files)}",
                    {"oversized_files": oversized_files, "limit_mb": 30}
                )
            else:
                return ValidationCheck(
                    "file_sizes",
                    "pass",
                    "All files are under 30MB limit"
                )
    except Exception as e:
        return ValidationCheck(
            "file_sizes",
            "error",
            f"Failed to check file sizes: {str(e)}"
        )


def _check_metadata(epub_path: str) -> ValidationCheck:
    """Check for required metadata (title, author, language)"""
    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            # Find OPF file
            opf_file = None
            for filename in epub_zip.namelist():
                if filename.endswith('.opf'):
                    opf_file = filename
                    break

            if not opf_file:
                return ValidationCheck(
                    "metadata",
                    "fail",
                    "No OPF file found in EPUB"
                )

            # Parse OPF file
            with epub_zip.open(opf_file) as f:
                opf_content = f.read().decode('utf-8')

            # Parse XML
            root = ET.fromstring(opf_content)

            # Check Dublin Core metadata
            dc_ns = '{http://purl.org/dc/elements/1.1/}'
            metadata_elem = root.find('.//{http://www.idpf.org/2007/opf}metadata')

            if metadata_elem is None:
                return ValidationCheck(
                    "metadata",
                    "fail",
                    "No metadata section found in OPF"
                )

            title = metadata_elem.find(f'.//{dc_ns}title')
            creator = metadata_elem.find(f'.//{dc_ns}creator')
            language = metadata_elem.find(f'.//{dc_ns}language')

            missing = []
            if title is None or not title.text:
                missing.append("title")
            if creator is None or not creator.text:
                missing.append("author")
            if language is None or not language.text:
                missing.append("language")

            if missing:
                return ValidationCheck(
                    "metadata",
                    "fail",
                    f"Missing required metadata: {', '.join(missing)}"
                )
            else:
                return ValidationCheck(
                    "metadata",
                    "pass",
                    f"Metadata present: title='{title.text}', author='{creator.text}', language='{language.text}'"
                )

    except Exception as e:
        return ValidationCheck(
            "metadata",
            "error",
            f"Failed to check metadata: {str(e)}"
        )


def _check_nav_xhtml(epub_path: str) -> ValidationCheck:
    """Check for nav.xhtml file"""
    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            files = epub_zip.namelist()

            nav_files = [f for f in files if 'nav.xhtml' in f]
            if not nav_files:
                return ValidationCheck(
                    "nav_xhtml",
                    "fail",
                    "No nav.xhtml file found (required for EPUB 3)"
                )
            else:
                return ValidationCheck(
                    "nav_xhtml",
                    "pass",
                    f"nav.xhtml found: {nav_files[0]}"
                )
    except Exception as e:
        return ValidationCheck(
            "nav_xhtml",
            "error",
            f"Failed to check nav.xhtml: {str(e)}"
        )


def _check_fonts(epub_path: str) -> ValidationCheck:
    """Check for embedded fonts"""
    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            files = epub_zip.namelist()

            font_files = [f for f in files if f.lower().endswith(('.ttf', '.otf', '.woff', '.woff2'))]

            if not font_files:
                return ValidationCheck(
                    "fonts",
                    "warning",
                    "No embedded fonts found (fonts recommended for consistent rendering)"
                )
            else:
                # Check for OFL license when fonts are present
                ofl_license_files = [f for f in files if 'ofl' in f.lower() and f.lower().endswith('.txt')]
                if not ofl_license_files:
                    return ValidationCheck(
                        "fonts",
                        "warning",
                        f"Embedded fonts found: {len(font_files)} ({', '.join(font_files)}), but no OFL license text detected. Ensure font licensing compliance.",
                        {"font_files": font_files, "ofl_license_missing": True}
                    )
                else:
                    return ValidationCheck(
                        "fonts",
                        "pass",
                        f"Embedded fonts found: {len(font_files)} ({', '.join(font_files)}) with OFL license ({', '.join(ofl_license_files)})"
                    )
    except Exception as e:
        return ValidationCheck(
            "fonts",
            "error",
            f"Failed to check fonts: {str(e)}"
        )


def _check_structure(epub_path: str) -> ValidationCheck:
    """Check basic EPUB structure"""
    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            files = epub_zip.namelist()

            # Check for required files
            has_mimetype = 'mimetype' in files
            has_container = 'META-INF/container.xml' in files
            has_opf = any(f.endswith('.opf') for f in files)

            missing = []
            if not has_mimetype:
                missing.append("mimetype")
            if not has_container:
                missing.append("META-INF/container.xml")
            if not has_opf:
                missing.append("OPF file")

            if missing:
                return ValidationCheck(
                    "structure",
                    "fail",
                    f"Missing required EPUB files: {', '.join(missing)}"
                )
            else:
                return ValidationCheck(
                    "structure",
                    "pass",
                    "EPUB structure is valid (mimetype, container.xml, OPF present)"
                )

    except Exception as e:
        return ValidationCheck(
            "structure",
            "error",
            f"Failed to check EPUB structure: {str(e)}"
        )


def _check_epubcheck_installed() -> bool:
    """Check if epubcheck is installed"""
    try:
        # Try the wrapper script first
        result = subprocess.run(
            ['epubcheck', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback to JAR path
    try:
        result = subprocess.run(
            ['java', '-jar', '/opt/epubcheck/epubcheck.jar', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def generate_epub_validation_report(report: EPUBValidationReport, output_path: str):
    """
    Generate a human-readable EPUB validation report

    Args:
        report: EPUBValidationReport to write
        output_path: Path to write the report (HTML format)
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE html>\n")
        f.write("<html>\n<head>\n")
        f.write("<meta charset='utf-8'>\n")
        f.write("<title>EPUB Validation Report</title>\n")
        f.write("<style>\n")
        f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
        f.write(".pass { color: green; }\n")
        f.write(".fail { color: red; }\n")
        f.write(".warning { color: orange; }\n")
        f.write(".error { color: red; font-weight: bold; }\n")
        f.write("h1, h2 { color: #333; }\n")
        f.write(".summary { background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0; }\n")
        f.write("</style>\n")
        f.write("</head>\n<body>\n")

        f.write(f"<h1>EPUB Validation Report</h1>\n")
        f.write(f"<p><strong>File:</strong> {report.epub_path}</p>\n")
        f.write(f"<p><strong>Overall Status:</strong> <span class='{report.overall_status}'>{report.overall_status.upper()}</span></p>\n")

        # KDP Blockers
        if report.kdp_blockers:
            f.write("<h2>KDP Blockers</h2>\n")
            f.write("<ul>\n")
            for blocker in report.kdp_blockers:
                f.write(f"<li class='fail'>{blocker}</li>\n")
            f.write("</ul>\n")

        # Warnings
        if report.warnings:
            f.write("<h2>Warnings</h2>\n")
            f.write("<ul>\n")
            for warning in report.warnings:
                f.write(f"<li class='warning'>{warning}</li>\n")
            f.write("</ul>\n")

        # Detailed Checks
        f.write("<h2>Detailed Checks</h2>\n")
        for check in report.checks:
            status_class = check.status
            status_icon = {
                'pass': '✓',
                'fail': '✗',
                'warning': '⚠',
                'error': '✗'
            }.get(check.status, '?')

            f.write(f"<div class='summary'>\n")
            f.write(f"<h3>{status_icon} {check.check_name} - <span class='{status_class}'>{check.status.upper()}</span></h3>\n")
            f.write(f"<p>{check.message}</p>\n")

            if check.details:
                f.write("<ul>\n")
                for key, value in check.details.items():
                    f.write(f"<li><strong>{key}:</strong> {value}</li>\n")
                f.write("</ul>\n")

            f.write("</div>\n")

        # Epubcheck Output
        if report.epubcheck_output and report.epubcheck_output not in ["epubcheck not available", "timeout"]:
            f.write("<h2>Epubcheck Output</h2>\n")
            f.write("<pre style='background: #f5f5f5; padding: 10px; border-radius: 5px;'>\n")
            f.write(report.epubcheck_output)
            f.write("</pre>\n")

        f.write("</body>\n</html>\n")
