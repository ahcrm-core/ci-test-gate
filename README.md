# ci-test-gate

**LLM-powered test selection for CI — run only the tests that matter.**

Tired of waiting 30+ minutes for CI when your change touches one file? `ci-test-gate` analyzes your PR diff and recommends which tests to run, skip, or require.

```bash
pip install git+https://github.com/yunaremaia/ci-test-gate.git
ci-test-gate suggest --diff pr.diff --test-files tests.txt
```

### How it works

```
┌──────────────────────────────────────────────────┐
│                    GitHub PR                      │
│                     │                             │
│         git diff main...HEAD                     │
│                     │                             │
│                     ▼                             │
│  ┌────────────────────────────────────────────┐  │
│  │           ci-test-gate engine              │  │
│  │                                            │  │
│  │  1. Parse diff into structured changes     │  │
│  │  2. Build context (imports, functions)     │  │
│  │  3. Classify tests (required/recommended/  │  │
│  │     optional)                              │  │
│  │  4. Output recommendation (JSON/Markdown) │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Why?

- **Save CI minutes** — skip irrelevant tests
- **Faster feedback** — required tests run first
- **Risk-aware** — conservative by default
- **Multi-language** — Python, JS/TS, Go, Rust

See [docs/LANGUAGES.md](docs/LANGUAGES.md) for language-specific test pattern documentation.

### Modes

- `suggest` — Comment on PR with recommendations
- `gate` — Block merge if required tests didn't run
- `local` — Run before push to catch issues early

### Roadmap

- [ ] LLM semantic classification (v0.2.0)
- [ ] Gate mode enforcement (v0.2.0)
- [ ] Dashboard with savings metrics (v0.4.0)

### License

MIT

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing guidelines, and how to add a new classifier.
