#!/bin/bash

# KDP Formatter - Localhost Development Server
# This script starts the FastAPI web UI for local testing and development
#
# Usage:
#   chmod +x scripts/start_localhost.sh
#   ./scripts/start_localhost.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOST="localhost"
PORT="8001"
APP_MODULE="app.main:app"

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

    # Check required Python packages
    local required_packages=("fastapi" "uvicorn" "weasyprint" "pypdf")
    local missing_packages=()

    for package in "${required_packages[@]}"; do
        if ! python -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done

    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        print_error "Missing Python packages: ${missing_packages[*]}"
        echo "Run: pip install -r requirements.txt"
        exit 1
    fi

    print_success "Python dependencies OK"

    # Check Pandoc for EPUB generation
    if ! command_exists pandoc; then
        print_warning "Pandoc not found. EPUB generation will be limited."
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

    # Check for required fonts
    if [[ ! -f "poc/fonts/SourceSerif4-Regular.ttf" ]] || [[ ! -f "poc/fonts/SourceSerif4-Semibold.ttf" ]]; then
        print_warning "Required fonts not found in poc/fonts/"
        echo "Run: bash poc/fonts/download_fonts.sh"
    else
        print_success "Fonts available"
    fi
}

# Function to check port availability
check_port() {
    if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port ${PORT} is already in use"
        echo "Try killing the existing process or use a different port:"
        echo "  lsof -ti:${PORT} | xargs kill -9"
        echo "  Or edit PORT in this script"
        exit 1
    fi
}

# Function to cleanup on exit
cleanup() {
    print_info "Shutting down server..."
    exit 0
}

# Function to check health endpoint
check_health() {
    print_info "Checking server health..."
    sleep 3  # Wait for server to start

    if curl -s -f "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
        print_success "Server health check passed"
    else
        print_warning "Health check failed - server may not be fully ready"
    fi
}

# Function to start server
start_server() {
    # Set PYTHONPATH to include project root
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"

    print_info "Starting KDP Formatter Web UI..."

    # Display access information
    echo
    echo -e "${GREEN}✓${NC} All dependencies installed"
    echo -e "${GREEN}✓${NC} Fonts available"
    echo -e "${GREEN}✓${NC} Starting KDP Formatter Web UI..."
    echo
    echo -e "${BLUE}🌐${NC} Access the interface at: http://${HOST}:${PORT}"
    echo
    echo -e "${BLUE}📋${NC} Features:"
    echo "  - Drag & drop file upload (.txt, .docx, .pdf, .md)"
    echo "  - Configuration options (page size, margins, drop caps, AI detection)"
    echo "  - PDF preview with zoom controls"
    echo "  - Download PDF, EPUB, and validation reports"
    echo "  - Automatic cleanup after 1 hour"
    echo
    echo -e "${BLUE}🧪${NC} Test formatting: http://${HOST}:${PORT}/formatting-test"
    echo
    print_info "Press Ctrl+C to stop"

    # Set trap to handle Ctrl+C
    trap cleanup SIGINT SIGTERM

    # Start uvicorn server in background to allow health check
    uvicorn ${APP_MODULE} \
        --host ${HOST} \
        --port ${PORT} \
        --reload \
        --log-level info &
    SERVER_PID=$!

    # Check server health
    check_health

    # Wait for server process
    wait $SERVER_PID

    print_success "Server stopped"
}

# Main execution
main() {
    echo "🚀 KDP Formatter - Local Development Server"
    echo

    check_virtual_env
    check_dependencies
    check_port

    echo
    start_server
}

# Run main function
main "$@"
