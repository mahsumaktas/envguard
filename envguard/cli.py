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
def scan(path, strict, env_file):
    """Scan for missing or orphaned environment variables."""
    usages = scan_directory(path)
    code_vars = get_unique_vars(usages)
    
    # Find env file
    env_path = env_file or find_env_file(path)
    env_vars = parse_env_file(env_path) if env_path else set()
    
    missing = find_missing(code_vars, env_vars)
    orphaned = find_orphaned(code_vars, env_vars)
    
    file_count = len({u.filename for u in usages})
    
    if RICH:
        console.print(f"\n[bold]envguard[/bold] v0.0.4\n")
        console.print(f"Scanning: {path} ({file_count} files)")
        if env_path:
            console.print(f"Env file: {env_path}\n")
        else:
            console.print("[yellow]No .env.example found[/yellow]\n")
        
        if missing:
            console.print(f"[red bold]MISSING in .env.example ({len(missing)})[/red bold]")
            for var in sorted(missing):
                refs = [(u.filename, u.line_number) for u in usages if u.var_name == var]
                ref_str = f"{refs[0][0]}:{refs[0][1]}" if refs else ""
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
        print(f"envguard v0.0.4 — Scanning: {path}")
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