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
