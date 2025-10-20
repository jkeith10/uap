# Contributing to UAP

Thank you for your interest in contributing to the Unified Autonomy Protocol (UAP)! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Guidelines](#documentation-guidelines)
- [Issue Guidelines](#issue-guidelines)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Release Process](#release-process)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/uap.git
   cd uap
   ```
3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/original-org/uap.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Poetry for dependency management
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+

### Setup Steps

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Install pre-commit hooks**:
   ```bash
   poetry run pre-commit install
   ```

3. **Start development services**:
   ```bash
   docker-compose up -d
   ```

4. **Run tests** to ensure everything works:
   ```bash
   poetry run pytest
   ```

## Contributing Process

### 1. Create a Branch

Create a feature branch from the latest `main` branch:

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write your code following the [Code Style Guidelines](#code-style-guidelines)
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/e2e/

# Run with coverage
poetry run pytest --cov=src/uap --cov-report=html
```

### 4. Code Quality Checks

```bash
# Run linting
poetry run ruff check src/ tests/

# Run formatting
poetry run black src/ tests/
poetry run isort src/ tests/

# Run type checking
poetry run mypy src/
```

### 5. Commit Your Changes

Use conventional commit messages:

```bash
git add .
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in component"
git commit -m "docs: update API documentation"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style Guidelines

### Python Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [Ruff](https://docs.astral.sh/ruff/) for linting

### Type Hints

- Add type hints to all new functions and methods
- Use `from __future__ import annotations` for forward references
- Use `typing` module for complex types

### Documentation

- Add docstrings to all public functions, classes, and methods
- Use Google-style docstrings
- Include type information in docstrings

### Example

```python
from __future__ import annotations
from typing import Dict, List, Optional

def process_intent(
    intent: IntentPacket,
    context: Optional[Dict[str, Any]] = None
) -> ProcessingResult:
    """Process an intent packet with optional context.
    
    Args:
        intent: The intent packet to process
        context: Optional context information
        
    Returns:
        The processing result
        
    Raises:
        ValidationError: If the intent is invalid
        ProcessingError: If processing fails
    """
    # Implementation here
    pass
```

## Testing Guidelines

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete workflows

### Test Naming

- Use descriptive test names: `test_should_return_error_when_invalid_input`
- Group related tests in classes: `class TestIntentProcessor`

### Test Coverage

- Aim for 80%+ code coverage
- Test both success and failure cases
- Test edge cases and boundary conditions

### Example Test

```python
import pytest
from src.uap.models.intent import IntentPacket, IntentType

class TestIntentProcessor:
    def test_should_process_valid_intent(self):
        # Arrange
        intent = IntentPacket(
            type=IntentType.ACTION,
            content="Test intent"
        )
        
        # Act
        result = process_intent(intent)
        
        # Assert
        assert result.status == "success"
        assert result.intent_id == intent.id
```

## Documentation Guidelines

### API Documentation

- Update API documentation for any changes to public interfaces
- Include examples in docstrings
- Document breaking changes clearly

### README Updates

- Update README.md for significant changes
- Include new features in the overview
- Update installation and usage instructions

### Code Comments

- Add comments for complex logic
- Explain business rules and decisions
- Keep comments up to date with code changes

## Issue Guidelines

### Bug Reports

- Use the bug report template
- Include steps to reproduce
- Provide environment information
- Include relevant logs and error messages

### Feature Requests

- Use the feature request template
- Describe the use case clearly
- Explain the expected behavior
- Consider implementation complexity

### Questions

- Use the question template
- Provide context and background
- Include relevant code or configuration
- Be specific about what you need help with

## Pull Request Guidelines

### PR Description

- Use the pull request template
- Describe the changes clearly
- Link to related issues
- Include testing information

### Review Process

- Ensure all CI checks pass
- Address reviewer feedback promptly
- Keep PRs focused and reasonably sized
- Update documentation as needed

### Merge Requirements

- All tests must pass
- Code coverage must not decrease
- All reviewers must approve
- No merge conflicts

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a release tag
4. GitHub Actions will automatically build and publish

## Getting Help

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers directly for urgent issues

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to UAP! 🚀
