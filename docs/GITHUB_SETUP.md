# GitHub Repository Setup

This document explains how the KDP Formatter GitHub repository was initialized and configured.

## Repository Information
- **URL**: https://github.com/MarquisdeMayfair/KDP-Formatter.git
- **Owner**: MarquisdeMayfair
- **Visibility**: Public (or Private - specify based on actual setup)

## Initial Setup Steps

1. **Initialize Git Repository**
   ```bash
   cd "/Users/nik/Downloads/KDP Formatter"
   git init
   ```

2. **Add Remote Origin**
   ```bash
   git remote add origin https://github.com/MarquisdeMayfair/KDP-Formatter.git
   ```

3. **Stage All Files**
   ```bash
   git add .
   ```

4. **Create Initial Commit**
   ```bash
   git commit -m "Initial commit: POC implementation with document processing pipeline

   - Complete POC implementation in /poc directory
   - Document converters (PDF, DOCX, TXT, MD)
   - WeasyPrint PDF renderer with KDP geometry
   - Pandoc EPUB 3 generator
   - AI structure detection with OpenAI integration
   - Validation tools (pypdf, epubcheck)
   - Comprehensive documentation in /docs
   - Sample test data in /test_data
   - VM deployment scripts in /scripts
   - Project structure for future production code (/src, /tests)"
   ```

5. **Push to GitHub**
   ```bash
   git branch -M main
   git push -u origin main
   ```

## Repository Structure

The repository is organized as follows:

- `/poc/` - Proof of concept implementation (working code)
- `/src/` - Production code (to be implemented in future phases)
- `/tests/` - Unit and integration tests (to be implemented)
- `/docs/` - Documentation, templates, and protocols
- `/test_data/` - Sample manuscripts for testing
- `/scripts/` - VM setup and deployment scripts
- `/app/` - FastAPI application skeleton
- `/deployment/` - Systemd service files and deployment configs

## Branch Strategy

- `main` - Stable, production-ready code
- `develop` - Integration branch for features (to be created)
- `feature/*` - Feature branches for new development
- `bugfix/*` - Bug fix branches

## Collaboration Workflow

1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Submit a Pull Request
5. Address review feedback
6. Merge after approval

See `CONTRIBUTING.md` for detailed contribution guidelines.

## GitHub Features to Enable

- **Issues**: Track bugs, features, and tasks
- **Projects**: Organize work into phases (optional)
- **Wiki**: Additional documentation (optional)
- **Actions**: CI/CD workflows (to be implemented)
- **Releases**: Version tagging for milestones

## Next Steps

1. Enable GitHub Issues for bug tracking
2. Set up branch protection rules for `main`
3. Configure GitHub Actions for automated testing (future phase)
4. Create project milestones for tracking progress
5. Add collaborators with appropriate permissions

## File Organization Standards

### Directory Structure
- Use lowercase with underscores for directory names: `test_data/`
- Group related functionality in subdirectories
- Keep flat hierarchies where possible

### File Naming
- Python files: `lowercase_with_underscores.py`
- Documentation: `UPPERCASE_WITH_UNDERSCORES.md` for important docs
- Scripts: `lowercase_with_underscores.sh`
- Configuration: `.lowercase` for dotfiles

### Commit Message Format
```
Type: Brief description of change

Detailed explanation if needed. Reference issues with #123.
```

Types:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test additions/updates
- `chore:` - Maintenance tasks

## Repository Settings

### Branch Protection (Recommended)
- Require pull request reviews before merging
- Require status checks to pass
- Include administrators in restrictions
- Require branches to be up to date

### Issue Templates
- Bug report template (created in `.github/ISSUE_TEMPLATE/`)
- Feature request template (created in `.github/ISSUE_TEMPLATE/`)
- Pull request template (created in `.github/`)

### Labels (Suggested)
- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `question` - Further information needed

## Automation Setup (Future)

### GitHub Actions Workflows
1. **CI Pipeline** - Run tests on every push/PR
2. **Code Quality** - Lint and format code
3. **Security** - Scan for vulnerabilities
4. **Release** - Automated releases on tags

### Dependabot
- Enable for automatic dependency updates
- Configure update schedule and PR limits

## Repository Maintenance

### Regular Tasks
- Review and merge pull requests promptly
- Keep dependencies updated
- Monitor GitHub Issues and community feedback
- Update documentation as code evolves

### Archive Strategy
- Archive inactive issues after 6 months
- Use milestones for version planning
- Create releases for major versions

## Troubleshooting

### Common Issues
- **Permission denied**: Check repository access and SSH keys
- **Merge conflicts**: Rebase feature branches regularly
- **Failed CI**: Check test failures and fix issues
- **Large files**: Use Git LFS for binary assets if needed

### Getting Help
- Check GitHub documentation
- Review repository issues
- Contact repository maintainers

## Migration Notes

If migrating from another version control system:
1. Export repository history
2. Convert to Git format
3. Clean up large files and sensitive data
4. Set up new repository structure
5. Import with `git fast-import`

This setup provides a solid foundation for collaborative development of the KDP Formatter project.

