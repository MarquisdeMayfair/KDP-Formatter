#!/bin/bash

# KDP Formatter POC Test Runner
# This script runs the POC on available test data files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
POC_DIR="$SCRIPT_DIR"
TEST_DATA_DIR="$PROJECT_ROOT/test_data"
OUTPUT_DIR="$PROJECT_ROOT/output"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "KDP Formatter POC Test Runner"
echo "============================="
echo "Test Data Directory: $TEST_DATA_DIR"
echo "Output Directory: $OUTPUT_DIR"
echo

# Check if POC script exists
if [ ! -f "$POC_DIR/kdp_poc.py" ]; then
    echo -e "${RED}Error: POC script not found: $POC_DIR/kdp_poc.py${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Check if epubcheck is available
EPUBCHECK_AVAILABLE=false
if command -v epubcheck &> /dev/null; then
    EPUBCHECK_AVAILABLE=true
    echo -e "${GREEN}✓ epubcheck found - EPUB validation enabled${NC}"
else
    echo -e "${YELLOW}⚠ epubcheck not found - EPUB validation will be limited${NC}"
fi

# Test files to check
TEST_FILES=(
    "sample_short.txt"
    "sample_medium.docx"
    "sample_medium.txt"
    "sample_nonfiction.txt"
    "sample_long.pdf"
)

PASSED=0
FAILED=0
SKIPPED=0

for test_file in "${TEST_FILES[@]}"; do
    input_path="$TEST_DATA_DIR/$test_file"

    if [ -f "$input_path" ]; then
        echo -e "${BLUE}Testing: $test_file${NC}"

        # Determine output filename
        base_name="${test_file%.*}"

        # Test both with and without drop caps for comparison
        echo -e "  Testing without drop caps..."
        output_pdf="$OUTPUT_DIR/${base_name}_print.pdf"

        # Run POC without drop caps (default)
        if python3 "$POC_DIR/kdp_poc.py" --input "$input_path" --output "$output_pdf" --epub; then
            echo -e "${GREEN}✓ PASSED: $test_file${NC}"

            # Check if output files were created
            idm_file="$OUTPUT_DIR/${base_name}_print_idm.json"
            pdf_report_file="$OUTPUT_DIR/${base_name}_print_report.txt"
            epub_file="$OUTPUT_DIR/${base_name}_print.epub"
            epub_report_file="$OUTPUT_DIR/${base_name}_print_epub_report.html"

            generated_files=""
            if [ -f "$output_pdf" ]; then generated_files="${generated_files}PDF "; fi
            if [ -f "$epub_file" ]; then generated_files="${generated_files}EPUB "; fi
            if [ -f "$idm_file" ]; then generated_files="${generated_files}IDM "; fi
            if [ -f "$pdf_report_file" ]; then generated_files="${generated_files}PDF_Report "; fi
            if [ -f "$epub_report_file" ]; then generated_files="${generated_files}EPUB_Report "; fi

            if [ -n "$generated_files" ]; then
                echo -e "  Generated files: $generated_files"
            else
                echo -e "${YELLOW}  Warning: No output files found${NC}"
            fi

            ((PASSED++))

            # Test with drop caps enabled
            echo -e "  Testing with drop caps..."
            output_pdf_dropcaps="$OUTPUT_DIR/${base_name}_print_dropcaps.pdf"

            if python3 "$POC_DIR/kdp_poc.py" --input "$input_path" --output "$output_pdf_dropcaps" --drop-caps; then
                echo -e "${GREEN}✓ PASSED: $test_file (with drop caps)${NC}"

                # Check validation differences
                pdf_report_dropcaps="$OUTPUT_DIR/${base_name}_print_dropcaps_report.txt"

                if [ -f "$pdf_report_file" ] && [ -f "$pdf_report_dropcaps" ]; then
                    echo -e "  Comparing validation results..."
                    # Simple comparison - check if warnings differ
                    warnings_normal=$(grep -c "WARNING\|⚠" "$pdf_report_file" 2>/dev/null || echo "0")
                    warnings_dropcaps=$(grep -c "WARNING\|⚠" "$pdf_report_dropcaps" 2>/dev/null || echo "0")

                    if [ "$warnings_normal" != "$warnings_dropcaps" ]; then
                        echo -e "${YELLOW}  ⚠ Validation differs: normal=${warnings_normal}, dropcaps=${warnings_dropcaps}${NC}"
                    else
                        echo -e "  Validation results similar between versions"
                    fi
                fi

                ((PASSED++))
            else
                echo -e "${RED}✗ FAILED: $test_file (with drop caps)${NC}"
                ((FAILED++))
            fi
        else
            echo -e "${RED}✗ FAILED: $test_file${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${YELLOW}⚠ SKIPPED: $test_file (file not found)${NC}"
        ((SKIPPED++))
    fi

    echo
done

# AI Detection Tests (requires OPENAI_API_KEY)
echo "AI Detection Tests"
echo "=================="

if [ -n "$OPENAI_API_KEY" ]; then
    echo "OpenAI API key found - running AI detection tests..."

    # Test AI detection on short sample
    if [ -f "$TEST_DATA_DIR/sample_short.txt" ]; then
        echo -e "${BLUE}Testing AI detection: sample_short.txt${NC}"

        output_pdf="$OUTPUT_DIR/sample_short_ai_print.pdf"

        if python3 "$POC_DIR/kdp_poc.py" --input "$TEST_DATA_DIR/sample_short.txt" --output "$output_pdf" --use-ai; then
            echo -e "${GREEN}✓ PASSED: AI detection on sample_short.txt${NC}"

            # Extract AI cost from output (this is a bit hacky but works)
            ai_cost=$(python3 -c "
import json
import os
idm_file = '$OUTPUT_DIR/sample_short_ai_print_idm.json'
if os.path.exists(idm_file):
    with open(idm_file) as f:
        data = json.load(f)
        cost = data.get('metadata', {}).get('ai_cost', 0)
        print(f'{cost:.4f}')
else:
    print('0.0000')
")

            echo -e "  AI Cost: \$${ai_cost}"
            ((PASSED++))
        else
            echo -e "${RED}✗ FAILED: AI detection on sample_short.txt${NC}"
            ((FAILED++))
        fi
    fi

    # Run AI detection test suite
    echo -e "${BLUE}Running AI detection test suite...${NC}"
    if python3 "$POC_DIR/test_ai_detection.py" --output "$PROJECT_ROOT/docs/ai_detection_test_results.md"; then
        echo -e "${GREEN}✓ PASSED: AI detection test suite${NC}"
        echo -e "  Results: $PROJECT_ROOT/docs/ai_detection_test_results.md"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED: AI detection test suite${NC}"
        ((FAILED++))
    fi

    echo
else
    echo -e "${YELLOW}⚠ SKIPPED: AI tests (OPENAI_API_KEY not set)${NC}"
    echo "  To run AI tests: export OPENAI_API_KEY=your-key-here"
    ((SKIPPED++))
fi

# Comparison test (requires OPENAI_API_KEY)
if [ -n "$OPENAI_API_KEY" ] && [ -f "$TEST_DATA_DIR/sample_short.txt" ]; then
    echo -e "${BLUE}Running detection method comparison...${NC}"

    if python3 "$POC_DIR/kdp_poc.py" --input "$TEST_DATA_DIR/sample_short.txt" --output /tmp/compare_test.pdf --compare-methods; then
        echo -e "${GREEN}✓ PASSED: Detection method comparison${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED: Detection method comparison${NC}"
        ((FAILED++))
    fi
fi

# EPUB-only Tests
echo
echo "EPUB-Only Tests"
echo "==============="

if [ -f "$TEST_DATA_DIR/sample_short.txt" ]; then
    echo -e "${BLUE}Testing EPUB-only generation: sample_short.txt${NC}"

    epub_output="$OUTPUT_DIR/sample_short_epub_only.epub"

    if python3 "$POC_DIR/kdp_poc.py" --input "$TEST_DATA_DIR/sample_short.txt" --output "$epub_output" --epub --skip-pdf; then
        echo -e "${GREEN}✓ PASSED: EPUB-only generation${NC}"

        # Check if output files were created
        idm_file="$OUTPUT_DIR/sample_short_epub_only_idm.json"
        epub_report_file="$OUTPUT_DIR/sample_short_epub_only_epub_report.html"

        generated_files=""
        if [ -f "$epub_output" ]; then generated_files="${generated_files}EPUB "; fi
        if [ -f "$idm_file" ]; then generated_files="${generated_files}IDM "; fi
        if [ -f "$epub_report_file" ]; then generated_files="${generated_files}EPUB_Report "; fi

        if [ -n "$generated_files" ]; then
            echo -e "  Generated files: $generated_files"
        fi

        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED: EPUB-only generation${NC}"
        ((FAILED++))
    fi
fi

echo

# Summary
echo "Test Summary"
echo "============"
echo -e "Passed: $PASSED"
echo -e "Failed: $FAILED"
echo -e "Skipped: $SKIPPED"

# Show test results locations
if [ -n "$OPENAI_API_KEY" ]; then
    echo
    echo "AI Test Results:"
    echo -e "  Detailed results: $PROJECT_ROOT/docs/ai_detection_test_results.md"
    if [ -f "$PROJECT_ROOT/docs/ai_detection_test_results.md" ]; then
        echo -e "${GREEN}  ✓ AI test report generated${NC}"
    fi
fi

echo
echo "Drop Caps Testing Notes:"
echo -e "${YELLOW}⚠ Drop caps are tested for compatibility but disabled by default${NC}"
echo "  - Default (no drop caps): Recommended for most use cases"
echo "  - With drop caps: May cause formatting issues - test carefully in KDP Preview"
echo "  - Always verify drop cap rendering manually before publishing"
echo "  - Reference: $PROJECT_ROOT/docs/kdp_preview_testing_protocol.md"

echo
echo "Output Files:"
echo -e "  Generated files are in: $OUTPUT_DIR"
echo -e "  Drop caps comparison: Look for '*_dropcaps.pdf' files"

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Some tests failed${NC}"
    exit 1
elif [ $PASSED -gt 0 ]; then
    echo -e "${GREEN}All available tests passed${NC}"
    if [ "$EPUBCHECK_AVAILABLE" = true ]; then
        echo -e "${GREEN}EPUB validation is enabled (epubcheck found)${NC}"
    else
        echo -e "${YELLOW}EPUB validation is limited (epubcheck not found)${NC}"
    fi
else
    echo -e "${YELLOW}No tests were run${NC}"
fi
