"""Scan source code for environment variable usage."""
import re
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class EnvUsage:
    var_name: str
    filename: str
    line_number: int
    usage_type: str  # "python_environ", "python_getenv", "js_process_env", etc.


# Supported file extensions and their scanner type
EXTENSION_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.rb': 'ruby',
    '.go': 'go',
    '.sh': 'shell',
    '.bash': 'shell',
    '.env': 'dotenv',
}

# Default extensions to scan
DEFAULT_EXTENSIONS = set(EXTENSION_MAP.keys())

# Patterns per language: (regex, usage_type)
PYTHON_PATTERNS = [
    # os.environ["VAR"] or os.environ['VAR']
    (r'os\.environ\s*\[\s*["\']([A-Z_][A-Z0-9_]*)["\']', "python_environ"),
    # os.environ.get("VAR")
    (r'os\.environ\.get\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']', "python_environ_get"),
    # os.getenv("VAR")
    (r'os\.getenv\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']', "python_getenv"),
    # environ["VAR"] (from: from os import environ)
    (r'(?<![.\w])environ\s*\[\s*["\']([A-Z_][A-Z0-9_]*)["\']', "python_environ"),
    # environ.get("VAR")
    (r'(?<![.\w])environ\.get\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']', "python_environ_get"),
    # getenv("VAR")
    (r'(?<![.\w])getenv\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']', "python_getenv"),
    # settings.VAR_NAME (Django-style, only uppercase)
    # config("VAR") - decouple style
    (r'config\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']', "python_config"),
]

JS_TS_PATTERNS = [
    # process.env.VAR_NAME
    (r'process\.env\.([A-Z_][A-Z0-9_]*)', "js_process_env"),
    # process.env["VAR"] or process.env['VAR']
    (r"process\.env\s*\[\s*[\"']([A-Z_][A-Z0-9_]*)[\"']", "js_process_env_bracket"),
    # import.meta.env.VITE_VAR (Vite)
    (r'import\.meta\.env\.([A-Z_][A-Z0-9_]*)', "js_import_meta_env"),
    # process.env.NEXT_PUBLIC_VAR (Next.js)
    # Already covered by js_process_env pattern above
]

RUBY_PATTERNS = [
    # ENV["VAR"] or ENV['VAR']
    (r"ENV\s*\[\s*[\"']([A-Z_][A-Z0-9_]*)[\"']\s*\]", "ruby_env"),
    # ENV.fetch("VAR")
    (r"ENV\.fetch\s*\(\s*[\"']([A-Z_][A-Z0-9_]*)[\"']", "ruby_env_fetch"),
]

GO_PATTERNS = [
    # os.Getenv("VAR")
    (r'os\.Getenv\s*\(\s*"([A-Z_][A-Z0-9_]*)"', "go_getenv"),
    # os.LookupEnv("VAR")
    (r'os\.LookupEnv\s*\(\s*"([A-Z_][A-Z0-9_]*)"', "go_lookupenv"),
]

SHELL_PATTERNS = [
    # $VAR_NAME or ${VAR_NAME}
    (r'\$\{([A-Z_][A-Z0-9_]*)\}', "shell_env"),
    (r'\$([A-Z_][A-Z0-9_]*)', "shell_env"),
]

LANGUAGE_PATTERNS = {
    'python': PYTHON_PATTERNS,
    'javascript': JS_TS_PATTERNS,
    'typescript': JS_TS_PATTERNS,
    'ruby': RUBY_PATTERNS,
    'go': GO_PATTERNS,
    'shell': SHELL_PATTERNS,
}


def scan_file(filepath) -> List[EnvUsage]:
    """Scan a single file for environment variable usage."""
    filepath = Path(filepath)
    usages: List[EnvUsage] = []

    lang = EXTENSION_MAP.get(filepath.suffix.lower())
    if not lang:
        return []

    # Skip dotenv files themselves (not source code)
    if lang == 'dotenv':
        return []

    patterns = LANGUAGE_PATTERNS.get(lang, [])
    if not patterns:
        return []

    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return []

    filename = str(filepath)
    for line_no, line in enumerate(content.splitlines(), 1):
        for pattern, usage_type in patterns:
            for match in re.finditer(pattern, line):
                var_name = match.group(1)
                usages.append(EnvUsage(
                    var_name=var_name,
                    filename=filename,
                    line_number=line_no,
                    usage_type=usage_type,
                ))

    return usages


def scan_directory(
    path: str,
    extensions: Optional[List[str]] = None,
) -> dict:
    """Scan all supported files in a directory.

    Returns dict {VAR_NAME: [file:line, ...]} for backward compatibility.
    Use scan_directory_detailed() for EnvUsage objects.
    """
    results: dict = {}
    for usage in scan_directory_detailed(path, extensions):
        key = usage.var_name
        results.setdefault(key, []).append(f"{usage.filename}:{usage.line_number}")
    return results


def scan_directory_detailed(
    path: str,
    extensions: Optional[List[str]] = None,
) -> List[EnvUsage]:
    """Scan all supported files in a directory, return EnvUsage objects."""
    usages: List[EnvUsage] = []
    target = Path(path)

    if not target.exists():
        return []

    if target.is_file():
        return scan_file(target)

    skip_dirs = {
        '.git', 'node_modules', '__pycache__', '.venv', 'venv',
        '.mypy_cache', '.pytest_cache', 'dist', 'build', '.eggs',
        'coverage', '.coverage', '.tox',
    }

    ext_filter = set(extensions) if extensions else DEFAULT_EXTENSIONS

    for filepath in target.rglob('*'):
        if not filepath.is_file():
            continue
        # Skip hidden/build directories
        if any(part in skip_dirs or part.startswith('.') for part in filepath.parts[:-1]):
            continue
        if filepath.suffix.lower() not in ext_filter:
            continue
        usages.extend(scan_file(filepath))

    return usages


def get_code_vars(path: str) -> set:
    """Return set of unique variable names found in code."""
    return {u.var_name for u in scan_directory_detailed(path)}
