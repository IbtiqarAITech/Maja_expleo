# Audit détaillé et plan d’amélioration du workflow MAJA pour ENSO

## Résumé exécutif
Le workflow est démonstratif, Docker-first et centré Sentinel-2. Les améliorations ajoutent parallélisation sûre, agents de contrôle, récupération ENSO, tests, CI et livrables PDF sans modifier les scripts MAJA historiques.

## Périmètre et méthodologie
Audit des scripts Bash, Python, Dockerfile, `folder.txt`, README et tests. Les constats distinguent corrigé, partiellement corrigé, restant, validation scientifique et approbation client.

## Inventaire du dépôt
| Élément | Rôle |
|---|---|
| `maja_setup.sh` | Préparation hôte |
| `run_maja_wrapper.sh` | Lancement conteneur |
| `0_seed_example_safe.sh` | Copie SAFE exemple |
| `1_enso_download_example.sh` | Téléchargement ENSO démonstration |
| `2_dtmcreation_example.sh` | Création DTM |
| `3_startmaja_example.sh` | Lancement `startmaja` |
| `folder.txt` | Chemins MAJA |
| `scripts/maja_batch.py` | Nouveau runner batch |
| `tools/agents/agentctl.py` | Nouveaux agents |

## Architecture existante
Dockerfile installe MAJA dans `/opt/maja-precompiled`, workspace `/opt/maja-workspace`, données `/data/MAJA-metadata`. L'entrée L2A est `startmaja`.

## Constats détaillés
| Finding ID | Category | Description | Evidence | Impact | Severity | Recommendation | Priority | Complexity | Related files | Validation method | Implementation status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F-001 | Batch | Absence initiale de batch sûr complet | anciens manifestes simples | collisions possibles | High | runner avec verrous/empreintes | P1 | Medium | `scripts/maja_batch.py` | pytest + dry-run | Corrected |
| F-002 | Resume | Reprise initiale par liste completed insuffisante | `logs/state` | succès stale | High | metadata atomique par sortie | P1 | Medium | `scripts/maja_batch.py` | tests resume | Corrected |
| F-003 | Docker | Build dépend de gros fichiers non versionnés | Dockerfile COPY zip/SAFE | build bloqué | Medium | documenter prérequis | P1 | Low | `Dockerfile` | docker build | Remaining |
| F-004 | Science | Compatibilité ENSO non prouvée | absence spec | risque qualité | Critical | obtenir métadonnées et référence | P0 | High | rapports | atelier | Requires scientific validation |
| F-005 | Logging | Scripts historiques logs console | scripts Bash | diagnostic limité | Medium | logs batch/agents | P2 | Low | `logs/` | agent debug | Partially corrected |
| F-006 | Security | Credentials auxiliaires externes hors dépôt | CAMS/ECMWF | échec opérationnel | Medium | procédure secrets | P2 | Low | README | revue | Remaining |
| F-007 | Docs | README initial incomplet WP_02 | README | onboarding | Medium | README enrichi | P1 | Low | `README.md` | docscheck | Corrected |
| F-008 | CI | Couverture initiale limitée | tests initiaux | régression | Medium | pytest + py_compile | P1 | Low | `.github/workflows/ci.yml` | CI | Corrected |

## Qualité Python, Bash, Docker, dépendances, configuration
Python: modules additifs avec type hints et subprocess sans shell. Bash historique conservé. Docker: robuste pour environnement préconstruit, mais build local nécessite archives non commitées. Configuration: `folder.txt` garde chemins fixes.

## Performance, CPU, mémoire, disque, temporaire
Aucune mesure MAJA réelle disponible. Le runner capture les durées par job et permet protocole workers. Les besoins disque/temp doivent être mesurés sur scènes réelles.

## Parallélisation, verrous, cache, idempotence, reprise
La nouvelle architecture isole `output`, `working_dir`, `log_file`, utilise un répertoire verrou atomique par job et une empreinte déterministe. Les caches partagés CAMS/DTM restent à contrôler en production.

## Tests et CI/CD
Tests ajoutés pour manifestes YAML/JSON, conflits, verrous, reprise, fetch ENSO, agents, rapports et PDF. CI GitHub Actions exécute py_compile, pytest et shellcheck si disponible.

## Sécurité, maintenabilité, portabilité
Pas de secrets ajoutés. Les scripts sont portables Linux/Python; le verrou par répertoire est compatible fichiers locaux mais NFS doit être validé.

## Compatibilité ENSO et angles variables
Risque critique: représentation d'angles inconnue. Sans métadonnées par produit/bande/détecteur/grille/pixel, toute conclusion scientifique serait non vérifiée.

## Plan d'amélioration priorisé
| ID | Improvement | Priority | Business value | Scientific value | Technical effort | Dependencies | Status |
|---|---|---|---|---|---|---|---|
| I-001 | Spécification ENSO complète | P0 | High | High | Medium | Client | Open |
| I-002 | Adaptateur format ENSO | P1 | High | High | High | I-001 | Open |
| I-003 | Runner batch sûr | P1 | High | Medium | Medium | None | Done |
| I-004 | Benchmark réel | P2 | Medium | Medium | Low | données | Open |
| I-005 | Monitoring long terme | P3 | Medium | Low | Medium | exploitation | Open |

## Quick wins
Utiliser `--dry-run`, exécuter agents, versionner manifestes, conserver logs, figer required_outputs.

## Moyen terme
Adapter parsing metadata ENSO, définir campagnes, intégrer métriques mémoire/disque.

## Long terme
Validation scientifique complète, éventuelles adaptations algorithmiques MAJA, industrialisation orchestration.

## Architecture cible
Manifeste versionné → batch runner → entrée MAJA existante → sorties isolées → résumé → agents → rapports.

## Conclusions
Le dépôt est maintenant mieux testable et exploitable. Les risques principaux restants sont scientifiques et infrastructurels, non logiciels.
