# Matrice de traçabilité WP_02

| Need | Requirement | Use case | Component | Implementation | Test | Evidence | Status |
|---|---|---|---|---|---|---|---|
| Préserver MAJA | BUS-001 | UC-08, UC-09 | scripts existants | Changement additif | inspection dépôt | README, PLAN | Ready for review |
| Lot parallèle sûr | FUN-001, FUN-002 | UC-02, UC-05 | `scripts/maja_batch.py` | verrous, empreintes, résumé | `pytest -q` | rapports batch | Ready for review |
| Mesures opérationnelles | PERF-001 | UC-11 | runner batch | durées et statuts JSON | tests summary | `outputs/batch/batch-summary.json` | Ready for review |
| Validation scientifique | SCI-001 | UC-03, UC-13 | rapports WP_02 | matrices risques/angles | revue documentaire | rapport WP_02 | Draft |
| Actifs ENSO locaux | DATA-001 | UC-14 | `scripts/fetch_enso_images.py` | manifest et checksum | tests ENSO | `docs/assets/enso/manifest.json` | Ready for review |
| PDF livrables | VAL-001 | UC-15 | `scripts/build_reports.py` | PDF minimal reproductible | validation script | `deliverables/*.pdf` | Ready for review |
