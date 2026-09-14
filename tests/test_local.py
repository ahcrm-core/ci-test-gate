"""Tests for the local subcommand."""
from __future__ import annotations
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ci_test_gate.cli import main


class TestLocalCommand:
    def test_local_no_changes(self, tmp_path, capsys):
        with patch("ci_test_gate.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = main(["local", "--base", "main"])
            assert result == 0

    def test_local_with_changes(self, tmp_path, capsys):
        with patch("ci_test_gate.cli.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="src/app.py\n", returncode=0),
                MagicMock(stdout="diff --git a/src/app.py\n+new line\n", returncode=0),
                MagicMock(stdout="tests/test_app.py\n", returncode=0),
            ]
            result = main(["local"])
            assert result == 0

    def test_local_custom_base(self, tmp_path):
        with patch("ci_test_gate.cli.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="src/app.py\n", returncode=0),
                MagicMock(stdout="diff content", returncode=0),
                MagicMock(stdout="tests/test_app.py\n", returncode=0),
            ]
            result = main(["local", "--base", "develop"])
            assert result == 0
            assert mock_run.call_args_list[0][0][0] == ["git", "diff", "--name-only", "develop...HEAD"]

    def test_local_git_error(self, tmp_path, capsys):
        import subprocess
        with patch("ci_test_gate.cli.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git", stderr="fatal: bad revision")
            result = main(["local", "--base", "nonexistent"])
            assert result == 1

    def test_local_json_output(self, tmp_path, capsys):
        with patch("ci_test_gate.cli.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="src/app.py\n", returncode=0),
                MagicMock(stdout="diff content", returncode=0),
                MagicMock(stdout="tests/test_app.py\n", returncode=0),
            ]
            result = main(["local", "--output", "json"])
            assert result == 0
