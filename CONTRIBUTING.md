# Contributing to Certificate Generator

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Adding New Features](#adding-new-features)

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to a positive environment:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/certificate-generator.git
   cd certificate-generator
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/Ifihan/certificate-generator.git
   ```

## Development Setup

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run the application**:
   ```bash
   uv run python app.py
   ```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior**
- **Actual behavior**
- **Screenshots** (if applicable)
- **Environment details** (OS, Python version, etc.)

Example:

```markdown
**Bug**: CSV upload fails with non-ASCII characters

**Steps to reproduce**:
1. Create CSV with name "José García"
2. Upload via web interface
3. Click "Generate Certificates"

**Expected**: Certificate generated successfully
**Actual**: Error "UnicodeDecodeError..."

**Environment**:
- OS: Windows 10
- Python: 3.11.2
- Browser: Chrome 120
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why is this enhancement useful?
- **Proposed solution** - how should it work?
- **Alternatives considered**
- **Additional context** (mockups, examples, etc.)

### Your First Code Contribution

Unsure where to start? Look for issues labeled:

- `good first issue` - simple issues for beginners
- `help wanted` - issues where we need community help
- `documentation` - improvements to docs

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some exceptions:

- **Line length**: 100 characters (not 79)
- **Quotes**: Prefer single quotes `'` unless double quotes `"` avoid escaping
- **Docstrings**: Use triple double quotes `"""`

### Code Formatting

Use automatic formatters:

```bash
# Install formatters
uv pip install black isort

# Format code
black app.py certificate_generator.py pdf_uploader.py
isort app.py certificate_generator.py pdf_uploader.py
```

### Type Hints

Use type hints for function parameters and return values:

```python
def generate_certificate(name: str) -> str:
    """Generate a certificate PDF for a given name"""
    ...
```

### Documentation

- **All functions** should have docstrings
- **Complex logic** should have inline comments
- **Configuration options** should be documented in `config.py`

Example:

```python
def save_progress(progress_data: dict) -> None:
    """Save progress to tracking file

    Args:
        progress_data: Dictionary containing:
            - csv_hash: MD5 hash of current CSV
            - processed_names: List of processed names
            - results: List of result dictionaries

    Raises:
        IOError: If unable to write to progress file
    """
    with open(config.PROGRESS_FILE, 'w') as f:
        json.dump(progress_data, f, indent=2)
```

## Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(upload): add support for Excel files

- Added xlsx parsing using pandas
- Updated UI to accept .xlsx files
- Added validation for Excel format

Closes #123
```

```
fix(generator): handle names with special characters

Previously, names with accents caused encoding errors.
Now using UTF-8 encoding throughout the pipeline.

Fixes #456
```

## Pull Request Process

### Before Submitting

1. **Update your fork**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write tests if applicable
   - Update documentation
   - Follow coding standards

4. **Test your changes**:
   ```bash
   # Run the application
   uv run python app.py

   # Test manually through the UI
   # Upload test CSV, generate certificates, etc.
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Submitting Pull Request

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested manually
- [ ] Added automated tests
- [ ] All existing tests pass

## Screenshots (if applicable)
Add screenshots here

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

- Maintainers will review your PR within 3-5 business days
- Address any requested changes
- Once approved, maintainers will merge your PR

## Adding New Features

### Adding a New Storage Provider

1. **Add provider method** to `pdf_uploader.py`:

```python
def _upload_newprovider(self, file_path):
    """Upload to NewProvider"""
    url = "https://newprovider.com/api/upload"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
        response.raise_for_status()

        result = response.json()
        if result.get('success'):
            return result['url']
        else:
            raise Exception(f"Upload failed: {result.get('error')}")
```

2. **Add to upload method**:

```python
def upload(self, file_path, name):
    """Upload a file and return its public URL"""
    if self.service == 'cloudinary':
        return self._upload_cloudinary(file_path, name)
    # ... existing providers
    elif self.service == 'newprovider':
        return self._upload_newprovider(file_path)
    else:
        raise ValueError(f"Unknown service: {self.service}")
```

3. **Document in README.md** under Storage Provider Comparison

### Adding Custom Certificate Layouts

1. **Add configuration options** to `config.py`:

```python
# Layout Settings
LAYOUT_TYPE = 'centered'  # Options: centered, top, bottom, custom
CUSTOM_X_POSITION = None
CUSTOM_Y_POSITION = None
```

2. **Update certificate_generator.py**:

```python
if config.LAYOUT_TYPE == 'custom':
    name_x_position = config.CUSTOM_X_POSITION
    name_y_position = config.CUSTOM_Y_POSITION
elif config.LAYOUT_TYPE == 'top':
    name_y_position = int(height * 0.2)
# ... etc
```

3. **Update documentation** in README.md

## Questions?

If you have questions, feel free to:

- Open an issue with the `question` label
- Join our discussions on GitHub Discussions
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
