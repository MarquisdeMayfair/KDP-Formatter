#!/bin/bash

# KDP Formatter - System Dependencies Installation Script
# This script installs all required system-level dependencies for the KDP Formatter application
# Supports both PDF and EPUB generation with validation tools
# Run with: sudo bash scripts/install_system_deps.sh

set -euo pipefail
IFS=$'\n\t'

echo "=== KDP Formatter - System Dependencies Installation ==="
echo "This script will install all required system packages."
echo "It requires sudo privileges and will take several minutes."
echo ""

# Helper functions
has_cmd() { command -v "$1" >/dev/null 2>&1; }
has_pkg() { dpkg -s "$1" >/dev/null 2>&1; }
ensure_pkg() { has_pkg "$1" || apt install -y "$1"; }

# Function to log versions
log_version() {
    local package=$1
    local version_cmd=$2
    local expected="${3:-}"
    local cmd_name="${version_cmd%% *}"

    echo "Checking $package version..."
    if command -v "$cmd_name" &> /dev/null; then
        local version=$(bash -lc "$version_cmd" 2>&1 | head -n 1)
        echo "$package: $version" >> /tmp/versions_log.txt
        echo "✓ $package installed: $version"
        if [[ -n "$expected" ]] && [[ "$version" != *"$expected"* ]]; then
            echo "⚠ Warning: Expected $expected, got $version"
        fi
    else
        echo "✗ Failed to verify $package installation"
        return 1
    fi
}

# Initialize version log
echo "KDP Formatter - Installed Versions" > /tmp/versions_log.txt
echo "Installation Date: $(date)" >> /tmp/versions_log.txt
echo "" >> /tmp/versions_log.txt

echo "Step 1: Updating package lists..."
apt update
echo "✓ Package lists updated"
echo ""

echo "Step 2: Installing Python 3.11+..."
ensure_pkg python3.11
ensure_pkg python3.11-venv
ensure_pkg python3.11-dev
ensure_pkg python3-pip
log_version "Python" "python3.11 --version" "3.11"
echo ""

echo "Step 3: Installing Pandoc..."
ensure_pkg pandoc
log_version "Pandoc" "pandoc --version" "3."
echo ""

echo "Step 4: Installing Tesseract OCR..."
ensure_pkg tesseract-ocr
ensure_pkg tesseract-ocr-eng
log_version "Tesseract" "tesseract --version" "5."
echo ""

echo "Step 5: Installing ImageMagick..."
ensure_pkg imagemagick
log_version "ImageMagick" "convert --version" "7."
echo ""

echo "Step 6: Installing Ghostscript..."
ensure_pkg ghostscript
log_version "Ghostscript" "gs --version" "10."
echo ""

echo "Step 7: Installing system libraries for WeasyPrint..."
ensure_pkg libpango-1.0-0
ensure_pkg libpangocairo-1.0-0
ensure_pkg libgdk-pixbuf2.0-0
ensure_pkg libffi-dev
ensure_pkg shared-mime-info
echo "✓ WeasyPrint system libraries installed"
echo ""

echo "Step 8: Installing Poppler utils for PDF validation..."
ensure_pkg poppler-utils
log_version "pdffonts" "pdffonts -v" ""
log_version "pdfinfo" "pdfinfo -v" ""
echo ""

echo "Step 9: Installing Java and epubcheck for EPUB validation..."
ensure_pkg default-jre
log_version "Java" "java -version" ""

# Download and install epubcheck
EPUBCHECK_DIR=/opt/epubcheck
EPUBCHECK_JAR="$EPUBCHECK_DIR/epubcheck.jar"
EPUBCHECK_VERSION_DESIRED="5.1.0"
mkdir -p "$EPUBCHECK_DIR"
if [ -f "$EPUBCHECK_JAR" ]; then
  current_ver=$(java -jar "$EPUBCHECK_JAR" --version 2>&1 | awk '{print $2}')
else
  current_ver=""
fi
if [ "$current_ver" != "$EPUBCHECK_VERSION_DESIRED" ]; then
  echo "Downloading epubcheck $EPUBCHECK_VERSION_DESIRED..."
  tmp=/tmp/epubcheck-${EPUBCHECK_VERSION_DESIRED}
  cd /tmp
  wget -q https://github.com/w3c/epubcheck/releases/download/v${EPUBCHECK_VERSION_DESIRED}/epubcheck-${EPUBCHECK_VERSION_DESIRED}.zip
  unzip -q epubcheck-${EPUBCHECK_VERSION_DESIRED}.zip
  install -m 0755 epubcheck-${EPUBCHECK_VERSION_DESIRED}/epubcheck.jar "$EPUBCHECK_JAR"

  # Create wrapper script instead of symlink
  cat > /usr/local/bin/epubcheck << 'EOF'
#!/bin/bash
exec java -jar /opt/epubcheck/epubcheck.jar "$@"
EOF
  chmod +x /usr/local/bin/epubcheck
else
  echo "✓ epubcheck $EPUBCHECK_VERSION_DESIRED already installed"
fi
log_version "epubcheck" "java -jar /opt/epubcheck/epubcheck.jar --version" "5."
echo ""

echo "Note: Kindle Previewer 3 for EPUB device testing must be installed manually:"
echo "  - Download from: https://kdp.amazon.com/en_US/help/topic/G202131170"
echo "  - Windows/Mac only (GUI application, no CLI version available)"
echo "  - Required for comprehensive EPUB compatibility testing"
echo ""

echo "Step 10: Creating application user..."
if ! id -u kdp-formatter &>/dev/null; then
    useradd -r -s /bin/bash -d /opt/kdp-formatter kdp-formatter
    echo "✓ Created kdp-formatter user"
else
    echo "✓ kdp-formatter user already exists"
fi
echo ""

echo "Step 12: Creating directory structure..."
mkdir -p /opt/kdp-formatter/{app,uploads,outputs,logs}
chown -R kdp-formatter:kdp-formatter /opt/kdp-formatter
chmod 755 /opt/kdp-formatter
chmod 700 /opt/kdp-formatter/uploads /opt/kdp-formatter/outputs
echo "✓ Directory structure created and permissions set"
echo ""

echo "Step 13: Logging installed versions..."
cp /tmp/versions_log.txt /opt/kdp-formatter/VERSIONS.txt
echo "✓ Versions logged to /opt/kdp-formatter/VERSIONS.txt"
echo ""

echo "=== Installation Complete ==="
echo ""
echo "Installed components:"
echo "✓ PDF generation: WeasyPrint, Pango, Cairo"
echo "✓ Document conversion: Pandoc"
echo "✓ PDF validation: Poppler utils (pdffonts, pdfinfo)"
echo "✓ EPUB validation: epubcheck (Java-based)"
echo "✓ OCR support: Tesseract"
echo "✓ Image processing: ImageMagick, Ghostscript"
echo ""
echo "Manual installations required:"
echo "• Kindle Previewer 3 (for EPUB device testing):"
echo "  https://kdp.amazon.com/en_US/help/topic/G202131170"
echo ""
echo "Installed versions summary:"
cat /opt/kdp-formatter/VERSIONS.txt
echo ""
echo "Next steps:"
echo "1. Run 'bash scripts/setup_vm.sh' to set up Python environment"
echo "2. Configure Google Cloud Secret Manager secrets"
echo "3. Copy systemd service file and start the service"
echo ""
echo "For detailed deployment instructions, see docs/DEPLOYMENT.md"
