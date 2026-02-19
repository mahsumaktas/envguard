import click
from pathlib import Path
from .scanners.code_scanner import scan_directory, get_unique_vars
from .scanners.env_scanner import parse_env_file, find_env_file, find_missing, find_orphaned

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    RICH = True
except ImportError:
    RICH = False

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """envguard: Never deploy with a missing environment variable."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@main.command()
@click.argument('path', default='.')
@click.option('--strict', is_flag=True, help='Exit code 1 if issues found')
@click.option('--env-file', default=None, help='Path to .env.example file')
@click.option('--actions', is_flag=True, help='Also scan GitHub Actions workflows')
def scan(path, strict, env_file, actions):
    """Scan for missing or orphaned environment variables."""
    from .scanners.actions_scanner import scan_actions_directory, get_github_secret_names

    # Code scanning
    usages = scan_directory(path)
    code_vars = get_unique_vars(usages)

    # GitHub Actions scanning
    actions_vars = set()
    actions_usages = []
    if actions:
        actions_usages = scan_actions_directory(path)
        actions_vars = get_github_secret_names(actions_usages)
        code_vars = code_vars | actions_vars

    env_path = env_file or find_env_file(path)
    env_vars = parse_env_file(env_path) if env_path else set()

    missing = find_missing(code_vars, env_vars)
    orphaned = find_orphaned(code_vars, env_vars)

    file_count = len({u.filename for u in usages})

    if RICH:
        console.print(f"\n[bold]envguard[/bold] v0.0.6\n")
        console.print(f"Scanning: {path} ({file_count} files)")
        if env_path:
            console.print(f"Env file: {env_path}\n")
        else:
            console.print("[yellow]No .env.example found[/yellow]\n")

        if actions and actions_vars:
            console.print(f"[bold blue]GitHub Actions Secrets ({len(actions_vars)})[/bold blue]")
            for var in sorted(actions_vars):
                refs = [(u.filename, u.line_number) for u in actions_usages if u.var_name == var]
                ref_str = f"{Path(refs[0][0]).name}:{refs[0][1]}" if refs else ""
                console.print(f"  [blue]{var}[/blue]   {ref_str}")
            console.print()

        if missing:
            console.print(f"[red bold]MISSING in .env.example ({len(missing)})[/red bold]")
            for var in sorted(missing):
                all_usages = usages + actions_usages
                refs = [(u.filename, u.line_number) for u in all_usages if u.var_name == var]
                ref_str = f"{Path(refs[0][0]).name}:{refs[0][1]}" if refs else ""
                console.print(f"  [red]{var}[/red]   {ref_str}")

        if orphaned:
            console.print(f"\n[yellow bold]ORPHANED in .env.example ({len(orphaned)})[/yellow bold]")
            for var in sorted(orphaned):
                console.print(f"  [yellow]{var}[/yellow]   (defined but unused in code)")

        if not missing and not orphaned:
            console.print("[green]All environment variables are accounted for![/green]")
        else:
            total = len(missing) + len(orphaned)
            console.print(f"\n[red]✗ {total} issue(s) found.[/red]\n")
    else:
        print(f"envguard v0.0.6 — Scanning: {path}")
        if actions and actions_vars:
            print(f"\nGitHub Actions Secrets ({len(actions_vars)}):")
            for var in sorted(actions_vars):
                print(f"  {var}")
        if missing:
            print(f"\nMISSING ({len(missing)}):")
            for var in sorted(missing):
                print(f"  {var}")
        if orphaned:
            print(f"\nORPHANED ({len(orphaned)}):")
            for var in sorted(orphaned):
                print(f"  {var}")
        if not missing and not orphaned:
            print("All clear!")

    if strict and (missing or orphaned):
        raise SystemExit(1)

if __name__ == '__main__':
    main()