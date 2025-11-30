# KDP Formatter Repository Structure

This document provides a complete overview of the repository organization and the purpose of each directory and key file.

## Root Directory

```
KDP Formatter/
├── .git/                    # Git repository metadata (created by git init)
├── .github/                 # GitHub-specific files (issue templates, PR templates)
├── .gitignore              # Git ignore patterns
├── LICENSE                 # Project license (MIT)
├── README.md               # Main project documentation
├── CONTRIBUTING.md         # Contribution guidelines
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
├── poc/                    # Proof of Concept implementation (CURRENT PHASE)
├── src/                    # Production code (FUTURE)
├── tests/                  # Unit and integration tests (FUTURE)
├── docs/                   # Documentation and protocols
├── test_data/             # Sample manuscripts for testing
├── scripts/               # Setup and deployment scripts
├── app/                   # FastAPI application skeleton
└── deployment/            # Systemd service files
```

## Directory Purposes

### `/poc` - Proof of Concept (Active Development)
Contains the working POC implementation that validates the KDP formatting approach. This is where active development happens until the POC is validated with KDP Preview.

**Key Files**:
- `kdp_poc.py` - Main CLI script for document conversion
- `converters.py` - Document format converters (PDF, DOCX, TXT, MD)
- `renderer.py` - WeasyPrint PDF renderer with KDP geometry
- `epub_generator.py` - Pandoc-based EPUB 3 generator
- `ai_structure_detector.py` - OpenAI integration for structure detection
- `validator.py` - PDF validation tools
- `epub_validator.py` - EPUB validation with epubcheck
- `idm_schema.py` - Intermediate Document Model definitions
- `styles.css` - KDP-compliant PDF styling
- `epub_styles.css` - KDP-compliant EPUB styling
- `fonts/` - Open-source fonts (Source Serif 4)

See `/poc/README.md` for detailed usage instructions.

### `/src` - Production Code (Future)
Will contain production-ready code refactored from the POC after successful validation. Currently empty.

**Planned Structure**:
- `/src/api/` - FastAPI endpoints
- `/src/converters/` - Production converters
- `/src/renderers/` - Production PDF/EPUB renderers
- `/src/validators/` - Production validators
- `/src/ai/` - AI structure detection
- `/src/models/` - Database models
- `/src/utils/` - Shared utilities

See `/src/README.md` for planned architecture.

### `/tests` - Test Suite (Future)
Will contain pytest-based unit tests, integration tests, and end-to-end tests for production code. Currently empty.

**Planned Structure**:
- `/tests/unit/` - Unit tests for individual modules
- `/tests/integration/` - Integration tests for component interactions
- `/tests/e2e/` - End-to-end workflow tests
- `/tests/fixtures/` - Test fixtures and sample data

See `/tests/README.md` for testing conventions.

### `/docs` - Documentation
Comprehensive documentation including POC results, testing protocols, cost analysis, and setup guides.

**Key Files**:
- `poc_results.md` - POC validation results and KDP Preview testing
- `ai_cost_analysis.md` - OpenAI API cost analysis and projections
- `kdp_preview_testing_protocol.md` - Step-by-step KDP testing guide
- `GOOGLE_CLOUD_SETUP.md` - Google Cloud configuration
- `DEPLOYMENT.md` - VM deployment instructions
- `GITHUB_SETUP.md` - GitHub repository setup guide
- `REPOSITORY_STRUCTURE.md` - This file

### `/test_data` - Sample Manuscripts
Sample manuscripts in various formats for testing the conversion pipeline.

**Available Files**:
- `sample_short.txt` - Short story (~350 words)
- `sample_medium.txt` - Medium manuscript (~2500 words)
- `sample_nonfiction.txt` - Non-fiction sample
- `sample_medium.docx` - DOCX format test

See `/test_data/README.md` for file descriptions and creation guidelines.

### `/scripts` - Setup Scripts
Automated scripts for VM setup and dependency installation.

**Key Files**:
- `install_system_deps.sh` - Install system packages (Pandoc, Tesseract, etc.)
- `setup_vm.sh` - Set up Python virtual environment
- `verify_installation.sh` - Verify all dependencies are installed

### `/app` - FastAPI Application Skeleton
Basic FastAPI application structure for future production deployment.

**Key Files**:
- `main.py` - FastAPI application entry point
- `config.py` - Configuration management

### `/deployment` - Deployment Configuration
Systemd service files and deployment configurations for the e2-medium VM.

**Key Files**:
- `kdp-formatter.service` - Systemd service definition

## Development Phases

**Current Phase**: POC Validation & GitHub Setup
- ✅ POC implementation complete
- ✅ AI detection integrated
- ✅ EPUB generation working
- 🔄 GitHub repository setup
- ⏳ KDP Preview validation pending

**Next Phases**:
1. Complete KDP Preview validation (document in `/docs/poc_results.md`)
2. Migrate POC to production code in `/src`
3. Implement FastAPI backend with job queue
4. Add Firebase authentication
5. Integrate Stripe payments
6. Deploy to VM with Nginx reverse proxy

## File Naming Conventions

- **Python modules**: `lowercase_with_underscores.py`
- **Test files**: `test_*.py` for test files
- **Documentation**: `UPPERCASE_WITH_UNDERSCORES.md` for important docs, `lowercase.md` for others
- **Configuration**: `.lowercase` for dotfiles
- **Scripts**: `lowercase_with_underscores.sh`

## Key Configuration Files

- `.gitignore` - Excludes temporary files, outputs, credentials
- `.env.example` - Template for environment variables
- `requirements.txt` - Python dependencies
- `LICENSE` - MIT License
- `CONTRIBUTING.md` - Contribution guidelines

## Repository Metadata

### `.github/` Directory
- `ISSUE_TEMPLATE/bug_report.md` - Bug report template
- `ISSUE_TEMPLATE/feature_request.md` - Feature request template
- `pull_request_template.md` - Pull request template

### Version Control
- **Repository**: https://github.com/MarquisdeMayfair/KDP-Formatter.git
- **Branch Strategy**: main for stable, feature branches for development
- **Commit Convention**: Clear messages with issue references

## Development Workflow

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature/your-feature`
4. **Develop** and test changes
5. **Commit** with clear messages
6. **Push** to your fork
7. **Create** a Pull Request
8. **Address** review feedback
9. **Merge** after approval

## Quality Assurance

### Testing Strategy
- POC tests before any changes: `bash poc/run_tests.sh`
- KDP Preview validation for output quality
- Cross-platform testing (Linux, macOS, Windows where possible)
- Performance benchmarking for large documents

### Code Quality
- PEP 8 compliance
- Type hints on all functions
- Comprehensive docstrings
- 80%+ test coverage (future)

### Documentation Standards
- README files in every major directory
- Inline code comments for complex logic
- API documentation for public interfaces
- Change logs for version releases

## Collaboration Guidelines

### Communication
- Use GitHub Issues for bugs and features
- Pull Request discussions for code review
- Clear commit messages and PR descriptions
- Respectful and constructive feedback

### Code Review Process
- At least one approval required for merge
- Automated checks must pass
- Test coverage maintained or improved
- Documentation updated for changes

### Release Process
- Version tags for releases
- Changelog updates
- Migration guides for breaking changes
- Deployment validation before release

## Maintenance

### Regular Tasks
- Dependency updates and security patches
- Issue triage and community support
- Documentation updates
- Performance monitoring

### Archive Policy
- Close stale issues after 6 months
- Archive inactive branches
- Maintain release branches for LTS versions

For more information on specific components, see the README files in each directory or the main project documentation.

