# Changelog

All notable changes to ci-test-gate will be documented in this file.

## [Unreleased]

### Fixed
- **BUG**: Gate mode logic was inverted — failed when no required tests existed and passed when required tests were missing. Now correctly returns exit code 2 only when required tests are NOT covered by the provided test files list. (#43)

## [0.1.0] - 2026-09-11

### Added
- Initial release: LLM-powered test selection for CI
- Multi-language support (Python, JS/TS, Go, Rust)
- Required/recommended/optional test classification
- GitHub Actions composite action
- Pre-commit hook support

### Added (2026-09-12)
- `.pre-commit-hooks.yaml` for native pre-commit integration
