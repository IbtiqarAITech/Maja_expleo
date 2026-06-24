# Catalogue des exigences WP_02

| Requirement ID | Category | Requirement | Source | Priority | Acceptance criterion | Status |
|---|---|---|---|---|---|---|
| BUS-001 | BUS | Le workflow doit préserver les démonstrations MAJA existantes. | Dépôt: scripts `0_*` à `3_*` | P0 | Les scripts restent présents et inchangés fonctionnellement. | Ready for review |
| FUN-001 | FUN | Le traitement par lot doit exécuter l'entrée MAJA réelle ou une commande de manifeste explicite. | WP_02 / audit dépôt | P1 | `scripts/maja_batch.py --dry-run` affiche la commande exacte. | Ready for review |
| FUN-002 | FUN | Chaque job doit avoir sortie, répertoire de travail, log et verrou dédiés. | Contrainte parallélisme | P1 | Tests de verrouillage et manifeste passent. | Ready for review |
| PERF-001 | PERF | Les indicateurs durée, débit, utilisation workers, disque, erreurs et reprise doivent être mesurables. | WP_02 | P2 | Le résumé JSON contient statuts, durées et workers. | Ready for review |
| SCI-001 | SCI | La compatibilité scientifique ENSO/MAJA ne doit être validée qu'avec métadonnées, angles et jeux de référence. | WP_02 | P0 | Le rapport classe l'élément comme validation scientifique requise. | Draft |
| DATA-001 | DATA | Les images ENSO documentaires doivent être stockées localement et tracées par manifeste. | WP_02 | P2 | `docs/assets/enso/manifest.json` est généré. | Ready for review |
| OPS-001 | OPS | Le workflow doit fonctionner localement et en conteneur Docker sans données propriétaires en CI. | WP_02 / Dockerfile | P1 | Les tests utilisent un wrapper MAJA factice. | Ready for review |
| VAL-001 | VAL | Les PDF livrables doivent être générés de manière reproductible. | WP_02 | P1 | `python scripts/build_reports.py` crée deux PDF non vides. | Ready for review |
| DOC-001 | DOC | Les exigences, la traçabilité et la préparation de validation partie prenante doivent être éditables. | WP_02 | P1 | Les trois fichiers `docs/requirements/WP_02_*.md` existent. | Ready for review |
| SEC-001 | SEC | Les secrets, jetons et credentials CAMS/ECMWF ne doivent pas être journalisés. | Audit sécurité | P1 | Les outils n'écrivent pas de variables sensibles connues. | Ready for review |
