"""Scan GitHub Actions YAML files for secret/env var references."""
import re
from pathlib import Path
from typing import List, Set
from ..scanners.code_scanner import EnvUsage

def scan_actions_directory(repo_path: str) -> List[EnvUsage]:
    """Scan .github/workflows/*.yml for secrets.VAR and env.VAR references."""
    usages = []
    workflows_dir = Path(repo_path) / ".github" / "workflows"
    if not workflows_dir.exists():
        return usages
    
    for yml_file in workflows_dir.glob("*.yml"):
        usages.extend(scan_actions_file(str(yml_file)))
    for yml_file in workflows_dir.glob("*.yaml"):
        usages.extend(scan_actions_file(str(yml_file)))
    
    return usages

def scan_actions_file(filepath: str) -> List[EnvUsage]:
    """Scan a single GitHub Actions YAML file."""
    usages = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (IOError, OSError):
        return usages
    
    for i, line in enumerate(lines, 1):
        # ${{ secrets.VAR_NAME }}
        for match in re.finditer(r'\$\{\{\s*secrets\.([A-Z0-9_]+)\s*\}\}', line):
            usages.append(EnvUsage(
                var_name=match.group(1),
                filename=filepath,
                line_number=i,
                usage_type="github_secret"
            ))
        # ${{ env.VAR_NAME }} or env: VAR_NAME: value
        for match in re.finditer(r'\$\{\{\s*env\.([A-Z0-9_a-z_]+)\s*\}\}', line):
            usages.append(EnvUsage(
                var_name=match.group(1).upper(),
                filename=filepath,
                line_number=i,
                usage_type="github_env"
            ))
    
    return usages

def get_github_secret_names(usages: List[EnvUsage]) -> Set[str]:
    """Get all secret names referenced in Actions."""
    return {u.var_name for u in usages if u.usage_type == "github_secret"}
