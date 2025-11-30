# Production Code Directory

This directory will contain production-ready application code migrated and refactored from the POC implementations in `/poc`. Currently empty as we're still in the POC validation phase, but establishing the structure now ensures a clear separation between proof-of-concept code (`/poc`) and production code (`/src`).

## Planned Structure

The production implementation will follow this structure:

- `/src/api/` - FastAPI application and endpoints
- `/src/converters/` - Production document converters (refactored from `/poc/converters.py`)
- `/src/renderers/` - PDF and EPUB renderers (refactored from `/poc/renderer.py` and `/poc/epub_generator.py`)
- `/src/validators/` - Document validators (refactored from `/poc/validator.py` and `/poc/epub_validator.py`)
- `/src/ai/` - AI structure detection (refactored from `/poc/ai_structure_detector.py`)
- `/src/models/` - Database models and schemas
- `/src/utils/` - Shared utilities and helpers
- `/src/config.py` - Production configuration management

## Migration Plan

After successful POC validation with KDP Preview, the production implementation will:

1. **Refactor POC code** - Move working POC implementations from `/poc` to `/src` with proper error handling, logging, and production hardening
2. **Implement FastAPI backend** - Create RESTful APIs for document upload, processing, and download
3. **Add job queue** - Implement background processing for large documents using Celery/Redis
4. **Database integration** - Add PostgreSQL models for user accounts, document history, and processing metadata
5. **Authentication** - Integrate Firebase authentication for user management
6. **Payment processing** - Add Stripe integration for subscription billing
7. **Monitoring** - Implement proper logging, metrics, and health checks

## Development Timeline

- **Phase 6**: Production Backend - Migrate POC to FastAPI application
- **Phase 7**: Authentication - Firebase integration
- **Phase 8**: Payments - Stripe subscription management
- **Phase 9**: Deployment - Nginx, PostgreSQL, Redis setup
- **Phase 10**: Monitoring - Logging, metrics, alerting

## Dependencies

Production code will use the same core dependencies as POC:
- WeasyPrint for PDF rendering
- Pandoc for document conversion
- OpenAI API for structure detection
- FastAPI for web framework
- PostgreSQL for data persistence
- Redis for job queue and caching

Additional production dependencies will include:
- SQLAlchemy for ORM
- Alembic for database migrations
- Celery for background tasks
- Firebase Admin SDK for authentication
- Stripe SDK for payments
- Sentry for error monitoring

## Testing

Unit tests, integration tests, and end-to-end tests will be located in `/tests` and will achieve >80% code coverage. All production code must pass CI/CD pipelines before deployment.

See `/tests/README.md` for testing conventions and structure.

