# Roadmap (Kommz Voice)

This file tracks the current priorities for **Kommz Voice** (STT/TTS engine layer + API).
It is intentionally practical and will evolve based on feedback and infrastructure constraints.

## Product goals

- **Stability**: a backend that stays up, restarts cleanly, and degrades gracefully (fallbacks).
- **Security**: no secrets in Git, safe templates, automated secret scanning, documented rotation.
- **Interoperability**: a clear API contract for clients (e.g. Kommz Gamer Community).

## Near-term (0-4 weeks)

- **Fix STT Whisper reliability / endpoints**
  - Normalize routes (e.g. `/transcribe`) and avoid client-side 404s.
  - Retry/backoff + actionable error messages.
  - Healthchecks for STT/TTS (status + latency).
- **More robust STT fallback**
  - Deterministic behavior when Whisper is unavailable (Deepgram fallback + clear UI message).
  - Handle "no audio" / timeouts (keepalive) to reduce `ConnectionClosed 1011`.
- **Config & secret hygiene**
  - Keep sanitizing: `settings.example.json`, `env.template`, `.gitignore`.
  - Gitleaks (CI) + documented rotation process.

## Mid-term (1-3 months)

- **API auth & rate limiting**
  - API keys (voice id management, synthesis) + server-side quotas.
  - Rate limit (per-key/per-IP) + abuse logs.
- **Developer packaging**
  - Optional Docker compose or simpler setup scripts for dev/test.
- **Observability**
  - Structured logs (optional JSON), correlation ids, latency metrics per step.

## R&D (3-6 months)

- **Quality & expressivity**
  - Expose style/prosody/expressivity parameters cleanly via the API.
  - Simple A/B evaluation (presets: fast/balanced/natural).
- **Multi-tenant readiness**
  - Session isolation, cache controls, cleanup and memory limits.

## Links

- Architecture overview: `docs/architecture-overview.md`
- Message guidelines: `docs/message-guidelines.md`
- Security: `SECURITY.md`

