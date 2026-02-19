import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

@dataclass
class EnvUsage:
    var_name: str
    filename: str
    line_number: int
    usage_type: str  # "python_environ", "python_getenv", "js_process_env"

PYTHON_PATTERNS = [
    (r'os\.environ\[[\'"]([\w]+)[\'"]\]', "python_environ"),
    (r'os\.environ\.get\([\'\"]([\w]+)[\'\"]\)', "python_environ_get"),
    (r'os\.getenv\([\'\"]([\w]+)[\'\"]\)', "python_getenv"),
    (r'config\.([\w]+)', "config_attr"),
    (r'settings\.([\w]+)', "settings_attr"),
]

JS_PATTERNS = [
    (r'process\.env\.([\w]+)', "js_process_env"),
    (r'process\.env\[[\'\"]([\w]+)[\'\"]\]', "js_process_env_bracket"),
    (r'import\.meta\.env\.([\w]+)', "vite_env"),
]

SUPPORTED_EXTENSIONS = {
    '.py': 'python',
    '.js': 'js',
    '.ts': 'js',
    '.jsx': 'js',
    '.tsx': 'js',
    '.mjs': 'js',
}

def scan_file(filepath: str) -> List[EnvUsage]:
    usages = []
    path = Path(filepath)
    lang = SUPPORTED_EXTENSIONS.get(path.suffix, None)
    if not lang:
        return usages
    
    patterns = PYTHON_PATTERNS if lang == 'python' else JS_PATTERNS
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except (IOError, OSError):
        return usages
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//'):
            continue
        for pattern, usage_type in patterns:
            for match in re.finditer(pattern, line):
                var_name = match.group(1).upper()
                # Filter out noise
                if len(var_name) < 2 or var_name.isdigit():
                    continue
                usages.append(EnvUsage(
                    var_name=var_name,
                    filename=filepath,
                    line_number=i,
                    usage_type=usage_type
                ))
    return usages

def scan_directory(path: str) -> List[EnvUsage]:
    usages = []
    ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}
    for p in Path(path).rglob('*'):
        if p.is_file() and p.suffix in SUPPORTED_EXTENSIONS:
            if not any(d in p.parts for d in ignore_dirs):
                usages.extend(scan_file(str(p)))
    return usages

def get_unique_vars(usages: List[EnvUsage]) -> Set[str]:
    return {u.var_name for u in usages}