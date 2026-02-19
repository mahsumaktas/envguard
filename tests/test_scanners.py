import os
import tempfile
from envguard.scanners.code_scanner import scan_file, scan_directory, get_unique_vars
from envguard.scanners.env_scanner import parse_env_file, find_missing, find_orphaned

def test_scan_python_os_environ():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("import os\napi_key = os.environ['API_KEY']")
        filepath = f.name
    
    usages = scan_file(filepath)
    os.unlink(filepath)
    
    assert len(usages) == 1
    assert usages[0].var_name == 'API_KEY'
    assert usages[0].usage_type == 'python_environ'

def test_scan_python_getenv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("import os\nsecret = os.getenv('DB_SECRET')")
        filepath = f.name
        
    usages = scan_file(filepath)
    os.unlink(filepath)
    
    assert len(usages) == 1
    assert usages[0].var_name == 'DB_SECRET'
    assert usages[0].usage_type == 'python_getenv'

def test_scan_js_process_env():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write("const port = process.env.PORT;")
        filepath = f.name
        
    usages = scan_file(filepath)
    os.unlink(filepath)

    assert len(usages) == 1
    assert usages[0].var_name == 'PORT'
    assert usages[0].usage_type == 'js_process_env'

def test_scan_ignores_comments():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("# token = os.environ['COMMENTED_OUT']")
        filepath = f.name
        
    usages = scan_file(filepath)
    os.unlink(filepath)
    
    assert len(usages) == 0

def test_parse_env_file():
    content = "KEY1=VALUE1\n# COMMENT\nKEY2=VALUE2"
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(content)
        filepath = f.name
        
    variables = parse_env_file(filepath)
    os.unlink(filepath)

    assert variables == {'KEY1', 'KEY2'}

def test_find_missing():
    code_vars = {'API_KEY', 'DB_HOST', 'TIMEOUT'}
    env_vars = {'API_KEY', 'DB_HOST'}
    missing = find_missing(code_vars, env_vars)
    assert missing == {'TIMEOUT'}

def test_find_orphaned():
    code_vars = {'API_KEY', 'DB_HOST'}
    env_vars = {'API_KEY', 'DB_HOST', 'UNUSED_VAR'}
    orphaned = find_orphaned(code_vars, env_vars)
    assert orphaned == {'UNUSED_VAR'}

def test_no_false_positive_path_var():
    code_vars = {'PATH', 'API_KEY'}
    env_vars = {'API_KEY'}
    missing = find_missing(code_vars, env_vars)
    assert missing == set()

def test_scan_directory_returns_usages():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "test.py"), "w") as f:
            f.write("import os\nkey=os.getenv('MY_KEY')")
        
        usages = scan_directory(tmpdir)
        assert len(usages) == 1
        assert usages[0].var_name == 'MY_KEY'

def test_get_unique_vars():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "test.py"), "w") as f:
            f.write("import os\nkey1=os.getenv('KEY_A')\nkey2=os.getenv('KEY_B')")
        with open(os.path.join(tmpdir, "test2.py"), "w") as f:
            f.write("import os\nkey3=os.getenv('KEY_A')")

        usages = scan_directory(tmpdir)
        unique_vars = get_unique_vars(usages)
        assert unique_vars == {'KEY_A', 'KEY_B'}