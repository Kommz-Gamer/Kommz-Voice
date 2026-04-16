## Kommz Voice

Kommz Voice est la brique moteur de l'écosystème Kommz.

Ce repo regroupe la partie vocale et services autour de :
- la synthèse vocale temps réel
- les moteurs XTTS et GPT-SoVITS
- la transcription Whisper
- les services backend liés aux usages temps réel

Voice engine layer for the Kommz ecosystem.

Kommz Voice is the backend speech brick that powers:
- XTTS synthesis flows
- GPT-SoVITS voice style / timbre flows
- Whisper-related transcription routes used by connected clients

This repository is distinct from the open-source client app (`Kommz Gamer Community`).

L'objectif de Kommz Voice est de proposer une base plus claire, plus modulaire et plus robuste pour alimenter l'écosystème vocal autour de Kommz.

### Rôle dans l'écosystème
- `Kommz Gamer Community` : client desktop open source
- `Kommz Voice` : moteurs et services vocaux
- `Discord` : communauté, support, retours
- `Patreon` : soutien au développement et avantages liés à l'écosystème

### Priorités actuelles
- fiabilisation des moteurs vocaux
- amélioration des fallbacks et du routage
- meilleure structure documentaire
- meilleure séparation entre client et brique moteur
- amélioration du support pour les usages temps réel

### Liens
- Community : https://github.com/Kommz-Gamer/Kommz-Gamer
- Discord : https://discord.gg/uv25d6uGKZ
- Patreon : https://www.patreon.com/KommzInnovations
- Site : https://kommz.fr


## Ecosystem positioning

- Client / community app: `Kommz Gamer Community` (GitHub community repo)
- Engine layer: `Kommz Voice` (this repository)
- Community and support channels: Discord + Patreon

Reference docs:
- `docs/architecture-overview.md`
- `docs/message-guidelines.md`

## Quick start (security-first)

1. Copy `env.template` to `.env`.
2. Fill only rotated secrets (never commit `.env`).
3. Install pre-commit:
   - `pip install pre-commit detect-secrets`
   - `pre-commit install`
   - `detect-secrets scan > .secrets.baseline`

## Runtime validation

`vtp_web_server.py` fails fast in production when required secrets are missing
or when `SUPABASE_KEY` looks like an `anon` key.

## Security and operations

- Rotation and cutover: `docs/security-rotation-runbook.md`
- Release checks: `docs/release-security-checklist.md`
- Git history purge after key rotation: `scripts/purge-git-history.ps1`
- Security policy (EN): `SECURITY.md`
- Politique de securite (FR): `SECURITY.fr.md`

## Public links

- Community GitHub: https://github.com/Kommz-Gamer/Kommz-Gamer
- Discord: https://discord.gg/uv25d6uGKZ
- Patreon: https://www.patreon.com/KommzInnovations
