"""Tests to boost coverage for context.py and context_builder.py."""

import pytest
from pathlib import Path

from ci_test_gate.context import (
    AnalysisContext,
    FileContext,
    build_context,
    detect_language,
    detect_test_framework,
    find_test_files,
)
from ci_test_gate.context_builder import ChangeContext, ContextBuilder
from ci_test_gate.diff_parser import FileChange
from ci_test_gate.models import Diff, DiffFile, Language


# ===== context.py coverage boosts =====

class TestDetectLanguageEdgeCases:
    def test_empty_files(self):
        diff = Diff(files=[])
        assert detect_language(diff) == Language.UNKNOWN

    def test_unknown_extension(self):
        diff = Diff(files=[DiffFile(path="src/main.txt")])
        assert detect_language(diff) == Language.UNKNOWN

    def test_typescript_priority(self):
        diff = Diff(files=[
            DiffFile(path="src/a.ts"),
            DiffFile(path="src/b.py"),
        ])
        assert detect_language(diff) == Language.TYPESCRIPT


class TestDetectTestFramework:
    def test_unknown_language(self):
        assert detect_test_framework(Language.UNKNOWN) == "unknown"

    def test_all_languages(self):
        for lang in Language:
            fw = detect_test_framework(lang)
            assert fw != "" or lang == Language.UNKNOWN


class TestFindTestFiles:
    def test_python_tests(self, tmp_path):
        (tmp_path / "test_foo.py").touch()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_bar.py").touch()
        result = find_test_files(tmp_path, Language.PYTHON)
        assert len(result) == 2

    def test_javascript_tests(self, tmp_path):
        (tmp_path / "foo.test.js").touch()
        result = find_test_files(tmp_path, Language.JAVASCRIPT)
        assert len(result) == 1

    def test_rust_tests(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "lib.rs").touch()
        result = find_test_files(tmp_path, Language.RUST)
        assert len(result) == 0

    def test_go_tests(self, tmp_path):
        (tmp_path / "foo_test.go").touch()
        result = find_test_files(tmp_path, Language.GO)
        assert len(result) == 1

    def test_unknown_language(self, tmp_path):
        (tmp_path / "test_foo.txt").touch()
        result = find_test_files(tmp_path, Language.UNKNOWN)
        assert len(result) == 1


class TestBuildContext:
    def test_python_imports_extraction(self):
        diff = Diff(files=[
            DiffFile(path="src/main.py", additions=2, deletions=0, hunks=["@@ -1,2 +1,5 @@\n import os\n from pathlib import Path\n+\n+import sys\n+from datetime import datetime"]),
        ])
        ctx = build_context(diff, repo_root=Path("/nonexistent"))
        assert ctx.language == Language.PYTHON
        assert len(ctx.file_contexts) == 1
        # Context lines (no prefix) are captured; +added lines are skipped by design
        assert "import os" in ctx.file_contexts[0].imports

    def test_ts_imports_extraction(self):
        diff = Diff(files=[
            DiffFile(path="src/app.ts", additions=2, deletions=0, hunks=["@@ -1,1 +1,3 @@\n import React from 'react'\n+\n+import { useState } from 'react'"]),
        ])
        ctx = build_context(diff, repo_root=Path("/nonexistent"))
        assert ctx.language == Language.TYPESCRIPT

    def test_multiple_files(self):
        diff = Diff(files=[
            DiffFile(path="src/a.py", additions=1, deletions=0),
            DiffFile(path="src/b.ts", additions=1, deletions=0),
        ])
        ctx = build_context(diff, repo_root=Path("/nonexistent"))
        assert len(ctx.file_contexts) == 2


# ===== context_builder.py coverage boosts =====

class TestContextBuilderImports:
    def test_js_imports(self):
        changes = [
            FileChange(path="src/app.js", added_lines=["import React from 'react'"]),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "src/app.js" in ctx.imports_added
        assert "react" in ctx.imports_added["src/app.js"]

    def test_ts_imports(self):
        changes = [
            FileChange(path="src/app.ts", added_lines=["import { foo } from 'bar'"]),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "src/app.ts" in ctx.imports_added

    def test_py_imports(self):
        changes = [
            FileChange(path="src/main.py", added_lines=["from os import path", "import sys"]),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "src/main.py" in ctx.imports_added
        assert "os" in ctx.imports_added["src/main.py"]
        assert "sys" in ctx.imports_added["src/main.py"]

    def test_go_imports(self):
        changes = [
            FileChange(path="main.go", added_lines=['import "fmt"']),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "main.go" in ctx.imports_added

    def test_rust_imports(self):
        changes = [
            FileChange(path="src/lib.rs", added_lines=["use std::collections::HashMap;"]),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "src/lib.rs" in ctx.imports_added


class TestContextBuilderTestRunners:
    def test_pytest_ini(self):
        changes = [FileChange(path="pytest.ini", added_lines=["[pytest]"])]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "pytest" in ctx.test_runners_detected

    def test_setup_cfg(self):
        changes = [FileChange(path="setup.cfg", added_lines=["[tool:pytest]"])]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "pytest" in ctx.test_runners_detected

    def test_tox_ini(self):
        changes = [FileChange(path="tox.ini", added_lines=["[tox]"])]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "pytest" in ctx.test_runners_detected

    def test_jest_config(self):
        changes = [FileChange(path="jest.config.js", added_lines=["module.exports = {}"])]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "jest" in ctx.test_runners_detected

    def test_package_json_jest(self):
        changes = [FileChange(path="package.json", added_lines=['"jest"'])]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "jest" in ctx.test_runners_detected

    def test_package_json_vitest(self):
        changes = [FileChange(path="package.json", added_lines=['"vitest"'])]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "vitest" in ctx.test_runners_detected

    def test_cargo_toml(self):
        changes = [FileChange(path="Cargo.toml", added_lines=["[package]"])]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "cargo test" in ctx.test_runners_detected

    def test_go_mod(self):
        changes = [FileChange(path="go.mod", added_lines=["module foo"])]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "go test" in ctx.test_runners_detected


class TestContextBuilderFunctions:
    def test_python_functions(self):
        changes = [
            FileChange(path="src/main.py", added_lines=["def hello():", "class World:"]),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "src/main.py" in ctx.functions_changed

    def test_ts_functions(self):
        changes = [
            FileChange(path="src/app.ts", added_lines=["function hello(): void", "export async function bar()"]),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "src/app.ts" in ctx.functions_changed

    def test_go_functions(self):
        changes = [
            FileChange(path="main.go", added_lines=["func main()"]),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "main.go" in ctx.functions_changed

    def test_rust_functions(self):
        changes = [
            FileChange(path="src/lib.rs", added_lines=["pub fn hello()"]),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert "src/lib.rs" in ctx.functions_changed


class TestContextBuilderScopeEstimation:
    def test_medium_scope_by_files(self):
        changes = [FileChange(path=f"file{i}.py", added_lines=[f"+line{j}" for j in range(3)]) for i in range(10)]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert ctx.estimated_scope == "medium"

    def test_medium_scope_by_lines(self):
        changes = [FileChange(path="big.py", added_lines=[f"+line{i}" for i in range(200)])]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        assert ctx.estimated_scope == "medium"


class TestChangeContextToJson:
    def test_full_output(self):
        changes = [
            FileChange(path="src/main.py", added_lines=["import os", "def hello():"]),
        ]
        builder = ContextBuilder()
        ctx = builder.build(changes)
        output = ctx.to_prompt_context()
        assert "Scope: small" in output
        assert "Changed files: 1" in output
        assert "Imports added:" in output
        assert "Functions changed:" in output
