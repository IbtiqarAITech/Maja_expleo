# Préparation de validation des parties prenantes WP_02

## Statut des exigences
Les exigences sont en statut **Draft** ou **Ready for review**. Aucune approbation client n'est revendiquée.

## Décisions scientifiques requises
| Decision ID | Sujet | Question | Owner attendu | Statut |
|---|---|---|---|---|
| SCI-DEC-001 | Angles de vue ENSO | Représentation par produit, bande, détecteur, grille ou pixel ? | Expert télédétection / fournisseur ENSO | Blocked |
| SCI-DEC-002 | Produits de référence | Quelles scènes et métriques valident la correction atmosphérique ? | Client scientifique | Draft |

## Décisions techniques requises
| Decision ID | Sujet | Question | Owner attendu | Statut |
|---|---|---|---|---|
| TECH-DEC-001 | Entrée MAJA ENSO | Adaptateur produit nécessaire ou conversion vers format supporté ? | Architecte MAJA | Ready for review |
| TECH-DEC-002 | CAMS/ECMWF | Mode connecté, proxy, cache ou dépôt auxiliaire figé ? | DevOps / exploitation | Ready for review |

## Agenda d'atelier proposé
1. Validation du périmètre ENSO et du rôle de MAJA.
2. Revue des exigences P0/P1.
3. Revue des métadonnées d'angles et radiométrie.
4. Choix du protocole benchmark et validation scientifique.
5. Décisions Docker/VM, stockage, logs, rétention.

## Checklist de validation
- [ ] Exigences P0 acceptées.
- [ ] Jeux de données ENSO fournis.
- [ ] Métadonnées angles documentées.
- [ ] Accès CAMS/ECMWF confirmé.
- [ ] Critères scientifiques signés.
- [ ] Contraintes d'exploitation validées.

## Tableau d'approbation
| Partie prenante | Rôle | Décision | Statut | Date |
|---|---|---|---|---|
| Client métier | Priorisation besoins | Non reçue | Draft | Non définie |
| Expert scientifique | Validité ENSO/MAJA | Non reçue | Blocked | Non définie |
| Exploitation | Docker/VM/stockage | Non reçue | Ready for review | Non définie |

Statuts possibles: Draft, Ready for review, Under review, Approved, Approved with conditions, Rejected, Blocked.
