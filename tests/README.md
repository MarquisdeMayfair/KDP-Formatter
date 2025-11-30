# Test Suite Directory

This directory will contain pytest-based test suites that validate the functionality of modules in `/src`. Currently empty as we're still in the POC validation phase, but establishing the structure now ensures testing is a first-class concern in the production implementation.

## Planned Test Structure

The test suite will follow this structure:

- `/tests/unit/` - Unit tests for individual modules and functions
- `/tests/integration/` - Integration tests for component interactions
- `/tests/e2e/` - End-to-end tests for complete workflows
- `/tests/fixtures/` - Test fixtures and sample data
- `/tests/conftest.py` - Pytest configuration and shared fixtures

## Testing Conventions

- **Framework**: pytest as the primary testing framework
- **Naming**: `test_*.py` for test files, `test_*` for test functions
- **Coverage**: Aim for >80% code coverage across all production modules
- **Mocking**: Mock external dependencies (OpenAI API, file I/O, database connections)
- **Fixtures**: Use pytest fixtures for reusable test data and setup
- **Test Data**: Use sample manuscripts from `/test_data` for integration tests

## Test Categories

### Unit Tests (`/tests/unit/`)

Test individual functions and classes in isolation:

```python
# Example: tests/unit/test_converters.py
def test_txt_to_idm_conversion():
    """Test TXT to IDM conversion logic."""
    converter = TextConverter()
    result = converter.convert("test content")
    assert result.format == "idm"
    assert "content" in result.data

def test_ai_structure_detection():
    """Test AI structure detection with mocked OpenAI response."""
    mock_openai_response = {"chapters": ["Chapter 1", "Chapter 2"]}
    with patch('openai.ChatCompletion.create') as mock_api:
        mock_api.return_value = mock_openai_response
        detector = AIStructureDetector()
        structure = detector.detect("sample text")
        assert len(structure.chapters) == 2
```

### Integration Tests (`/tests/integration/`)

Test component interactions and data flow:

```python
# Example: tests/integration/test_conversion_pipeline.py
def test_full_conversion_pipeline(sample_txt_file):
    """Test complete conversion from TXT to PDF and EPUB."""
    # Convert TXT to IDM
    converter = TextConverter()
    idm = converter.convert(sample_txt_file)

    # Apply AI structure detection
    ai_detector = AIStructureDetector()
    structured_idm = ai_detector.detect(idm)

    # Render PDF
    pdf_renderer = PDFRenderer()
    pdf_bytes = pdf_renderer.render(structured_idm)

    # Render EPUB
    epub_generator = EPUBGenerator()
    epub_bytes = epub_generator.generate(structured_idm)

    # Validate outputs
    pdf_validator = PDFValidator()
    epub_validator = EPUBValidator()

    assert pdf_validator.validate(pdf_bytes)
    assert epub_validator.validate(epub_bytes)
```

### End-to-End Tests (`/tests/e2e/`)

Test complete user workflows through the API:

```python
# Example: tests/e2e/test_document_processing.py
def test_upload_and_convert_workflow(client, auth_token):
    """Test complete document upload and conversion workflow."""
    # Upload document
    with open("test_data/sample_short.txt", "rb") as f:
        response = client.post("/api/documents/upload",
                             files={"file": f},
                             headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    document_id = response.json()["id"]

    # Start conversion job
    response = client.post(f"/api/documents/{document_id}/convert",
                          json={"formats": ["pdf", "epub"]},
                          headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # Wait for completion (in real test, use polling or websockets)
    # Download results
    response = client.get(f"/api/documents/{document_id}/download/pdf",
                         headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run tests matching pattern
pytest -k "conversion"

# Run tests with verbose output
pytest -v
```

## CI/CD Integration

Tests will be automatically run in GitHub Actions on:
- Every push to main/develop branches
- Every pull request
- Nightly builds for integration testing

## Performance Testing

Include performance benchmarks for:
- Document conversion speed (< 30 seconds for typical manuscripts)
- Memory usage during processing
- API response times (< 2 seconds for most endpoints)
- Concurrent user handling

## Test Data Management

- Use fixtures for consistent test data
- Mock external APIs to ensure reliable tests
- Include edge cases: empty files, corrupted files, very large files
- Test with real sample data from `/test_data` for integration validation

## Reference Implementation

The POC test scripts in `/poc/run_tests.sh` and `/poc/test_ai_detection.py` serve as examples of testing approaches that will be formalized in this directory during production implementation.

All production code must pass the complete test suite before deployment to production environments.

