"""Scan source code for environment variable usage."""
import re
from pathlib import Path


ENV_PATTERNS = [
    r'process\.env\.([A-Z_][A-Z0-9_]*)',        # JS/TS
    r'os\.environ(?:\.get)?\(["\']([A-Z_][A-Z0-9_]*)',  # Python
    r'os\.getenv\(["\']([A-Z_][A-Z0-9_]*)',     # Python
    r'ENV\[[\'"]([ A-Z_][A-Z0-9_]*)[\'"]',      # Ruby
]


def scan_directory(path: str) -> dict[str, list[str]]:
    """Return {VAR_NAME: [file:line, ...]} for all env vars used in code."""
    results: dict[str, list[str]] = {}
    extensions = {".js", ".ts", ".py", ".rb", ".go"}
    for file in Path(path).rglob("*"):
        if file.suffix not in extensions or "node_modules" in str(file):
            continue
        try:
            content = file.read_text(errors="ignore")
            for line_no, line in enumerate(content.splitlines(), 1):
                for pattern in ENV_PATTERNS:
                    for match in re.finditer(pattern, line):
                        var = match.group(1)
                        results.setdefault(var, []).append(f"{file}:{line_no}")
        except Exception:
            continue
    return results
