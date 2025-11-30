# KDP Formatter - Google Cloud Setup Guide

## Overview

This guide explains how to set up Google Cloud Secret Manager for secure storage of API keys and credentials. The KDP Formatter application uses Secret Manager to avoid storing sensitive information in code or environment variables.

### Why Secret Manager?
- Secure storage of API keys, passwords, and certificates
- No secrets in application code or version control
- Centralized secret management across environments
- Audit logging for all secret access
- Fine-grained access controls via IAM

### Required Secrets

The application requires the following secrets to be created:

1. **`kdp-formatter-openai-key`** - OpenAI API key for AI-powered document structure detection
2. **`kdp-formatter-stripe-key`** - Stripe secret key for payment processing
3. **`kdp-formatter-stripe-webhook`** - Stripe webhook secret for payment verification
4. **`kdp-formatter-firebase-creds`** - Firebase service account JSON for authentication

## Step 1: Enable Secret Manager API

### Using Google Cloud Console
1. Navigate to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Go to "APIs & Services" > "Library"
4. Search for "Secret Manager API"
5. Click "Enable"

### Using gcloud CLI
```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com
```

## Step 2: Create Service Account

Create a dedicated service account for the KDP Formatter application:

```bash
# Create service account
gcloud iam service-accounts create kdp-formatter \
    --display-name="KDP Formatter Service Account" \
    --description="Service account for KDP Formatter SaaS application"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:kdp-formatter@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Optional: Grant more granular permissions
# gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
#     --member="serviceAccount:kdp-formatter@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
#     --role="roles/secretmanager.viewer"
```

## Step 3: Create Secrets

### Method 1: Using gcloud CLI (Recommended)

#### OpenAI API Key
```bash
echo -n "sk-your-actual-openai-api-key-here" | \
gcloud secrets create kdp-formatter-openai-key --data-file=-
```

#### Stripe Secret Key
```bash
echo -n "sk_live_your-actual-stripe-secret-key-here" | \
gcloud secrets create kdp-formatter-stripe-key --data-file=-
```

#### Stripe Webhook Secret
```bash
echo -n "whsec_your-actual-stripe-webhook-secret-here" | \
gcloud secrets create kdp-formatter-stripe-webhook --data-file=-
```

#### Firebase Credentials
```bash
# If you have the JSON file locally
gcloud secrets create kdp-formatter-firebase-creds --data-file=firebase-service-account.json

# Or create from JSON content
gcloud secrets create kdp-formatter-firebase-creds --data-file=- <<EOF
{
  "type": "service_account",
  "project_id": "your-firebase-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "firebase-adminsdk@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
EOF
```

### Method 2: Using Google Cloud Console

1. Go to [Secret Manager](https://console.cloud.google.com/security/secret-manager)
2. Click "Create Secret"
3. Enter secret name (e.g., `kdp-formatter-openai-key`)
4. Enter secret value
5. Click "Create Secret"

Repeat for each required secret.

## Step 4: Configure VM Authentication

### Option A: Attach Service Account to VM (Recommended)

Attach the service account directly to your VM instance:

```bash
gcloud compute instances set-service-account tax-treaty-server-restored \
    --service-account=kdp-formatter@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --scopes=cloud-platform \
    --zone=europe-west4-b
```

**Pros:**
- No service account keys stored on VM
- Automatic credential management
- More secure than key files

**Cons:**
- Requires VM restart for changes to take effect
- Service account applies to entire VM

### Option B: Service Account Key File

Create and download a service account key (less secure):

```bash
# Create key file
gcloud iam service-accounts keys create ~/kdp-formatter-key.json \
    --iam-account=kdp-formatter@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Copy to VM
scp ~/kdp-formatter-key.json mrdeansgate@VM_IP:/opt/kdp-formatter/

# Set environment variable in .env
echo 'GOOGLE_APPLICATION_CREDENTIALS=/opt/kdp-formatter/kdp-formatter-key.json' >> /opt/kdp-formatter/.env
```

**Note:** Never commit key files to version control. Use Option A when possible.

## Step 5: Test Secret Access

### Test from Local Machine
```bash
# Authenticate
gcloud auth login

# Test secret access
gcloud secrets versions access latest --secret="kdp-formatter-openai-key"
```

### Test from VM
```bash
# SSH into VM
ssh mrdeansgate@VM_IP

# Test secret access (requires authentication)
gcloud secrets versions access latest --secret="kdp-formatter-openai-key"
```

### Test from Python Application
```python
# On VM, activate virtual environment and test
cd /opt/kdp-formatter
source venv/bin/activate

python3 -c "
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = f'projects/YOUR_PROJECT_ID/secrets/kdp-formatter-openai-key/versions/latest'
response = client.access_secret_version(request={'name': name})
print('Secret retrieved successfully:', response.payload.data.decode('UTF-8')[:10] + '...')
"
```

## Security Best Practices

### IAM Permissions
- Use principle of least privilege
- Grant only `roles/secretmanager.secretAccessor` for production
- Use separate service accounts for different environments
- Regularly rotate service account keys (if used)

### Secret Management
- Never store secrets in code or version control
- Use different secrets for different environments
- Rotate secrets regularly
- Enable audit logging for secret access

### VM Security
- Use OS Login for VM access
- Enable VPC Service Controls
- Use private IPs when possible
- Regularly update VM OS and packages

## Troubleshooting

### Permission Denied Errors
```bash
# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --filter="bindings.members:serviceAccount:kdp-formatter@YOUR_PROJECT_ID.iam.gserviceaccount.com"

# Check if API is enabled
gcloud services list --filter="secretmanager"

# Test authentication
gcloud auth list
```

### Secret Not Found Errors
```bash
# List all secrets
gcloud secrets list

# Check secret versions
gcloud secrets versions list kdp-formatter-openai-key

# Verify secret name spelling
gcloud secrets describe kdp-formatter-openai-key
```

### Authentication Issues
```bash
# For service account key method
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# For attached service account
gcloud auth application-default login

# Check current authentication
gcloud auth list
```

### Common Issues

#### "Request had insufficient authentication scopes"
- VM needs `cloud-platform` scope
- Reattach service account with proper scopes

#### "Secret not found"
- Check secret name matches exactly
- Verify project ID is correct
- Ensure secret exists in the correct project

#### "Permission denied"
- Service account lacks `secretmanager.secretAccessor` role
- API not enabled for project
- Authentication not configured properly

## Cost Considerations

- Secret Manager is free for storage and access (within limits)
- First 10,000 access operations per month are free
- Additional operations cost ~$0.03 per 10,000 operations
- No storage costs for reasonable number of secrets

## Monitoring and Audit

### Enable Audit Logging
```bash
# Enable Secret Manager audit logs
gcloud logging sinks create kdp-secret-audit \
    logging.googleapis.com/projects/YOUR_PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity \
    --log-filter='resource.type="secretmanager.googleapis.com/Secret"'
```

### Monitor Access
```bash
# View recent secret access
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" \
    --limit=10 \
    --format="table(timestamp,severity,resource.labels.secret_id,protoPayload.authenticationInfo.principalEmail)"
```

## Migration and Backup

### Export Secrets
```bash
# Export all secrets (for backup/migration)
gcloud secrets list --format="value(name)" | \
xargs -I {} sh -c 'echo "Secret: {}"; gcloud secrets versions access latest --secret="$1"' _ {}
```

### Import Secrets
```bash
# Import secrets to new project
gcloud secrets create new-secret-name --data-file=secret-value.txt --project=new-project-id
```

This setup ensures secure, centralized management of all application secrets with proper access controls and audit trails.
