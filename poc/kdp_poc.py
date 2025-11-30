#!/usr/bin/env python3
"""
KDP Formatter POC (Proof of Concept)

This script demonstrates the KDP formatting workflow:
1. Convert input document to IDM (Internal Document Model)
2. Render IDM to PDF and/or EPUB with KDP-compatible styling
3. Validate the generated files for KDP requirements

Usage:
    # Generate PDF
    python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_print.pdf

    # Generate both PDF and EPUB
    python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample_print.pdf --epub

    # Generate only EPUB
    python poc/kdp_poc.py --input test_data/sample_short.txt --output output/sample.epub --epub --skip-pdf
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add poc directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from converters import convert, compare_detection_methods
    from renderer import render_document_to_pdf
    from validator import validate_pdf_file, generate_validation_report
    from epub_generator import generate_epub
    from epub_validator import validate_epub_file, generate_epub_validation_report
except ImportError:
    # Fallback for direct script execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from converters import convert, compare_detection_methods
    from renderer import render_document_to_pdf
    from validator import validate_pdf_file, generate_validation_report
    from epub_generator import generate_epub
    from epub_validator import validate_epub_file, generate_epub_validation_report


def main():
    parser = argparse.ArgumentParser(description='KDP Formatter POC')
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input document path (supports .txt, .pdf, .docx, .md)'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output PDF path'
    )
    parser.add_argument(
        '--css',
        help='Custom CSS stylesheet path (default: poc/styles.css)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing PDF, do not generate'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--use-ai',
        action='store_true',
        help='Use OpenAI for structure detection (requires OPENAI_API_KEY)'
    )
    parser.add_argument(
        '--ai-model',
        choices=['gpt-4-turbo-preview', 'gpt-3.5-turbo'],
        default='gpt-4-turbo-preview',
        help='OpenAI model to use for AI detection (default: gpt-4-turbo-preview)'
    )
    parser.add_argument(
        '--compare-methods',
        action='store_true',
        help='Compare regex vs AI detection methods and show differences'
    )
    parser.add_argument(
        '--epub',
        action='store_true',
        help='Generate EPUB output alongside PDF (or instead of PDF if --skip-pdf is used)'
    )
    parser.add_argument(
        '--epub-output',
        help='Custom EPUB output path (default: replace .pdf extension with .epub)'
    )
    parser.add_argument(
        '--skip-pdf',
        action='store_true',
        help='Skip PDF generation, only generate EPUB (requires --epub flag)'
    )
    parser.add_argument(
        '--drop-caps',
        action='store_true',
        help='Enable drop caps for first letter of each chapter (optional, may cause formatting issues)'
    )

    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if args.validate_only:
        # Only validate existing PDF
        if not os.path.exists(args.output):
            print(f"Error: PDF file not found for validation: {args.output}")
            sys.exit(1)

        print(f"Validating existing PDF: {args.output}")
        validate_and_report(args.output, args.verbose)
        return

    # Check input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Handle comparison mode
    if args.compare_methods:
        print(f"Comparing detection methods for: {args.input}")
        try:
            comparison = compare_detection_methods(args.input)
            print("\n=== Detection Method Comparison ===")
            print(f"File: {comparison['file']}")

            if "error" not in comparison["regex"]:
                regex = comparison["regex"]
                print(f"\nRegex Detection:")
                print(f"  Chapters: {regex['chapters_detected']}")
                print(f"  Paragraphs: {regex['paragraphs_detected']}")
                print(f"  Cost: ${regex['cost']:.4f}")

            if "error" not in comparison["ai"]:
                ai = comparison["ai"]
                print(f"\nAI Detection:")
                print(f"  Chapters: {ai['chapters_detected']}")
                print(f"  Blocks: {ai['blocks_detected']}")
                print(f"  Front Matter: {ai['has_front_matter']}")
                print(f"  Back Matter: {ai['has_back_matter']}")
                print(f"  Cost: ${ai['cost']:.4f}")

            if "error" not in comparison["regex"] and "error" not in comparison["ai"]:
                comp = comparison["comparison"]
                print(f"\nComparison:")
                print(f"  Chapter Difference: {comp['chapter_difference']}")
                print(f"  Cost Difference: ${comp['cost_difference']:.4f}")
                if comp['ai_improved_chapter_detection']:
                    print("  ✓ AI improved chapter detection")
                else:
                    print("  ⚠ AI did not improve chapter detection")

        except Exception as e:
            print(f"Error during comparison: {str(e)}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
        return

    print(f"Processing: {args.input}")
    print(f"Output: {args.output}")

    # Determine output paths
    pdf_output = args.output if not args.skip_pdf else None
    epub_output = None
    if args.epub:
        if args.epub_output:
            epub_output = args.epub_output
        elif pdf_output:
            epub_output = pdf_output.replace('.pdf', '.epub')
        else:
            # EPUB-only mode with default naming
            epub_output = args.output.replace('.pdf', '.epub')

    # Validate arguments
    if args.skip_pdf and not args.epub:
        print("Error: --skip-pdf requires --epub flag")
        sys.exit(1)

    if not pdf_output and not epub_output:
        print("Error: Must generate either PDF or EPUB (use --epub flag)")
        sys.exit(1)

    try:
        # Step 1: Convert input to IDM
        if args.verbose:
            print("Step 1: Converting document to IDM...")
        document = convert(args.input, use_ai=args.use_ai, ai_model=args.ai_model)

        # Step 2: Save IDM as JSON (for inspection)
        if pdf_output:
            idm_path = pdf_output.replace('.pdf', '_idm.json')
        else:
            idm_path = epub_output.replace('.epub', '_idm.json')
        with open(idm_path, 'w', encoding='utf-8') as f:
            json.dump(document.to_dict(), f, indent=2, ensure_ascii=False)
        if args.verbose:
            print(f"IDM saved to: {idm_path}")

        # Report AI detection results
        if document.metadata.detected_by_ai:
            print(f"Structure detected by: AI (cost: ${document.metadata.ai_cost:.4f})")
        else:
            print("Structure detected by: Regex (cost: $0.00)")

        step_counter = 3

        # Step 3: Render to PDF (if not skipped)
        if pdf_output:
            if args.verbose:
                print(f"Step {step_counter}: Rendering PDF...")
            render_document_to_pdf(document, pdf_output, args.css, use_drop_caps=args.drop_caps)

            if args.verbose:
                print(f"PDF generated: {pdf_output}")

            # Step 4: Validate PDF
            if args.verbose:
                print(f"Step {step_counter + 1}: Validating PDF...")
            validate_and_report(pdf_output, args.verbose)
            step_counter += 2

        # Step X: Generate EPUB (if requested)
        if epub_output:
            if args.verbose:
                print(f"Step {step_counter}: Generating EPUB...")
            generate_epub(document, epub_output)

            if args.verbose:
                print(f"EPUB generated: {epub_output}")

            # Step X+1: Validate EPUB
            if args.verbose:
                print(f"Step {step_counter + 1}: Validating EPUB...")
            validate_epub_and_report(epub_output, args.verbose)
            step_counter += 2

        print("\nSuccess! Generated files:")
        if pdf_output:
            print(f"  PDF: {pdf_output}")
            print(f"  PDF Report: {pdf_output.replace('.pdf', '_report.txt')}")
            if args.drop_caps:
                print("  Drop Caps: Enabled (test carefully in KDP Preview)")
        if epub_output:
            print(f"  EPUB: {epub_output}")
            print(f"  EPUB Report: {epub_output.replace('.epub', '_epub_report.html')}")
        print(f"  IDM: {idm_path}")
        if document.metadata.detected_by_ai:
            print(f"  AI Cost: ${document.metadata.ai_cost:.4f}")

    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def validate_and_report(pdf_path: str, verbose: bool = False):
    """Validate PDF and generate report"""
    try:
        report = validate_pdf_file(pdf_path)

        # Generate text report
        report_path = pdf_path.replace('.pdf', '_report.txt')
        generate_validation_report(report, report_path)

        # Print summary
        icon_map = {'pass': '✓','fail': '✗','warning': '⚠','error': '✗'}
        overall_icon = icon_map.get(report.overall_status, '?')
        print(f"PDF Validation: {overall_icon} {report.overall_status.upper()}")

        if verbose:
            for check in report.checks:
                icon = icon_map.get(check.status, '?')
                print(f"  {icon} {check.check_name}: {check.message}")

        print(f"PDF Report saved: {report_path}")

    except Exception as e:
        print(f"PDF validation failed: {str(e)}")


def validate_epub_and_report(epub_path: str, verbose: bool = False):
    """Validate EPUB and generate report"""
    try:
        report = validate_epub_file(epub_path)

        # Generate HTML report
        report_path = epub_path.replace('.epub', '_epub_report.html')
        generate_epub_validation_report(report, report_path)

        # Print summary
        icon_map = {'pass': '✓','fail': '✗','warning': '⚠','error': '✗'}
        overall_icon = icon_map.get(report.overall_status, '?')
        print(f"EPUB Validation: {overall_icon} {report.overall_status.upper()}")

        if verbose:
            for check in report.checks:
                icon = icon_map.get(check.status, '?')
                print(f"  {icon} {check.check_name}: {check.message}")

            if report.kdp_blockers:
                print("  KDP Blockers:")
                for blocker in report.kdp_blockers:
                    print(f"    ✗ {blocker}")

            if report.warnings:
                print("  Warnings:")
                for warning in report.warnings:
                    print(f"    ⚠ {warning}")

        print(f"EPUB Report saved: {report_path}")

    except Exception as e:
        print(f"EPUB validation failed: {str(e)}")


if __name__ == '__main__':
    main()
