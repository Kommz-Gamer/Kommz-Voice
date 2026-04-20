# Issues suggérées (copier/coller)

Ce fichier transforme `ROADMAP.md` en **tickets GitHub** faciles à créer.

## Option A (simple) : 1 seule issue “Roadmap”

**Titre** : `Roadmap (P0 / P1 / P2)`

**Labels** : `enhancement` (optionnel : `documentation`)

**Description** (à coller) :

### P0 (bloquant / stabilité)
- [ ] **[P0] STT Whisper : unifier les endpoints et supprimer les 404**
  Objectif : aligner les routes STT (ex. `/transcribe`) entre serveur et clients.
  Résultat attendu : plus de 404 côté client, messages d’erreur clairs.
  DoD : endpoints documentés dans le README ; compat client (ancienne route → alias/redirection si applicable) ; tests smoke (local) + note release.

- [ ] **[P0] Healthchecks STT/TTS (status + latence)**
  DoD : endpoint(s) de santé (dispo moteurs, latence, version) ; utilisé par le client pour afficher ready/warm/cold/down.

- [ ] **[P0] Fallback STT déterministe (Whisper → Deepgram) + message UI**
  DoD : fallback stable sans boucle ; retour API explicite (`fallback_used=true` + raison) + message UI.

- [ ] **[P0] STT streaming : keepalive + gestion “no-audio” (Deepgram 1011)**
  DoD : éviter les timeouts “no audio” (silence long / pause) ; keepalive/heartbeat ; backoff + reconnexion propre.

### P1 (améliorations importantes)
- [ ] **[P1] API keys + quotas (voice id / synthèse) côté serveur**
  DoD : API key par client/utilisateur ; quotas (générations, secondes audio, rate limit) ; réponses HTTP cohérentes + logs.

- [ ] **[P1] Rate limiting (par key + par IP) + journaux**
  DoD : protection anti-spam (warmups, synthèses, transcribes) ; message clair + `retry-after`.

- [ ] **[P1] Observabilité : logs structurés + correlation id + métriques latence**
  DoD : `request_id` et suivi STT/TR/TTS ; option logs JSON (toggle).

### P2 (docs / infra)
- [ ] **[P2] Docs : setup dev simplifié (Docker compose optionnel)**
  DoD : guide démarrage reproductible ; séparation “local dev” vs “cloud/Modal”.

## Option B (détaillée) : issues séparées

### P0 - STT Whisper : endpoints 404 + contrat API

**Titre** : `[P0] STT Whisper : unifier les endpoints et supprimer les 404`

**Labels** : `bug`, `backend`, `stt`

**Description** :
- Objectif : aligner les routes STT (ex. `/transcribe`) entre serveur et clients.
- Résultat attendu : plus de 404 côté client, messages d'erreur clairs.
- Definition of done :
  - endpoints documentés dans `README.md`
  - compat client : ancienne route → redirection/alias (si applicable)
  - tests smoke (local) + note release

### P0 - Healthcheck STT/TTS + latence

**Titre** : `[P0] Ajouter des healthchecks STT/TTS (status + latence)`

**Labels** : `enhancement`, `backend`, `observability`

**Description** :
- Endpoint(s) de santé : dispo moteurs + latence + version.
- Utilisé par le client pour afficher l'état (ready/warm/cold/down).

### P0 - Fallback STT : déterministe + UX

**Titre** : `[P0] Fallback STT déterministe (Whisper → Deepgram) + message UI`

**Labels** : `bug`, `backend`, `stt`

**Description** :
- Si Whisper indisponible : fallback stable (Deepgram), sans boucle.
- Message UI/retour API explicite : `fallback_used=true` + raison.

### P0 - Keepalive / no-audio : réduire ConnectionClosed 1011

**Titre** : `[P0] STT streaming : keepalive et gestion no-audio (1011 Deepgram)`

**Labels** : `bug`, `backend`, `stt`

**Description** :
- Éviter les timeouts "no audio" (silence long, stream pause).
- Ajout keepalive / frames silence / heartbeat.
- Backoff + reconnexion propre.

### P1 - Auth API : clés + quotas

**Titre** : `[P1] API keys + quotas (voice id / synthèse) côté serveur`

**Labels** : `enhancement`, `security`, `backend`

**Description** :
- API key par client/utilisateur.
- Quotas : générations, secondes audio, rate limit.
- Logs d'abus + réponses HTTP cohérentes.

### P1 - Rate limit per-key / per-IP

**Titre** : `[P1] Rate limiting (per-key + per-IP) + journaux`

**Labels** : `enhancement`, `security`, `backend`

**Description** :
- Protection anti-spam (warmups, synthèses, transcribes).
- Message de blocage clair + retry-after.

### P1 - Observabilité : logs structurés + correlation id

**Titre** : `[P1] Logs structurés + correlation id + métriques latence`

**Labels** : `enhancement`, `observability`, `backend`

**Description** :
- Ajouter `request_id` et suivre STT/TR/TTS.
- Option JSON logs (toggle).

### Docs - Docker / setup dev simplifié

**Titre** : `[Docs] Setup dev simplifié (Docker compose optionnel)`

**Labels** : `documentation`

**Description** :
- Guide de démarrage reproductible.
- Séparer "local dev" vs "cloud/Modal".

