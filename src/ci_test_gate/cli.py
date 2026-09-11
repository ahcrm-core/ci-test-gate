"""CLI entry point for ci-test-gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .context import build_context
from .llm import classify_with_llm
from .models import OutputMode, TestRisk
from .parser import parse_unified_diff


console = Console()


def _format_table(result) -> Table:
    """Format analysis result as a rich table."""
    table = Table(title="ci-test-gate Analysis", show_lines=True)
    table.add_column("Risk", style="bold", width=12)
    table.add_column("Test Path", min_width=40)
    table.add_column("Reason", min_width=30)
    table.add_column("Conf.", justify="right", width=6)

    risk_styles = {
        TestRisk.REQUIRED: "red",
        TestRisk.RECOMMENDED: "yellow",
        TestRisk.OPTIONAL: "green",
    }

    for rec in result.recommendations:
        style = risk_styles.get(rec.risk, "white")
        table.add_row(
            f"[{style}]{rec.risk.value.upper()}[/{style}]",
            rec.suite.path,
            rec.reason[:60],
            f"{rec.confidence:.0%}",
        )

    return table


def _format_markdown(result) -> str:
    """Format analysis result as a Markdown comment."""
    lines = [
        "## 🧪 ci-test-gate Test Selection",
        "",
        f"**Language:** {result.language.value} | **Framework:** Unknown",
        "",
    ]

    if result.required:
        lines.append(f"### 🔴 REQUIRED ({len(result.required)})")
        lines.append("")
        for rec in result.required:
            lines.append(f"- `{rec.suite.path}` — {rec.reason}")
        lines.append("")

    if result.recommended:
        lines.append(f"### 🟡 RECOMMENDED ({len(result.recommended)})")
        lines.append("")
        for rec in result.recommended:
            lines.append(f"- `{rec.suite.path}` — {rec.reason}")
        lines.append("")

    if result.optional:
        lines.append(f"### 🟢 OPTIONAL ({len(result.optional)})")
        lines.append("")
        for rec in result.optional:
            lines.append(f"- `{rec.suite.path}` — {rec.reason}")
        lines.append("")

    if result.estimated_savings > 0:
        lines.append(f"**Estimated savings:** {result.estimated_savings:.0f}s vs full suite")
        lines.append("")

    lines.append(f"*{result.summary}*")
    lines.append("")
    lines.append("---")
    lines.append("*Analyzed by [ci-test-gate](https://github.com/yunaremaia/ci-test-gate)*")
    return "\n".join(lines)


@click.group()
@click.version_option()
def main():
    """ci-test-gate — LLM-powered test selection for CI."""
    pass


@main.command()
@click.option("--diff-file", type=click.Path(exists=True), help="Path to diff file")
@click.option("--diff-text", help="Raw diff text")
@click.option("--repo-root", default=".", help="Repository root directory")
@click.option("--mode", type=click.Choice(["suggest", "gate", "local"]), default="suggest")
@click.option("--output", type=click.Choice(["table", "json", "markdown"]), default="table")
@click.option("--base", default="main", help="Base branch for diff")
def analyze(diff_file, diff_text, repo_root, mode, output, base):
    """Analyze a diff and recommend which tests to run."""
    if diff_file:
        raw = Path(diff_file).read_text()
    elif diff_text:
        raw = diff_text
    else:
        # Try to get diff from git
        import subprocess
        result = subprocess.run(
            ["git", "diff", f"{base}...HEAD", "--unified=3"],
            capture_output=True, text=True, cwd=repo_root,
        )
        if result.returncode != 0:
            console.print(f"[red]Error: git diff failed: {result.stderr}[/red]")
            sys.exit(1)
        raw = result.stdout

    diff = parse_unified_diff(raw)
    ctx = build_context(diff, repo_root=repo_root)
    result = classify_with_llm(ctx)

    if output == "table":
        console.print(_format_table(result))
    elif output == "json":
        console.print_json(result.model_dump_json())
    elif output == "markdown":
        console.print(_format_markdown(result))

    # Exit code for gate mode
    if mode == "gate":
        if result.required:
            console.print(f"\n[green]✓ {len(result.required)} required tests identified[/green]")
        else:
            console.print("\n[yellow]⚠ No required tests — all changes are low-risk[/yellow]")


@main.command()
@click.option("--repo-root", default=".", help="Repository root directory")
@click.option("--base", default="main", help="Base branch for diff")
def discover(repo_root, base):
    """Discover available test files in a repository."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", f"{base}...HEAD", "--unified=3"],
        capture_output=True, text=True, cwd=repo_root,
    )
    if result.returncode != 0:
        console.print(f"[red]Error: git diff failed: {result.stderr}[/red]")
        sys.exit(1)

    diff = parse_unified_diff(result.stdout)
    ctx = build_context(diff, repo_root=repo_root)

    console.print(f"[bold]Language:[/bold] {ctx.language.value}")
    console.print(f"[bold]Framework:[/bold] {ctx.test_framework}")
    console.print(f"\n[bold]Modified files:[/bold]")
    for f in diff.files:
        console.print(f"  {f.path} (+{f.additions}/-{f.deletions})")
    console.print(f"\n[bold]Available test files ({len(ctx.test_files_in_repo)}):[/bold]")
    for t in ctx.test_files_in_repo:
        console.print(f"  {t}")


if __name__ == "__main__":
    main()
