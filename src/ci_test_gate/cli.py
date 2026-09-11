"""CLI entry point for ci-test-gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ci_test_gate import __version__
from ci_test_gate.classifier import TestClassifier
from ci_test_gate.context_builder import ContextBuilder
from ci_test_gate.diff_parser import DiffParser


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ci-test-gate",
        description="LLM-powered test selection for CI — run only the tests that matter",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # `suggest` command
    suggest_parser = subparsers.add_parser("suggest", help="Suggest which tests to run")
    suggest_parser.add_argument(
        "--diff",
        type=Path,
        required=True,
        help="Path to diff file (or - for stdin)",
    )
    suggest_parser.add_argument(
        "--test-files",
        type=Path,
        help="File listing all test files (one per line)",
    )
    suggest_parser.add_argument(
        "--mode",
        choices=["suggest", "gate"],
        default="suggest",
        help="Output mode: suggest (comment) or gate (fail if required missing)",
    )
    suggest_parser.add_argument(
        "--output",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format",
    )

    args = parser.parse_args(argv)

    if args.command == "suggest":
        return _handle_suggest(args)
    return 0


def _handle_suggest(args) -> int:
    """Handle the suggest command."""
    # Read diff
    if str(args.diff) == "-":
        diff_text = sys.stdin.read()
    else:
        diff_text = args.diff.read_text()

    # Parse diff
    parser = DiffParser()
    changes = parser.parse(diff_text)

    # Build context
    builder = ContextBuilder()
    context = builder.build(changes)

    # Read test files list
    test_files: list[str] = []
    if args.test_files:
        test_files = [line.strip() for line in args.test_files.read_text().splitlines() if line.strip()]

    # Classify
    classifier = TestClassifier()
    recommendation = classifier.classify(changes, context, test_files or None)

    # Output
    if args.output == "json":
        print(recommendation.to_json())
    else:
        print(recommendation.to_markdown())

    # Gate mode: return non-zero if required tests are missing
    if args.mode == "gate" and not recommendation.required and test_files:
        return 2  # No tests identified as required

    return 0


if __name__ == "__main__":
    sys.exit(main())
