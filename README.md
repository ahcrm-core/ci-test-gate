# ci-test-gate

**LLM-powered test selection for CI pipelines — picks which tests to run based on semantic analysis of your diff.**

```bash
pip install ci-test-gate
ci-test-gate analyze --output markdown
```

## The Problem

CI suites are slow. Running 5,000+ tests on every PR wastes time and money. Path-based selection (`pytest tests/api/`) is fragile — it doesn't capture cross-module impact. Manual selection is error-prone.

Meanwhile, 84% of developers use AI coding tools, but **no open-source tool uses AI to pick which tests to run**.

## The Solution

`ci-test-gate` analyzes your PR's diff, builds context (language, framework, imports), and uses an LLM to classify each test suite by risk:

- 🔴 **REQUIRED** — Must run (direct test of changed code, critical path)
- 🟡 **RECOMMENDED** — Should run (integration tests touching related modules)
- 🟢 **OPTIONAL** — Can skip (unrelated modules, pure docs)

## Quick Start

```bash
# Install
pip install ci-test-gate

# Analyze current branch vs main
ci-test-gate analyze

# Output as Markdown (for PR comments)
ci-test-gate analyze --output markdown

# Gate mode (fails if required tests missing)
ci-test-gate analyze --mode gate

# Local development
ci-test-gate discover
```

## GitHub Action

```yaml
# .github/workflows/test-gate.yml
name: Test Gate
on: pull_request

jobs:
  test-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: yunaremaia/ci-test-gate@v0.1.0
        with:
          mode: suggest
          output: markdown
```

## How It Works

1. **Diff Parser** — Parses `git diff main...HEAD` into structured changes
2. **Context Builder** — Detects language, test framework, imports, and finds test files
3. **LLM Classifier** — Sends context to LLM with a system prompt for risk classification
4. **Output** — JSON for CI, Markdown for PR comments, or rich table for local use

## Fallback

If no LLM API key is configured, `ci-test-gate` falls back to rule-based classification:
- Test files that changed → REQUIRED
- Source files with matching test files (`foo.py` → `test_foo.py`) → REQUIRED
- Everything else → RECOMMENDED

## Supported Languages

| Language   | Test Framework | Status |
|------------|----------------|--------|
| Python     | pytest         | ✅     |
| JavaScript | jest           | ✅     |
| TypeScript | jest           | ✅     |
| Rust       | cargo test     | ✅     |
| Go         | go test        | ✅     |
| Java       | junit          | ✅     |

## Development

```bash
git clone https://github.com/yunaremaia/ci-test-gate.git
cd ci-test-gate
pip install -e ".[dev]"
pytest
```

## License

MIT © Yunaremaia
