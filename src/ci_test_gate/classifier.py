"""LLM-powered test classifier — recommends which tests to run."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .context_builder import ChangeContext
from .diff_parser import DiffParser, FileChange


@dataclass
class TestRecommendation:
    """Recommendation of which tests to run."""
    required: list[str] = field(default_factory=list)
    recommended: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)
    reasoning: str = ""
    estimated_savings_pct: int = 0

    def to_json(self) -> str:
        return json.dumps({
            "required": self.required,
            "recommended": self.recommended,
            "optional": self.optional,
            "reasoning": self.reasoning,
            "estimated_savings_pct": self.estimated_savings_pct,
        }, indent=2)

    def to_markdown(self) -> str:
        lines = ["## ci-test-gate Recommendation", ""]
        if self.reasoning:
            lines.append(f"**Reasoning:** {self.reasoning}")
            lines.append("")
        if self.required:
            lines.append("### Required (must run)")
            for t in self.required:
                lines.append(f"- {t}")
            lines.append("")
        if self.recommended:
            lines.append("### Recommended")
            for t in self.recommended:
                lines.append(f"- {t}")
            lines.append("")
        if self.optional:
            lines.append("### Optional (can skip)")
            for t in self.optional:
                lines.append(f"- {t}")
            lines.append("")
        if self.estimated_savings_pct:
            lines.append(f"**Estimated CI time savings:** {self.estimated_savings_pct}%")
        return "\n".join(lines)


class TestClassifier:
    """Classify tests based on code changes."""

    SYSTEM_PROMPT = """You are a test selection expert. Given code changes, determine which tests should be run.
Return JSON with:
- required: array of test files/paths that MUST run (high regression risk)
- recommended: array of test files/paths that SHOULD run (medium risk)
- optional: array of test files/paths that CAN be skipped (low risk)
- reasoning: one sentence explaining the decision
- estimated_savings_pct: number 0-95 estimating CI time saved by skipping optional tests

Rules:
1. If source file changed, its direct test file is required
2. If a shared util/module changed, all consumers' tests are required
3. Doc-only changes → required=[], optional=all
4. Test file changes themselves → that test file is required
5. Be conservative: when in doubt, mark as recommended not optional"""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model

    def classify(
        self,
        changes: list[FileChange],
        context: ChangeContext,
        test_files: list[str] | None = None,
    ) -> TestRecommendation:
        """Classify which tests should run based on changes."""
        if not changes:
            return TestRecommendation(
                required=[],
                recommended=[],
                optional=test_files or [],
                reasoning="No code changes detected",
                estimated_savings_pct=90,
            )

        # Check if only documentation changed
        doc_extensions = {".md", ".rst", ".txt", ".adoc"}
        non_doc_changes = [c for c in changes if c.extension not in doc_extensions]
        if not non_doc_changes:
            return TestRecommendation(
                required=[],
                recommended=[],
                optional=test_files or [],
                reasoning="Documentation-only changes",
                estimated_savings_pct=95,
            )

        # Default path-based classification as fallback
        return self._path_based_classify(changes, context, test_files or [])

    def _path_based_classify(
        self,
        changes: list[FileChange],
        context: ChangeContext,
        test_files: list[str],
    ) -> TestRecommendation:
        """Fallback: classify based on file paths (no LLM)."""
        required = []
        recommended = []
        optional = []

        for change in changes:
            if change.is_test_file:
                required.append(change.path)
                continue

            # Find corresponding test file
            candidate = self._find_test_file(change.path, test_files)
            if candidate and candidate not in required:
                required.append(candidate)

        # Remaining test files are optional
        for tf in test_files:
            if tf not in required:
                optional.append(tf)

        return TestRecommendation(
            required=required,
            recommended=recommended,
            optional=optional,
            reasoning=f"Path-based selection: {len(changes)} files changed, {len(required)} test files matched",
            estimated_savings_pct=self._estimate_savings(required, optional),
        )

    def _find_test_file(self, source_path: str, test_files: list[str]) -> str | None:
        """Find the test file corresponding to a source file."""
        from pathlib import Path
        p = Path(source_path)
        candidates = [
            f"tests/test_{p.name}",
            f"tests/{p.stem}_test.py",
            f"test/test_{p.name}",
            f"{p.parent}/test_{p.name}",
            f"{p.parent}/{p.stem}_test.py",
        ]
        for c in candidates:
            if c in test_files:
                return c
        return None

    def _estimate_savings(self, required: list[str], optional: list[str]) -> int:
        """Estimate CI time savings percentage."""
        total = len(required) + len(optional)
        if total == 0:
            return 0
        return min(95, int(len(optional) / total * 100))


class LLMTestClassifier(TestClassifier):
    """LLM-powered classifier using OpenAI-compatible API."""

    def classify(
        self,
        changes: list[FileChange],
        context: ChangeContext,
        test_files: list[str] | None = None,
    ) -> TestRecommendation:
        """Classify using LLM."""
        if not self.api_key:
            # Fall back to path-based
            return self._path_based_classify(changes, context, test_files or [])

        # For now, use path-based (LLM integration will be v0.2.0)
        return self._path_based_classify(changes, context, test_files or [])
