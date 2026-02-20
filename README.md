# KommzVoice

## Security-first setup
1. Copy `env.template` to `.env`.
2. Fill only rotated secrets (never commit `.env`).
3. Install pre-commit:
   - `pip install pre-commit detect-secrets`
   - `pre-commit install`
   - `detect-secrets scan > .secrets.baseline`

## Runtime validation
`vtp_web_server.py` now fails fast in production when required secrets are missing or when `SUPABASE_KEY` looks like an `anon` key.

## Rotation and cutover
See `docs/security-rotation-runbook.md`.

## Git history purge
Use `scripts/purge-git-history.ps1` after rotating secrets.
