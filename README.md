# envguard 🔐

[![CI](https://github.com/mahsumaktas/envguard/actions/workflows/ci.yml/badge.svg)](https://github.com/mahsumaktas/envguard/actions)
[![PyPI](https://img.shields.io/pypi/v/envguard?color=blue)](https://pypi.org/project/envguard/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Scan your codebase and GitHub Actions for missing, undefined, or orphaned environment variables and secrets.

Never deploy with a missing `STRIPE_KEY` again.

## Features

- 🕵️ **Code scanning** — detects `process.env`, `os.environ`, `Config.get()` across JS/TS/Python
- 📋 **`.env.example` diff** — reports vars used in code but missing from `.env.example`
- 🔄 **GitHub Actions support** — checks workflow YAML files against your repo secrets
- 🎨 **Rich output** — colorized table with severity levels
- 🚪 **Exit code 1 on failure** — CI/CD ready
- ⚙️ **GitHub Action wrapper** — add to any workflow in 3 lines

## Install

```bash
pip install envguard
```

## Usage

```bash
# Scan application code vs .env.example
envguard scan

# Scan GitHub Actions workflows
envguard scan --actions

# Scan everything
envguard scan --all

# Fail CI if issues found
envguard scan --all --strict
```

## Example Output

```
envguard v0.0.1

Scanning: ./src (23 files)

❌ MISSING in .env.example (3)
  STRIPE_SECRET_KEY   — used in src/payments.py:14
  SENDGRID_API_KEY    — used in src/email.py:8
  REDIS_URL           — used in src/cache.py:3

⚠️  ORPHANED in .env.example (1)
  OLD_DATABASE_URL    — defined but never used in code

✗ 4 issues found. Fix before deploying.
```

## GitHub Action

```yaml
- uses: mahsumaktas/envguard@v0.1.0
  with:
    strict: true
```

## Roadmap

- [x] v0.0.1 — Project skeleton
- [ ] v0.0.2 — JS/TS code scanner
- [ ] v0.0.3 — `.env.example` diff
- [ ] v0.0.4 — Rich colorized output
- [ ] v0.0.5 — GitHub Actions YAML parser
- [ ] v0.0.6 — Orphaned secrets detection
- [ ] v0.0.7 — `.envguard.toml` config
- [ ] v0.0.8 — GitHub Action wrapper
- [ ] v0.1.0 — Stable release with full test coverage

## Contributing

PRs welcome! See [open issues](https://github.com/mahsumaktas/envguard/issues).

## License

MIT
