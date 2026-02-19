"""envguard CLI entry point."""
import typer
from rich.console import Console

app = typer.Typer(help="Scan for missing or orphaned environment variables")
console = Console()


@app.command()
def scan(
    src: str = typer.Option(".", help="Source directory to scan"),
    actions: bool = typer.Option(False, help="Also scan GitHub Actions workflows"),
    all_: bool = typer.Option(False, "--all", help="Scan code + actions"),
):
    """Scan for missing or orphaned environment variables."""
    console.print("[bold green]envguard v0.0.1[/bold green]")
    console.print("[yellow]Scanning... (coming soon)[/yellow]")
