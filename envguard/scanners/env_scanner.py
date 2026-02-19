"""Parse .env files and compare with code usage."""
import re
from pathlib import Path
from typing import Optional


def parse_env_file(filepath: str) -> set:
    """Parse .env or .env.example file, return set of variable names.

    Handles:
    - VAR=value
    - VAR= (empty value)
    - export VAR=value
    - # comments (skipped)
    - blank lines (skipped)
    """
    env_path = Path(filepath)
    if not env_path.exists():
        return set()

    variables = set()
    try:
        content = env_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return set()

    for line in content.splitlines():
        line = line.strip()
        # Skip comments and blank lines
        if not line or line.startswith('#'):
            continue
        # Handle `export VAR=value`
        if line.startswith('export '):
            line = line[len('export '):]
        # Extract VAR from VAR=value or VAR
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|$)', line)
        if match:
            variables.add(match.group(1))

    return variables


def find_missing(code_vars: set, env_vars: set) -> set:
    """Return vars used in code but NOT defined in .env.example.

    These are variables the app needs but are not documented.
    """
    return code_vars - env_vars


def find_orphaned(code_vars: set, env_vars: set) -> set:
    """Return vars defined in .env.example but NOT used in code.

    These are documented variables that may no longer be needed.
    """
    return env_vars - code_vars


def find_env_file(directory: str) -> Optional[str]:
    """Find the most appropriate .env example file in directory."""
    candidates = [
        '.env.example',
        '.env.sample',
        '.env.template',
        '.env.defaults',
        '.env',
    ]
    base = Path(directory)
    for name in candidates:
        path = base / name
        if path.exists():
            return str(path)
    return None


# Legacy compatibility
def parse_env_example(path: str = ".env.example") -> set:
    """Legacy function - use parse_env_file instead."""
    return parse_env_file(path)
