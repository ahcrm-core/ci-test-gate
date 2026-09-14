# Language Test Pattern Support

ci-test-gate recognizes test files by language. The classifier uses file extension matching to associate source files with their corresponding tests.

## Supported Languages

### Python

Test patterns:
- `tests/test_*.py` — conventional pytest layout
- `test_*.py` — flat layout
- `*_test.py` — unittest convention

| Source | Test |
|--------|------|
| `src/app.py` | `tests/test_app.py` |
| `src/utils/helpers.py` | `tests/test_helpers.py` |
| `package/module.py` | `package/test_module.py` |

### JavaScript / TypeScript

Test patterns:
- `*.test.js`, `*.test.ts` — Jest, Vitest
- `*.spec.js`, `*.spec.ts` — Angular, older Jasmine
- `__tests__/*.js` — colocated tests

| Source | Test |
|--------|------|
| `src/app.ts` | `src/app.test.ts` |
| `src/components/Button.tsx` | `src/components/__tests__/Button.tsx` |
| `lib/utils.js` | `lib/utils.spec.js` |

### Go

Test pattern: `*_test.go`

Go uses a simple convention — test files are in the same package directory as source files.

| Source | Test |
|--------|------|
| `cmd/server.go` | `cmd/server_test.go` |
| `pkg/handler/user.go` | `pkg/handler/user_test.go` |

### Rust

Test patterns:
- `tests/*.rs` — integration tests
- `src/**/*.rs` inline `#[cfg(test)]` modules

| Source | Test |
|--------|------|
| `src/lib.rs` | `tests/integration.rs` |
| `src/handler.rs` | `src/handler.rs` (inline test mod) |

## Mixed-Language Example

Monorepo with multiple languages:

```yaml
# ci-test-gate.yml
languages:
  python:
    test_patterns: ["tests/test_*.py", "test_*.py"]
  javascript:
    test_patterns: ["*.test.js", "*.spec.js"]
  go:
    test_patterns: ["*_test.go"]
  rust:
    test_patterns: ["tests/*.rs"]

# Override auto-detection per path
overrides:
  path: "frontend/**"
  language: "javascript"
```

## File Extension Mapping

The classifier matches file extensions to ecosystems:

| Extension | Language |
|-----------|----------|
| `.py` | Python |
| `.js`, `.jsx` | JavaScript |
| `.ts`, `.tsx` | TypeScript |
| `.go` | Go |
| `.rs` | Rust |
| `.java` | Java |
| `.kt` | Kotlin |
| `.rb` | Ruby |
| `.php` | PHP |
