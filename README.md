# envguard 🔐

> Scan your source code and GitHub Actions for missing, undefined, or orphaned environment variables and secrets.

Never deploy with a missing `STRIPE_KEY` again.

## Install

```bash
pip install envguard
```

## Usage

```bash
# Scan application code vs .env.example
envguard scan

# Scan GitHub Actions workflows vs GitHub Secrets
envguard scan --actions

# Scan everything
envguard scan --all
```

## Example Output

```
envguard v0.0.1

Scanning source: ./src
Scanning env:    .env.example

✅ DEFINED (4): DATABASE_URL, REDIS_URL, JWT_SECRET, API_KEY
⚠️  MISSING (2): STRIPE_KEY used in src/payment.js:34 but not in .env.example
                 SENDGRID_KEY used in src/email.py:12 but not in .env.example
🗑️  ORPHAN (1): OLD_WEBHOOK_URL defined in .env.example but never used
```

## Status

🚧 v0.0.1 — Under active development

## License

MIT
