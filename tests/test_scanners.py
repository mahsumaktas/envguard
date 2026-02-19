"""Tests for envguard scanners."""
import tempfile
from pathlib import Path
from envguard.scanners.code_scanner import scan_directory
from envguard.scanners.env_scanner import parse_env_example


def test_scan_js_file():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "app.js").write_text('const key = process.env.STRIPE_KEY;')
        result = scan_directory(tmp)
        assert "STRIPE_KEY" in result


def test_scan_python_file():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "app.py").write_text('import os\nkey = os.environ.get("API_KEY")')
        result = scan_directory(tmp)
        assert "API_KEY" in result


def test_parse_env_example():
    with tempfile.TemporaryDirectory() as tmp:
        env_file = Path(tmp, ".env.example")
        env_file.write_text("DATABASE_URL=\nAPI_KEY=\n# comment\n")
        result = parse_env_example(str(env_file))
        assert "DATABASE_URL" in result
        assert "API_KEY" in result
