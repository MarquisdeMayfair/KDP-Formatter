# KDP Formatter - Deployment Guide

## Prerequisites

### VM Requirements
- Ubuntu 24.04 (Noble) VM with 4GB RAM
- SSH access: `ssh mrdeansgate@35.234.146.243` (or appropriate user for tax-treaty-server)
- Google Cloud project with Secret Manager API enabled
- Service account with Secret Manager access

### Google Cloud Setup
- GCP project created and configured
- Secret Manager API enabled
- Service account created with appropriate permissions
- VM has access to Google Cloud (service account attached or key configured)

### Domain Configuration
- Domain `kdppublish.newmarylebonepress.com` configured
- DNS pointing to VM IP address

## Step 1: Transfer Files to VM

### Option A: Using scp/rsync (Recommended)
```bash
# From your local machine
rsync -avz --exclude 'venv' . mrdeansgate@35.234.146.243:/tmp/kdp-formatter/
```

### Option B: Using git (if repository exists)
```bash
# On the VM
cd /tmp
git clone <repository-url> kdp-formatter
```

## Step 2: Install System Dependencies

SSH into the VM and run the system dependencies installation script:

```bash
# SSH into VM
ssh mrdeansgate@35.234.146.243

# Run system dependencies installation (requires sudo)
sudo bash /tmp/kdp-formatter/scripts/install_system_deps.sh
```

This script will:
- Update package lists
- Install Python 3.11+
- Install Pandoc, Tesseract OCR, ImageMagick, Ghostscript
- Install WeasyPrint system libraries
- Install Java and epubcheck
- Create the `kdp-formatter` user
- Set up directory structure at `/opt/kdp-formatter`
- Log all installed versions to `/opt/kdp-formatter/VERSIONS.txt`

Verify installations:
```bash
# Check installed versions
cat /opt/kdp-formatter/VERSIONS.txt

# Test key dependencies
pandoc --version
tesseract --version
convert --version
gs --version
java -jar /opt/epubcheck/epubcheck.jar --version
```

## Step 3: Set Up Python Environment

Move files to the application directory and set up the Python environment:

```bash
# Move files to final location
sudo mv /tmp/kdp-formatter/* /opt/kdp-formatter/

# Change ownership to kdp-formatter user
sudo chown -R kdp-formatter:kdp-formatter /opt/kdp-formatter

# Run setup script as kdp-formatter user
sudo -u kdp-formatter bash /opt/kdp-formatter/scripts/setup_vm.sh
```

This script will:
- Create Python virtual environment
- Install all Python dependencies from `requirements.txt`
- Create `.env.example` file
- Set proper permissions
- Create log files
- Test critical imports

## Step 4: Configure Google Cloud Secrets

Create the required secrets in Google Cloud Secret Manager:

### Using gcloud CLI (from your local machine or VM with auth)

```bash
# Set your project
export GCP_PROJECT_ID=your-project-id

# Create OpenAI API key secret
echo -n "sk-your-openai-key-here" | gcloud secrets create kdp-formatter-openai-key --data-file=-

# Create Stripe secret key
echo -n "sk_live_your-stripe-key-here" | gcloud secrets create kdp-formatter-stripe-key --data-file=-

# Create Stripe webhook secret
echo -n "whsec_your-webhook-secret-here" | gcloud secrets create kdp-formatter-stripe-webhook --data-file=-

# Create Firebase credentials (JSON as string)
gcloud secrets create kdp-formatter-firebase-creds --data-file=firebase-service-account.json
```

### Verify Secrets
```bash
# Test secret access
gcloud secrets versions access latest --secret="kdp-formatter-openai-key"
```

## Step 5: Configure Environment Variables

Set up the environment configuration:

```bash
# Navigate to application directory
cd /opt/kdp-formatter

# Copy environment template
cp .env.example .env

# Edit .env file with your GCP project ID
nano .env
# Change: GCP_PROJECT_ID=your-gcp-project-id

# Set proper permissions
chmod 600 .env
```

## Step 6: Install and Start Systemd Service

Configure the systemd service for automatic startup:

```bash
# Copy service file to systemd directory
sudo cp /opt/kdp-formatter/deployment/kdp-formatter.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable kdp-formatter

# Start the service
sudo systemctl start kdp-formatter

# Check service status
sudo systemctl status kdp-formatter
```

## Step 7: Verify Installation

Run the verification script to ensure everything is working:

```bash
# Run verification script
bash /opt/kdp-formatter/scripts/verify_installation.sh
```

Test the application:

```bash
# Test health endpoint
curl http://localhost:8001/health

# Check application logs
sudo journalctl -u kdp-formatter -f
```

## Service Management

### Basic Commands
```bash
# Check status
sudo systemctl status kdp-formatter

# View logs
sudo journalctl -u kdp-formatter -f

# Restart service
sudo systemctl restart kdp-formatter

# Stop service
sudo systemctl stop kdp-formatter

# Start service
sudo systemctl start kdp-formatter
```

### Monitoring Resource Usage
```bash
# Check memory usage
systemctl show kdp-formatter --property=MemoryCurrent

# Check CPU usage
systemctl show kdp-formatter --property=CPUUsageNSec

# Check disk usage
df -h /opt/kdp-formatter
```

## Troubleshooting

### Common Issues

#### Service fails to start
```bash
# Check service status and logs
sudo systemctl status kdp-formatter
sudo journalctl -u kdp-formatter -n 50

# Check if port 8001 is in use
sudo lsof -i :8001
```

#### Permission errors
```bash
# Check directory permissions
ls -la /opt/kdp-formatter/

# Check user exists
id kdp-formatter

# Fix ownership if needed
sudo chown -R kdp-formatter:kdp-formatter /opt/kdp-formatter
```

#### Python import errors
```bash
# Activate virtual environment
source /opt/kdp-formatter/venv/bin/activate

# Test imports manually
python3 -c "import fastapi, weasyprint, google.cloud.secretmanager"

# Check pip list
pip list
```

#### Secret Manager access issues
```bash
# Test authentication
gcloud auth list

# Test secret access
gcloud secrets versions access latest --secret="kdp-formatter-openai-key"
```

### Log Locations
- Application logs: `/opt/kdp-formatter/logs/app.log`
- Systemd logs: `journalctl -u kdp-formatter`
- Error logs: `/opt/kdp-formatter/logs/error.log`
- Installation versions: `/opt/kdp-formatter/VERSIONS.txt`

### Rollback Procedures
```bash
# Stop service
sudo systemctl stop kdp-formatter

# Backup current installation
cp -r /opt/kdp-formatter /opt/kdp-formatter.backup

# Revert to previous version (if available)
# ... deployment steps ...

# Restart service
sudo systemctl start kdp-formatter
```

## Next Steps

1. **Configure Nginx Reverse Proxy** (Phase 11)
   - Install Nginx
   - Configure SSL certificate
   - Set up reverse proxy to port 8001

2. **Set up SSL Certificate**
   - Use Let's Encrypt or GCP managed certificates
   - Configure HTTPS for `kdppublish.newmarylebonepress.com`

3. **Test External Access**
   - Test from external network
   - Verify domain resolution
   - Test with real file uploads

4. **Monitoring and Alerts**
   - Set up log aggregation
   - Configure health checks
   - Set up alerting for service failures

## Security Considerations

- Service runs as non-root `kdp-formatter` user
- Resource limits prevent resource exhaustion
- Secrets stored in Google Cloud Secret Manager
- File uploads restricted to 50MB
- No direct internet access for application user
- Systemd security hardening applied
