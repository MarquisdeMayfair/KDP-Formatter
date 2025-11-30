#!/bin/bash

# KDP Formatter - Installation Verification Script
# This script verifies that all system dependencies, Python packages, and configurations are correctly installed
# Run after completing the installation steps

set -e  # Exit on any error

echo "=== KDP Formatter - Installation Verification ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC}: $message"
    else
        echo -e "${YELLOW}? WARN${NC}: $message"
    fi
}

# Initialize counters
total_checks=0
passed_checks=0
failed_checks=0

# Function to track results
check_result() {
    local result=$1
    local message=$2
    ((total_checks++))
    if [ "$result" = "PASS" ]; then
        ((passed_checks++))
        print_status "PASS" "$message"
    else
        ((failed_checks++))
        print_status "FAIL" "$message"
    fi
}

echo "Checking system dependencies..."
echo "------------------------------"

# Check Python 3.11+
if command -v python3.11 &> /dev/null; then
    version=$(python3.11 --version 2>&1 | grep -oP '\d+\.\d+')
    if [[ $(echo "$version >= 3.11" | bc -l) -eq 1 ]]; then
        check_result "PASS" "Python 3.11+ installed: $version"
    else
        check_result "FAIL" "Python version too old: $version (need 3.11+)"
    fi
else
    check_result "FAIL" "Python 3.11 not found"
fi

# Check Pandoc
if command -v pandoc &> /dev/null; then
    version=$(pandoc --version | head -n 1 | grep -oP '\d+\.\d+')
    if [[ $(echo "$version >= 3.0" | bc -l) -eq 1 ]]; then
        check_result "PASS" "Pandoc 3.x installed: $version"
    else
        check_result "FAIL" "Pandoc version too old: $version (need 3.x)"
    fi
else
    check_result "FAIL" "Pandoc not found"
fi

# Check Tesseract
if command -v tesseract &> /dev/null; then
    version=$(tesseract --version | head -n 1 | grep -oP '\d+\.\d+')
    if [[ $(echo "$version >= 5.0" | bc -l) -eq 1 ]]; then
        check_result "PASS" "Tesseract 5.x installed: $version"
    else
        check_result "FAIL" "Tesseract version too old: $version (need 5.x)"
    fi
else
    check_result "FAIL" "Tesseract not found"
fi

# Check ImageMagick
if command -v convert &> /dev/null; then
    version=$(convert --version | head -n 1 | grep -oP '\d+\.\d+\.\d+')
    check_result "PASS" "ImageMagick installed: $version"
else
    check_result "FAIL" "ImageMagick not found"
fi

# Check Ghostscript
if command -v gs &> /dev/null; then
    version=$(gs --version 2>&1)
    if [[ $(echo "$version >= 10.0" | bc -l) -eq 1 ]]; then
        check_result "PASS" "Ghostscript 10.x installed: $version"
    else
        check_result "FAIL" "Ghostscript version too old: $version (need 10.x)"
    fi
else
    check_result "FAIL" "Ghostscript not found"
fi

# Check Java for epubcheck
if command -v java &> /dev/null; then
    version=$(java -version 2>&1 | head -n 1 | grep -oP '\d+\.\d+')
    check_result "PASS" "Java installed: $version"
else
    check_result "FAIL" "Java not found (required for epubcheck)"
fi

# Check epubcheck
if [ -f "/opt/epubcheck/epubcheck.jar" ]; then
    version=$(java -jar /opt/epubcheck/epubcheck.jar --version 2>&1 | head -n 1)
    check_result "PASS" "epubcheck installed: $version"
else
    check_result "FAIL" "epubcheck not found at /opt/epubcheck/epubcheck.jar"
fi

echo ""
echo "Checking directory structure..."
echo "------------------------------"

# Check application directory
if [ -d "/opt/kdp-formatter" ]; then
    check_result "PASS" "Application directory exists: /opt/kdp-formatter"
else
    check_result "FAIL" "Application directory not found: /opt/kdp-formatter"
fi

# Check subdirectories
for dir in "app" "uploads" "outputs" "logs" "venv"; do
    if [ -d "/opt/kdp-formatter/$dir" ]; then
        check_result "PASS" "Directory exists: $dir"
    else
        check_result "FAIL" "Directory missing: $dir"
    fi
done

# Check user
if id -u kdp-formatter &>/dev/null; then
    check_result "PASS" "Application user exists: kdp-formatter"
else
    check_result "FAIL" "Application user not found: kdp-formatter"
fi

echo ""
echo "Checking Python environment..."
echo "-----------------------------"

# Check virtual environment
if [ -d "/opt/kdp-formatter/venv" ]; then
    check_result "PASS" "Virtual environment exists"

    # Check if we can activate venv
    if source /opt/kdp-formatter/venv/bin/activate 2>/dev/null; then
        check_result "PASS" "Virtual environment can be activated"

        # Check Python version in venv
        venv_python=$(python --version 2>&1 | grep -oP '\d+\.\d+')
        if [[ $(echo "$venv_python >= 3.11" | bc -l) -eq 1 ]]; then
            check_result "PASS" "Python in venv: $venv_python"
        else
            check_result "FAIL" "Python in venv too old: $venv_python"
        fi

        # Check critical imports
        echo "Testing Python imports..."
        python3 -c "
import sys
imports = [
    ('fastapi', 'FastAPI'),
    ('uvicorn', 'ASGI server'),
    ('pydantic', 'Data validation'),
    ('weasyprint', 'PDF generation'),
    ('PIL', 'Image processing'),
    ('pdfminer.six', 'PDF text extraction'),
    ('google.cloud.secretmanager', 'Secret Manager'),
    ('firebase_admin', 'Firebase SDK'),
    ('stripe', 'Payment processing'),
    ('openai', 'AI API'),
    ('sqlalchemy', 'Database ORM'),
    ('alembic', 'Database migrations')
]

for module, description in imports:
    try:
        __import__(module.replace('.', '_') if '.' in module else module)
        print(f'✓ {description}')
    except ImportError as e:
        print(f'✗ {description}: Import failed')
        sys.exit(1)
" && check_result "PASS" "All critical Python imports successful" || check_result "FAIL" "Some Python imports failed"

        deactivate
    else
        check_result "FAIL" "Cannot activate virtual environment"
    fi
else
    check_result "FAIL" "Virtual environment not found"
fi

echo ""
echo "Checking configuration..."
echo "-----------------------"

# Check .env file
if [ -f "/opt/kdp-formatter/.env" ]; then
    check_result "PASS" ".env file exists"
    # Check if GCP_PROJECT_ID is set (not default)
    if grep -q "^GCP_PROJECT_ID=your-gcp-project-id" /opt/kdp-formatter/.env; then
        check_result "FAIL" "GCP_PROJECT_ID not configured in .env"
    else
        check_result "PASS" "GCP_PROJECT_ID appears to be configured"
    fi
else
    check_result "FAIL" ".env file not found (run: cp .env.example .env)"
fi

# Check versions file
if [ -f "/opt/kdp-formatter/VERSIONS.txt" ]; then
    check_result "PASS" "Versions file exists: VERSIONS.txt"
    echo "Installed versions:"
    cat /opt/kdp-formatter/VERSIONS.txt
else
    check_result "FAIL" "Versions file not found: VERSIONS.txt"
fi

echo ""
echo "Checking systemd service..."
echo "--------------------------"

# Check service file
if [ -f "/etc/systemd/system/kdp-formatter.service" ]; then
    check_result "PASS" "Systemd service file exists"
else
    check_result "FAIL" "Systemd service file not found"
fi

# Check service status
if systemctl is-enabled kdp-formatter &>/dev/null; then
    check_result "PASS" "Service is enabled"
else
    check_result "FAIL" "Service is not enabled"
fi

# Check if service is running
if systemctl is-active kdp-formatter &>/dev/null; then
    check_result "PASS" "Service is running"
else
    check_result "FAIL" "Service is not running"
fi

echo ""
echo "Checking application..."
echo "----------------------"

# Test health endpoint
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    response=$(curl -s http://localhost:8001/health)
    if echo "$response" | grep -q '"status": "ok"'; then
        check_result "PASS" "Health endpoint responding correctly"
    else
        check_result "FAIL" "Health endpoint not responding properly: $response"
    fi
else
    check_result "FAIL" "Cannot reach health endpoint at http://localhost:8001/health"
fi

echo ""
echo "Resource usage check..."
echo "----------------------"

# Check memory usage if service is running
if systemctl is-active kdp-formatter &>/dev/null; then
    memory=$(systemctl show kdp-formatter --property=MemoryCurrent --value 2>/dev/null)
    if [ -n "$memory" ]; then
        memory_mb=$((memory / 1024 / 1024))
        check_result "PASS" "Service memory usage: ${memory_mb}MB"
    fi
fi

# Check disk usage
disk_usage=$(df -h /opt/kdp-formatter | tail -n 1 | awk '{print $5}')
check_result "PASS" "Disk usage for /opt/kdp-formatter: $disk_usage"

echo ""
echo "=== Verification Summary ==="
echo "Total checks: $total_checks"
echo "Passed: $passed_checks"
echo "Failed: $failed_checks"

if [ $failed_checks -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Installation appears successful.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test the application: curl http://localhost:8001/"
    echo "2. Check logs: sudo journalctl -u kdp-formatter -f"
    echo "3. Configure Google Cloud secrets if not done already"
    echo "4. Set up Nginx reverse proxy (Phase 11)"
    exit 0
else
    echo -e "${RED}✗ $failed_checks check(s) failed. Please review the errors above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "- Run 'sudo bash scripts/install_system_deps.sh' if system deps are missing"
    echo "- Run 'bash scripts/setup_vm.sh' if Python environment is incomplete"
    echo "- Check 'docs/DEPLOYMENT.md' for detailed troubleshooting"
    exit 1
fi
