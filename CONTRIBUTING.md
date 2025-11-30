# Contributing to KDP Formatter

Thank you for your interest in contributing to the KDP Formatter project! This document provides guidelines for contributing to ensure a smooth collaboration process.

## Getting Started

### Fork and Clone
1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/KDP-Formatter.git
   cd KDP-Formatter
   ```

3. Set up the development environment:
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt

   # Install system dependencies (Ubuntu/Debian)
   sudo apt install pandoc poppler-utils tesseract-ocr imagemagick ghostscript

   # Optional: Install fonts for better KDP compatibility
   bash poc/fonts/download_fonts.sh
   ```

4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Start with the POC
Before making changes, familiarize yourself with the proof-of-concept implementation:
- Review [`poc/README.md`](poc/README.md) for detailed usage
- Run POC tests: `bash poc/run_tests.sh`
- Experiment with sample data in [`test_data/`](test_data/)

### Code Standards
- Follow Python PEP 8 style guidelines
- Use type hints for function parameters and return values
- Add docstrings to all functions and classes using Google style
- Keep functions focused on single responsibilities
- Use meaningful variable and function names

### Making Changes
1. **Plan your changes**: Create an issue or discuss with maintainers first
2. **Write tests**: Add tests for new functionality before implementing
3. **Implement**: Keep changes focused and well-documented
4. **Test thoroughly**: Run POC tests and validate with KDP Preview
5. **Document**: Update relevant documentation

## Testing

### POC Testing
- Run POC tests before submitting: `bash poc/run_tests.sh`
- Test with multiple file types: TXT, DOCX, MD
- Validate outputs with KDP Preview (see [`docs/kdp_preview_testing_protocol.md`](docs/kdp_preview_testing_protocol.md))
- Document test results in [`docs/poc_results.md`](docs/poc_results.md)

### Test Files
- Add new test manuscripts to [`test_data/`](test_data/)
- Include variety: fiction, non-fiction, different lengths
- Test edge cases: special characters, formatting, large files
- Ensure files are shareable (no copyrighted content)

### Validation Checklist
- [ ] POC tests pass: `bash poc/run_tests.sh`
- [ ] Sample files in `test_data/` work correctly
- [ ] Generated PDFs validate with KDP Preview
- [ ] EPUB files pass epubcheck validation
- [ ] AI detection works (if modified)
- [ ] Performance is acceptable (< 30 seconds for typical manuscripts)

## Submitting Changes

### Commit Guidelines
- Use clear, descriptive commit messages
- Reference issue numbers when applicable: `Fix PDF rendering bug #123`
- Keep commits focused on single changes
- Squash related commits before merging

### Pull Request Process
1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**:
   - Use descriptive title and detailed description
   - Reference related issues: `Fixes #123`
   - Fill out the PR template completely

3. **Address Review Feedback**:
   - Be responsive to reviewer comments
   - Make requested changes promptly
   - Update PR description if scope changes

### PR Requirements
- All CI checks pass
- Code review approved by at least one maintainer
- Tests added/updated for new functionality
- Documentation updated if needed
- No breaking changes without prior discussion

## Code Review Process

### For Contributors
- Be open to feedback and suggestions
- Explain your reasoning when requested
- Update code based on review comments
- Ask questions if anything is unclear

### For Reviewers
- Review code for correctness, style, and maintainability
- Test changes when possible
- Provide constructive feedback
- Approve when requirements are met

### Review Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added/updated appropriately
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Backwards compatibility maintained

## Reporting Issues

### Bug Reports
- Use the bug report template in GitHub Issues
- Include reproduction steps
- Attach sample files (if shareable)
- Note environment details (OS, Python version, etc.)
- Include error messages and stack traces

### Feature Requests
- Use the feature request template
- Describe the problem you're solving
- Explain how the feature would work
- Consider implementation complexity
- Reference KDP requirements if applicable

### Issue Guidelines
- Check existing issues before creating duplicates
- Use clear, descriptive titles
- Provide all requested information
- Be patient and respectful

## Development Environment

### Recommended Setup
- Python 3.11+ in virtual environment
- Ubuntu 24.04 or similar Linux distribution
- Git for version control
- VS Code or similar IDE with Python extensions

### Virtual Environment
```bash
# Create and activate venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Useful Commands
```bash
# Run POC
python poc/kdp_poc.py -i test_data/sample_short.txt -o output/test.pdf

# Run tests
bash poc/run_tests.sh

# Validate EPUB
java -jar epubcheck.jar output/test.epub

# Check PDF
python poc/validator.py output/test.pdf
```

## Project Architecture

### Current Structure (POC Phase)
- `/poc/` - Working proof-of-concept code
- `/docs/` - Documentation and protocols
- `/test_data/` - Sample manuscripts
- `/scripts/` - Setup and deployment scripts

### Future Structure (Production)
- `/src/` - Production FastAPI application
- `/tests/` - Unit and integration tests
- `/app/` - Current FastAPI skeleton (will be replaced)

### Key Components
- **Converters**: Document format parsers (TXT, DOCX, MD, PDF)
- **AI Detection**: OpenAI-powered structure analysis
- **Renderers**: WeasyPrint PDF and Pandoc EPUB generation
- **Validators**: PDF and EPUB compliance checking

## Communication

### Discussion Channels
- GitHub Issues for bugs and features
- Pull Request comments for code discussions
- Email for private matters

### Community Guidelines
- Be respectful and professional
- Help newcomers when possible
- Focus on constructive feedback
- Maintain project scope and vision

## Licensing

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project. See [LICENSE](LICENSE) for details.

## Recognition

Contributors will be recognized in:
- Git commit history
- CHANGELOG.md (when implemented)
- GitHub contributor statistics

Thank you for contributing to KDP Formatter! Your help makes professional publishing more accessible for authors worldwide.

