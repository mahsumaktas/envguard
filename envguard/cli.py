"""envguard CLI - scan for missing or orphaned environment variables."""
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from envguard.scanners.code_scanner import scan_directory_detailed, get_code_vars
from envguard.scanners.env_scanner import (
    parse_env_file, find_missing, find_orphaned, find_env_file
)

app = typer.Typer(
    help="Scan source code for missing or orphaned environment variables",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)

VERSION = "0.0.4"


@app.command()
def scan(
    src: str = typer.Argument(".", help="Source directory to scan"),
    env_file: Optional[str] = typer.Option(
        None, "--env-file", "-e",
        help="Path to .env.example file (auto-detected if not specified)",
    ),
    strict: bool = typer.Option(
        False, "--strict",
        help="Exit with code 1 if any issues found",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Save report to file (.md)",
    ),
) -> None:
    """Scan for missing or orphaned environment variables."""
    console.print(f"\n[bold cyan]envguard[/bold cyan] [dim]v{VERSION}[/dim]\n")

    src_path = Path(src).resolve()
    if not src_path.exists():
        err_console.print(f"[red]Error:[/red] Path not found: {src}")
        raise typer.Exit(code=2)

    # Find env file
    env_path = env_file or find_env_file(str(src_path))
    if not env_path:
        env_path = find_env_file(".")  # Try current directory

    # Scan code
    usages = scan_directory_detailed(str(src_path))
    code_vars = {u.var_name for u in usages}

    # Count files scanned
    scanned_files = len(set(u.filename for u in usages))

    console.print(f"[dim]Scanning:[/dim] [bold]{src}[/bold] ({scanned_files} files)\n")

    # Parse env file
    env_vars: set = set()
    if env_path:
        env_vars = parse_env_file(env_path)
        console.print(f"[dim]Env file:[/dim]  [bold]{env_path}[/bold] ({len(env_vars)} variables)\n")
    else:
        console.print("[yellow]Warning:[/yellow] No .env.example file found\n")

    # Calculate diffs
    missing = find_missing(code_vars, env_vars)
    orphaned = find_orphaned(code_vars, env_vars)
    total_issues = len(missing) + len(orphaned)

    # Display missing vars
    if missing:
        console.print(f"[bold red]Missing in .env.example[/bold red] ({len(missing)})")
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold red")
        table.add_column("Variable", style="red")
        table.add_column("Used at", style="dim")

        for var in sorted(missing):
            locations = [u for u in usages if u.var_name == var]
            loc_str = ", ".join(
                f"{Path(u.filename).name}:{u.line_number}"
                for u in locations[:3]
            )
            if len(locations) > 3:
                loc_str += f" (+{len(locations)-3} more)"
            table.add_row(f" {var}", loc_str)
        console.print(table)

    # Display orphaned vars
    if orphaned:
        console.print(f"[bold yellow]Orphaned in .env.example[/bold yellow] ({len(orphaned)})")
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold yellow")
        table.add_column("Variable", style="yellow")
        table.add_column("Status", style="dim")
        for var in sorted(orphaned):
            table.add_row(f"⚠️  {var}", "defined in .env.example but not used in code")
        console.print(table)

    # Summary
    if total_issues == 0:
        console.print("[bold green]All clear! No issues found.[/bold green]\n")
    else:
        console.print(
            f"\n[bold red]✗ {total_issues} issue(s) found.[/bold red] "
            f"({len(missing)} missing, {len(orphaned)} orphaned)\n"
        )

    # Save report
    if output:
        report = _make_report(src, env_path, missing, orphaned, code_vars, env_vars, usages)
        Path(output).write_text(report)
        console.print(f"[dim]Report saved to: {output}[/dim]")

    if strict and total_issues > 0:
        raise typer.Exit(code=1)


def _make_report(src, env_path, missing, orphaned, code_vars, env_vars, usages) -> str:
    """Generate a Markdown report."""
    lines = [
        "# envguard Report",
        "",
        f"**Source directory:** `{src}`",
        f"**Env file:** `{env_path or 'not found'}`",
        f"**Code variables found:** {len(code_vars)}",
        f"**Env file variables:** {len(env_vars)}",
        "",
    ]

    if not missing and not orphaned:
        lines.append("All clear! No issues found.")
        return "\n".join(lines)

    if missing:
        lines += [
            f"## Missing in .env.example ({len(missing)})",
            "",
            "| Variable | Used at |",
            "|----------|---------|",
        ]
        for var in sorted(missing):
            locations = [u for u in usages if u.var_name == var]
            loc_str = ", ".join(
                f"`{Path(u.filename).name}:{u.line_number}`"
                for u in locations[:3]
            )
            lines.append(f"| `{var}` | {loc_str} |")
        lines.append("")

    if orphaned:
        lines += [
            f"## Orphaned in .env.example ({len(orphaned)})",
            "",
            "| Variable | Status |",
            "|----------|--------|",
        ]
        for var in sorted(orphaned):
            lines.append(f"| `{var}` | defined but never used in code |")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    app()
