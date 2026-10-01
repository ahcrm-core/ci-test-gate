"""Regression tests for the CI Test Gate workflow (.github/workflows/test-gate.yml).

The gate's "Publish recommendation" step had two defects that no unit test could
see, because they live entirely in the workflow file:

1. It treated a 403 from the comment API as a hard failure. Every pull request
   opened from a fork gets a read-only GITHUB_TOKEN, so the step could never
   succeed by design and the gate was permanently red on outside contributions.
2. It interpolated diff-derived text into the github-script body through a
   ``${{ }}`` expression. A backtick in a fork PR's diff could break out of the
   template literal and run arbitrary JavaScript in the runner.

These tests parse the workflow and assert the properties that keep both defects
from coming back. They are deliberately static: the point is that the workflow
itself keeps the invariant, not that a simulated runner behaves correctly.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "test-gate.yml"

GITHUB_EXPRESSION = re.compile(r"\$\{\{.*?\}\}", re.DOTALL)


@pytest.fixture(scope="module")
def workflow_text() -> str:
    if not WORKFLOW.is_file():
        pytest.skip(f"workflow not present at {WORKFLOW}")
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow(workflow_text: str) -> dict:
    return yaml.safe_load(workflow_text)


@pytest.fixture(scope="module")
def script_body(workflow_text: str) -> str:
    """The JavaScript passed to actions/github-script, as raw text.

    Read as text rather than via the YAML parser on purpose: interpolating the
    report through a ``${{ }}`` expression is invisible once YAML has parsed it
    into a plain string, so the assertion below needs the original bytes.
    """
    match = re.search(r"^[ \t]*script:[ \t]*\|[ \t]*\r?\n", workflow_text, re.MULTILINE)
    assert match, "no github-script 'script: |' block found"
    rest = workflow_text[match.end() :]
    indent = re.match(r"^[ \t]*", rest.split("\n")[0]).group(0)
    assert indent, "empty github-script block"
    lines = []
    for line in rest.split("\n"):
        if not line.strip():
            lines.append("")
            continue
        if not line.startswith(indent):
            break
        lines.append(line[len(indent) :])
    return "\n".join(lines)


def test_workflow_parses_as_valid_yaml(workflow: dict) -> None:
    """A YAML error here silently disables the gate on every PR."""
    assert isinstance(workflow, dict)
    assert "jobs" in workflow, "workflow defines no jobs"


def test_gate_job_grants_issues_write(workflow: dict) -> None:
    """Commenting needs issues: write; without it even same-repo PRs get a 403."""
    permissions = workflow["jobs"]["ci-test-gate"].get("permissions", {})
    assert permissions.get("issues") == "write"


def test_report_is_not_interpolated_into_the_script(script_body: str) -> None:
    """The report is untrusted (it is derived from a fork PR's diff).

    Passing it through a ``${{ }}`` expression would splice its text into the
    JavaScript source, so a backtick could break out of the template literal.
    """
    assert not GITHUB_EXPRESSION.search(script_body), (
        "the github-script body interpolates a ${{ }} expression; diff-derived text "
        "must be read from disk via an env var instead"
    )


def test_report_is_read_from_an_env_var(workflow: dict) -> None:
    steps = workflow["jobs"]["ci-test-gate"]["steps"]
    publish = next(s for s in steps if s.get("name") == "Publish recommendation")
    report_path = publish.get("env", {}).get("GATE_REPORT")
    assert report_path, "GATE_REPORT env var is not wired up"
    assert "readFileSync(process.env.GATE_REPORT" in publish["with"]["script"]


def _strip_js_comments(source: str) -> str:
    """Remove // line comments so commented-out code cannot satisfy an assertion."""
    return "\n".join(re.sub(r"(?m)//.*$", "", line) for line in source.split("\n"))


def _catch_block(script_body: str) -> str:
    """The body of the ``catch`` block around the comment API call.

    Returned as real statements with comments stripped, so a test can reason about
    which code actually runs. Matching the closing brace by counting (rather than
    by regex up to the next ``if``) means the whole block is covered, including any
    unreachable code left behind after an unconditional ``throw``.
    """
    match = re.search(r"catch\s*\(\s*(\w+)\s*\)\s*\{", script_body)
    assert match, "the comment API call is not wrapped in a try/catch"
    start = match.end() - 1
    depth = 0
    for index in range(start, len(script_body)):
        char = script_body[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return _strip_js_comments(script_body[start + 1 : index])
    raise AssertionError("unbalanced braces in the catch block")


def test_403_from_the_comment_api_is_not_fatal(script_body: str) -> None:
    """Fork PRs get a read-only token: a 403 must not turn the gate red.

    Asserts on the real statements rather than on the presence of a guard, so an
    unreachable ``if (error.status === 403)`` sitting after an unconditional
    ``throw`` is correctly treated as a failure.
    """
    block = _catch_block(script_body)
    guard = re.search(r"if\s*\([^)]*\.status\s*===\s*403[^)]*\)\s*\{", block)
    assert guard, f"403 is not detected in the catch block:\n{block.strip()}"

    before = block[: guard.start()]
    after = block[guard.end() :]

    assert "throw" not in before, (
        "the catch block throws before the 403 guard, so a read-only token still "
        f"fails the step:\n{before.strip()}"
    )
    guard_body = re.match(r"\s*([^{}]*)\}", after)
    assert guard_body and "return" in guard_body.group(1), (
        "the 403 branch does not return; a 403 would keep propagating"
    )


def test_other_api_errors_are_still_fatal(script_body: str) -> None:
    """Swallowing every error would turn the gate into a no-op that always passes."""
    block = _catch_block(script_body)
    guard = re.search(r"if\s*\([^)]*\.status\s*===\s*403[^)]*\)\s*\{", block)
    assert guard, "no 403 guard, so there is no selective handling to verify"
    assert "throw" in block[guard.end() :], (
        "non-403 errors are swallowed; a genuine API failure would be reported as a "
        "passing gate"
    )


def _top_level_prefix(script_body: str, end: int) -> str:
    """The part of the script before ``end``, with deferred code blanked out.

    Two constructs can hold code that does *not* run at this point in the script:

    * ``{ ... }`` blocks belonging to a function, class or arrow callback;
    * a brace-less arrow body, ``() => doThing()``, which ends at the next
      statement terminator rather than at any brace.

    Both are replaced by blanks so their contents cannot masquerade as statements
    that execute before the comment API call. Only genuinely top-level statements
    survive.
    """
    text = _strip_js_comments(script_body[:end])
    out = []
    depth = 0
    for char in text:
        if char == "{":
            depth += 1
            out.append(" ")
            continue
        if char == "}":
            depth = max(0, depth - 1)
            out.append(" ")
            continue
        out.append("\n" if char == "\n" else (" " if depth else char))

    top = "".join(out)
    # Blank out brace-less arrow bodies: from "=>" up to the next ";".
    result = []
    index = 0
    while index < len(top):
        if top.startswith("=>", index):
            end_arrow = top.find(";", index)
            if end_arrow == -1:
                end_arrow = len(top)
            result.append(" " * (end_arrow - index))
            index = end_arrow
            continue
        result.append(top[index])
        index += 1
    return "".join(result)


def test_recommendation_is_always_written_to_the_job_summary(script_body: str) -> None:
    """On fork PRs the comment is impossible, so the summary is the only channel.

    The report must reach the summary file *before* the comment is attempted.
    Deferring it -- even to a closure declared earlier in the source -- does not
    count: on a fork PR the 403 is thrown at the call site, so anything that has
    not actually executed by then is lost exactly when it matters most.
    """
    call_at = script_body.index("createComment")
    # Statements that really run before the API call: text outside function,
    # class and callback bodies. A wrapper like `() => fs.appendFileSync(...)`
    # only runs when invoked, so its position in the source says nothing.
    prelude = _top_level_prefix(script_body, call_at)

    summary_at = prelude.find("GITHUB_STEP_SUMMARY")
    assert summary_at != -1, (
        "the report is not written to the job summary as a top-level statement "
        f"before the comment is attempted:\n{prelude.strip()}"
    )
    # Nothing that can throw may run first: on a fork PR the report would be lost
    # together with the failure that precedes it.
    before = prelude[:summary_at]
    for hazard in ("await", "throw", "createComment", "createCheckRun"):
        assert hazard not in before, (
            f"{hazard!r} runs before the job summary is written; on a fork PR that "
            "failure would discard the recommendation entirely"
        )


def test_analyze_step_fails_on_empty_output(workflow: dict) -> None:
    """An empty report must not be posted as a successful-looking comment."""
    steps = workflow["jobs"]["ci-test-gate"]["steps"]
    analyze = next(s for s in steps if s.get("name") == "Analyze PR")
    assert "test -s" in analyze["run"], "an empty gate report is not rejected"


def test_no_step_is_allowed_to_fail_silently(workflow: dict) -> None:
    """``continue-on-error`` would hide real breakage in the gate itself."""
    steps = workflow["jobs"]["ci-test-gate"]["steps"]
    offenders = [s.get("name", s.get("uses")) for s in steps if s.get("continue-on-error")]
    assert not offenders, f"steps ignoring failures: {offenders}"