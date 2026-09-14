# Contributing to ci-test-gate

Thank you for your interest in contributing! This document will help you get started.

## Prerequisites

- Python 3.10+
- pip or uv package manager
- Git

## Installation for development

```bash
# Clone the repository
git clone https://github.com/yunaremaia/ci-test-gate.git
cd ci-test-gate

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Running tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=ci_test_gate --cov-report=term-missing

# Run a specific test file
pytest tests/test_classifier.py

# Run with verbose output
pytest -v
```

Current test coverage target: **80%+**. New features should include tests.

## Project structure

```
ci-test-gate/
├── src/ci_test_gate/       # Main package
│   ├── __init__.py         # Public API exports
│   ├── cli.py              # Command-line interface
│   ├── classifier.py       # LLM-powered test classification
│   ├── context_builder.py  # Build change context from diffs
│   ├── context.py          # Context data models
│   ├── diff_parser.py      # Parse git diffs into structured changes
│   ├── llm.py              # LLM client (OpenAI-compatible)
│   ├── models.py           # Shared data models
│   └── parser.py           # General-purpose parsing utilities
├── tests/                  # Test suite
├── pyproject.toml          # Project metadata and dependencies
└── README.md
```

## How to add a new classifier

The core abstraction is `TestClassifier` in `src/ci_test_gate/classifier.py`. To create a custom classifier:

1. **Subclass `TestClassifier`** and override the `classify()` method:

```python
from ci_test_gate.classifier import TestClassifier, TestRecommendation

class MyCustomClassifier(TestClassifier):
    def classify(self, changes, test_files, **kwargs):
        # Your logic here
        return TestRecommendation(
            required=["tests/test_core.py"],
            recommended=[],
            optional=["tests/test_docs.py"],
            reasoning="Custom logic applied",
            estimated_savings_pct=50,
        )
```

2. **Register it in the CLI** by adding a new `--classifier` option in `src/ci_test_gate/cli.py`.

3. **Add tests** in `tests/test_classifier.py` or a new `tests/test_custom.py`.

## Code style

- Follow PEP 8 conventions
- Use type hints for all function signatures
- Docstrings follow Google style (or reStructuredText)
- Maximum line length: 120 characters

We recommend using [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
pip install ruff
ruff check src/
ruff format src/
```

## Contribution workflow

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create a branch** for your feature: `git checkout -b feat/my-feature`
4. **Make your changes** and add tests
5. **Run the test suite**: `pytest` (all tests must pass)
6. **Commit** with a descriptive message following [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add new classifier for Rust projects`
   - `fix: handle empty diff edge case`
   - `docs: update README with new examples`
7. **Push** to your fork: `git push origin feat/my-feature`
8. **Open a Pull Request** against `yunaremaia/ci-test-gate:main`

## LLM integration roadmap

ci-test-gate uses LLM APIs for semantic test classification. Current status:

- ✅ Basic LLM client (OpenAI-compatible)
- ✅ System prompt for test selection rules
- 🔄 Streaming responses (planned v0.2.0)
- 🔄 Local model support (planned v0.2.0)
- 🔄 Cost estimation per classification (planned v0.3.0)

When contributing LLM-related changes, ensure:
- API keys are never hardcoded (use environment variables)
- Prompts are versioned and tested
- Fallback heuristics work when LLM is unavailable

## Code of conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on what's best for the project

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
