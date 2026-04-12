# CHANGELOG_GAMER

Ce fichier regroupe l’historique complet reconstitué du logiciel **Kommz Gamer** (incluant l’ancienne base **ValorantTranslatorPro / Kommz Voice runtime**), à partir des documents fournis.

Périmètre de reconstruction:
- `Reprendre conversation mémorisée.pdf`
- `Reprendre conversation mémorisée 2éme partie.pdf`
- `Reprendre conversation mémorisée 3éme partie.pdf`
- `Reprendre conversation mémorisée 4éme partie.pdf`
- `Reprendre conversation mémorisée 5éme partie.pdf`
- `Reprendre conversation mémorisée 6éme partie.txt`
- `Gemini-Kommz Gamer - ElevenLabs.md`
- `Gemini-Kommz Gamer - ElevenLabs_Part2.md`
- `Gemini-Kommz Gamer + Amélioration Moteurs IA.md`
- `_Google Gemini 7éme parite.md`

---

## [KG-2026.03.10] - 2026-03-10 (Release Kommz Gamer 4.3)

### Added
- Mode hybride étendu côté client aux langues cibles:
  - `FR`
  - `EN`
  - `JA`
  - `KO`
  - `ZH`
- Support du chemin GPT-SoVITS distant (upload de la référence audio vers endpoint backend/Modal) en plus du mode local.

### Changed
- Bump de version produit côté runtime/build:
  - `version.txt` -> `4.3`
  - fallback interne de version aligné sur `4.3`
  - script `final_build.bat` aligné sur `4.3`
- Interface Hybrid simplifiée:
  - libellés génériques “Hybrid” au lieu de “Hybrid FR”
  - résumé d’usage mis à jour selon la langue active
  - état UI explicite quand la langue cible est hors périmètre Hybrid
- Auto-activation Hybrid désormais pilotée sur le périmètre multilingue supporté et non plus uniquement sur le français.

### Fixed
- Correction du périmètre fonctionnel Hybrid dans le client:
  - plus de restriction stricte au français alors que GPT-SoVITS/XTTS permettent un sous-ensemble multilingue crédible
- Meilleure lisibilité produit dans l’UI pour distinguer:
  - mode Hybrid réellement actif
  - fallback `voice_id / clone direct`
  - langue hors périmètre Hybrid
- Alignement des textes produit/présentation avec la release `4.3`.

### Notes
- Le mode Hybrid reste volontairement limité à `FR/EN/JA/KO/ZH`.
- Les autres langues du logiciel continuent de fonctionner via la chaîne standard `voice_id / clone direct`.
- Cette release vise d’abord la cohérence produit, la qualité du timbre et la clarté de l’expérience utilisateur.

---

## [KG-2025.09] - 2025-09 (Fondation Core/Sidecar + Pipeline PTT)

### Added
- Architecture initiale en 2 services:
  - `vtp_core.py` (Flask, logique principale)
  - `vtp_sidecar*.py` (PTT/bridges/compat)
- Pipeline PTT serveur avec routes opérationnelles:
  - `POST /ptt/text`
  - `POST /ptt/config`
  - `POST /ptt/hold_down`
  - `POST /ptt/release`
  - `GET|POST /tts/say` (selon patch côté sidecar/core)
- Patch UI dédié (`vtp_ui_patch.js`) + variantes `index_patched_*` pour brancher le flux PTT final sans casser l’UI existante.

### Changed
- Normalisation des appels UI -> Core/Sidecar:
  - `/apply`
  - `/status`
  - `/obs/ping`
  - `/tts/say`
- Ajustement du comportement fallback traduction/TTS pour éviter le blocage de la chaîne quand un moteur externe n’est pas disponible.

### Fixed
- Problème majeur de redirection MT (`307 Temporary Redirect`) sur:
  - `/api/mt/translate`
- Correction des routes MT pour accepter variantes avec/sans slash et éviter boucles de redirection.
- Stabilisation du retour JSON unifié (même en échec moteur) avec `engine_used=core_error` pour préserver le flux UI.

### Ops / Validation
- Tests curl systématisés sur:
  - `/api/mt/translate`
  - `/mt/translate`
- Critère de validation: passage en `200 OK` (plus de `307`/`500`).

---

## [KG-2025.10] - 2025-10 (Intégration CosyVoice2 / VC + Robustesse Sidecar)

### Added
- Intégration CosyVoice/CosyVoice2 dans le sidecar standalone (`vtp_sidecar_standalone_vc.py`).
- Endpoints techniques de supervision sidecar (selon versions):
  - `/health`
  - `/status`
  - `/debug/env`
- Compatibilité API VC/TTS côté sidecar pour appels `source_speech/prompt_speech/language/text`.

### Changed
- Préparation audio standardisée pour VC:
  - WAV PCM mono
  - 16 kHz
- Ajout scripts et procédures de nettoyage audio de test (`AudioTests`) pour fiabiliser l’inférence VC.

### Fixed
- Résolution des conflits de port `8781` (process/service déjà actif).
- Diagnostic et traitement des cas:
  - process Python orphelin
  - service Windows (`VTP-Sidecar`) auto-relancé
  - fallback temporaire sur port alternatif (`8782`)
- Correction des erreurs d’accès bind socket (`Errno 10048`) en procédure opératoire.

### Ops / Validation
- Checklist d’exploitation ajoutée:
  - `Test-NetConnection`
  - `netstat -ano`
  - `Stop-Process` / `taskkill`
  - `Stop-Service VTP-Sidecar`
- Smoke tests sidecar/core formalisés.

---

## [KG-2025.11] - 2025-11 (Stabilisation exploitation locale)

### Added
- Documentation opératoire de reprise complète (port, service, relance, smoke tests).
- Procédure de diagnostic hiérarchique:
  - PID occupant
  - parent process
  - service/tâche planifiée
  - mode de relance propre

### Changed
- Priorité donnée à la fiabilité runtime (santé endpoints, redémarrage propre, verification chainée).

### Fixed
- Régressions de démarrage sidecar en environnement déjà occupé.
- Cas de sidecar ancien en arrière-plan sans routes debug modernes.

---

## [KG-2025.12] - 2025-12 (Cloud Voice / ElevenLabs + Fusion Core)

### Added
- Intégration ElevenLabs dans le moteur principal:
  - gestion `api_key`
  - gestion `voice_id`
  - synthèse cloud mode
- Modes de lancement “cloud mode” et scénarios de test rapides.
- Overlay/OBS renforcé:
  - sous-titrage
  - sorties texte
  - routes de statut associées
- Bases de “core fusionné” (moins de dépendances externes type `mt_shim`).

### Changed
- Refonte progressive de `vtp_core.py` vers version monolithique plus autonome.
- Réduction des dépendances inter-services pour limiter les points de panne.

### Fixed
- Erreurs de configuration `voice_id` ElevenLabs côté UI/config.
- Cas de son non audible malgré succès API (ajustements routing/lecture).

---

## [KG-2026.01] - 2026-01 (Kommz Gamer Wiki/Modules/Build Pro)

### Added
- Enrichissement massif du produit “Kommz Gamer”:
  - guides `Ultimate Wiki` (v7/v8.3)
  - structure modules activables
- Modules fonctionnels intégrés ou spécifiés:
  - `Tilt Shield` (anti-toxicité)
  - `Stream Connect` (sorties stream/obs)
  - `Tactical Macros` (voix -> actions)
  - `Radio FX` (immersion)
  - `Polyglot Stream`
  - `Privacy Sentinel`
  - `Smart Marker`
- Hotkey globale:
  - support activation globale
  - sélection dynamique côté UI
- Mode furtif/logging discret:
  - `stealth_print`
  - réduction des fuites console
- Chaîne de build EXE:
  - scripts `compile.bat`, `final_build.bat`, scripts de réparation
  - itérations packaging pour runtime stable

### Changed
- Refonte UI index:
  - mapping modules
  - toggles
  - panneau configuration enrichi
- Refonte audio routing:
  - scénarios VB-Cable
  - contrôle de lecture locale vs injectée
- Consolidation codebase autour d’un core plus complet (traduction + TTS + modules).

### Fixed
- Multiples erreurs de robustesse Python/JS:
  - `NameError`
  - `SyntaxError` (f-string / accolades CSS)
  - `UnicodeEncodeError`
  - erreurs d’imports et de structure script
- Correctifs anti-écho et anti-auto-réinjection dans le pipeline d’écoute.
- Correctifs volume/perception (volume trop faible / saturation) avec instrumentation et réglage progressif.

### Build & Packaging
- Durcissement du packaging runtime pour exe standalone.
- Itérations de scripts de build/réparation jusqu’à exécution stable de la version compilée.

---

## [KG-2026.03] - 2026-03-05 (Cycle XTTS avancé + VoiceID backend)

### Added
- Routage voix forcée via backend web (`voice_id`) côté client Gamer.
- Compat routes synthèse côté backend:
  - `POST /v1/synthesis`
  - `POST /v1/synthesis/`
  - `POST /api/v1/synthesis`
  - `POST /api/v1/synthesis/`
- Contrôles XTTS avancés exposés côté logiciel:
  - `top_k`, `top_p`, `repetition_penalty`, `length_penalty`
  - `enable_text_splitting`
  - `gpt_cond_len`, `gpt_cond_chunk_len`, `max_ref_len`, `sound_norm_refs`
- Presets XTTS côté logiciel (mode rapide de tuning).
- Onglet `Secure TTS` (visibilité conditionnelle), bouton déconnexion rétabli.
- Slider vitesse (remplacement du sélecteur discret).

### Changed
- Pipeline PTT/STT client renforcé:
  - fallback canaux micro (résolution `PaErrorCode -9998`)
  - capture fin de relâche PTT (tail)
  - logs plus explicites côté transcription
- Intégration Deepgram ajustée (suppression alternatives incompatibles Nova-2).
- Flux hybride GPT-SoVITS -> XTTS intégré avec fallback automatique clone.

### Fixed
- 404 de synthèse sur variantes route API.
- 500 backend `name 'top_k' is not defined`.
- Fallback `voice_id` indisponible mieux diagnostiqué et contrôlé.
- Régression capture micro / ouverture stream selon channels.

### Audio / Quality
- Réduction saturation/souffle rire par itérations côté `modal_xtts.py`.
- Ajout puis assouplissement des chaînes de mastering rire pour éviter étouffement/coupure.
- Configuration stable finale recommandée:
  - `XTTS_POSTPROCESS_MODE=strong`
  - `XTTS_MASTERING_ENABLED=1`
  - `XTTS_LAUGH_MASTERING_ENABLED=0`
  - `XTTS_LAUGH_BREATH_REDUCTION_ENABLED=0`

---

## Public API / Interfaces (Kommz Gamer runtime)

### Backend synthesis
- `POST /v1/synthesis`
- `POST /v1/synthesis/`
- `POST /api/v1/synthesis`
- `POST /api/v1/synthesis/`

### Paramètres XTTS relayés
- `top_k`
- `top_p`
- `repetition_penalty`
- `length_penalty`
- `enable_text_splitting`
- `gpt_cond_len`
- `gpt_cond_chunk_len`
- `max_ref_len`
- `sound_norm_refs`

### Variables d’environnement critiques
- `MODAL_XTTS_URL`
- `MODAL_XTTS_WARMUP_URL`
- `MODAL_XTTS_HEALTH_URL`
- `XTTS_POSTPROCESS_MODE`
- `XTTS_MASTERING_ENABLED`
- `XTTS_LAUGH_MASTERING_ENABLED`
- `XTTS_LAUGH_BREATH_REDUCTION_ENABLED`

---

## Known Behavior / Limites (Gamer)
- La qualité des interjections (`ha ha`, rires, souffles) reste sensible à la qualité STT d’entrée.
- Le mode hybride GPT-SoVITS exige une référence conforme (3–10s) pour éviter les `HTTP 400`.
- Le mode `voice_id` forcé dépend strictement de la présence du profil côté backend/account ciblé.
- Les configurations audio Windows (écoute micro, virtual cable, sample rate) restent déterminantes pour éviter écho/saturation.

---

## Checklist de déploiement / validation (Gamer)
1. `git pull` + `git push` du backend et scripts client.
2. Render: `Deploy latest commit`.
3. Modal: `modal deploy modal_xtts.py`.
4. Vérifier `GET /health` backend.
5. Tester `POST /v1/synthesis` avec vraie API key et vrai `voice_id`.
6. Test manuel PTT phrase normale + phrase émotion (`je rigole ha ha ha`).
7. Vérifier fallback clone seulement en cas d’indisponibilité `voice_id`.

---

## Annexe détaillée (granulaire) — itérations historiques Gamer

Légende statut:
- **[CONFIRMÉ]**: implémentation/correctif effectivement intégré dans une version de travail mentionnée.
- **[DOCUMENTÉ]**: prototypé, spécifié ou livré en script/patch dans les échanges, à valider dans la build cible.

### A. Pipeline STT/MT/TTS et fiabilité requêtes
- [CONFIRMÉ] Correction du cycle `307` sur `/api/mt/translate`.
- [CONFIRMÉ] Ajout de compat routes avec et sans slash sur MT/synthesis.
- [CONFIRMÉ] Retour JSON stable en cas d’échec moteur (`core_error`) pour ne pas casser l’UI.
- [DOCUMENTÉ] Variantes fallback DeepL/Google selon clés disponibles.
- [CONFIRMÉ] Ajustement Deepgram Nova-2 (suppression alternatives > 1 incompatibles).
- [CONFIRMÉ] Logs HTTP détaillés pour diagnostics STT/TTS.

### B. Audio routing, capture et anti-écho
- [CONFIRMÉ] Fallback canaux micro pour éviter `PaErrorCode -9998`.
- [CONFIRMÉ] Ajustements de fin d’enregistrement PTT (release tail).
- [CONFIRMÉ] Filtrage anti auto-réinjection (éviter que le moteur se réécoute).
- [DOCUMENTÉ] Scénarios VB-Cable “obligatoire vs facultatif” selon contexte jeu/stream.
- [DOCUMENTÉ] Calibration volume (silence/saturation) avec points de contrôle.

### C. Voice engines (ElevenLabs, XTTS, CosyVoice)
- [CONFIRMÉ] Intégration ElevenLabs (API key + voice id + fallback).
- [CONFIRMÉ] Intégration XTTS backend + modal pour génération clone.
- [CONFIRMÉ] Paramètres avancés XTTS relayés de bout en bout.
- [CONFIRMÉ] Compat route `/v1/synthesis` + alias `/api/v1/synthesis`.
- [CONFIRMÉ] Correction bug runtime `/v1/synthesis` (`top_k` non défini).
- [CONFIRMÉ] Correction dépendances japonaises XTTS (`cutlet`, `fugashi`, `unidic-lite`).
- [CONFIRMÉ] Keepalive/warmup XTTS pour réduire cold start.
- [CONFIRMÉ] Cache conditioning XTTS pour latence réduite sur voix répétées.
- [DOCUMENTÉ] Itérations CosyVoice2 VC/TTS avec normalisation WAV 16k mono.

### D. Qualité voix (saturation, souffle, rire)
- [CONFIRMÉ] Post-process audio (DC offset, limiter, fade, guard).
- [CONFIRMÉ] Mastering ffmpeg de sortie.
- [CONFIRMÉ] Normalisation interjections/rire.
- [CONFIRMÉ] Plusieurs profils rire testés puis assouplis pour éviter étouffement.
- [CONFIRMÉ] Defaults stables finaux: rire mastering désactivé par défaut.
- [DOCUMENTÉ] Mode anti-souffle renforcé en option sur segments rire.

### E. UI/UX logiciel Gamer
- [CONFIRMÉ] Onglet Secure TTS ajouté (visibilité conditionnelle).
- [CONFIRMÉ] Bouton déconnexion rendu visible/corrigé.
- [CONFIRMÉ] Slider vitesse remplaçant sélecteur discret.
- [CONFIRMÉ] Presets XTTS + panneau paramètres avancés.
- [DOCUMENTÉ] Variantes interface modules streamer/esport dans guides UI.

### F. OBS / overlay / stream tooling
- [DOCUMENTÉ] Modes overlay “fantôme/boîte fixe”.
- [DOCUMENTÉ] Intégration sorties texte stream (`.txt`) et alignements OBS.
- [DOCUMENTÉ] Modules Polyglot Stream / Privacy Sentinel / Smart Marker.
- [DOCUMENTÉ] Scénarios de mise en page et shortcuts (ex F8) dans versions wiki.

### G. Modules “Diamond / Ultimate Wiki”
- [DOCUMENTÉ] Tilt Shield (anti-toxicité).
- [DOCUMENTÉ] Tactical Macros (voix -> commandes).
- [DOCUMENTÉ] Radio FX (immersion audio).
- [DOCUMENTÉ] Stream Connect (pipeline export stream).
- [DOCUMENTÉ] Lot complet modules v6.0/v7.0/v8.3 décrit et packagé en guides.

### H. Build/packaging/exploitation Windows
- [DOCUMENTÉ] Itérations build `.bat` successives (compile/final/repair).
- [DOCUMENTÉ] Correctifs spécifiques erreurs pyav/pyaudio/imports/encodage.
- [CONFIRMÉ] Procédures diagnostic ports/services (8781, PID, service `VTP-Sidecar`).
- [CONFIRMÉ] Procédure fallback port alternatif (8782) et variables associées.

### I. Checklist de validation recommandée (étendue)
- Vérifier `/health`, `/status`, `/v1/synthesis`, `/api/v1/synthesis`.
- Vérifier `voice_id` forcé avec vraie API key + profil existant.
- Vérifier fallback clone si `voice_id` absent.
- Vérifier phrase neutre + phrase émotion + phrase longue.
- Vérifier comportement micro 44.1k/48k et stabilité canaux.
- Vérifier rendu en jeu + rendu stream + rendu local (écoute opérateur).
## Matrice de Tra?abilit? Exhaustive

### Couverture des sources

- **Gemini-Kommz Gamer - ElevenLabs.md** (type=.md size=593286) -> `overlay`=189, `hotkey`=79, `google`=69, `ptt`=63, `license`=61, `elevenlabs`=21, `whisper`=17, `echo`=13, `vb-cable`=10, `nuitka`=4, `auth`=3, `build`=3
- **Gemini-Kommz Gamer - ElevenLabs_Part2.md** (type=.md size=1358156) -> `nuitka`=470, `obs`=385, `echo`=363, `vtp_core`=291, `elevenlabs`=178, `build`=122, `overlay`=101, `whisper`=83, `ptt`=74, `license`=58, `hotkey`=51, `pyaudio`=51

### R?f?rences d?taill?es (source -> ligne -> ?l?ment)

#### Gemini-Kommz Gamer - ElevenLabs.md

| Ligne | ?l?ment extrait | Tags |
|---:|---|---|
| 78 | ### 2\. Le Script Python (La Solution) | build |
| 155 | ### Piège fréquent avec VB-Cable | audio |
| 991 | ### Modifie cette partie dans ton `<script>` (à la fin de ton fichier) | build |
| 1095 | ### Ce qui va se passer pour tes clients : | ui |
| 1349 | ### 1\. Remplace tout le bloc `if(d.ok) { ... }` par celui-ci : | ui |
| 1391 | ### 2\. (Important) Mets à jour le bouton "Sauvegarder" plus bas | ui |
| 1522 | ### 2\. Dans le JEU (Paramètres Audio) | audio |
| 2344 | ### 🔴 Le Diagnostic | - |
| 2348 | ### 🛠️ Les Solutions | - |
| 2350 | #### 1\. Solution immédiate (Le "Soft Reset") | - |
| 4277 | ### ✅ La Solution : Utiliser Groq aussi pour la traduction | - |
| 4348 | ### 2\. Là où ton script est MEILLEUR que YouTube | build |
| 4371 | ### 🚀 Comment le rendre aussi fluide que possible ? | ui |
| 4409 | ### 2\. La Solution : Rendre le logiciel plus "nerveux" | - |
| 4560 | ### 🛠️ LA SOLUTION FINALE (À appliquer maintenant) | - |
| 4647 | ### 2\. Si le volume est TROP FORT (La Saturation) | audio |
| 4977 | ### 1\. La raison la plus fréquente : Le bouton "ACTIVER" | ui |
| 4996 | ### 3\. La raison "Technique" : Le script ne charge pas le son | build |
| 7997 | ### 1\. Le Diagnostic des Chiffres | - |
| 8043 | ### 🚑 LA SOLUTION RADICALE | - |
| 8250 | ### Ce qui change avec cette version : | ui |
| 8427 | ### 🛠️ La Solution : Mettre à jour le modèle | - |
| 8557 | ### Ce qui a changé : | ui |
| 8579 | ### 1\. Corrige la fonction d'écoute (transcribe\_safe) | stt |
| 8627 | ### 2\. Corrige la fonction PTT (stop\_rec) | stt |
| 8756 | ### Étape 2 : Modifier l'Interface Web (`index.html`) | ui |
| 8927 | ### 1\. Modification HTML (Le visuel) | - |
| 8950 | ### 2. Modification JavaScript (La logique) | build |
| 9137 | ### 2\. La partie JavaScript (La Logique) | build |
| 9830 | ### Copie et remplace TOUT le contenu entre `<script>` et `</script>` par ceci : | build |
| 10284 | ### Remplace le bloc "Overlay" dans `index.html` par celui-ci : | ui |
| 10337 | ### 🕵️‍♂️ Le Diagnostic | - |
| 10485 | ### 1\. Modification Majeure : `resample_and_play` | audio |
| 10640 | ### Étape 1 : Ajouter l'outil de comparaison | - |
| 10747 | ### Résumé de ce qui va se passer : | ui |
| 10831 | ### Étape 2 : Modifier le script pour qu'il te fasse entendre le son (Proprement) | build |
| 10977 | ### Étape 1 : Ajouter le paramètre de "Monitoring" | - |
| 10991 | ### Étape 2 : Créer la fonction du Bouton F3 | ui |
| 11009 | ### Étape 3 : Mettre à jour le Moteur Audio (`resample_and_play`) | audio |
| 11282 | ### 2\. Ajoute la fonction F3 tout en bas | - |
| 11384 | ### Étape 2 : Modifier le HTML (`index.html`) | ui |
| 11416 | ### Étape 3 : Modifier le JavaScript (`index.html`) | ui, build |
| 11544 | ### Ce qui a changé : | ui |
| 11674 | ### 3\. (Si ça ne marche toujours pas) Vérifie le bas du script | build |
| 11861 | ### Ce qui a été ajouté : | ui |
| 11924 | ### Étape 2 : Forcer le chargement de la librairie QR Code (`index.html`) | ui |
| 12068 | ### Remplace tout le bloc "GESTION COULEURS OVERLAY" par celui-ci : | ui |

#### Gemini-Kommz Gamer - ElevenLabs_Part2.md

| Ligne | ?l?ment extrait | Tags |
|---:|---|---|
| 154 | ### 2\. Où changer les "print" ? (La méthode rapide) | api |
| 225 | ### 3\. Tableau récapitulatif de ce qui change | api, ui |
| 453 | ### La modification à faire | - |
| 575 | ### 1\. Corrige la fonction `stealth_print` | - |
| 611 | ### La solution la plus sûre | - |
| 685 | ### 2\. Remplacer par ce code corrigé | - |
| 787 | ### Ce qui a été corrigé : | ui |
| 867 | ### Voici comment corriger votre fichier `vtp_core.py` : | - |
| 869 | #### Étape A : Corriger le gestionnaire de crash (Ligne 105) | - |
| 1066 | ### 🎧 Audio & Immersion | audio |
| 2807 | ### Pourquoi ces modifications sont importantes pour ton site ? | - |
| 2888 | ### Ce qui a changé dans ton tableau de bord | ui |
| 3722 | ### Ce qui a été ajouté dans ton Wiki : | ui |
| 3912 | ### Ce qui est maintenant inclus (Rien n'a été oublié) : | ui |
| 3960 | ### 1\. Style CSS (À ajouter dans la balise `<style>`) | - |
| 3999 | ### 3\. Touche F8 (À ajouter dans la liste `<ul class="cmd-list">`) | - |
| 4012 | ### Pourquoi ces ajouts sont essentiels ? | - |
| 4067 | ### 2\. Ajout des modules (HTML) | - |
| 4089 | ### 3\. Ajout de la touche F8 (Dans la liste des raccourcis) | - |
| 4134 | ### 1\. La solution au SyntaxError | - |
| 4138 | ### 2\. Le code complet corrigé (Section CSS et Modules) | - |
| 4269 | ### Pourquoi l'erreur `f-string` se produit ? | ui |
| 5111 | ### Ce qui a été corrigé : | ui |
| 6426 | ### 2\. Module "Stream Connect" (Sortie OBS .txt) | ui |
| 6479 | ### 4\. Module "Radio FX" (Immersion Audio) | audio |
| 6533 | ### Étape 2 : Ajouter la fonction "Tilt Shield" | - |
| 6663 | ### Résumé des ajouts | - |
| 6828 | ### Récapitulatif des dépendances : | api |
| 6923 | ### Étape 2 : Ajouter les boutons dans `index.html` | ui |
| 8622 | ### Vérification rapide | api |
| 8723 | ### 2\. Mettre à jour le Javascript (Mapping) | build |
| 8876 | ### 2\. Ajoute les 3 lignes de liaison | - |
| 9149 | ### Où l'ajouter ? | - |
| 9153 | ### Le code à ajouter : | - |
| 9211 | ### Étape 2 : Ajouter la source dans OBS | ui |
| 9328 | ### La solution "Boîte Fixe" (Indestructible) | - |
| 9570 | ### Ce que contient ce guide : | ui |
| 9642 | ### 2\. Module "Privacy Sentinel" (Anti-Leak) | security |
| 9710 | ### Mise à jour de l'Interface (`index.html` et `vtp_core.py`) | ui |
| 10248 | ### 2\. Module "Privacy Sentinel" (Anti-Leak) | security |
| 10289 | ### Intégration dans l'Interface (`index.html`) | ui |
| 10325 | ### Intégration dans le Mapping JS (`index.html`) | ui |
| 10448 | ### 2\. La Nouvelle Fonction `apply_privacy_sentinel` | security |
| 10548 | ### Étape 1 : Ajouter les routes API dans `vtp_core.py` | api |
| 10575 | ### Étape 2 : Ajouter l'interface visuelle dans `index.html` | ui |
| 10604 | ### Étape 3 : Le CSS et le Javascript (`index.html`) | ui, build |
| 10750 | ### 1\. Le code à ajouter | - |
| 10786 | ### 3\. Réponse pour l'EXE | build |
| 10832 | ### 2\. ⚠️ ATTENTION : L'erreur classique avec Nuitka | ui, build |
| 10999 | ### La Bonne Solution : Ton Interface 📱 | - |
| 11279 | ### Ce qui a changé (Important) : | ui |
| 12201 | ### Si tu veux le code complet corrigé pour éviter les erreurs de copier-coller : | - |
| 13762 | ### 🚀 Dernière petite astuce avant de compiler | build |
| 13840 | ### Étape 1 : Modification du Python (`vtp_core.py`) | - |
| 13879 | ### Étape 2 : Ajout des Boutons dans l'Interface (`index.html`) | ui |
| 13909 | ### Étape 3 : La Compilation "Magique" avec Nuitka 📦 | ui, build |
| 13967 | ### 1\. Le Code HTML (Pour `index.html`) | ui |
| 14031 | ### 2\. Le Javascript (Toujours dans `index.html`) | ui, build |
| 14132 | ### Remplace la route `/guide/open/<name>` par celle-ci : | api, ui |
| 14172 | ### Rappel important pour la compilation (Nuitka) | ui, build |
| 14227 | ### 2\. Dans la commande de Compilation (Nuitka) | ui, build |
| 14235 | ### 3\. Dans l'Interface (`index.html`) | ui |
| 14644 | ### 1\. La Modification Indispensable (Pour les Guides) | ui |
| 14657 | ### 2\. Est-ce que ça sera stable ? (Analyse Nuitka) | ui, build |
| 14669 | ### 3\. Ton Script .BAT Corrigé (Version Finale) | build |
| 14845 | ### La Fonction Corrigée (À remplacer dans `vtp_core.py`) | - |
| 15025 | ### 2\. Ajout de sécurité global (Très important) | - |
| 15162 | ### 1\. La Solution "Magique" (À faire tout de suite) | ui |
| 15296 | ### 2\. Solution Alternative (Augmenter la mémoire virtuelle) | - |
| 18376 | ### 🔍 Le Coupable : Les Espaces dans le nom "GUIDE LOGICIEL" | ui |
| 18388 | ### ✅ La Solution | - |
| 18401 | #### Méthode 2 : Mettre des guillemets (Si tu tiens à l'espace) | ui |
| 18407 | ### Voici ton script `.bat` CORRIGÉ (Méthode 1 - Plus stable) | build |
| 21580 | ### LA SOLUTION (À faire dans cet ordre précis) | - |
| 21589 | #### Étape 2 : Utiliser ce script corrigé | build |
| 21758 | ### 1\. Modification du Python (`vtp_core.py`) | - |
| 21776 | ### 2\. Le Script de Compilation FINAL (`.bat`) | build |
| 21950 | ### Étape 2 : Le Script "Blindé" (Avec guillemets) | ui, build |
| 22129 | ### 🛠️ LA SOLUTION ULTIME : Le "Bloc Compact" | - |
| 22262 | ### Ce qui a changé (et pourquoi ça va marcher) : | ui |
| 22354 | ### Étape 3 : Le Script `.bat` Simplifié (Et Fonctionnel) | build |
| 22733 | ### Étape 2 : Installer PyAudio (Souvent indispensable) | audio |
| 22793 | ### Étape 1 : Installer PyAudio dans le bon dossier (le venv) | audio |
| 22801 | ### Étape 2 : Mettre à jour le script de compilation | build |
| 22980 | ### Étape 2 : Le Script de Compilation (V8.3) | build |
| 23161 | ### Étape 2 : Script de Compilation (V8.4 - HEAVY DUTY) | build |
| 23437 | ### 🚀 SCRIPT FINAL V8.5 (Avec fermeture automatique) | build |
| 23722 | ### ⏳ La suite ? | ui |
| 23806 | ### 🚀 SCRIPT FINAL V8.6 (PyAV FIX) | build |
| 24018 | ### Étape 2 : Le Script de Compilation FINAL (V8.7) | build |
| 24772 | ### 3\. La Compilation V8.9 (La Solution Finale pour PyAV) | - |
| 24980 | #### A. Corriger l'erreur `NameError` (Guides) | ui |
| 25033 | ### Étape 2 : Le Script de Compilation V9.0 (Anti-Cython) | build |
| 25585 | #### A. Réparer l'erreur `view_guide` (Le `NameError`) | ui |
| 25868 | ### 2\. Retirer les Voix Françaises (Edge TTS) | tts |
| 25894 | ### 3\. Retirer le Français pour ElevenLabs | tts |
| 26035 | ### 3\. ATTENTION : Mise à jour Nuitka (V9.1) 🚨 | ui, build |
| 26428 | ### 1\. Ajoute/Remplace cette fonction de récupération | - |
| 30885 | ### 1\. Le Problème ElevenLabs (Fonction Manquante) | tts |
| 31321 | ### 🛠️ LA SOLUTION DÉFINITIVE | - |
| 31394 | ### Vérification rapide avant de compiler : | api, build |

