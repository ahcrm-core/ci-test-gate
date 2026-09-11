"""Tests for classifier."""

import pytest

from ci_test_gate.classifier import TestClassifier, TestRecommendation
from ci_test_gate.context_builder import ChangeContext
from ci_test_gate.diff_parser import FileChange


class TestTestClassifier:
    def test_classify_empty_diff(self):
        classifier = TestClassifier()
        context = ChangeContext(changed_files=[])
        rec = classifier.classify([], context)
        assert rec.required == []

    def test_classify_doc_only(self):
        classifier = TestClassifier()
        changes = [FileChange(path="README.md", added_lines=["# Title"])]
        context = ChangeContext(changed_files=changes)
        rec = classifier.classify(changes, context, ["tests/test_foo.py"])
        assert rec.required == []
        assert "tests/test_foo.py" in rec.optional

    def test_classify_test_file_changed(self):
        classifier = TestClassifier()
        changes = [FileChange(path="tests/test_foo.py", added_lines=["def test():"])]
        context = ChangeContext(changed_files=changes)
        rec = classifier.classify(changes, context, ["tests/test_foo.py", "tests/test_bar.py"])
        assert "tests/test_foo.py" in rec.required
        assert "tests/test_bar.py" in rec.optional

    def test_classify_with_test_files(self):
        classifier = TestClassifier()
        changes = [FileChange(path="src/main.py", added_lines=["def main():"])]
        context = ChangeContext(changed_files=changes)
        rec = classifier.classify(changes, context, ["tests/test_main.py", "tests/test_other.py"])
        assert len(rec.required) >= 1

    def test_estimate_savings(self):
        classifier = TestClassifier()
        savings = classifier._estimate_savings(["a"], ["b", "c", "d"])
        assert 0 <= savings <= 95


class TestTestRecommendation:
    def test_to_json(self):
        rec = TestRecommendation(required=["a"], recommended=["b"], optional=["c"])
        output = rec.to_json()
        assert '"required"' in output

    def test_to_markdown(self):
        rec = TestRecommendation(required=["a"], optional=["b"], reasoning="test")
        output = rec.to_markdown()
        assert "## ci-test-gate" in output
        assert "test" in output
