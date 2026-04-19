# Issues suggérées (copier/coller)

Ce fichier transforme `ROADMAP.md` en **tickets GitHub** faciles à créer.

## P0 - STT Whisper: endpoints 404 + contrat API

**Titre**: `[P0] STT Whisper: unifier les endpoints et supprimer les 404`

**Labels**: `bug`, `backend`, `stt`

**Description**:
- Objectif: aligner les routes STT (ex: `/transcribe`) entre serveur et clients.
- Résultat attendu: plus de 404 coté client, messages d'erreur clairs.
- Definition of done:
  - endpoints documentés dans `README.md`
  - compat client: ancienne route -> redirection/alias (si applicable)
  - tests smoke (local) + note release

## P0 - Healthcheck STT/TTS + latence

**Titre**: `[P0] Ajouter des healthchecks STT/TTS (status + latence)`

**Labels**: `enhancement`, `backend`, `observability`

**Description**:
- Endpoint(s) de santé: dispo moteurs + latence + version.
- Utilisé par le client pour afficher l'état (ready/warm/cold/down).

## P0 - Fallback STT: deterministe + UX

**Titre**: `[P0] Fallback STT deterministe (Whisper -> Deepgram) + message UI`

**Labels**: `bug`, `backend`, `stt`

**Description**:
- Si Whisper indisponible: fallback stable (Deepgram), sans boucle.
- Message UI/retour API explicite: "fallback_used=true" + raison.

## P0 - Keepalive / no-audio: réduire ConnectionClosed 1011

**Titre**: `[P0] STT streaming: keepalive et gestion no-audio (1011 Deepgram)`

**Labels**: `bug`, `backend`, `stt`

**Description**:
- Éviter les timeouts "no audio" (silence long, stream pause).
- Ajout keepalive / frames silence / heartbeat.
- Backoff + reconnexion propre.

## P1 - Auth API: clés + quotas

**Titre**: `[P1] API keys + quotas (voice id / synthese) coté serveur`

**Labels**: `enhancement`, `security`, `backend`

**Description**:
- API key par client/utilisateur.
- Quotas: generations, secondes audio, rate limit.
- Logs d'abus + réponses HTTP cohérentes.

## P1 - Rate limit per-key / per-IP

**Titre**: `[P1] Rate limiting (per-key + per-IP) + journaux`

**Labels**: `enhancement`, `security`, `backend`

**Description**:
- Protection anti-spam (warmups, syntheses, transcribes).
- Message de blocage clair + retry-after.

## P1 - Observabilité: logs structurés + correlation id

**Titre**: `[P1] Logs structurés + correlation id + métriques latence`

**Labels**: `enhancement`, `observability`, `backend`

**Description**:
- Ajouter `request_id` et suivre STT/TR/TTS.
- Option JSON logs (toggle).

## Docs - Docker / setup dev simplifié

**Titre**: `[Docs] Setup dev simplifié (Docker compose optionnel)`

**Labels**: `docs`, `infra`

**Description**:
- Guide de démarrage reproductible.
- Séparer "local dev" vs "cloud/Modal".

