# Maja_Git_2.0 — Project Plan & Entrypoint Analysis

## Repository Overview

Flat Docker-based MAJA 4.10.0 (Sentinel-2 L2A atmospheric correction) environment.
Host-side scripts manage the container lifecycle; container-side scripts run MAJA workflows.

## Entrypoint Analysis

### Host-Side Entrypoints (run on bare metal)

| File | Role | Dependencies |
|------|------|--------------|
| `maja_setup.sh` | System validation (CPU/RAM/disk/Docker), metadata tree creation, image pull | `docker`, `lsblk`, `lscpu`, `free` |
| `run_maja_wrapper.sh` | Container lifecycle: create/start/exec persistent `maja-run` container | `docker` |

### Container-Side Entrypoints (run inside Docker image)

| File | Role | Dependencies |
|------|------|--------------|
| `0_seed_example_safe.sh` | Copy example L1C SAFE from image to host mount | `cp`, `mkdir` |
| `1_enso_download_example.sh` | Download ENSO satellite images for example date | `wget`, `grep` |
| `2_dtmcreation_example.sh` | Generate DTM from DEM via DTMCreation.py | `python3.8`, `DTMCreation.py` |
| `3_startmaja_example.sh` | Run MAJA L2A processing with `startmaja` | `startmaja` (MAJA binary), `folder.txt` |

### Configuration

| File | Role |
|------|------|
| `folder.txt` | INI-style MAJA paths config (`[Maja_Inputs]`, `[DTM_Creation]`) |
| `Dockerfile` | Image build: Ubuntu 20.04 + MAJA 4.10.0 + Python 3.8 |
| `.gitignore` | Excludes large SAFE / MAJA zip from version control |

## New Feature Map (this implementation)

```
tools/agents/agentctl.py       Multi-agent dev toolkit (review, debug, profile, docscheck)
scripts/maja_batch.py          Multiprocessing batch runner for MAJA
scripts/fetch_enso_images.py   ENSO satellite image downloader
tests/                         Unit tests for new Python modules
.github/workflows/ci.yml       CI pipeline (lint + test + shellcheck)
examples/                      Example manifests and configs
docs/assets/enso/              Local ENSO satellite images
reports/                       Agent report output directory
logs/                          Batch runner log directory
```

## Architecture Decisions

1. **Parallelism**: `ProcessPoolExecutor` with file-lock coordination (`portalocker` or `fcntl`-style lock files) to prevent concurrent writes to shared DTM/ENSO directories.
2. **Idempotency**: Per-job status tracking via JSON state files under `logs/`. On `--resume`, completed jobs are skipped.
3. **Backward compatibility**: All new code is purely additive. Existing shell scripts, `folder.txt`, and Docker workflow are untouched.
