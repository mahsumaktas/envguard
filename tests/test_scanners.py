"""Tests for envguard scanners."""
import tempfile
from pathlib import Path
import pytest
from envguard.scanners.code_scanner import scan_directory, scan_file, scan_directory_detailed, get_code_vars
from envguard.scanners.env_scanner import parse_env_file, parse_env_example, find_missing, find_orphaned, find_env_file


# === Code Scanner Tests ===

def test_scan_js_process_env():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "app.js").write_text('const key = process.env.STRIPE_KEY;')
        result = scan_directory(tmp)
        assert "STRIPE_KEY" in result


def test_scan_python_environ_get():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "app.py").write_text('import os\nkey = os.environ.get("API_KEY")')
        result = scan_directory(tmp)
        assert "API_KEY" in result


def test_scan_python_getenv():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "config.py").write_text('DB_URL = os.getenv("DATABASE_URL")')
        result = scan_directory(tmp)
        assert "DATABASE_URL" in result


def test_scan_python_environ_bracket():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "settings.py").write_text('SECRET = os.environ["DJANGO_SECRET_KEY"]')
        result = scan_directory(tmp)
        assert "DJANGO_SECRET_KEY" in result


def test_scan_typescript_file():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "config.ts").write_text('const url = process.env.API_BASE_URL;')
        result = scan_directory(tmp)
        assert "API_BASE_URL" in result


def test_scan_ts_bracket_notation():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "app.ts").write_text('const key = process.env["SECRET_KEY"];')
        result = scan_directory(tmp)
        assert "SECRET_KEY" in result


def test_scan_multiple_files():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "app.py").write_text('os.getenv("DB_HOST")\nos.getenv("DB_PORT")')
        Path(tmp, "server.js").write_text('process.env.PORT')
        result = scan_directory(tmp)
        assert "DB_HOST" in result
        assert "DB_PORT" in result
        assert "PORT" in result


def test_scan_excludes_node_modules():
    with tempfile.TemporaryDirectory() as tmp:
        nm = Path(tmp, "node_modules", "pkg")
        nm.mkdir(parents=True)
        (nm / "index.js").write_text('process.env.SECRET_IN_NODE_MODULES')
        Path(tmp, "app.js").write_text('process.env.MY_VAR')
        result = scan_directory(tmp)
        assert "MY_VAR" in result
        assert "SECRET_IN_NODE_MODULES" not in result


def test_scan_file_detailed():
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write('KEY = os.getenv("MY_API_KEY")\n')
        fname = f.name
    usages = scan_file(Path(fname))
    assert len(usages) == 1
    assert usages[0].var_name == "MY_API_KEY"
    assert usages[0].usage_type == "python_getenv"
    assert usages[0].line_number == 1


def test_scan_directory_detailed_returns_env_usage():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "app.py").write_text('os.environ.get("AUTH_TOKEN")')
        usages = scan_directory_detailed(tmp)
        assert any(u.var_name == "AUTH_TOKEN" for u in usages)
        auth = [u for u in usages if u.var_name == "AUTH_TOKEN"][0]
        assert auth.usage_type == "python_environ_get"


def test_get_code_vars():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "app.py").write_text('os.getenv("FOO")\nos.getenv("BAR")')
        vars_set = get_code_vars(tmp)
        assert {"FOO", "BAR"}.issubset(vars_set)


# === Env File Scanner Tests ===

def test_parse_env_file_basic():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("DATABASE_URL=postgres://localhost/mydb\nAPI_KEY=\n# comment\nDEBUG=false\n")
        fname = f.name
    result = parse_env_file(fname)
    assert "DATABASE_URL" in result
    assert "API_KEY" in result
    assert "DEBUG" in result


def test_parse_env_file_ignores_comments():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("# This is a comment\nVAR=value\n")
        fname = f.name
    result = parse_env_file(fname)
    assert "VAR" in result
    assert len(result) == 1


def test_parse_env_file_handles_export():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("export MY_VAR=value\n")
        fname = f.name
    result = parse_env_file(fname)
    assert "MY_VAR" in result


def test_parse_env_file_nonexistent():
    result = parse_env_file("/nonexistent/.env.example")
    assert result == set()


def test_parse_env_example_legacy():
    """parse_env_example is a legacy alias for parse_env_file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env.example", delete=False) as f:
        f.write("DATABASE_URL=\nAPI_KEY=\n# comment\n")
        fname = f.name
    result = parse_env_example(fname)
    assert "DATABASE_URL" in result
    assert "API_KEY" in result


def test_find_missing():
    code_vars = {"DB_HOST", "DB_PORT", "API_KEY", "SECRET"}
    env_vars = {"DB_HOST", "DB_PORT"}
    missing = find_missing(code_vars, env_vars)
    assert "API_KEY" in missing
    assert "SECRET" in missing
    assert "DB_HOST" not in missing


def test_find_orphaned():
    code_vars = {"DB_HOST", "API_KEY"}
    env_vars = {"DB_HOST", "API_KEY", "OLD_VAR", "DEPRECATED_KEY"}
    orphaned = find_orphaned(code_vars, env_vars)
    assert "OLD_VAR" in orphaned
    assert "DEPRECATED_KEY" in orphaned
    assert "DB_HOST" not in orphaned


def test_find_missing_empty():
    assert find_missing(set(), set()) == set()
    assert find_missing({"A"}, {"A"}) == set()


def test_find_orphaned_empty():
    assert find_orphaned(set(), set()) == set()
    assert find_orphaned({"A"}, {"A"}) == set()


def test_find_env_file(tmp_path):
    (tmp_path / ".env.example").write_text("VAR=\n")
    found = find_env_file(str(tmp_path))
    assert found is not None
    assert ".env.example" in found


def test_find_env_file_not_found(tmp_path):
    found = find_env_file(str(tmp_path))
    assert found is None
