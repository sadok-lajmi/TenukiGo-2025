# Photo Module Testing Guide

This document provides comprehensive information about testing the photo module's functionality.

Note: The tests may not be working properly since the last file structure refactor.

## Overview

The photo module test suite provides comprehensive coverage for:
- FastAPI endpoints for photo processing and model management
- Go board state analysis and move completion services
- AI model loading and management
- Image processing with YOLO detection
- SGF file generation and management

## Test Structure

```
modules/photo/tests/
├── __init__.py
├── conftest.py                      # Shared fixtures and test configuration
├── pytest.ini                       # Pytest configuration
├── README.md                        # This file
├── test_board_state.py              # BoardState class tests
├── test_image_processor.py          # Image processing tests
├── test_main.py                     # FastAPI endpoint tests
├── test_model_manager.py            # AI model loading tests
├── test_move_completion_service.py  # Move completion service tests
├── test_requirements.txt            # Test dependencies
└── test_sgf_generator_service.py    # SGF generation tests
```

## Setup and Installation

### 1. Install Testing Dependencies

```bash
cd modules/photo/tests
pip install -r test_requirements.txt
```

The test dependencies include:
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `httpx>=0.24.0` - HTTP client for FastAPI testing
- `pytest-mock>=3.10.0` - Mocking utilities
- `pytest-cov>=4.1.0` - Coverage reporting

### 2. Configure Test Environment

The tests use pytest configuration defined in `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
asyncio_mode = auto
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py

# Run specific test class
pytest tests/test_api.py::TestHealthEndpoint

# Run specific test method
pytest tests/test_api.py::TestHealthEndpoint::test_health_check_success
```

### Test Coverage

```bash
# Run tests with coverage report
pytest --cov=modules/photo tests/

# Generate HTML coverage report
pytest --cov=modules/photo --cov-report=html tests/

# Generate coverage report excluding tests
pytest --cov=modules/photo --cov-report=term-missing tests/
```

### Running Tests by Category

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Fixtures and Utilities

### Common Fixtures (`conftest.py`)

- `test_client` - FastAPI test client
- `sample_board_19x19` - Sample Go board with stones
- `sample_board_states` - Initial and final board state pairs
- `mock_ai_model` - Mock TensorFlow/Keras model
- `mock_model_loader` - Mock AI model loader
- `mock_image_processor` - Mock YOLO image processor
- `sample_image_bytes` - Sample JPEG image data
- `temp_model_file` - Temporary model file for testing
- `mock_sgf_generator` - Mock SGF generator

### Mocking Strategy

Tests extensively use mocking to isolate units and avoid external dependencies:

- **YOLO Models** - Mocked to avoid requiring actual YOLO model files
- **TensorFlow/Keras** - Mocked to test without heavy ML dependencies
- **File System** - Mocked file operations for predictable testing
- **Image Processing** - Mocked OpenCV operations
- **External Services** - All network calls and external services mocked

## Example Test Cases

### Testing API Endpoints

```python
def test_health_check_success(self, client, mock_completion_service):
    """Test health check endpoint returns success."""
    with patch('api.completion_service', mock_completion_service):
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "model_loaded" in data
```

### Testing Board Analysis

```python
def test_get_differences_stones_added(self):
    """Test detecting added stones."""
    initial = np.zeros((19, 19), dtype=int)
    final = np.zeros((19, 19), dtype=int)
    final[3, 3] = 1  # Add black stone
    
    initial_state = BoardState(initial, 19)
    final_state = BoardState(final, 19)
    
    differences = initial_state.get_differences(final_state)
    
    assert len(differences[1]["ajout"]) == 1
    assert (3, 3, 1) in differences[1]["ajout"]
```

### Testing Model Loading

```python
def test_load_legacy_model_success(self, temp_model_file):
    """Test successful loading of legacy model."""
    mock_model = Mock()
    mock_model.input_shape = (None, 19, 19, 1)
    
    with patch('model_loader.load_model', return_value=mock_model):
        loader = AIModelLoader()
        result = loader.load_legacy_model(temp_model_file)
        
        assert result["success"] is True
        assert loader.model == mock_model
```

## Continuous Integration

### Docker Testing

Tests can be run inside the Docker container:

```bash
# Enter the photo container
docker exec -it tenuki-photo bash

# Install test dependencies
pip install -r test_requirements.txt

# Run tests
pytest tests/
```

### GitHub Actions Integration

Add to your CI pipeline:

```yaml
- name: Run Photo Module Tests
  run: |
    cd modules/photo
    pip install -r test_requirements.txt
    pytest tests/ --cov=. --cov-report=xml
    
- name: Upload Coverage Reports
  uses: codecov/codecov-action@v3
  with:
    file: modules/photo/coverage.xml
```

## Test Data and Fixtures

### Board Configurations

Tests use various board configurations:
- Empty 19x19 boards
- Boards with corner stone patterns
- Progressive game states
- Invalid board dimensions for error testing

### Image Data

Mock image processing uses:
- PIL-generated test images
- Simulated YOLO detection results
- Various confidence levels and object classes

### SGF Examples

SGF tests validate against:
- Standard SGF format specifications
- Game metadata inclusion
- Move sequence accuracy
- File format compliance

## Debugging Failed Tests

### Common Issues

1. **Missing Dependencies**
   ```bash
   # Install missing packages
   pip install ultralytics tensorflow pillow
   ```

2. **Mock Configuration**
   - Check that mocks match actual API signatures
   - Verify mock return values are realistic

3. **Async Test Issues**
   - Ensure `pytest-asyncio` is installed
   - Use `async def` for async test functions

4. **File Path Issues**
   - Use `temp_model_file` fixture for temporary files
   - Mock file system operations appropriately

### Debugging Commands

```bash
# Run tests with maximum verbosity
pytest -vvv

# Run single test with output capture disabled
pytest -s tests/test_api.py::TestHealthEndpoint::test_health_check_success

# Run tests with debugging on first failure
pytest --pdb

# Show local variables on failures
pytest --tb=long
```

## Best Practices

1. **Isolation** - Each test should be independent and not rely on others
2. **Mocking** - Mock external dependencies to ensure fast, reliable tests
3. **Coverage** - Aim for high test coverage while focusing on critical paths
4. **Readability** - Write clear test names that describe the scenario
5. **Data** - Use realistic test data that reflects actual usage patterns

## Contributing

When adding new functionality:

1. Write tests for new features before implementing
2. Ensure existing tests continue to pass
3. Add appropriate mock fixtures for new dependencies
4. Update this documentation for significant changes
5. Maintain test coverage above 90%

For questions or issues with testing, refer to the main project documentation or create an issue in the project repository.