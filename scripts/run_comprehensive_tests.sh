#!/bin/bash

# KDP Formatter - Comprehensive Testing Script
# This script automates PDF generation for all test files with multiple configuration combinations
#
# Usage:
#   chmod +x scripts/run_comprehensive_tests.sh
#   ./scripts/run_comprehensive_tests.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OUTPUT_DIR="output/test_results"
TEST_FILES=(
    "test_data/sample_short.txt"
    "test_data/sample_medium.txt"
    "test_data/sample_nonfiction.txt"
)
AI_COST=0

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python virtual environment
check_virtual_env() {
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        print_warning "No virtual environment detected"

        # Try to find and activate virtual environment
        if [[ -f "venv/bin/activate" ]]; then
            print_info "Activating virtual environment: venv"
            source venv/bin/activate
        elif [[ -f ".venv/bin/activate" ]]; then
            print_info "Activating virtual environment: .venv"
            source .venv/bin/activate
        else
            print_error "Virtual environment not found. Please run:"
            echo "  python -m venv venv"
            echo "  source venv/bin/activate"
            echo "  pip install -r requirements.txt"
            exit 1
        fi
    else
        print_success "Virtual environment active: ${VIRTUAL_ENV}"
    fi
}

# Function to check dependencies
check_dependencies() {
    print_info "Checking dependencies..."

    # Check Python packages
    python -c "import weasyprint" 2>/dev/null || {
        print_error "WeasyPrint not installed. Run: pip install -r requirements.txt"
        exit 1
    }

    print_success "Python dependencies OK"

    # Check system dependencies
    if ! command_exists pandoc; then
        print_warning "Pandoc not found. EPUB generation will be skipped."
        echo "Install with:"
        if command_exists brew; then
            echo "  brew install pandoc"
        elif command_exists apt; then
            echo "  sudo apt install pandoc"
        else
            echo "  Visit: https://pandoc.org/installing.html"
        fi
    else
        print_success "Pandoc found"
    fi
}

# Function to create output directory
create_output_dir() {
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        mkdir -p "$OUTPUT_DIR"
        print_success "Created output directory: $OUTPUT_DIR"
    else
        print_info "Output directory exists: $OUTPUT_DIR"
    fi
}

# Function to run POC script with given arguments
run_poc() {
    local input_file="$1"
    local output_file="$2"
    local config_name="$3"
    shift 3
    local extra_args="$@"

    local filename=$(basename "$input_file" .txt)
    local base_output="$OUTPUT_DIR/${filename}_${config_name}"

    print_info "Testing: $filename - $config_name"

    # Run POC script
    if python poc/kdp_poc.py -i "$input_file" -o "$output_file" $extra_args -v 2>&1; then
        print_success "Generated: $(basename "$output_file")"

        # Check if validation report exists and display status
        local report_file="${output_file%.*}_report.txt"
        if [[ -f "$report_file" ]]; then
            # Extract validation status from report
            if grep -q "Overall Status: PASS" "$report_file"; then
                print_success "Validation: PASS"
            elif grep -q "Overall Status: WARNING" "$report_file"; then
                print_warning "Validation: WARNING"
            elif grep -q "Overall Status: FAIL" "$report_file"; then
                print_error "Validation: FAIL"
            fi
        fi

        # Check for AI cost if AI was used
        if [[ "$extra_args" == *"--use-ai"* ]]; then
            local idm_file="${output_file%.*}_idm.json"
            if [[ -f "$idm_file" ]]; then
                # Extract AI cost from IDM file (rough estimate)
                local word_count=$(wc -w < "$input_file")
                # Approximate cost: ~$0.001 per 1k tokens, roughly 750 words per 1k tokens
                local estimated_cost=$(echo "scale=4; $word_count * 0.001 / 750" | bc 2>/dev/null || echo "0.0001")
                AI_COST=$(echo "$AI_COST + $estimated_cost" | bc 2>/dev/null || echo "$AI_COST")
                print_info "Estimated AI cost: \$${estimated_cost}"
            fi
        fi

        return 0
    else
        print_error "Failed to generate: $(basename "$output_file")"
        return 1
    fi
}

# Function to generate test summary
generate_summary() {
    print_header "Test Summary"

    echo "Generated files in $OUTPUT_DIR:"
    echo

    # Count files by type
    local pdf_count=$(find "$OUTPUT_DIR" -name "*.pdf" | wc -l)
    local epub_count=$(find "$OUTPUT_DIR" -name "*.epub" | wc -l)
    local report_count=$(find "$OUTPUT_DIR" -name "*_report.txt" | wc -l)
    local json_count=$(find "$OUTPUT_DIR" -name "*.json" | wc -l)

    echo "PDF files: $pdf_count"
    echo "EPUB files: $epub_count"
    echo "Validation reports: $report_count"
    echo "IDM JSON files: $json_count"
    echo

    # Show file listing
    echo "Detailed file listing:"
    find "$OUTPUT_DIR" -type f -name "*.pdf" -o -name "*.epub" -o -name "*_report.txt" | sort

    # Show AI costs if any
    if (( $(echo "$AI_COST > 0" | bc -l 2>/dev/null || echo "0") )); then
        echo
        print_info "Total estimated AI costs: \$${AI_COST}"
    fi

    echo
    print_success "Comprehensive testing completed!"
    echo
    print_info "Next steps:"
    echo "  1. Review validation reports in $OUTPUT_DIR"
    echo "  2. Upload PDFs to KDP Preview for validation"
    echo "  3. Document results in docs/poc_results.md"
    echo "  4. Use web UI for manual testing: bash scripts/start_localhost.sh"
}

# Main execution
main() {
    echo "🧪 KDP Formatter - Comprehensive Testing"
    echo

    # Setup
    check_virtual_env
    check_dependencies
    create_output_dir

    echo
    print_header "Starting Comprehensive Tests"

    local total_tests=0
    local successful_tests=0

    # Test matrix for each file
    for input_file in "${TEST_FILES[@]}"; do
        if [[ ! -f "$input_file" ]]; then
            print_warning "Test file not found: $input_file"
            continue
        fi

        local filename=$(basename "$input_file" .txt)

        echo
        print_header "Testing $filename"

        # Test 1: Standard configuration
        ((total_tests++))
        if run_poc "$input_file" "$OUTPUT_DIR/${filename}_standard.pdf" "standard"; then
            ((successful_tests++))
        fi

        # Test 2: With drop caps
        ((total_tests++))
        if run_poc "$input_file" "$OUTPUT_DIR/${filename}_dropcaps.pdf" "dropcaps" --drop-caps; then
            ((successful_tests++))
        fi

        # Test 3: With AI detection
        ((total_tests++))
        if run_poc "$input_file" "$OUTPUT_DIR/${filename}_ai.pdf" "ai" --use-ai; then
            ((successful_tests++))
        fi

        # Test 4: With EPUB generation
        ((total_tests++))
        if command_exists pandoc && run_poc "$input_file" "$OUTPUT_DIR/${filename}_both.pdf" "both" --epub; then
            ((successful_tests++))
        else
            print_warning "EPUB test skipped (Pandoc not available)"
        fi
    done

    echo
    print_header "Test Results"
    echo "Total tests run: $total_tests"
    echo "Successful tests: $successful_tests"
    echo "Failed tests: $((total_tests - successful_tests))"

    if [[ $successful_tests -eq $total_tests ]]; then
        print_success "All tests passed!"
    else
        print_warning "Some tests failed. Check output above for details."
    fi

    echo
    generate_summary
}

# Run main function
main "$@"

