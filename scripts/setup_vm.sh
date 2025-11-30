#!/bin/bash

# KDP Formatter - VM Setup Script
# This script sets up the Python virtual environment and installs application dependencies
# Run with: sudo -u kdp-formatter bash scripts/setup_vm.sh

set -e  # Exit on any error

echo "=== KDP Formatter - VM Setup ==="
echo "Setting up Python virtual environment and installing dependencies..."
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3.11 &> /dev/null; then
    echo "✗ Python 3.11 not found. Run install_system_deps.sh first."
    exit 1
fi

if [ ! -d "/opt/kdp-formatter" ]; then
    echo "✗ /opt/kdp-formatter directory not found. Run install_system_deps.sh first."
    exit 1
fi

echo "✓ Prerequisites check passed"
echo ""

# Navigate to application directory
cd /opt/kdp-formatter

echo "Step 1: Creating virtual environment..."
python3.11 -m venv venv
echo "✓ Virtual environment created"
echo ""

echo "Step 2: Activating virtual environment and upgrading pip..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
echo "✓ Pip upgraded"
echo ""

echo "Step 3: Installing Python dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo "✗ requirements.txt not found in /opt/kdp-formatter"
    exit 1
fi

pip install -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

echo "Step 4: Verifying installations..."
pip list
echo ""

echo "Step 5: Creating .env.example file..."
cat > .env.example << 'EOF'
# Google Cloud Configuration
GCP_PROJECT_ID=your-gcp-project-id

# Secret Manager Secret Names
OPENAI_SECRET_NAME=kdp-formatter-openai-key
STRIPE_SECRET_NAME=kdp-formatter-stripe-key
STRIPE_WEBHOOK_SECRET_NAME=kdp-formatter-stripe-webhook
FIREBASE_CREDENTIALS_SECRET_NAME=kdp-formatter-firebase-creds

# Application Configuration
APP_PORT=8001
UPLOAD_DIR=/opt/kdp-formatter/uploads
OUTPUT_DIR=/opt/kdp-formatter/outputs
MAX_UPLOAD_SIZE=52428800

# Database
DATABASE_URL=sqlite:///./kdp_formatter.db

# Environment
ENVIRONMENT=production
EOF
echo "✓ .env.example created"
echo ""

echo "Step 6: Setting permissions..."
chmod 755 app
chmod 700 uploads outputs
echo "✓ Permissions set"
echo ""

echo "Step 7: Creating log file..."
touch logs/app.log
chmod 644 logs/app.log
echo "✓ Log file created"
echo ""

echo "Step 8: Testing critical imports..."
python -c "
try:
    import fastapi
    import uvicorn
    import pydantic
    import weasyprint
    try:
        import pdfminer
        from pdfminer.high_level import extract_text  # smoke test
    except Exception as e:
        print(f'pdfminer import failed: {e}')
        raise
    import PIL
    import google.cloud.secretmanager
    import firebase_admin
    import stripe
    import openai
    import sqlalchemy
    import alembic
    print('✓ All critical imports successful')
except ImportError as e:
    print(f'✗ Import error: {e}')
    exit(1)
"
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Configure Google Cloud Secret Manager secrets:"
echo "   - kdp-formatter-openai-key"
echo "   - kdp-formatter-stripe-key"
echo "   - kdp-formatter-stripe-webhook"
echo "   - kdp-formatter-firebase-creds"
echo ""
echo "2. Copy .env.example to .env and configure:"
echo "   cp .env.example .env"
echo "   # Edit .env with your GCP project ID"
echo ""
echo "3. Copy systemd service file:"
echo "   sudo cp deployment/kdp-formatter.service /etc/systemd/system/"
echo ""
echo "4. Enable and start the service:"
echo "   sudo systemctl enable kdp-formatter"
echo "   sudo systemctl start kdp-formatter"
echo ""
echo "5. Verify installation:"
echo "   bash scripts/verify_installation.sh"
echo ""
echo "For detailed deployment instructions, see docs/DEPLOYMENT.md"
