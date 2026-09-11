"""Tests for diff parser."""

import pytest

from ci_test_gate.diff_parser import DiffParser, FileChange


class TestDiffParser:
    def test_parse_simple_diff(self):
        diff_text = """diff --git a/src/foo.py b/src/foo.py
--- a/src/foo.py
+++ b/src/foo.py
@@ -1,3 +1,5 @@
 def hello():
-    return "hello"
+    return "world"
+
+def extra():
+    pass
"""
        parser = DiffParser()
        changes = parser.parse(diff_text)
        assert len(changes) == 1
        assert changes[0].path == "src/foo.py"
        assert len(changes[0].added_lines) == 4
        assert len(changes[0].removed_lines) == 1

    def test_parse_new_file(self):
        diff_text = """diff --git a/new_file.py b/new_file.py
new file mode 100644
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,3 @@
+def new_func():
+    return True
"""
        parser = DiffParser()
        changes = parser.parse(diff_text)
        assert len(changes) == 1
        assert changes[0].is_new is True

    def test_parse_deleted_file(self):
        diff_text = """diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def old():
-    pass
"""
        parser = DiffParser()
        changes = parser.parse(diff_text)
        assert len(changes) == 1
        assert changes[0].is_deleted is True

    def test_parse_multiple_files(self):
        diff_text = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,2 @@
-old
+new
diff --git b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -1,2 +1,2 @@
-old2
+new2
"""
        parser = DiffParser()
        changes = parser.parse(diff_text)
        assert len(changes) == 2

    def test_get_changed_extensions(self):
        diff_text = """diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,2 +1,2 @@
-a
+b
diff --git a/bar.ts b/bar.ts
--- a/bar.ts
+++ b/bar.ts
@@ -1,2 +1,2 @@
-c
+d
"""
        parser = DiffParser()
        changes = parser.parse(diff_text)
        exts = parser.get_changed_extensions(changes)
        assert exts == {".py", ".ts"}

    def test_filter_by_extension(self):
        diff_text = """diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,2 +1,2 @@
-a
+b
diff --git a/bar.ts b/bar.ts
--- a/bar.ts
+++ b/bar.ts
@@ -1,2 +1,2 @@
-c
+d
"""
        parser = DiffParser()
        changes = parser.parse(diff_text)
        py_changes = parser.filter_by_extension(changes, ".py")
        assert len(py_changes) == 1
        assert py_changes[0].path == "foo.py"


class TestFileChange:
    def test_extension(self):
        fc = FileChange(path="src/foo.py")
        assert fc.extension == ".py"

    def test_is_test_file_pytest(self):
        fc = FileChange(path="tests/test_foo.py")
        assert fc.is_test_file is True

    def test_is_test_file_jest(self):
        fc = FileChange(path="src/component.test.ts")
        assert fc.is_test_file is True

    def test_is_test_file_not_test(self):
        fc = FileChange(path="src/main.py")
        assert fc.is_test_file is False
