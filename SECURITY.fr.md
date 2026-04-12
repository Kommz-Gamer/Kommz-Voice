# Politique de sécurité

## Signaler une vulnérabilité

Si vous découvrez un problème de sécurité, n'ouvrez pas une issue publique avec les détails d'exploitation.

Merci de signaler en privé avec :
- Un résumé court du problème
- Le fichier/endpoint concerné
- Les étapes de reproduction
- L'impact estimé
- Une proposition de correctif (si possible)

Canal de contact :
- GitHub Security Advisories (préféré)
- Ou demande privée via les canaux mainteneur du projet

Nous essayons d'accuser réception rapidement et de proposer un plan de remédiation.

## Gestion des secrets

- Ne jamais committer de secrets réels (`.env`, clés API, tokens privés, identifiants).
- Utiliser les templates (`env.template`, `env.production.template`) et des fichiers locaux non versionnés.
- Lancer les vérifications avant push :
  - `pre-commit run --all-files`
- La CI exécute aussi `gitleaks` sur les push/PR.

En cas de secret exposé :
1. Révoquer/rotater immédiatement.
2. Retirer le secret du code courant.
3. Purger l'historique si nécessaire.
4. Relancer les scans sécurité.

