# Release Security Checklist

- [ ] No real secret in changed files (`.env`, templates, docs, scripts).
- [ ] `env.template` contains placeholders only.
- [ ] Secret scan CI passes (gitleaks + pre-commit detect-secrets).
- [ ] Production env uses `SUPABASE_KEY` = service_role.
- [ ] `SECRET_KEY`, `ADMIN_SECRET`, salts rotated.
- [ ] Third-party credentials rotated (DeepL/SMTP/Make).
- [ ] Blue/green cutover validated (`/health`, auth, license, upload, transcribe, generate).
- [ ] Old credentials revoked after successful cutover.
- [ ] If history rewrite was done: force-push complete, team informed to re-clone.
