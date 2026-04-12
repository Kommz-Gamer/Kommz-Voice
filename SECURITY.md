# Security Policy

## Reporting a vulnerability

If you discover a security issue, do not open a public issue with exploit details.

Please report privately with:
- Short summary of the issue
- Affected file/endpoint
- Reproduction steps
- Impact assessment
- Suggested fix (if any)

Contact:
- GitHub Security Advisories (preferred)
- Or open a private maintainer contact request via project channels

We aim to acknowledge reports quickly and provide a remediation plan.

## Secret handling

- Never commit real secrets (`.env`, API keys, private tokens, credentials).
- Use templates (`env.template`, `env.production.template`) and local-only config files.
- Run secret checks before push:
  - `pre-commit run --all-files`
- CI also runs `gitleaks` on push/PR.

If a secret is exposed:
1. Rotate/revoke immediately.
2. Remove from current code.
3. Purge from history if needed.
4. Re-run security scans.

