"""Parse .env.example files."""
from pathlib import Path


def parse_env_example(path: str = ".env.example") -> set[str]:
    """Return set of variable names defined in .env.example."""
    env_file = Path(path)
    if not env_file.exists():
        return set()
    variables = set()
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            variables.add(line.split("=")[0].strip())
    return variables
