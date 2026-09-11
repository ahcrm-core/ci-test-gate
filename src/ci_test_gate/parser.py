"""Diff parsing utilities."""

from __future__ import annotations

import re

from .models import Diff, DiffFile

# Matches: diff --git a/path b/path
DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)
# Matches: @@ -old,count +new,count @@
HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)


def parse_unified_diff(raw: str) -> Diff:
    """Parse a unified diff string into a Diff model."""
    if not raw.strip():
        return Diff(raw=raw)

    files: list[DiffFile] = []

    # Split by diff headers
    parts = DIFF_HEADER_RE.split(raw)
    # parts[0] is everything before first header (empty or preamble)
    # then alternating: path_a, path_b, body...

    for i in range(1, len(parts), 3):
        if i + 2 > len(parts):
            break

        path_b = parts[i + 1]
        body = parts[i + 2] if i + 2 < len(parts) else ""

        # Count additions and deletions from hunks
        additions = 0
        deletions = 0
        hunks: list[str] = []

        # Split body into per-file sections
        lines = body.split("\n")
        current_hunk_lines: list[str] = []
        in_hunk = False

        for line in lines:
            if line.startswith("@@"):
                if current_hunk_lines:
                    hunks.append("\n".join(current_hunk_lines))
                current_hunk_lines = [line]
                in_hunk = True
            elif in_hunk:
                if line.startswith("+") and not line.startswith("+++"):
                    additions += 1
                    current_hunk_lines.append(line)
                elif line.startswith("-") and not line.startswith("---"):
                    deletions += 1
                    current_hunk_lines.append(line)
                elif line.startswith(" "):
                    current_hunk_lines.append(line)
                elif line.startswith("\\"):
                    # "\ No newline at end of file" — skip
                    pass
                elif line == "":
                    current_hunk_lines.append(line)
                else:
                    # End of hunk
                    if current_hunk_lines:
                        hunks.append("\n".join(current_hunk_lines))
                        current_hunk_lines = []
                    in_hunk = False

        if current_hunk_lines:
            hunks.append("\n".join(current_hunk_lines))

        files.append(
            DiffFile(
                path=path_b,
                additions=additions,
                deletions=deletions,
                hunks=hunks[:10],  # limit stored hunks
            )
        )

    return Diff(files=files, raw=raw)


def parse_from_git(base: str = "main", head: str = "HEAD") -> Diff:
    """Generate and parse a diff from git."""
    import subprocess

    result = subprocess.run(
        ["git", "diff", f"{base}...{head}", "--unified=3"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr}")

    return parse_unified_diff(result.stdout)
