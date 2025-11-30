# KDP Formatter - Local Testing Web UI

A modern web interface for testing and validating KDP formatting fixes before deployment. This FastAPI application provides a localhost environment for developers and testers to verify PDF formatting requirements.

## Quick Start

```bash
# From the project root directory
cd app
uvicorn app.main:app --host localhost --port 8001 --reload
```

Then open [http://localhost:8001](http://localhost:8001) in your browser.

## Features

- **Drag-and-drop file upload** with instant validation
- **Real-time PDF preview** with PDF.js viewer
- **Comprehensive validation** against KDP formatting requirements
- **Flexible configuration** options for testing different settings
- **Multiple output formats** (PDF, EPUB)
- **AI-powered structure detection** (optional, requires OpenAI API key)
- **Session management** with automatic cleanup
- **Formatting test generation** for quick verification

## Configuration Options

### Page Size
- **6" x 9"** (Standard KDP): Recommended for most books
- **8.5" x 11"** (Letter): For larger format books

### Margins
- Range: 0.5" to 1.5" inches
- Default: 0.75" (Standard KDP requirement)
- Applied to all sides (top, bottom, left, right)

### Drop Caps
- **Enabled/Disabled**: Adds decorative first letters to chapters
- **Warning**: May cause formatting issues - test carefully
- CSS ensures drop caps don't overlap adjacent text

### Structure Detection
- **Regex-based** (Free): Fast, basic document structure detection
- **AI-powered** (Requires API key): Enhanced detection using GPT models

## Testing Workflow

1. **Upload Document**: Drag & drop or click to select a file (.txt, .pdf, .docx, .md)
2. **Configure Options**: Select page size, margins, and other settings
3. **Generate & Validate**: Click "Generate & Validate" to process the document
4. **Review Results**: Check validation status and detailed results
5. **Preview PDF**: Use the built-in PDF viewer to inspect formatting
6. **Manual Verification**: Check against KDP formatting checklist
7. **Download**: Get the formatted PDF for KDP Preview testing

## KDP Formatting Checklist

When reviewing generated PDFs, verify these requirements:

- ✅ **First paragraphs after headings have no indent**
- ✅ **Subsequent paragraphs have 0.2-0.25in indent**
- ✅ **Drop caps (if enabled) don't overlap adjacent text**
- ✅ **No pages with single lines** (orphan/widow control)
- ✅ **Chapters start on new pages**
- ✅ **Margins are consistent** (0.75in or configured value)
- ✅ **No text cutoff at page edges**

## Dependencies

### Required System Dependencies
- **Python 3.8+**: Core runtime
- **Pandoc**: Document conversion (install via package manager)
- **Poppler tools**: PDF processing (`pdfinfo`, `pdftotext`)

### Python Dependencies
All required packages are listed in `requirements.txt`:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `weasyprint`: PDF generation
- `pypdf`: PDF processing
- `python-multipart`: File upload handling
- `jinja2`: Template rendering
- `openai`: AI structure detection (optional)

### Installation
```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root for local development:

```env
# Optional: OpenAI API key for AI detection
OPENAI_API_KEY=sk-your-api-key-here

# Development mode settings
ENVIRONMENT=development
DEBUG=true
```

## File Structure

```
app/
├── main.py              # FastAPI application and endpoints
├── config.py            # Configuration management
├── templates/           # Jinja2 HTML templates
│   ├── index.html       # Main upload page
│   └── preview.html     # PDF preview and validation page
└── static/              # Static assets
    ├── style.css        # Modern responsive styling
    └── script.js        # Client-side JavaScript
```

## API Endpoints

### Core Endpoints
- `GET /`: Main upload interface
- `POST /convert`: Process uploaded files and generate outputs
- `GET /preview/{session_id}`: PDF preview page
- `GET /download/{session_id}/{type}`: Download generated files

### Utility Endpoints
- `GET /config`: Available configuration options
- `GET /validate/{session_id}`: Validation results as JSON
- `POST /cleanup/{session_id}`: Clean up session files
- `GET /health`: Health check and dependency status

### Testing Endpoints
- `GET /formatting-test`: Generate test PDF with known formatting patterns

## Troubleshooting

### Common Issues

**Server won't start**
- Check if port 8001 is already in use: `lsof -i :8001`
- Ensure virtual environment is activated
- Verify Python dependencies: `pip install -r requirements.txt`

**File upload fails**
- Check file size limit (50MB)
- Verify file type (.txt, .pdf, .docx, .md)
- Ensure write permissions in output directory

**PDF generation fails**
- Verify WeasyPrint installation
- Check CSS syntax in `poc/styles.css`
- Review error logs in terminal

**AI detection not working**
- Set `OPENAI_API_KEY` in `.env` file
- Check API key validity and credits
- Ensure internet connectivity

### Error Logs
Check the terminal output for detailed error messages. The application logs all processing steps and errors with timestamps.

### File Cleanup
- Sessions are automatically cleaned up after 1 hour
- Use the "Delete Files" button in preview to manually clean up
- Old files in `app/output/` are cleaned on startup

## Development

### Running in Development Mode
```bash
# With auto-reload for code changes
uvicorn app.main:app --host localhost --port 8001 --reload

# With verbose logging
uvicorn app.main:app --host localhost --port 8001 --reload --log-level debug
```

### Adding New Features
1. Update `app/main.py` for new endpoints
2. Modify templates in `app/templates/` for UI changes
3. Add JavaScript in `app/static/script.js` for interactivity
4. Update this README with new features and instructions

### Testing
- Use the built-in formatting test endpoint for quick verification
- Upload test documents from `test_data/` directory
- Compare results with KDP Preview tool
- Check validation reports for detailed feedback

## Security Notes

- All uploaded files are processed in memory and stored temporarily
- Session files are automatically deleted after 1 hour
- No sensitive data is logged or stored
- CORS is configured for localhost development only
- File size and type validation prevents malicious uploads

## Contributing

See the main project `CONTRIBUTING.md` for development guidelines and code standards.
