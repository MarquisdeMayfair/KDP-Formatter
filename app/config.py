"""
KDP Formatter - Configuration Module
This module handles all application configuration using Pydantic settings and Google Cloud Secret Manager.
"""

import os
import functools
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and Google Cloud Secret Manager."""

    # Google Cloud Configuration (optional for development)
    gcp_project_id: Optional[str] = Field(None, description="Google Cloud Project ID")

    # Secret Manager Secret Names
    openai_secret_name: str = "kdp-formatter-openai-key"
    stripe_secret_name: str = "kdp-formatter-stripe-key"
    stripe_webhook_secret_name: str = "kdp-formatter-stripe-webhook"
    firebase_credentials_secret_name: str = "kdp-formatter-firebase-creds"

    # Application Configuration
    app_port: int = 8001
    upload_dir: str = "/opt/kdp-formatter/uploads"
    output_dir: str = "app/output"  # Local development default
    max_upload_size: int = 52428800  # 50MB

    # Database
    database_url: str = "sqlite:///./kdp_formatter.db"

    # Environment
    environment: str = "development"

    # Development mode settings
    development_mode: bool = Field(default=True, description="Enable development mode (disables GCP secrets)")
    debug: bool = Field(default=False, description="Enable debug logging")
    cors_origins: list = Field(default_factory=lambda: ["http://localhost:8001", "http://127.0.0.1:8001"], description="Allowed CORS origins")

    # Local development secrets (fallback when not using GCP)
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for local development")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-detect development mode
        if self.environment != "production" or self._is_local_development():
            self.development_mode = True
        else:
            self.development_mode = False

    def _is_local_development(self) -> bool:
        """Check if running in local development environment."""
        import os
        # Check for .env file
        if os.path.exists(".env"):
            return True
        # Check for DEVELOPMENT environment variable
        if os.getenv("DEVELOPMENT", "").lower() in ("true", "1", "yes"):
            return True
        # Check if we're not in a containerized environment
        if not os.path.exists("/opt/kdp-formatter"):
            return True
        return False


@functools.lru_cache()
def get_secret(secret_name: str) -> str:
    """
    Retrieve a secret from Google Cloud Secret Manager or local environment.

    In development mode, falls back to environment variables from .env file.
    In production mode, uses Google Cloud Secret Manager.

    Args:
        secret_name: Name of the secret to retrieve

    Returns:
        The secret value as a string

    Raises:
        Exception: If secret retrieval fails
    """
    settings = get_settings()

    # In development mode, try environment variables first
    if settings.development_mode:
        # Map secret names to environment variable names
        env_mapping = {
            "kdp-formatter-openai-key": "OPENAI_API_KEY",
            "kdp-formatter-stripe-key": "STRIPE_SECRET_KEY",
            "kdp-formatter-stripe-webhook": "STRIPE_WEBHOOK_SECRET",
            "kdp-formatter-firebase-creds": "FIREBASE_CREDENTIALS"
        }

        env_var = env_mapping.get(secret_name)
        if env_var:
            import os
            value = os.getenv(env_var)
            if value:
                print(f"Using {env_var} from environment (development mode)")
                return value

        # Special handling for OpenAI key from settings
        if secret_name == "kdp-formatter-openai-key" and settings.openai_api_key:
            print("Using OpenAI API key from settings (development mode)")
            return settings.openai_api_key

        print(f"Secret '{secret_name}' not found in environment (development mode)")
        raise Exception(f"Secret '{secret_name}' not available in development mode")

    # Production mode: use Google Cloud Secret Manager
    try:
        try:
            from google.cloud import secretmanager
        except ImportError as e:
            raise Exception(f"google-cloud-secretmanager package is required for production mode but not installed: {e}")

        if not settings.gcp_project_id:
            raise Exception("GCP_PROJECT_ID not configured for production mode")

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{settings.gcp_project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        # Log error but don't expose sensitive details
        print(f"Failed to retrieve secret '{secret_name}': {type(e).__name__}")
        raise


@functools.lru_cache()
def get_settings() -> Settings:
    """
    Get application settings singleton instance.

    This function caches the settings to avoid reloading on every call.

    Returns:
        Settings instance with all configuration loaded
    """
    return Settings()


# Configuration Setup
#
# DEVELOPMENT MODE (Local Testing):
# 1. Create a .env file in the project root
# 2. Add environment variables:
#    ENVIRONMENT=development
#    OPENAI_API_KEY=sk-your-openai-key-here  # Optional, for AI detection
#    DEBUG=true                              # Optional, verbose logging
#
# The app automatically detects development mode when:
# - ENVIRONMENT is not "production"
# - A .env file exists in the project root
# - Running outside /opt/kdp-formatter directory
# - DEVELOPMENT=true environment variable is set
#
# PRODUCTION MODE (Google Cloud):
# 1. Enable Secret Manager API in your GCP project
# 2. Create a service account with Secret Manager access
# 3. Attach the service account to your VM or use a service account key
# 4. Create the following secrets:
#    - kdp-formatter-openai-key: Your OpenAI API key
#    - kdp-formatter-stripe-key: Your Stripe secret key
#    - kdp-formatter-stripe-webhook: Your Stripe webhook secret
#    - kdp-formatter-firebase-creds: Firebase service account JSON (as string)
#
# 5. Set environment variables:
#    GCP_PROJECT_ID=your-project-id
#    ENVIRONMENT=production
#
# Secret formats:
# - OpenAI: "sk-..."
# - Stripe keys: "sk_live_..." or "sk_test_..."
# - Stripe webhook: "whsec_..."
# - Firebase: Full JSON service account credentials as a string
#
# Security note: Never commit .env files or secrets to version control!
