"""Context builder for LLM classification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import Diff, Language


@dataclass
class FileContext:
    """Context for a modified file."""

    path: str
    imports: list[str]
    exports: list[str]
    test_files: list[str]  # test files that might cover this file


@dataclass
class AnalysisContext:
    """Full analysis context for LLM."""

    diff: Diff
    language: Language
    file_contexts: list[FileContext]
    test_files_in_repo: list[str]
    test_framework: str = "unknown"

    @property
    def summary(self) -> str:
        """Generate a summary for the LLM prompt."""
        parts = [
            f"Language: {self.language.value}",
            f"Test framework: {self.test_framework}",
            f"\nModified files ({len(self.diff.files)}):",
        ]

        for f in self.diff.files:
            parts.append(f"  - {f.path} (+{f.additions}/-{f.deletions})")

        if self.test_files_in_repo:
            parts.append(f"\nAvailable test files ({len(self.test_files_in_repo)}):")
            for t in self.test_files_in_repo[:50]:
                parts.append(f"  - {t}")
            if len(self.test_files_in_repo) > 50:
                parts.append(f"  ... and {len(self.test_files_in_repo) - 50} more")

        return "\n".join(parts)


def detect_language(diff: Diff) -> Language:
    """Detect the primary language of a diff."""
    ext_map = {
        ".py": Language.PYTHON,
        ".js": Language.JAVASCRIPT,
        ".jsx": Language.JAVASCRIPT,
        ".ts": Language.TYPESCRIPT,
        ".tsx": Language.TYPESCRIPT,
        ".rs": Language.RUST,
        ".go": Language.GO,
        ".java": Language.JAVA,
    }

    counts: dict[Language, int] = {}
    for f in diff.files:
        ext = Path(f.path).suffix
        lang = ext_map.get(ext, Language.UNKNOWN)
        counts[lang] = counts.get(lang, 0) + 1

    if not counts:
        return Language.UNKNOWN

    return max(counts, key=counts.get)  # type: ignore[arg-type,return-value]


def detect_test_framework(language: Language) -> str:
    """Detect the likely test framework for a language."""
    framework_map = {
        Language.PYTHON: "pytest",
        Language.JAVASCRIPT: "jest",
        Language.TYPESCRIPT: "jest",
        Language.RUST: "cargo test",
        Language.GO: "go test",
        Language.JAVA: "junit",
        Language.UNKNOWN: "unknown",
    }
    return framework_map.get(language, "unknown")


def find_test_files(repo_root: Path, language: Language) -> list[str]:
    """Find test files in a repository."""
    patterns = {
        Language.PYTHON: ["test_*.py", "*_test.py", "tests/**/*.py"],
        Language.JAVASCRIPT: ["**/*.test.js", "**/*.spec.js", "**/tests/**/*.js"],
        Language.TYPESCRIPT: ["**/*.test.ts", "**/*.spec.ts", "**/tests/**/*.ts"],
        Language.RUST: ["src/**/*_test.rs", "tests/**/*.rs"],
        Language.GO: ["**/*_test.go"],
        Language.JAVA: ["**/*Test.java", "**/*Tests.java"],
    }

    glob_patterns = patterns.get(language, ["**/test*"])
    results = []
    for pattern in glob_patterns:
        for f in repo_root.glob(pattern):
            results.append(str(f.relative_to(repo_root)))
    return sorted(results)


def build_context(
    diff: Diff,
    repo_root: str | Path = ".",
) -> AnalysisContext:
    """Build full analysis context."""
    repo_root = Path(repo_root)
    language = detect_language(diff)
    framework = detect_test_framework(language)

    # Try to find imports/exports from hunks
    file_contexts: list[FileContext] = []
    for f in diff.files:
        imports = []
        exports = []
        for hunk in f.hunks:
            for line in hunk.split("\n"):
                line = line.strip()
                if language == Language.PYTHON:
                    if line.startswith(("import ", "from ")):
                        imports.append(line)
                    elif line.startswith(("def ", "class ")):
                        exports.append(line.split("(")[0])
                elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
                    if line.startswith(("import ", "require(")):
                        imports.append(line)
                    elif line.startswith(("export ", "function ", "class ", "const ")):
                        exports.append(line.split("(")[0].split(" ")[-1])

        file_contexts.append(FileContext(
            path=f.path,
            imports=imports,
            exports=exports,
            test_files=[],
        ))

    test_files = find_test_files(repo_root, language)

    return AnalysisContext(
        diff=diff,
        language=language,
        file_contexts=file_contexts,
        test_files_in_repo=test_files,
        test_framework=framework,
    )
