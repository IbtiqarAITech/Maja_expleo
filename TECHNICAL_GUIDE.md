# Maja_Git_2.0 — Technical Documentation Guide

**Version:** 1.1.0  
**Base Technology:** MAJA 4.10.0 (Sentinel-2 L2A Atmospheric Correction)  
**Repository:** `git@github.com:IbtiqarAITech/Maja_expleo.git`  
**Maintainer:** Reda El Hirech <reda.el-hirech@expleogroup.com>

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Environment Setup](#3-environment-setup)
4. [Project Installation](#4-project-installation)
5. [Directory Structure](#5-directory-structure)
6. [Configuration Reference](#6-configuration-reference)
7. [Execution Workflow](#7-execution-workflow)
8. [AI Processing Pipeline](#8-ai-processing-pipeline)
9. [Multi-Agent Developer Toolkit](#9-multi-agent-developer-toolkit)
10. [Batch Processing Runner](#10-batch-processing-runner)
11. [ENSO Satellite Image Fetcher](#11-enso-satellite-image-fetcher)
12. [Codebase Explanation](#12-codebase-explanation)
13. [Testing Strategy](#13-testing-strategy)
14. [CI/CD Pipeline](#14-cicd-pipeline)
15. [Deployment](#15-deployment)
16. [Troubleshooting](#16-troubleshooting)
17. [Best Practices](#17-best-practices)

---

## 1. Project Overview

### 1.1 Purpose

Maja_Git_2.0 provides a **containerised, reproducible environment** for running MAJA 4.10.0 — the CNES/ESA atmospheric correction processor that converts Sentinel-2 L1C (top-of-atmosphere) data into L2A (surface reflectance) products. The project wraps the complex MAJA dependency chain into a single Docker-based workflow with supporting developer tooling.

### 1.2 Main Features

| Feature | Description |
|---------|-------------|
| **Dockerised MAJA** | Pre-built Ubuntu 20.04 environment with MAJA 4.10.0 binaries, GDAL, Python 3.8 |
| **Host Validation** | `maja_setup.sh` validates CPU, RAM, disk, Docker before launch |
| **Persistent Container** | `run_maja_wrapper.sh` manages container lifecycle with persistent home volume |
| **ENSO Data Ingestion** | Download ROB1E satellite images from CNES/UMR server as example data |
| **DTM Generation** | Generate Digital Terrain Models via MAJA's `DTMCreation.py` |
| **L2A Processing** | Full atmospheric correction pipeline via `startmaja` |
| **Multi-Agent Toolkit** | Static analysis, log debugging, profiling, docs validation agents |
| **Batch Runner** | Multiprocessing pipeline runner with locking, resume, and reporting |
| **CI/CD** | GitHub Actions: lint, test, shellcheck, markdown validation |

### 1.3 Expected Outcomes

- Fully validated Sentinel-2 L2A surface reflectance products
- Digital Terrain Models (DTM) ready for geospatial analysis
- ENSO satellite image archives for supplementary climatological context
- Structured JSON/Markdown reports from developer agents
- Reproducible batch execution with audit trails

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        HOST SYSTEM                               │
│                                                                  │
│  ┌──────────────┐   ┌──────────────────┐   ┌─────────────────┐  │
│  │ maja_setup.sh │   │run_maja_wrapper  │   │  Docker Daemon  │  │
│  │ (validation)  │──▶│.sh (lifecycle)   │──▶│                 │  │
│  └──────────────┘   └──────────────────┘   └────────┬────────┘  │
│                                                      │           │
│  ┌──────────────────────────────────────────────────────┐       │
│  │           /data/MAJA-metadata/ (bind mount)         │       │
│  │  CAMS CDF DEM DTM ENSO GIPP GSW LUT S2-L1C S2-L2A tmp│      │
│  └──────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                     DOCKER CONTAINER (maja-run)                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  /opt/maja-workspace/                                      │  │
│  │   ├── 0_seed_example_safe.sh     (SAFE deployment)         │  │
│  │   ├── 1_enso_download_example.sh (ENSO download)          │  │
│  │   ├── 2_dtmcreation_example.sh   (DTM generation)         │  │
│  │   ├── 3_startmaja_example.sh     (L2A processing)         │  │
│  │   ├── scripts/                   (Python tooling)         │  │
│  │   ├── tools/                     (agent toolkit)          │  │
│  │   ├── tests/                     (test suite)             │  │
│  │   └── folder.txt                 (MAJA config)            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  /opt/maja-precompiled/ (MAJA 4.10.0 binaries + libs)     │  │
│  │   ├── bin/maja          (core engine)                      │  │
│  │   ├── bin/startmaja     (workflow launcher)               │  │
│  │   ├── bin/camsdownload  (CAMS data tool)                   │  │
│  │   └── lib/python3.8/    (MAJA Python env)                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  /home/maja/ (persistent volume: maja-home)               │  │
│  │   └── .cdsapirc         (CDS API credentials)              │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Communication

| Interaction | Protocol | Direction |
|-------------|----------|-----------|
| Host → Container | Docker bind mount (`-v`) | Read/Write |
| Container → Host FS | Bind mount at `/data/MAJA-metadata` | Read/Write |
| Container → CDS API | HTTPS (via `camsdownload`) | Outbound |
| Container → ENSO Server | HTTPS (via `wget`) | Outbound |
| Agent reports | File I/O | Local |
| Batch runner | `ProcessPoolExecutor` subprocess | Local |

### 2.3 Volume Map

```
Host Path                           Container Path
────────────────────────────────────────────────────
/data/MAJA-metadata/          ─▶   /data/MAJA-metadata/
/etc/localtime                ─▶   /etc/localtime (ro)
/etc/timezone                 ─▶   /etc/timezone (ro)
docker volume maja-home       ─▶   /home/maja/
```

---

## 3. Environment Setup

### 3.1 Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Docker | 24.0+ | 29.0+ |
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16 GB |
| Disk | 50 GB free | 100 GB free (SSD preferred) |
| OS | Linux (x86_64) | Ubuntu 20.04+ / Debian 11+ |
| Network | Outbound HTTPS | Broadband |

### 3.2 Required Software

- **Docker Engine** — container runtime
  - Install: `curl -fsSL https://get.docker.com | sh`
  - Post-install: `sudo usermod -aG docker $USER` then log out/in
- **Bash 4.0+** — script runtime (pre-installed on Linux)
- **Python 3.9+** — for developer toolkit (host-side only)
- **Git** — version control

### 3.3 Python Dependencies

```bash
pip install pyyaml pytest psutil
```

See `requirements.txt`:
```
pyyaml>=6.0
psutil>=5.9
pytest>=7.0
```

### 3.4 Host Directory Permissions

The MAJA container runs as UID 1000 (`maja`). The host-mounted volume must be accessible:

```bash
sudo mkdir -p /data/MAJA-metadata/{CAMS,CDF,DEM,DTM,ENSO,GIPP,GSW,LUT,S2-L1C,S2-L2A,tmp}
sudo chown -R 1000:1000 /data/MAJA-metadata
```

The UID 1000 requirement stems from `Dockerfile:80`:
```dockerfile
RUN useradd -ms /bin/bash maja && \
    chown -R maja:maja /opt /data/MAJA-metadata
```

At build time the directories are owned by `maja` (UID 1000), but at runtime the `-v` bind mount **overlays** the host directory, so the host must match the expected ownership.

---

## 4. Project Installation

### 4.1 Clone the Repository

```bash
git clone git@github.com:IbtiqarAITech/Maja_expleo.git maja-demo
cd maja-demo
```

### 4.2 Obtain MAJA Binary

MAJA 4.10.0 is **not** bundled in Git due to filesize (>800 MB). Download from the official source:

```bash
# Option A: GitLab releases
wget https://gitlab.orfeo-toolbox.org/maja/maja/-/releases/4.10.0/downloads/MAJA-4.10.0.zip

# Option B: Build from source (see MAJA docs)
# Place the zip in the repo root so Dockerfile can COPY it
```

Alternatively, download a pre-built image:

```bash
docker pull tareelou/maja-env:latest
```

### 4.3 (Optional) Obtain Example SAFE Product

The example Sentinel-2 L1C SAFE (approx 2 GB) is listed in `.gitignore`. Obtain from:

- [Copernicus Open Access Hub](https://scihub.copernicus.eu/)
- Tile: `T31TCJ`, Date: `2025-11-22`
- Or any user-provided L1C SAFE product

Place in the repo root so the Dockerfile can embed it, or skip this step and provide your own SAFE at runtime.

### 4.4 Build the Docker Image

```bash
docker build --build-arg IMAGE_VERSION=1.0.0 -t tareelou/maja-env:1.0.0 .
docker tag tareelou/maja-env:1.0.0 tareelou/maja-env:latest
```

**Build arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `IMAGE_VERSION` | `1.0.0` | Version label embedded in the image |

**Build stages:**

1. **Base** — Ubuntu 20.04 + system packages (ca-certificates, wget, curl, unzip, vim, bash-completion)
2. **User setup** — Create `maja` user, workspace directories, metadata directories
3. **MAJA install** — Unzip `MAJA-4.10.0.zip` and run the self-extracting installer to `/opt/maja-precompiled`
4. **Python env** — Source MAJA's internal Python 3.8, update certifi
5. **Scripts** — Copy example scripts, folder.txt, README
6. **Banner** — Write version file, configure MOTD

### 4.5 Verify the Build

```bash
docker images tareelou/maja-env
# Should show: tareelou/maja-env   latest    ...    1.0.0
```

---

## 5. Directory Structure

```
maja-demo/
│
├── 0_seed_example_safe.sh         # Container-side: deploy SAFE to host mount
├── 1_camsdownload_example.sh      # [DEPRECATED] Legacy CAMS download
├── 1_enso_download_example.sh     # Container-side: download ENSO images
├── 2_dtmcreation_example.sh       # Container-side: run DTMCreation.py
├── 3_startmaja_example.sh         # Container-side: run startmaja L2A
├── maja_setup.sh                  # Host-side: validate system + create dirs
├── run_maja_wrapper.sh            # Host-side: container lifecycle manager
├── Dockerfile                     # Image build definition
├── folder.txt                     # MAJA configuration (INI format)
├── requirements.txt               # Python dependencies (dev toolkit)
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI pipeline
│
├── tools/
│   ├── __init__.py
│   └── agents/
│       ├── __init__.py
│       └── agentctl.py            # Multi-agent CLI toolkit
│
├── scripts/
│   ├── __init__.py
│   ├── maja_batch.py              # Multiprocessing batch runner
│   └── fetch_enso_images.py       # Host-side ENSO downloader
│
├── tests/
│   ├── __init__.py
│   ├── test_manifest.py           # Manifest parsing & validation tests
│   ├── test_locking.py            # File-lock coordination tests
│   ├── test_resume.py             # State persistence tests
│   └── test_agents.py             # Agent toolkit unit tests
│
├── examples/
│   ├── manifest.yml               # Example YAML batch manifest
│   └── manifest.json              # Example JSON batch manifest
│
├── docs/
│   └── assets/
│       └── enso/                  # ENSO satellite images (downloaded)
│
├── reports/                       # Agent report output (auto-generated)
├── logs/                          # Batch runner logs (auto-generated)
│   ├── jobs/                      # Per-job log files
│   ├── locks/                     # Coordination lock directories
│   └── state/                     # Resume state JSON files
│
├── README.md                      # Project overview
├── README_EXAMPLES.md             # Example workflow documentation
├── PLAN.md                        # Entrypoint analysis & architecture decisions
├── TECHNICAL_GUIDE.md             # This document
└── .gitignore                     # Git exclusion rules
```

---

## 6. Configuration Reference

### 6.1 `folder.txt` — MAJA Processing Configuration

```ini
[Maja_Inputs]
repWork=/opt/maja-tmp              # Temporary workspace
repGipp=/data/MAJA-metadata/GIPP   # GIPP configuration files
repMNT=/data/MAJA-metadata/DTM     # DTM products
repL1=/data/MAJA-metadata/S2-L1C   # L1C input products
repL2=/data/MAJA-metadata/S2-L2A   # L2A output products
exeMaja=/opt/maja-precompiled/bin/maja  # MAJA binary path
repCAMS=/data/MAJA-metadata/CAMS   # CAMS atmospheric data

[DTM_Creation]
repRAW=/data/MAJA-metadata/DEM     # Raw DEM data
repGSW=/data/MAJA-metadata/GSW     # Global Surface Water mask
```

**Sections:**
- `[Maja_Inputs]` — paths for MAJA core processing engine
- `[DTM_Creation]` — paths for DTM generation step

### 6.2 Environment Variables

| Variable | Set By | Purpose |
|----------|--------|---------|
| `MAJA_IMAGE_VERSION` | `Dockerfile:61` | Version label from build arg |
| `DEBIAN_FRONTEND` | `Dockerfile:58` | `noninteractive` for apt |

### 6.3 Docker Labels

Set in `Dockerfile:45-53`, these OCI-compliant labels annotate the image:

```dockerfile
LABEL org.opencontainers.image.title="MAJA Processing Environment"
LABEL org.opencontainers.image.version="4.10.0"
LABEL org.opencontainers.image.source="https://gitlab.orfeo-toolbox.org/maja/maja"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL volumes_required='["/data/MAJA-metadata/CAMS", ...]'
```

---

## 7. Execution Workflow

### 7.1 Complete Pipeline (Host + Container)

```
┌─────────────────────────────────────────────────────────────────────┐
│ HOST COMMANDS                                                        │
│                                                                      │
│ ./maja_setup.sh                                                      │
│   ├── Checks CPU/RAM/disk                                           │
│   ├── Verifies Docker access                                         │
│   └── Creates /data/MAJA-metadata/ directory tree                    │
│                                                                      │
│ docker build ... (one time)                                          │
│                                                                      │
│ ./run_maja_wrapper.sh                                                │
│   ├── Creates docker volume maja-home (if missing)                   │
│   ├── Removes old container (docker rm -f maja-run)                  │
│   └── Runs new container with mounts                                 │
│       │                                                              │
│       ▼  (now inside container)                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ CONTAINER COMMANDS (/opt/maja-workspace/)                            │
│                                                                      │
│ ./0_seed_example_safe.sh                                             │
│   Copies SAFE from image to /data/MAJA-metadata/S2-L1C/             │
│                                                                      │
│ ./1_enso_download_example.sh                                         │
│   Downloads ENSO satellite images to /data/MAJA-metadata/ENSO/      │
│                                                                      │
│ ./2_dtmcreation_example.sh                                           │
│   Runs DTMCreation.py → DTM at /data/MAJA-metadata/DTM/T31TCJ/      │
│                                                                      │
│ ./3_startmaja_example.sh                                             │
│   Runs startmaja with folder.txt → L2A at /data/MAJA-metadata/S2-L2A/│
│                                                                      │
│ exit                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Step-by-Step Execution

#### Step 1: Host Setup

```bash
cd ~/maja-demo
./maja_setup.sh
```

Expected output:
```
[MAJA-SETUP] === CPU informations ===
[MAJA-SETUP] Architecture        : x86_64
[MAJA-SETUP] Logical cores       : 16
...
[MAJA-SETUP] === MAJA metadata directory structure ===
[MAJA-SETUP] Directory already exists: /data/MAJA-metadata/CAMS => OK
...
```

#### Step 2: Launch Container

```bash
docker rm -f maja-run 2>/dev/null; true
./run_maja_wrapper.sh
```

The wrapper logic (`run_maja_wrapper.sh:66-87`):
1. Checks if container `maja-run` exists
2. If **running** — `docker exec -it maja-run bash`
3. If **stopped** — `docker start -ai maja-run`
4. If **does not exist** — `docker run -it --name maja-run -v /data/MAJA-metadata:/data/MAJA-metadata ... tareelou/maja-env:latest`

You are now inside the container:
```
maja@sentinel-2:/opt/maja-workspace$
```

#### Step 3: Deploy Example SAFE

```bash
./0_seed_example_safe.sh
```

**Logic** (`0_seed_example_safe.sh:17-71`):
1. Reads `TILE=T31TCJ` and `SAFE_NAME` constants
2. Checks if source SAFE exists at `/opt/maja-workspace/example_data/...`
3. Checks if destination already exists at `/data/MAJA-metadata/S2-L1C/...` (idempotent)
4. Creates destination directory
5. Copies SAFE with `cp -r`

**Idempotency:** If the SAFE already exists on the host mount, the script exits early (line 44).

#### Step 4: Download ENSO Satellite Images

```bash
./1_enso_download_example.sh
```

**Logic** (`1_enso_download_example.sh:42-83`):
1. Fetches HTML directory listing from `https://ddp.csum.umontpellier.fr/rob1e/photos`
2. Extracts `.jpg` URLs via `grep -o 'href="[^"]*\.jpg"'`
3. Handles both absolute (`/static/ddp/...`) and relative paths
4. Downloads each image to `/data/MAJA-metadata/ENSO/` using `wget -q -O`
5. Skips existing files (line 72) — idempotent

**Why wget instead of Python?** The script runs inside the container where `wget` is guaranteed (installed via `Dockerfile:65`), while our Python scripts are host-side.

#### Step 5: Generate DTM

```bash
./2_dtmcreation_example.sh
```

**Logic** (`2_dtmcreation_example.sh:39-45`):
```bash
python3.8 /opt/maja-precompiled/lib/python/StartMaja/prepare_mnt/DTMCreation.py \
    -p /data/MAJA-metadata/S2-L1C/Toulouse/T31TCJ/<SAFE> \
    -o /data/MAJA-metadata/DTM/T31TCJ \
    -d /data/MAJA-metadata/DEM \
    -w /data/MAJA-metadata/GSW \
    -t /data/MAJA-metadata/tmp \
    -c 120
```

This calls MAJA's internal `DTMCreation.py` (Python 3.8 from the MAJA environment) which:
1. Loads raw DEM data from `repRAW` (`/data/MAJA-metadata/DEM`)
2. Applies Global Surface Water mask from `repGSW` (`/data/MAJA-metadata/GSW`)
3. Uses the Sentinel-2 SAFE product for geometric referencing
4. Outputs a tile-specific DTM at `/data/MAJA-metadata/DTM/T31TCJ/`

**Note:** Requires MAJA binaries (`/opt/maja-precompiled`) to be present.

#### Step 6: Run MAJA L2A Processing

```bash
./3_startmaja_example.sh
```

**Logic** (`3_startmaja_example.sh:32-37`):
```bash
startmaja \
  -f /opt/maja-workspace/folder.txt \
  -t T31TCJ \
  -s Toulouse \
  -d 2025-11-22 \
  -e 2025-11-23
```

**`startmaja` arguments:**

| Flag | Value | Description |
|------|-------|-------------|
| `-f` | `/opt/maja-workspace/folder.txt` | Configuration file path |
| `-t` | `T31TCJ` | Sentinel-2 tile identifier |
| `-s` | `Toulouse` | Site/zone name |
| `-d` | `2025-11-22` | Start date (sensing date) |
| `-e` | `2025-11-23` | End date (single-date Init Mode) |

**Processing mode:** The `-d`/`-e` with the same date (or +1 day) triggers **Init Mode**, which performs full atmospheric correction for a single date. Multi-date runs use **Cyclic Mode** for temporal consistency.

#### Step 7: Verify Outputs

```bash
ls -lh /data/MAJA-metadata/S2-L2A/
ls -lh /data/MAJA-metadata/DTM/T31TCJ/
ls /data/MAJA-metadata/ENSO/ | wc -l
```

#### Step 8: Exit

```bash
exit
```

### 7.3 Batch Mode (All Steps)

Replace steps 3-6 with a single command:

```bash
python scripts/maja_batch.py examples/manifest.yml --workers 2
```

Output:
```
Loaded manifest 'maja-demo-batch' with 4 jobs
Running 4/4 jobs with 2 workers...
  [OK] seed_safe: completed (2.3s)
  [OK] enso_download: completed (15.7s)
  [OK] dtm_creation: completed (45.1s)
  [OK] maja_l2a: completed (120.3s)
  Summary report: reports/batch/maja-demo-batch_20260513_121221.json
```

### 7.4 Expected Outputs

| Step | Output Location | Format | Size |
|------|----------------|--------|------|
| 0_seed | `/data/MAJA-metadata/S2-L1C/Toulouse/T31TCJ/` | SAFE directory | ~2 GB |
| 1_enso | `/data/MAJA-metadata/ENSO/` | JPEG images | ~50-200 MB |
| 2_dtm | `/data/MAJA-metadata/DTM/T31TCJ/` | GeoTIFF | ~100 MB |
| 3_maja | `/data/MAJA-metadata/S2-L2A/` | L2A SAFE format | ~1 GB |

---

## 8. AI Processing Pipeline

MAJA is not an AI/ML system in the modern sense; it is a **physics-based atmospheric correction processor** using radiative transfer models. The "AI" pipeline analogy maps as follows:

### 8.1 Data Flow Diagram

```
L1C Product (TOA Reflectance)
        │
        ▼
┌─────────────────┐
│  Input Acquisition │
│  - Read SAFE format │
│  - Parse metadata   │
│  - Extract bands    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Preprocessing    │
│  - Cloud detection │
│  - Land/water mask │
│  - Adjacency mask  │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│  Atmospheric Correction   │
│  (Radiative Transfer)     │
│                           │
│  Inputs:                  │
│  ├── Aerosol Optical Depth (AOT) │
│  ├── Water Vapor (WV)           │
│  └── DEM + DTM                  │
│                           │
│  Algorithm:               │
│  - Dense Dark Vegetation  │
│  - Multi-temporal analysis │
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│  Post-processing  │
│  - BRDF correction │
│  - Slope correction │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Output Generation │
│  - L2A SAFE format  │
│  - Surface reflectance │
│  - AOT/Water Vapor maps │
└─────────────────┘
```

### 8.2 Pipeline Stages

#### Stage 1: Input Acquisition (`startmaja`)

**What:** Reads Sentinel-2 L1C Top-Of-Atmosphere (TOA) reflectance from SAFE format.  
**Source:** `/data/MAJA-metadata/S2-L1C/`  
**Config:** `folder.txt[repL1]`

#### Stage 2: Preprocessing

**Cloud Detection:** MAJA uses a multi-temporal approach comparing the target image to a "clear-sky" composite built from recent acquisitions.  
**Land/Water Mask:** Uses GSW data (`/data/MAJA-metadata/GSW`) from the `folder.txt[DTM_Creation]` section.  
**Adjacency Mask:** Computed from DTM to identify shadowed/illuminated areas.

#### Stage 3: Atmospheric Correction (Core Physics)

**Aerosol Optical Thickness (AOT):** Estimated using the Dense Dark Vegetation (DDV) method — identifies dark targets in the scene and inverts the radiative transfer model at 2.1 µm.  
**Water Vapor (WV):** Retrieved from band ratio at 940 nm (atmospheric absorption feature).  
**Radiative Transfer:** Uses pre-computed LUTs (Look-Up Tables) at `/data/MAJA-metadata/LUT/` to convert TOA radiance to surface reflectance.

**Why `folder.txt` matters:**
```ini
repCAMS=/data/MAJA-metadata/CAMS
```
CAMS data provides initial atmospheric state estimates (aerosol, ozone) that constrain the retrieval.

#### Stage 4: Post-Processing

**BRDF Correction:** Normalizes surface reflectance to a standard viewing geometry.  
**Slope Correction:** Uses DTM to correct for topographic illumination effects.  
**Temporal Consistency:** In Cyclic Mode, MAJA applies temporal filtering across the time series.

#### Stage 5: Output Generation

**Format:** L2A SAFE (Standard Archive Format for Europe)  
**Contents:**
- Surface reflectance bands (R1-R13 at 10 m, 20 m, 60 m)
- AOT map (10 m)
- Water Vapor map (10 m)
- Cloud mask (60 m)
- Scene classification (20 m)
- Quality flags (20 m)

---

## 9. Multi-Agent Developer Toolkit

### 9.1 Overview

`tools/agents/agentctl.py` provides four specialised agents accessible via a unified CLI.

| Agent | Function | Use Case |
|-------|----------|----------|
| `review` | Static code review | Find missing shebangs, CRLF issues, TODOs |
| `debug` | Log anomaly detection | Scan MAJA logs for errors, OOM, disk issues |
| `profile` | Resource profiling | CPU/memory/disk of MAJA processes |
| `docscheck` | Documentation validation | Find broken links, missing assets |

### 9.2 Architecture

```
agentctl.py
├── ReviewAgent
│   ├── _gather_files()    — Collect .sh/.py/.md/.txt/.yml/.cfg/.ini
│   ├── _check_file()      — Per-file analysis
│   └── run()              — Execute with ThreadPoolExecutor
│
├── DebugAgent
│   ├── LOG_PATTERNS       — Compiled regex for error/warning/oom/disk
│   ├── scan_file()        — Search single log file
│   └── run()              — Walk logdir, categorize matches
│
├── ProfileAgent
│   ├── run()              — Captures psutil system + process stats
│   └── (requires psutil)
│
└── DocsCheckAgent
    ├── LINK_RE            — Regex for markdown links
    ├── run()              — Walk docsdir, validate references
    └── (detects broken images and file links)
```

### 9.3 Report Format

Each agent writes to `reports/<agent>/<timestamp>/`:
- `report.json` — structured data
- `report.md` — human-readable markdown

**JSON example (`report.json`):**
```json
{
  "agent": "review",
  "timestamp": "2026-05-13T12:12:53",
  "total_files": 12,
  "issues": [
    {
      "path": "scripts/old_script.sh",
      "count": 2,
      "items": ["Missing shebang", "CRLF line endings"]
    }
  ],
  "summary": {
    "files_with_issues": 1,
    "total_issues": 2
  }
}
```

**Markdown example (`report.md`):**
```markdown
# Review Agent Report

## Issues

### Path
- **path**: scripts/old_script.sh
- **count**: 2
- **items**:
  - Missing shebang
  - CRLF line endings
```

### 9.4 Usage

```bash
# Run all agents
python -m tools.agents.agentctl all

# Individual agents
python -m tools.agents.agentctl review --paths ./scripts/
python -m tools.agents.agentctl debug --logdir /data/MAJA-metadata/logs/
python -m tools.agents.agentctl profile --pid 12345
python -m tools.agents.agentctl docscheck --docsdir docs/
```

### 9.5 Design Decisions

**Why `ThreadPoolExecutor` for review?** File I/O is I/O-bound; threads are lighter than processes and sufficient for parallel file reads.  
**Why `os.mkdir` for locking?** Directory creation is atomic on all filesystems/POSIX systems, unlike file-based `O_EXCL` which has platform-specific behaviour. See `tests/test_locking.py`.  
**Why both JSON + Markdown?** JSON for programmatic consumption (CI pipelines, dashboards), Markdown for human review.

---

## 10. Batch Processing Runner

### 10.1 Overview

`scripts/maja_batch.py` orchestrates multiple MAJA pipeline steps with parallelism, locking, and resume capability.

### 10.2 Architecture

```
maja_batch.py
│
├── Manifest Loader
│   ├── load_manifest()     — Parse YAML or JSON
│   └── validate_manifest() — Check required fields
│
├── Job Executor
│   ├── ProcessPoolExecutor — Parallel subprocess execution
│   ├── _run_job()          — Single job via subprocess.run()
│   └── _append_log()       — Per-job structured log
│
├── Lock Manager
│   ├── _acquire_lock()     — Atomic mkdir with timeout
│   └── _release_lock()     — rmdir on completion
│
├── State Manager
│   ├── _load_state()       — Read JSON state file
│   └── _save_state()       — Write completed job IDs
│
└── Report Generator
    ├── _generate_summary() — Aggregate results
    └── _save_summary()     — JSON + Markdown output
```

### 10.3 Manifest Format

**YAML** (`examples/manifest.yml`):
```yaml
name: "maja-demo-batch"
description: "Example MAJA L2A batch processing pipeline"
version: "1.0"
jobs:
  - id: "seed_safe"
    command: "./0_seed_example_safe.sh"
    lock: "metadata"        # prevents concurrent metadata access
    timeout: 300            # seconds
  - id: "enso_download"
    command: "./1_enso_download_example.sh"
    lock: "enso"
    timeout: 600
```

**JSON** (`examples/manifest.json`) — structurally equivalent.

**Per-job fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique job identifier |
| `command` | string | Yes | Shell command to execute |
| `lock` | string | No | Lock group name (mutual exclusion) |
| `timeout` | int | No | Timeout in seconds (default: 3600) |

### 10.4 File-Lock Mechanism

**Why directory-based locking?**

```python
def _acquire_lock(lock_name: str, timeout: float = 30.0) -> Optional[Path]:
    lock_root = LOCK_DIR.resolve()
    lock_dir = lock_root / f"{lock_name}.lockdir"
    lock_root.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.mkdir(str(lock_dir))  # Atomic on all platforms
            return lock_dir
        except FileExistsError:
            time.sleep(0.5)
    return None
```

`os.mkdir` is atomically evaluated by the kernel — only one process succeeds. Directory-based locks do not suffer from the race conditions that file-based `O_EXCL` can exhibit on certain filesystems (NFS, Windows).

**Lock directory structure:**
```
logs/locks/
├── metadata.lockdir/    # Jobs with lock="metadata" serialise here
├── enso.lockdir/
├── dtm.lockdir/
└── maja.lockdir/
```

### 10.5 Resume/Cache Mechanism

```python
def _load_state(manifest_name: str) -> Dict[str, Any]:
    state_file = STATE_DIR / f"{manifest_name}_state.json"
    return json.loads(state_file.read_text()) if state_file.exists() else {}

def _save_state(manifest_name: str, state: Dict[str, Any]) -> None:
    state_file = STATE_DIR / f"{manifest_name}_state.json"
    state_file.write_text(json.dumps(state))
```

On `--resume`, the runner loads the state file, extracts `completed` job IDs, and submits only uncompleted jobs. The state file is updated atomically after all jobs finish.

**State file format (`logs/state/maja-demo-batch_state.json`):**
```json
{
  "completed": ["seed_safe", "enso_download"]
}
```

### 10.6 CLI Reference

```bash
python scripts/maja_batch.py <manifest> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--workers` | 2 | Number of parallel processes |
| `--resume` | false | Skip previously completed jobs |
| `--dry-run` | false | Print jobs without executing |
| `--timeout` | 3600 | Per-job timeout (seconds) |

### 10.7 Output Structure

```
logs/
├── jobs/
│   ├── seed_safe.log           # [2026-05-13T12:12:21] job=seed_safe status=completed rc=0 duration=2.3s
│   ├── enso_download.log
│   ├── dtm_creation.log
│   └── maja_l2a.log
├── state/
│   └── maja-demo-batch_state.json
└── locks/
    └── enso.lockdir/

reports/
└── batch/
    ├── maja-demo-batch_20260513_121221.json
    └── maja-demo-batch_20260513_121221.md
```

### 10.8 Design Decisions

**Why `ProcessPoolExecutor` over `ThreadPoolExecutor`?** Subprocess execution is CPU-bound (waiting for MAJA processes). The GIL would limit `ThreadPoolExecutor`. Processes also provide better isolation — a crashed job doesn't affect others.  
**Why `--resume` instead of auto-resume?** Explicit `--resume` avoids accidentally skipping jobs when the user intends a fresh run. The state file is overwritten only after all jobs complete.  
**Why file-based locks instead of Redis/ZooKeeper?** Zero infrastructure dependencies. Every Unix/POSIX system supports `os.mkdir` atomically.

---

## 11. ENSO Satellite Image Fetcher

### 11.1 Overview

`scripts/fetch_enso_images.py` downloads ROB1E (ENSO) satellite photos from the CNES/UMR public server at `https://ddp.csum.umontpellier.fr/rob1e/photos`.

### 11.2 Usage

```bash
# Preview available images (no download)
python scripts/fetch_enso_images.py --dry-run

# Download all images to docs/assets/enso/
python scripts/fetch_enso_images.py

# Custom source/destination
python scripts/fetch_enso_images.py \
  --url https://ddp.csum.umontpellier.fr/rob1e/photos \
  --dest /data/MAJA-metadata/ENSO
```

### 11.3 Implementation

**Image Discovery** (`list_remote_images`, line 27-40):
1. Fetches the HTML page at the source URL
2. Parses all `<a href="...">` links matching `*.jpg`, `*.png`, `*.gif`, `*.svg`
3. Returns sorted, de-duplicated list

**Download Logic** (`download_image`, line 43-54):
1. Creates destination directory
2. Checks if file already exists (idempotent)
3. Downloads with 60-second timeout
4. Returns success/failure boolean

**Idempotency:** Existing files are skipped (line 85), making repeated runs safe.

---

## 12. Codebase Explanation

### 12.1 Host-Side Scripts

#### `maja_setup.sh` (361 lines)

**Purpose:** Validate host system and prepare metadata directories.

| Section | Lines | Function | Description |
|---------|-------|----------|-------------|
| CPU | 26-50 | `cpu_info()` | Reads `/proc/cpuinfo`, `nproc` |
| RAM | 52-73 | `ram_info()` | Reads `/proc/meminfo` |
| Disk | 75-110 | `disk_info()` | `df -hP`, `lsblk` for disk type |
| Docker | 112-138 | `docker_info()` | `docker --version`, `docker info` |
| Digest | 140-166 | `get_local_digest()` / `get_remote_digest()` | SHA256 comparison |
| Update | 168-195 | `maja_check_update_latest()` | Local vs remote digest |
| Container | 197-225 | `maja_container_info()` | Existing container metadata |
| Metadata | 227-284 | `maja_create_metadata_tree()` | Creates 11 directories |

**Why digest comparison?** `maja_check_update_latest()` compares local vs remote Docker image digests to detect updates without pulling the entire image, saving bandwidth.

#### `run_maja_wrapper.sh` (88 lines)

**Purpose:** Container lifecycle manager.

| Section | Lines | Logic |
|---------|-------|-------|
| Init | 32-38 | Constants: `IMAGE_NAME`, `CONTAINER_NAME`, mounts |
| Docker check | 48-51 | `command -v docker` |
| Image check | 53-58 | `docker image inspect` |
| Volume | 61-64 | `docker volume create maja-home` |
| State detect | 67 | `docker ps -a --format` |
| Running | 71-73 | `docker exec -it` |
| Stopped | 75-76 | `docker start -ai` |
| New | 80-87 | `docker run -it --name maja-run -v ...` |

### 12.2 Container-Side Scripts

#### `0_seed_example_safe.sh`

**Pattern:** Idempotent copy. Checks existence before creating directories and copying.

#### `1_enso_download_example.sh`

**Pattern:** Web scrape + batch download. Uses `wget` to fetch an HTML index, `grep` + `cut` to extract image URLs, then iterates with `wget -q -O` per image.

**Why not use Python inside the container?** The container's Python 3.8 is MAJA's internal environment. The example scripts are intentionally kept as simple POSIX shell to avoid Python dependency issues.

#### `2_dtmcreation_example.sh`

**Pattern:** Fixed-argument invocation of MAJA's `DTMCreation.py`. All paths are hardcoded for the Toulouse demo.

#### `3_startmaja_example.sh`

**Pattern:** Fixed-argument invocation of `startmaja`. Single-date Init Mode.

### 12.3 Python Modules

#### `tools/agents/agentctl.py` (343 lines)

| Class | Lines | Methods | Purpose |
|-------|-------|---------|---------|
| `ReviewAgent` | 78-138 | `run()`, `_gather_files()`, `_check_file()` | Static analysis |
| `DebugAgent` | 141-184 | `run()` | Log anomaly detection |
| `ProfileAgent` | 187-226 | `run()` | Resource monitoring |
| `DocsCheckAgent` | 229-271 | `run()` | Doc validation |
| `main()` | 301-339 | CLI entry | Dispatches to agent |

#### `scripts/maja_batch.py` (271 lines)

| Function | Lines | Purpose |
|----------|-------|---------|
| `_acquire_lock()` | 40-51 | Atomic directory lock |
| `_release_lock()` | 54-56 | Directory unlock |
| `_load_state()` | 59-64 | JSON state read |
| `_save_state()` | 67-70 | JSON state write |
| `_run_job()` | 73-119 | Single job subprocess |
| `_append_log()` | 122-125 | Structured log write |
| `load_manifest()` | 128-136 | YAML/JSON parser |
| `validate_manifest()` | 139-147 | Schema validation |
| `_generate_summary()` | 150-172 | Aggregate statistics |
| `_save_summary()` | 175-200 | Report output |
| `main()` | 216-267 | CLI entrypoint |

#### `scripts/fetch_enso_images.py` (99 lines)

| Function | Lines | Purpose |
|----------|-------|---------|
| `list_remote_images()` | 27-40 | Parse HTML for image URLs |
| `download_image()` | 43-54 | Single image download |
| `main()` | 65-95 | CLI entrypoint |

### 12.4 Test Suite

| File | Tests | Coverage |
|------|-------|----------|
| `test_manifest.py` | 6 | JSON/YAML load, validation, missing fields |
| `test_locking.py` | 5 | Acquire/release, double-acquire fails, isolation, timeout |
| `test_resume.py` | 4 | Save/load, missing state, overwrite, file integrity |
| `test_agents.py` | 6 | File gathering, shell check, debug, profile, docscheck |

**Total: 21 tests**

---

## 13. Testing Strategy

### 13.1 Running Tests

```bash
pip install pytest pyyaml psutil
python -m pytest tests/ -v
```

### 13.2 Test Categories

| Category | Tests | Verification |
|----------|-------|--------------|
| **Manifest parsing** | 6 | Correct parsing of JSON/YAML, validation errors |
| **File locking** | 5 | Atomic acquire/release, contention, timeout, isolation |
| **State persistence** | 4 | State file write/read, overwrite, missing state |
| **Agent toolkit** | 6 | File gathering, file checking, debug scan, profile fallback, docs validation |

### 13.3 Test Design Principles

1. **No external dependencies** — Tests mock or skip unavailable imports (e.g., `psutil`).
2. **Temporary directories** — All file I/O uses `tmp_path` fixtures.
3. **Deterministic** — No network calls, no timing-dependent assertions.
4. **Fast** — Complete in <3 seconds.

---

## 14. CI/CD Pipeline

### 14.1 GitHub Actions Configuration

`.github/workflows/ci.yml` defines three parallel jobs:

```yaml
jobs:
  lint-and-test:        # Python 3.9, 3.10, 3.11 matrix
    - py_compile        # Syntax check all .py files
    - pytest tests/     # Run test suite

  shellcheck:           # Shell script linting
    - ludeeus/action-shellcheck
    - severity: warning

  markdown-lint:        # Markdown format validation
    - DavidAnson/markdownlint-cli2-action
```

### 14.2 Trigger Events

- Push to `main` or `master`
- Pull request targeting `main` or `master`

### 14.3 Local CI Simulation

```bash
# Python lint
python -m py_compile scripts/maja_batch.py
python -m py_compile scripts/fetch_enso_images.py
python -m py_compile tools/agents/agentctl.py

# Tests
python -m pytest tests/ -v --tb=short

# ShellCheck
shellcheck *.sh scripts/*.sh

# Markdown lint
markdownlint-cli2 "**/*.md" --ignore ".git/**"
```

---

## 15. Deployment

### 15.1 Docker Deployment

**Build and run locally:**
```bash
docker build -t tareelou/maja-env:1.0.0 .
docker run -it --rm \
  -v /data/MAJA-metadata:/data/MAJA-metadata \
  -v /etc/localtime:/etc/localtime:ro \
  -v /etc/timezone:/etc/timezone:ro \
  tareelou/maja-env:1.0.0 bash
```

### 15.2 Docker Compose

```yaml
# docker-compose.yml
version: "3.8"
services:
  maja:
    image: tareelou/maja-env:1.0.0
    container_name: maja-run
    stdin_open: true
    tty: true
    volumes:
      - /data/MAJA-metadata:/data/MAJA-metadata
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
      - maja-home:/home/maja
    command: bash -i

volumes:
  maja-home:
```

```bash
docker compose up -d
docker compose exec maja bash
```

### 15.3 Cloud Deployment (GCP)

**Step 1: Build and push to Artifact Registry:**
```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker tag tareelou/maja-env:1.0.0 \
  europe-west1-docker.pkg.dev/<PROJECT>/maja-repo/maja-env:1.0.0
docker push europe-west1-docker.pkg.dev/<PROJECT>/maja-repo/maja-env:1.0.0
```

**Step 2: Create a Compute Engine VM:**
```bash
gcloud compute instances create maja-worker \
  --machine-type=n2-standard-8 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=200GB \
  --zone=europe-west1-b
```

**Step 3: SSH and run:**
```bash
gcloud compute ssh maja-worker
sudo apt update && sudo apt install -y docker.io
sudo gcloud auth configure-docker europe-west1-docker.pkg.dev
sudo docker run -it --rm \
  -v /data/MAJA-metadata:/data/MAJA-metadata \
  europe-west1-docker.pkg.dev/<PROJECT>/maja-repo/maja-env:1.0.0 bash
```

### 15.4 Kubernetes

```yaml
# maja-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: maja-l2a-processing
spec:
  template:
    spec:
      containers:
      - name: maja
        image: tareelou/maja-env:1.0.0
        command: ["./3_startmaja_example.sh"]
        volumeMounts:
        - name: metadata
          mountPath: /data/MAJA-metadata
      volumes:
      - name: metadata
        persistentVolumeClaim:
          claimName: maja-metadata-pvc
      restartPolicy: Never
  backoffLimit: 2
```

---

## 16. Troubleshooting

### 16.1 Build Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `COPY failed: file not found` | `MAJA-4.10.0.zip` or SAFE missing | Download files or comment out COPY lines in Dockerfile |
| `RUN unzip: cannot find` | MAJA zip COPY was commented but RUN remains | Comment lines 109-117 in Dockerfile |
| `python3.8: No such file or directory` | MAJA not installed | Comment lines 129-130 in Dockerfile |
| `docker manifest inspect failed` | Network issue or image not on Docker Hub | Build locally, ignore warning |

### 16.2 Runtime Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `Permission denied` on `/data/MAJA-metadata` | Host directory owned by wrong UID | `sudo chown -R 1000:1000 /data/MAJA-metadata` |
| `mkdir: cannot create directory '/data/MAJA-metadata/...'` | Volume not mounted | Remove container: `docker rm -f maja-run`, relaunch |
| `camsdownload: command not found` | MAJA binaries not installed | Build image with MAJA-4.10.0.zip present |
| `startmaja: command not found` | Same as above | Same as above |
| `wget: command not found` | Base image missing wget | Check Dockerfile apt-get install includes wget |
| Container exits immediately | Wrong CMD or permissions | Run interactively: `docker run -it tareelou/maja-env bash` |
| `docker exec` fails | Container not running | Use `docker start -ai maja-run` instead |

### 16.3 Log Analysis

**Container logs:**
```bash
docker logs maja-run
```

**MAJA processing logs** (inside container):
```bash
cat /opt/maja-tmp/*.log
ls /data/MAJA-metadata/S2-L2A/*/MAS*/?MAJA*_LOGS/
```

**Batch runner logs:**
```bash
cat logs/jobs/*.log
```

**Agent reports:**
```bash
cat reports/debug/*/report.json | jq .
```

### 16.4 Debugging with Agent Toolkit

```bash
# Debug log analysis
python -m tools.agents.agentctl debug --logdir /opt/maja-tmp/

# Resource profile
python -m tools.agents.agentctl profile

# Code review
python -m tools.agents.agentctl review --paths /opt/maja-workspace/
```

### 16.5 Monitoring

**Inside container:**
```bash
htop                    # Real-time CPU/memory
df -h /data/MAJA-metadata  # Disk usage
du -sh /data/MAJA-metadata/*  # Per-directory sizes
```

**Host monitoring:**
```bash
docker stats maja-run   # Live container stats
docker system df        # Docker disk usage
```

---

## 17. Best Practices

### 17.1 Security

- **Never commit secrets.** `.cdsapirc`, SSH keys, and API tokens should never be in Git. The Dockerfile only supports them at runtime via the `maja-home` volume.
- **Use `--pull=never`** in `docker run` to prevent accidental image overwrites (`run_maja_wrapper.sh:81`).
- **Host volume permissions.** Restrict `/data/MAJA-metadata` to UID 1000 only. Do not use `chmod 777`.
- **No `sudo` inside container.** The `maja` user is non-root.
- **Network isolation.** The container has outbound HTTPS only. No inbound ports are exposed.

### 17.2 Performance Optimization

| Area | Recommendation | Rationale |
|------|---------------|-----------|
| Disk | Use SSD for `/data/MAJA-metadata` | MAJA reads/writes large GeoTIFF files |
| CPU | Match workers to core count: `--workers $(nproc)` | Prevents oversubscription |
| RAM | 16 GB minimum for L2A processing | Single tile processing requires ~8 GB peak |
| Parallelism | Use `--resume` for multi-session runs | Avoids redoing completed work |
| Docker | Keep `maja-home` volume, remove old containers | Prevents orphaned disk usage |

### 17.3 Maintainability

- **All new features must be additive.** Never modify `folder.txt`, `0-3_*.sh`, or `Dockerfile` in ways that break backward compatibility.
- **Use the manifest format** for any new pipeline jobs. The `lock` field prevents parallel collisions.
- **Write tests for stateful logic.** Locking, state persistence, and file I/O must be covered.
- **Follow the agent pattern** for new developer tools: implement a class with `run()` → `_write_report()`.
- **Log structure** must always include: `[timestamp] job=<id> status=<status> rc=<code> duration=<s>s`.

### 17.4 Development Workflow

```bash
# 1. Develop features
# 2. Run lint
python -m py_compile scripts/new_feature.py

# 3. Run tests
python -m pytest tests/ -v

# 4. Run agent docscheck
python -m tools.agents.agentctl docscheck

# 5. Run agent review
python -m tools.agents.agentctl review

# 6. Commit
git add -A
git commit -m "feat: add new feature"
```

### 17.5 Commit Convention

```
<type>: <description>

Types:
  feat     — New feature
  fix      — Bug fix
  docs     — Documentation
  refactor — Code restructure (no functional change)
  test     — Test additions/changes
  ci       — CI/CD changes
  chore    — Maintenance (deps, config)

Examples:
  feat: add ENSO download agent
  fix: correct lock timeout on Windows
  docs: update README with batch runner examples
```

---

## Appendix A: Dockerfile Evolution

```
FROM ubuntu:20.04
├── apt-get install (ca-certificates, wget, curl, unzip, vim, bash-completion, bzip2, file, lsof)
├── useradd maja
├── mkdir /opt/maja-precompiled, /opt/maja-tmp, /opt/maja-workspace, /data/MAJA-metadata/{11 dirs}
├── WORKDIR /opt/maja-workspace
├── COPY SAFE example → /opt/maja-workspace/example_data/
├── COPY MAJA-4.10.0.zip → unzip → install → cleanup
├── COPY folder.txt
├── RUN python3.8 -m pip install --upgrade certifi
├── COPY *.sh → /opt/maja-workspace/
├── chmod +x /*.sh
└── CMD ["bash", "-i"]
```

## Appendix B: Entrypoint Reference

| Script | Runs Where | When to Run | Dependencies |
|--------|-----------|-------------|--------------|
| `maja_setup.sh` | Host | First time, or after Docker reinstall | Docker, /data/ |
| `run_maja_wrapper.sh` | Host | Every session | Docker, tareelou/maja-env image |
| `0_seed_example_safe.sh` | Container | Once (before DTM/L2A) | Embedded SAFE in image |
| `1_enso_download_example.sh` | Container | Once (or to refresh) | wget |
| `2_dtmcreation_example.sh` | Container | After seed | MAJA binaries, DEM, GSW |
| `3_startmaja_example.sh` | Container | After DTM | MAJA binaries, CAMS data |
| `python scripts/maja_batch.py` | Container | After all | Python, PyYAML |
| `python -m tools.agents.agentctl` | Host | Any time | Python, (psutil optional) |

## Appendix C: Resource Requirements

| Resource | Minimum | Recommended | Peak Usage |
|----------|---------|-------------|------------|
| CPU | 4 cores | 8 cores | 16 cores (multi-tile) |
| RAM | 8 GB | 16 GB | 32 GB |
| Disk | 50 GB | 100 GB | 500 GB (time series) |
| Network | 10 Mbps | 100 Mbps | 1 Gbps |
| Docker Disk | 10 GB | 20 GB | 50 GB (image + cache) |

---

*End of Technical Documentation Guide — Maja_Git_2.0 v1.1.0*
