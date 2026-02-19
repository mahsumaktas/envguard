import pytest
from pathlib import Path
from envguard.scanners.actions_scanner import (
    scan_actions_directory,
    scan_actions_file,
    get_github_secret_names,
)
from envguard.scanners.code_scanner import EnvUsage

@pytest.fixture
def workflows_dir(tmp_path):
    """Create a temporary GitHub Actions workflows directory."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    return workflows

def test_scan_actions_finds_secrets(workflows_dir):
    """Test that secrets are found in a YAML file."""
    yml_file = workflows_dir / "ci.yml"
    yml_file.write_text(
        """
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
        env:
          API_KEY: ${{ secrets.API_KEY }}
          DB_PASSWORD: ${{secrets.DB_PASSWORD}}
    """
    )
    usages = scan_actions_directory(str(workflows_dir.parent.parent))
    assert len(usages) == 2
    assert EnvUsage("API_KEY", str(yml_file), 17, "github_secret") in usages
    assert EnvUsage("DB_PASSWORD", str(yml_file), 18, "github_secret") in usages

def test_scan_actions_finds_env_vars(workflows_dir):
    """Test that env vars are found in a YAML file."""
    yml_file = workflows_dir / "cd.yml"
    yml_file.write_text(
        """
name: CD
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    env:
        GLOBAL_VAR: "test"
    steps:
      - name: Deploy
        run: ./deploy.sh
        env:
          AWS_REGION: ${{ env.AWS_REGION }}
          S3_BUCKET_NAME: ${{env.S3_BUCKET_NAME}}
    """
    )
    usages = scan_actions_directory(str(workflows_dir.parent.parent))
    assert len(usages) == 2
    assert EnvUsage("AWS_REGION", str(yml_file), 14, "github_env") in usages
    assert EnvUsage("S3_BUCKET_NAME", str(yml_file), 15, "github_env") in usages

def test_scan_empty_workflows_dir(tmp_path):
    """Test scanning an empty or non-existent workflows directory."""
    assert scan_actions_directory(str(tmp_path)) == []
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    assert scan_actions_directory(str(tmp_path)) == []

def test_get_github_secret_names():
    """Test getting unique secret names from a list of usages."""
    usages = [
        EnvUsage("API_KEY", "ci.yml", 1, "github_secret"),
        EnvUsage("DB_PASSWORD", "ci.yml", 2, "github_secret"),
        EnvUsage("AWS_REGION", "cd.yml", 3, "github_env"),
    ]
    secret_names = get_github_secret_names(usages)
    assert secret_names == {"API_KEY", "DB_PASSWORD"}
