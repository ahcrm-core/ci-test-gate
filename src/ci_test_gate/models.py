"""Core models for ci-test-gate."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TestRisk(str, Enum):
    """Risk level for a test suite."""

    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class Language(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    UNKNOWN = "unknown"


class DiffFile(BaseModel):
    """A single file in a diff."""

    path: str
    additions: int = 0
    deletions: int = 0
    hunks: list[str] = Field(default_factory=list)


class Diff(BaseModel):
    """A parsed diff."""

    files: list[DiffFile] = Field(default_factory=list)
    raw: str = ""

    @property
    def all_paths(self) -> list[str]:
        return [f.path for f in self.files]

    @property
    def source_paths(self) -> list[str]:
        """Non-test source paths."""
        return [f.path for f in self.files if not self._is_test_path(f.path)]

    @property
    def test_paths(self) -> list[str]:
        """Test file paths."""
        return [f.path for f in self.files if self._is_test_path(f.path)]

    @staticmethod
    def _is_test_path(path: str) -> bool:
        """Heuristic: is this a test file?"""
        p = path.lower()
        markers = ["test_", "_test.", "test/", "tests/", "spec/", ".spec.", ".test."]
        return any(m in p for m in markers)


class TestSuite(BaseModel):
    """A test suite or file."""

    path: str
    framework: str = "unknown"
    estimated_duration: float = 0.0  # seconds


class TestRecommendation(BaseModel):
    """A test suite recommendation."""

    suite: TestSuite
    risk: TestRisk
    reason: str = ""
    confidence: float = 0.8  # 0-1


class AnalysisResult(BaseModel):
    """Full analysis result."""

    recommendations: list[TestRecommendation] = Field(default_factory=list)
    language: Language = Language.UNKNOWN
    estimated_savings: float = 0.0  # seconds saved vs running everything
    summary: str = ""

    @property
    def required(self) -> list[TestRecommendation]:
        return [r for r in self.recommendations if r.risk == TestRisk.REQUIRED]

    @property
    def recommended(self) -> list[TestRecommendation]:
        return [r for r in self.recommendations if r.risk == TestRisk.RECOMMENDED]

    @property
    def optional(self) -> list[TestRecommendation]:
        return [r for r in self.recommendations if r.risk == TestRisk.OPTIONAL]


class OutputMode(str, Enum):
    """CLI output mode."""

    SUGGEST = "suggest"
    GATE = "gate"
    LOCAL = "local"
