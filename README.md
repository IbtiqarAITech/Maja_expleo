========================================================
MAJA 4.10.0 – Docker Example Environment
Version 1.0.0
========================================================

--------------------------------------------------------
1. Overview
--------------------------------------------------------

This Docker image provides a complete example environment for running
MAJA 4.10.0 (Sentinel-2 L2A atmospheric correction).

It includes:

   - MAJA 4.10.0 precompiled binaries
   - Python 3.8 (MAJA internal environment)
   - Required system tools
   - Example scripts demonstrating ENSO satellite image download, DTM
     generation, and L2A processing
   - An embedded Sentinel-2 L1C SAFE product for tile T31TCJ (Toulouse),
     stored under /opt/maja-workspace/example_data/

This image is intended for training, testing, and demonstration, not production.

--------------------------------------------------------
2. Host Directory Requirements
--------------------------------------------------------

The following directories must exist on the host and are mounted
into the container via the wrapper script:

   - /data/MAJA-metadata/CAMS
   - /data/MAJA-metadata/CDF
   - /data/MAJA-metadata/DEM
   - /data/MAJA-metadata/DTM
   - /data/MAJA-metadata/ENSO
   - /data/MAJA-metadata/GIPP
   - /data/MAJA-metadata/GSW
   - /data/MAJA-metadata/LUT
   - /data/MAJA-metadata/S2-L1C
   - /data/MAJA-metadata/S2-L2A
   - /data/MAJA-metadata/tmp

Additionally, a persistent Docker volume named maja-home stores /home/maja.

--------------------------------------------------------
3. Starting the Container
--------------------------------------------------------

The environment must be launched using:
./run_maja_wrapper.sh

The wrapper:

   - creates the persistent volume maja-home (if missing)
   - starts or reattaches the container maja-run
   - mounts all required host directories
   - opens an interactive shell

--------------------------------------------------------
4. Deploying the Example L1C Product
--------------------------------------------------------

Before running DTM or L2A processing, the embedded SAFE product must be copied
from the image into the mounted host directory structure.

Inside the container, run:
./0_seed_example_safe.sh

This script checks if the SAFE is already present under
    /data/MAJA-metadata/S2-L1C/Toulouse/T31TCJ/
And if missing, copies it from:
    /opt/maja-workspace/example_data/...

--------------------------------------------------------
5. Example Scripts
--------------------------------------------------------

These example workflows are stored in /opt/maja-workspace.

- 5.1 ENSO Satellite Image Download

Run:
./1_enso_download_example.sh
Downloads ENSO (ROB1E) satellite photos from the CNES/UMR server
(https://ddp.csum.umontpellier.fr/rob1e/photos) into /data/MAJA-metadata/ENSO/.

- 5.2 DTM Generation Example

Run:
./2_dtmcreation_example.sh
Uses the SAFE deployed by 0_seed_example_safe.sh and generates a DTM for tile T31TCJ.
Output: /data/MAJA-metadata/DTM/T31TCJ

- 5.3 MAJA L2A Processing Example

Run:
./3_startmaja_example.sh
Performs L2A processing using folder.txt, the example L1C SAFE, and the generated DTM.
Output: /data/MAJA-metadata/S2-L2A

--------------------------------------------------------
6. Developer Toolkit (New in v1.1.0)
--------------------------------------------------------

Multi-agent CLI for code review, log debugging, profiling, and docs validation:

  python -m tools.agents.agentctl review
  python -m tools.agents.agentctl debug --logdir logs/
  python -m tools.agents.agentctl profile
  python -m tools.agents.agentctl docscheck --docsdir docs/
  python -m tools.agents.agentctl all

All agents produce JSON + Markdown reports under reports/<agent>/<timestamp>/.

--------------------------------------------------------
7. Batch Processing Runner (New in v1.1.0)
--------------------------------------------------------

Parallel MAJA job execution with file-lock safety and resume support:

  python scripts/maja_batch.py examples/manifest.yml --workers 4
  python scripts/maja_batch.py examples/manifest.json --dry-run
  python scripts/maja_batch.py examples/manifest.yml --resume

Output:
  - logs/jobs/<job_id>.log           Per-job output
  - logs/state/<name>_state.json     Resume state
  - logs/locks/<name>.lockdir        Coordination lock directories
  - reports/batch/<name>_<ts>.json   Summary report (JSON)
  - reports/batch/<name>_<ts>.md     Summary report (Markdown)

Manifests define job sequences with optional lock names and timeouts
(see examples/manifest.yml or examples/manifest.json).

--------------------------------------------------------
8. ENSO Satellite Images (New in v1.1.0)
--------------------------------------------------------

Download ENSO satellite images for documentation (host-side):

  python scripts/fetch_enso_images.py
  python scripts/fetch_enso_images.py --dry-run

Images saved to docs/assets/enso/.

Inside the container, use:
  ./1_enso_download_example.sh
which downloads to /data/MAJA-metadata/ENSO/.

--------------------------------------------------------
9. CI Pipeline (New in v1.1.0)
--------------------------------------------------------

  - GitHub Actions: .github/workflows/ci.yml
  - Python lint (py_compile) + pytest on 3.9-3.11
  - ShellCheck on all shell scripts
  - Markdown lint on all .md files

Run tests locally:

  pip install pytest pyyaml
  python -m pytest tests/ -v

--------------------------------------------------------
10. Tests (New in v1.1.0)
--------------------------------------------------------

  tests/test_manifest.py    Manifest parsing & validation
  tests/test_locking.py     File-lock acquire/release & concurrency
  tests/test_resume.py      State cache persistence
  tests/test_agents.py      Agent toolkit unit tests

--------------------------------------------------------
11. WP_02 ENSO Additions — Commands and Deliverables
--------------------------------------------------------

### Local setup
```bash
python -m pip install -r requirements.txt
```

### Existing MAJA demo
Host-side container entry:
```bash
./run_maja_wrapper.sh
```
Inside the container:
```bash
./0_seed_example_safe.sh
./2_dtmcreation_example.sh
./3_startmaja_example.sh
```
The real MAJA command used by the demo is `startmaja -f /opt/maja-workspace/folder.txt -t T31TCJ -s Toulouse -d 2025-11-22 -e 2025-11-23`.

### Multi-agent toolkit
```bash
python tools/agents/agentctl.py all
python tools/agents/agentctl.py review
python tools/agents/agentctl.py debug
python tools/agents/agentctl.py profile
python tools/agents/agentctl.py docscheck
```
Reports are written under `reports/`.

### Batch dry run and execution
```bash
python scripts/maja_batch.py --manifest examples/maja_batch_manifest.yaml --workers 2 --dry-run
python scripts/maja_batch.py --manifest examples/maja_batch_manifest.yaml --workers 2 --resume
```
The manifest supports YAML and JSON. Each job defines `id`, `command`, `output`, optional `working_dir`, `log_file`, `timeout`, `required_outputs`, and `enabled`.

Resume skips only jobs with matching fingerprint, valid `.maja_batch_success.json`, required outputs and no active lock. Locks are per-job directory locks next to each working directory. Failed jobs preserve `.maja_batch_failure.json`.

### ENSO image retrieval
```bash
python scripts/fetch_enso_images.py --output-dir docs/assets/enso --limit 10
python scripts/fetch_enso_images.py --output-dir docs/assets/enso --limit 10 --dry-run
```
Source: https://ddp.csum.umontpellier.fr/rob1e/photos. Verify licensing before external publication. Documentation must reference local `docs/assets/enso/` files, not hotlinks.

### Report/PDF generation
```bash
python scripts/build_reports.py
```
Outputs generated locally under `deliverables/`:
- `deliverables/WP_02_Analyse_Besoins_Etude_Faisabilite.pdf`
- `deliverables/Audit_Detaille_Amelioration_MAJA_ENSO.pdf`

The PDF files are generated artifacts and are intentionally ignored by Git (`deliverables/*.pdf`). They are available after local execution, after Docker execution inside `deliverables/`, and as downloadable CI workflow artifacts. The authoritative version-controlled deliverables are the editable Markdown sources in `docs/reports/` plus the requirements documents in `docs/requirements/`.

### Tests and lint
```bash
python -m py_compile scripts/*.py tools/agents/*.py
pytest -q
```
ShellCheck is used in CI when available.

### Docker commands
```bash
docker build -t maja-expleo:1.0.0 .
docker image inspect maja-expleo:1.0.0
docker run --rm -it \
  -v "$(pwd)/data:/workspace/data" \
  -v "$(pwd)/outputs:/workspace/outputs" \
  -v "$(pwd)/logs:/workspace/logs" \
  -v "$(pwd)/deliverables:/workspace/deliverables" \
  maja-expleo:1.0.0 bash
```
If the MAJA ZIP or SAFE directory referenced by `Dockerfile` is absent, Docker build is blocked until those artifacts are supplied.

### Output locations
- MAJA products: `/data/MAJA-metadata/S2-L2A`
- Batch outputs: `outputs/batch/`
- Batch summaries: `outputs/batch/batch-summary.json` and `.md`
- Job logs: `logs/maja-batch/`
- Agent reports: `reports/`
- ENSO assets: `docs/assets/enso/`
- PDF deliverables: `deliverables/`

### Known scientific limitations
Successful execution does not prove ENSO scientific validity. Required stakeholder decisions: ENSO product format, angle representation, radiometric calibration, CAMS/ECMWF access, validation datasets, target quality thresholds and operational sizing.

--------------------------------------------------------
12. Complete Docker launch-to-output checklist
--------------------------------------------------------

Use this sequence from the repository root when Docker and the MAJA/SAFE build artifacts are available.

### 12.1 Build or obtain the image
The repository wrapper expects the image name `tareelou/maja-env:latest`. Build and tag it as follows if you have `MAJA-4.10.0.zip` and the example SAFE directory referenced by the Dockerfile:

```bash
docker build --build-arg IMAGE_VERSION=1.0.0 -t tareelou/maja-env:latest .
docker image inspect tareelou/maja-env:latest
```

### 12.2 Prepare host data directories
```bash
sudo mkdir -p \
  /data/MAJA-metadata/CAMS \
  /data/MAJA-metadata/CDF \
  /data/MAJA-metadata/DEM \
  /data/MAJA-metadata/DTM \
  /data/MAJA-metadata/ENSO \
  /data/MAJA-metadata/GIPP \
  /data/MAJA-metadata/GSW \
  /data/MAJA-metadata/LUT \
  /data/MAJA-metadata/S2-L1C \
  /data/MAJA-metadata/S2-L2A \
  /data/MAJA-metadata/tmp
```

### 12.3 Start or attach to the MAJA container
```bash
./run_maja_wrapper.sh
```

The wrapper creates or reuses the persistent container `maja-run`, mounts `/data/MAJA-metadata` into the container, mounts `/data/MAJA-metadata/tmp` as `/opt/maja-tmp`, and opens an interactive shell in `/opt/maja-workspace`.

### 12.4 Run the Bash scripts inside the container
Inside the container shell, run the scripts in this order:

```bash
./0_seed_example_safe.sh
./1_enso_download_example.sh
./2_dtmcreation_example.sh
./3_startmaja_example.sh
```

`0_seed_example_safe.sh` copies the embedded Sentinel-2 L1C SAFE to `/data/MAJA-metadata/S2-L1C/Toulouse/T31TCJ/` if it is not already present. `1_enso_download_example.sh` downloads demonstration ROB1E/ENSO images to `/data/MAJA-metadata/ENSO/`. `2_dtmcreation_example.sh` creates the DTM under `/data/MAJA-metadata/DTM/T31TCJ`. `3_startmaja_example.sh` runs `startmaja` with `folder.txt` and writes MAJA L2A outputs under `/data/MAJA-metadata/S2-L2A`.

### 12.5 Verify final outputs from inside the container
```bash
find /data/MAJA-metadata/S2-L1C/Toulouse/T31TCJ -maxdepth 2 -type d | head
find /data/MAJA-metadata/ENSO -maxdepth 1 -type f | head
find /data/MAJA-metadata/DTM/T31TCJ -maxdepth 2 -type f | head
find /data/MAJA-metadata/S2-L2A -maxdepth 3 -type f | head
```

### 12.6 Run the added Python tooling inside the image
```bash
python tools/agents/agentctl.py all
python scripts/maja_batch.py --manifest examples/maja_batch_manifest.yaml --workers 2 --dry-run
python scripts/build_reports.py
pytest -q
```

The generated PDFs are local artifacts under `deliverables/` and are ignored by Git. In CI they are uploaded as workflow artifacts.

### 12.7 Copy outputs if the host directory was not mounted
When outputs are not already visible through `/data/MAJA-metadata`, copy them from a stopped or running container:

```bash
docker cp maja-run:/data/MAJA-metadata/S2-L2A ./S2-L2A
docker cp maja-run:/opt/maja-workspace/reports ./reports
docker cp maja-run:/opt/maja-workspace/deliverables ./deliverables
```

### 12.8 Cleanup
```bash
docker stop maja-run
docker rm maja-run
# Optional only if you no longer need the persisted /home/maja state:
# docker volume rm maja-home
```
