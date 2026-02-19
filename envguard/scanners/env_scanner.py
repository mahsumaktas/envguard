import re
from pathlib import Path
from typing import Set, Optional, Dict

def parse_env_file(filepath: str) -> Set[str]:
    """Parse .env or .env.example, return set of variable names."""
    vars = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # KEY=value or KEY=
                match = re.match(r'^([\w]+)\s*=', line)
                if match:
                    vars.add(match.group(1).upper())
    except (IOError, OSError):
        pass
    return vars

def find_env_file(directory: str) -> Optional[str]:
    """Find .env.example or .env in directory."""
    for name in ['.env.example', '.env.sample', '.env.template', '.env']:
        p = Path(directory) / name
        if p.exists():
            return str(p)
    return None

def find_missing(code_vars: Set[str], env_vars: Set[str]) -> Set[str]:
    """Vars used in code but not in .env.example (potential missing config)."""
    # Filter out common false positives
    noise = {'PATH', 'HOME', 'USER', 'SHELL', 'PWD', 'TERM', 'LANG', 'LC_ALL'}
    return (code_vars - env_vars) - noise

def find_orphaned(code_vars: Set[str], env_vars: Set[str]) -> Set[str]:
    """Vars in .env.example but not referenced in code."""
    return env_vars - code_vars