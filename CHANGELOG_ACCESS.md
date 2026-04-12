# CHANGELOG_ACCESS

Ce fichier regroupe l’historique complet reconstitué du logiciel **Kommz Access**, séparé du produit Gamer.

Périmètre de reconstruction:
- `Gemini-Site Web Kommz & Logiciel Kommz Access (1).md`
- `_Google Gemini 7éme parite.md` (parties communes architecture/runtime)
- `CHANGELOG_ACCESS.md` (consolidation précédente)
- documents de reprise fournis (contexte runtime global)

---

## [KA-2025.12] - 2025-12 (Base produit Access + UX conversation)

### Added
- Base interface `access.html` orientée conversation en temps réel:
  - zone transcription principale
  - bulles locuteurs (`MOI` / `INTERLOCUTEUR`)
  - contrôle taille police (A / A+ / A++)
  - thème clair/sombre
- Contrôles audio/TTS initiaux:
  - sélection voix
  - champ réponse texte + lecture vocale
  - boutons action démarrer/stop

### Changed
- Positionnement du produit Access vers usage quotidien/médical/professionnel (lisibilité et confiance avant “effets”).

### Fixed
- Stabilisation des premiers flux UI -> API locale pour éviter rupture conversationnelle.

---

## [KA-2026.01.0] - 2026-01 (Roadmap Phase 1: lisibilité et rassurance)

### Added
- Indicateur d’écoute dynamique:
  - statut micro visible
  - visualizer temps réel
  - messages d’état explicites
- Bulles de dialogue optimisées accessibilité:
  - contrastes renforcés
  - styles différenciés selon locuteur
  - animation d’entrée des messages

### Changed
- Priorité donnée à l’expérience visuelle pour public sourd/malentendant:
  - densité d’information mieux structurée
  - fatigue visuelle réduite

### Fixed
- Feedback utilisateur “le logiciel écoute ou non” rendu explicite (suppression incertitude d’usage).

---

## [KA-2026.01.1] - 2026-01 (Roadmap Phase 2: productivité conversation)

### Added
- Barre de **phrases rapides** (quick replies) pour réponses fréquentes en 1 clic.
- Mise en valeur automatique de contenu important:
  - chiffres
  - mots-clés critiques
  - style `important-word` (poids/couleur/soulignement)
- Panneau de confidentialité visible:
  - rappel traitement local
  - bouton de fermeture utilisateur

### Changed
- Flux conversation orienté “réaction immédiate” et lecture contextuelle.

### Fixed
- Corrections structure JS/CSS sur pages complètes Access (fonctions imbriquées, fermeture blocs, visualizer).

---

## [KA-2026.01.2] - 2026-01 (Voix personnalisées + moteur TTS double)

### Added
- Panneau vocal utilisateur (icône 👤) avec affichage/masquage dynamique.
- Choix moteur TTS:
  - système local
  - ElevenLabs (clonage voix)
- Champs de configuration ElevenLabs:
  - API key (champ masqué)
  - Voice ID

### Changed
- Persistance configuration voix via API locale (`/config/update`) et adaptation UI selon provider.

### Fixed
- Rétablissement audio sur `action/speak` après régression mapping fonctions lecture.
- Correction liaison bouton panneau vocal et état visuel actif.

---

## [KA-2026.01.3] - 2026-01 (Fonctions avancées 90 jours)

### Added
- Export conversation et fonctions d’archivage utilisateur.
- Lexique personnalisé éditable côté UI.
- Mode “Toujours au-dessus”/pin et gestion overlay.
- Mode “Ghost / Réalité augmentée” pour lecture superposée discrète.
- Bandeau d’alerte sécurité visuelle (`safetyAlert`) pour événements marqués.
- Préparation des briques “analyse ton/émotions” et “bruits critiques” côté roadmap.

### Changed
- Passage d’une UX “outil de transcription” à une UX “assistant conversationnel complet”.

### Fixed
- Corrections de cohérence d’affichage lors d’injection d’alertes et logs mixtes.

---

## [KA-2026.01.4] - 2026-01 (Diarisation et identité locuteurs)

### Added
- Introduction logique de diarisation/speaker tracking:
  - identifiants locuteurs
  - couleurs associées
  - base de gestion speaker dans logs
- Préparation intégration diarisation avancée (évolutif vers reconnaissance timbre réelle).

### Changed
- Ajustements comportement speaker pour réduire alternance artificielle de locuteurs.

### Fixed
- Correction des sauts de speaker non souhaités en mode mono-interlocuteur.

---

## [KA-2026.02.0] - 2026-02 (Sécurité licence et authentification moderne)

### Added
- Migration activation/licence vers backend robuste (Supabase).
- Endpoints auth/licence:
  - `POST /auth/activate`
  - `POST /auth/rebind`
  - `POST /auth/trial-start`
  - `GET /auth/status`
  - `GET /auth/license-info`
  - `GET /auth/pricing`
- Journal d’audit activation/rebind/trial.

### Changed
- Validation email renforcée:
  - `trim`
  - `lowercase`
  - suppression caractères invisibles
  - regex robuste

### Fixed
- Incohérences UI licence/expiration.
- Cas de validation email trop permissive entre frontend/backend.

---

## [KA-2026.02.1] - 2026-02 (Stabilité runtime / autosave / diarisation)

### Added
- Logs détaillés de transitions speaker:
  - `SPK switch[new]`
  - `SPK switch[bootstrap]`
  - `SPK switch[immediate]`
  - `SPK switch[confirm]`
- Option de restauration autosave au démarrage:
  - `ACCESS_RESTORE_AUTOSAVE_ON_START`

### Changed
- Smart Profiling diarisation:
  - rematch prioritaire profil existant
  - création nouveau speaker plus stricte
  - anti-contamination profils
  - confirmation multi-phrases + cooldown/lock
- Auto-scroll conversation non forcé si utilisateur lit l’historique.

### Fixed
- Réapparition conversation après suppression (autosave résiduel).
- Régressions encodage UI (caractères corrompus).
- Crashs démarrage no-console (renforcés par hook fatal).

---

## [KA-2026.02.2] - 2026-02 (Update, packaging, distribution)

### Added
- Update checker manifest distant + fallback local.
- Hook crash fatal orienté diagnostic production.

### Changed
- Packaging `onefile` stabilisé (Nuitka) avec inclusion explicite:
  - `web_access/`
  - `kommz-access-update.json`
  - dépendances runtime (`requests`, `certifi`, etc.)

### Fixed
- Erreur BOM UTF-8 (`Unexpected UTF-8 BOM`) sur manifest local.
- Régressions de build/exe avec assets non inclus.

### Build & Packaging
- Script `build_exe.bat` fiabilisé.
- Rebuild exécutable Access validé en lancement.

---

## [KA-2026.03] - 2026-03-05 (Consolidation opérationnelle)

### Added
- Consolidation des notes d’exploitation (sécurité + diarisation + update) dans une base unique de changelog.

### Changed
- Recommandation de profil stable production:
  - diarisation prudente
  - autosave contrôlé
  - UI licence stricte

### Fixed
- Alignement des pratiques de déploiement Access avec le reste de l’écosystème Kommz.

---

## Endpoints / Interfaces Access (référence consolidée)

### Auth / Licence
- `POST /auth/activate`
- `POST /auth/rebind`
- `POST /auth/trial-start`
- `GET /auth/status`
- `GET /auth/license-info`
- `GET /auth/pricing`

### Configuration / actions (selon builds Access)
- `POST /config/update`
- `POST /action/toggle`
- `POST /action/speak`
- `POST /action/save`
- `POST /action/clear`
- `POST /action/toggle_top`
- `POST /action/toggle_ghost`
- `POST /config/lexicon`
- `GET /audio/voices`
- `GET /audio/devices`

---

## Variables d’environnement / réglages importants (Access)
- `ACCESS_RESTORE_AUTOSAVE_ON_START`
- variables licence/API selon build Access
- variables update manifest (distantes/locales)

---

## Known Behavior / Limites (Access)
- La diarisation multi-locuteurs reste sensible aux conditions micro/bruit et à la durée d’échange.
- L’analyse émotionnelle basée mots-clés est indicative (pas un classifieur prosodique complet).
- Le mode overlay/ghost dépend du contexte d’affichage OS/fenêtrage.
- Le mode voix clonée dépend de la qualité API key/voice id/provider et de la connectivité.

---

## Checklist de livraison Access
1. Vérifier endpoints auth/licence (`/auth/*`).
2. Vérifier update manifest (distant + fallback local).
3. Valider suppression + non-réapparition conversation (autosave).
4. Valider diarisation sur scénario 1 locuteur puis 2 locuteurs.
5. Valider TTS provider (système + ElevenLabs).
6. Rebuilder package onefile et tester lancement no-console.

---

## Annexe détaillée (granulaire) — itérations historiques Access

Légende statut:
- **[CONFIRMÉ]**: implémentation/correctif explicitement intégré et réutilisé dans les itérations Access.
- **[DOCUMENTÉ]**: proposition/prototype livré dans les échanges, à valider dans la build cible finale.

### A. UX conversation et accessibilité
- [CONFIRMÉ] Bulle `MOI` / `INTERLOCUTEUR` avec distinction visuelle forte.
- [CONFIRMÉ] Contrôles taille de police (A/A+/A++) pour fatigue visuelle.
- [CONFIRMÉ] Indicateur d’écoute dynamique + visualizer micro.
- [CONFIRMÉ] Messages d’état rassurants (écoute, attente, pause).
- [CONFIRMÉ] Barre de phrases rapides pour réponses urgentes/fréquentes.
- [CONFIRMÉ] Animation entrée messages + lisibilité renforcée.

### B. Lecture intelligente du contenu
- [CONFIRMÉ] Highlight automatique des nombres/chiffres.
- [CONFIRMÉ] Highlight mots-clés importants (urgence, rdv, prix, etc.).
- [DOCUMENTÉ] Extensions NLP ton/émotion plus avancées (au-delà mots-clés).

### C. Confidentialité, confiance et sécurité perçue
- [CONFIRMÉ] Panneau confidentialité visible avec fermeture utilisateur.
- [DOCUMENTÉ] Évolutions “privacy by design” médical/juridique renforcées.
- [DOCUMENTÉ] Alertes sons critiques (sirène/alarme/sonnette) en mode sécurité.

### D. Modes d’affichage avancés
- [CONFIRMÉ] Mode “toujours au-dessus” (pin).
- [CONFIRMÉ] Mode ghost / overlay de lecture.
- [DOCUMENTÉ] Variantes “réalité augmentée” pro pour visio/réunions.

### E. Voix, TTS et panel utilisateur
- [CONFIRMÉ] Panneau vocal (icône 👤) + état actif.
- [CONFIRMÉ] Double moteur TTS (système + ElevenLabs selon config).
- [CONFIRMÉ] Champ clé API masqué + voice id persistant.
- [CONFIRMÉ] Correction route `action/speak` après régression mapping lecture.
- [DOCUMENTÉ] Ajouts de presets voix par contexte d’usage.

### F. Diarisation / speaker profiling
- [CONFIRMÉ] Introduction speaker_id + couleurs.
- [CONFIRMÉ] Smart profiling avec rematch prioritaire profil existant.
- [CONFIRMÉ] Création nouveau speaker plus stricte + confirmation multi-phrases.
- [CONFIRMÉ] Logs speaker détaillés (`SPK switch[*]`).
- [DOCUMENTÉ] Pipeline diarisation avancée timbre (pyannote/équivalent) en évolution.

### G. Données utilisateur, autosave, archivage
- [CONFIRMÉ] Export conversation.
- [CONFIRMÉ] Effacement conversation + purge autosave associée.
- [CONFIRMÉ] Option restauration autosave au lancement (`ACCESS_RESTORE_AUTOSAVE_ON_START`).
- [CONFIRMÉ] Correction bug “réapparition conversation supprimée”.

### H. Licence, auth et back-office
- [CONFIRMÉ] Migration licence vers logique distante Supabase.
- [CONFIRMÉ] Endpoints `/auth/*` (activate/rebind/trial/status/info/pricing).
- [CONFIRMÉ] Validation email renforcée (trim/lower/invisibles/regex).
- [CONFIRMÉ] Journal d’audit activation/rebind/trial.
- [CONFIRMÉ] UI licence/expiration harmonisée.

### I. Update checker et résilience production
- [CONFIRMÉ] Update checker manifest distant + fallback local.
- [CONFIRMÉ] Correction BOM UTF-8 sur manifest.
- [CONFIRMÉ] Hook crash fatal pour builds no-console.
- [CONFIRMÉ] Stabilisation globale démarrage runtime no-console.

### J. Build/packaging Access
- [CONFIRMÉ] Build Nuitka onefile durci.
- [CONFIRMÉ] Inclusion explicite assets web et manifest update.
- [CONFIRMÉ] Script `build_exe.bat` fiabilisé.
- [DOCUMENTÉ] Itérations alternatives de build “blind/radical” discutées pour environnements cassés.

### K. Endpoints/actions UI récurrents (historique)
- [CONFIRMÉ] `POST /config/update`
- [CONFIRMÉ] `POST /action/toggle`
- [CONFIRMÉ] `POST /action/speak`
- [CONFIRMÉ] `POST /action/save`
- [CONFIRMÉ] `POST /action/clear`
- [CONFIRMÉ] `POST /action/toggle_top`
- [CONFIRMÉ] `POST /action/toggle_ghost`
- [CONFIRMÉ] `POST /config/lexicon`
- [CONFIRMÉ] `GET /audio/voices`
- [CONFIRMÉ] `GET /audio/devices`

### L. Validation étendue recommandée (Access)
- Scénario 1 locuteur long (pas de switch parasite).
- Scénario 2 locuteurs alternés (switch contrôlé).
- Test suppression conversation + redémarrage (pas de résurrection autosave).
- Test activation licence + rebind + trial.
- Test provider TTS système puis ElevenLabs.
- Test overlay/ghost + pin + lisibilité A/A+/A++.
- Test build onefile puis exécution no-console.
## Matrice de Tra?abilit? Exhaustive

### Couverture des sources

- **Gemini-Site Web Kommz & Logiciel Kommz Access (1).md** (type=.md size=4740049) -> `elevenlabs`=403, `overlay`=393, `license`=254, `whisper`=242, `auth`=139, `build`=106, `speaker`=81, `obs`=67, `google`=66, `voice_id`=54, `vb-cable`=51, `cosy`=44

### R?f?rences d?taill?es (source -> ligne -> ?l?ment)

#### Gemini-Site Web Kommz & Logiciel Kommz Access (1).md

| Ligne | ?l?ment extrait | Tags |
|---:|---|---|
| 41 | ### Comment corriger le lien annuel ? | - |
| 174 | ### 2\. Où mettre le texte ? (Guide pratique) | ui |
| 451 | ### Option 2 : L'Intelligence Artificielle (Rapide) | api |
| 492 | ### 3\. Le Descriptif (Clair et net) | build |
| 793 | ### Comment mettre ce site en ligne gratuitement ? | ui |
| 6840 | ### Code `App.tsx` (Final avec boutons actifs) | ui |
| 9121 | ### 🛠️ La Solution (2 étapes) | - |
| 10583 | ### ⚠️ Voici la manipulation exacte à faire (Suivez bien l'ordre) : | ui |
| 11308 | ### 🚀 The Solution (Step-by-Step) | - |
| 12795 | ### Étape 3 : Le Code Final (Garanti sans erreur de Build) | ui, build |
| 15073 | ### Modifications effectuées : | - |
| 16831 | ### Ce qui a été ajouté précisément : | ui |
| 19798 | ### 1\. Modifications dans `access_core.py` | - |
| 19822 | ### 2\. Modifications dans `access.html` | - |
| 19901 | ### Pourquoi ces changements sont stratégiques selon ta Roadmap : | - |
| 20655 | ### Prochaine étape suggérée (Roadmap Phase 2-4) : | - |
| 20671 | ### 🛠️ Ce qui a été ajouté : | ui |
| 21841 | ### 🎯 Qu'est-ce qui a été corrigé ? | ui |
| 21873 | ### 🔒 Ce qui a été ajouté : | ui |
| 22626 | ### 1\. Modifications dans `access_core.py` | - |
| 22669 | ### 2\. Modifications dans `access.html` | - |
| 23056 | ### 1\. Modifications dans `access_core.py` | - |
| 23094 | ### 2\. Modifications dans `access.html` | - |
| 23444 | ### 1\. Détection des Bruits Environnants (Sécurité & Alertes) | ui |
| 23452 | ### 2\. Mode "Réalité Augmentée" (Overlay Fantôme pour Pro) | ui |
| 23473 | ### 5\. Reconnaissance des Locuteurs (Diarization) | diar |
| 25251 | ### 1\. Modifications dans `access_core.py` | - |
| 25307 | ### 2\. Modifications dans `access.html` | - |
| 25747 | ### Comment corriger : | - |
| 25767 | ### Pourquoi cela corrige l'erreur : | - |
| 25798 | ### Ce que j'ai ajouté dans vos fichiers pour cela : | - |
| 25813 | ### Rappel de l'étape 2 : Mode "Réalité Augmentée" (Overlay Fantôme) | ui |
| 25831 | ### 1\. Modifications dans `access_core.py` | - |
| 25856 | ### 2\. Modifications dans `access.html` | - |
| 26890 | ### 1\. Modifications dans `access_core.py` | - |
| 26934 | ### 2\. Modifications dans `access.html` | - |
| 27000 | ### 2\. Code `access.html` complet et corrigé | - |
| 27310 | ### 1\. Modifications dans `access_core.py` | - |
| 27346 | ### 2\. Modifications dans `access.html` | - |
| 27563 | ### Ce qui a été ajouté : | ui |
| 29009 | ### Voici comment corriger le bloc SETTINGS : | - |
| 29031 | ### Ce qui causait l'erreur : | ui |
| 29035 | ### Rappel des étapes suivantes (Diarization) : | ui, diar |
| 29373 | ### Ce qui a été corrigé : | ui |
| 29453 | ### 🛠️ Modifications apportées : | - |
| 29815 | ### 1\. Modifications dans `access_core.py` | - |
| 29846 | ### 2\. Modifications dans `access.html` | - |
| 29946 | ### Prochaine amélioration (Roadmap) | - |
| 30128 | ### 1\. Mise à jour de `process_audio_chunk_cloud` | audio |
| 30233 | ### 3\. Solution Ultime (Bouton Manuel) | ui |
| 30267 | ### 1\. Modifications dans `access_core.py` | - |
| 30308 | ### 2\. Modifications dans `access.html` | - |
| 30751 | ### Ce qui a été corrigé : | ui |
| 30780 | ### Pourquoi cette modification est nécessaire ? | - |
| 31799 | ### Pourquoi ces erreurs bloquaient le "Build" ? | ui, build |
| 33078 | ### Pour Kommz Gamer (La Roadmap "Invisible") : | - |
| 33086 | ### Pour Kommz Access Pro (La Roadmap "Intelligence") : | - |
| 33137 | ### 2\. Produits et Services | ui |
| 33156 | ### 5\. Licence et Utilisation | security |
| 33161 | ### 6\. Protection des Données et Confidentialité | security |
| 34327 | ### Ce qui change dans ce code : | ui |
| 34705 | ### Modifications apportées : | - |
| 35649 | ### Étape 3 : Sécurisation API (Token de Session) | api |
| 36550 | ### 1\. Correction du fichier `build_exe.bat` | ui, build |
| 36730 | ### Solution radicale (La commande ciblée) | - |
| 36814 | ### Étape 2 : Le fichier `build_exe.bat` "Infaillible" | ui, build |
| 36848 | ### Étape 3 : Lancez le build | ui, build |
| 36876 | ### La solution : Modifier `build_exe.bat` | ui, build |
| 36944 | ### La solution : Le script de construction "Blindé" | build |
| 37016 | ### Étape 1 : Le Script de Construction "Nettoyage Total" | build |
| 37160 | ### Solution 1 : L'installation "Force Brute" (Sans désinstallation) | - |
| 37174 | ### Solution 2 : Le Nettoyage Manuel (Si la Solution 1 échoue) | - |
| 37189 | ### Étape Finale : Le Build | ui, build |
| 37209 | ### La Solution | - |
| 37235 | ### Si vous préférez une méthode plus rapide (Sans ajouter de code) | api |
| 37742 | ### 📥 Installation Rapide | api |
| 37786 | ### Voici comment corriger ça dans Make.com : | - |
| 39873 | ### Ce qui a été fait : | ui |
| 44201 | ### Modifications apportées : | - |
| 63833 | ### A. Prérequis Techniques | ui |
| 63861 | ### A. Transcription Instantanée | build |
| 63947 | ### 2\. Configuration VB-Audio (Le Pont Sonore) | audio |
| 63976 | ### 1\. Transcription Instantanée Haute Précision | build |
| 64116 | ### 1\. Installation du prérequis | ui |
| 64124 | ### 2\. Le script Python (`generate_guide.py`) | ui, build |
| 64309 | ### Le script Python complet (`generate_full_guide.py`) | ui, build |
| 64677 | ### Ce qui a été respecté : | ui |
| 64900 | ### Ce qui a été ajouté par rapport à la version précédente : | ui |
| 64923 | ### 1\. Scénario où VB-AUDIO est INUTILE | audio |
| 64933 | ### 2\. Scénario où VB-AUDIO est INDISPENSABLE | audio |
| 65182 | ### Qu'est-ce qui a été ajouté dans cette version v1.4 ? | ui |
| 65207 | ### Un dernier petit détail pour la route ? | api |
| 65387 | ### Le Script Python Définitif (`generate_manual_v1.5.py`) | build |
| 65550 | ### Ce qui a été corrigé et ajouté : | ui |
| 65587 | ### 🎙 II. Gestion des flux audio : Présentiel vs Distanciel | audio |
| 65632 | ### ❓ VII. Dépannage Rapide | api |
| 65795 | ### Détails du script : | build |
| 67269 | ### Contenu Final du Guide (V3.0) : | ui |
| 68255 | ### Pourquoi cet ajout est important ? | - |
| 79300 | ### 1\. Remplace ton ancien composant `Terms` (tout en haut) par celui-ci : | ui |

