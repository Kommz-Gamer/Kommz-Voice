# Roadmap (Kommz Voice)

Ce fichier liste les axes de travail prioritaires pour **Kommz Voice** (brique moteur STT/TTS + API).
La roadmap est volontairement pragmatique et peut évoluer selon les retours et contraintes d'infra.

## Objectifs produit

- **Stabilite** : un serveur moteur qui tient la charge, redemarre proprement, et degrade proprement (fallback).
- **Securite** : aucun secret dans Git, templates de configuration, scans et rotation documentee.
- **Interoperabilite** : API claire pour les clients (ex: Kommz Gamer Community).

## Priorites (0-4 semaines)

- **Fiabiliser STT Whisper / endpoints**
  - Unifier les routes (ex: `/transcribe`) et eviter les 404 cote client.
  - Retry/backoff + messages d'erreur exploitables.
  - Healthcheck pour STT/TTS (status + latence).
- **Fallback STT plus robuste**
  - Comportement deterministe quand Whisper n'est pas dispo (fallback Deepgram, message UI).
  - Gestion "no audio" / timeouts (keepalive) pour limiter les `ConnectionClosed 1011`.
- **Configuration & secrets**
  - Continuer la sanitization: `settings.example.json`, `env.template`, `.gitignore`.
  - Gitleaks (CI) + procedure de rotation (docs).

## Priorites (1-3 mois)

- **Auth & rate limiting API**
  - API keys (lecture/creation voice id, synthese) + quotas cote serveur.
  - Rate limit (per-key/per-IP) + journaux d'abus.
- **Packaging dev**
  - Docker compose (optionnel) ou scripts d'install plus simples pour dev/test.
- **Observabilite**
  - Logs structurés (JSON optionnel), correlation id, metriques de latence par etape.

## R&D (3-6 mois)

- **Qualite & expressivite**
  - Parametres de style (prosodie/expressivite) exposes proprement via l'API.
  - Evaluation A/B simple (preset "fast/balanced/natural").
- **Multitenant**
  - Isolation des sessions, cache controle, nettoyage et limites memoire.

## Liens

- Vue d'ensemble architecture : `docs/architecture-overview.md`
- Guidelines messages : `docs/message-guidelines.md`
- Securite : `SECURITY.md`

