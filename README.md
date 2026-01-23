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
   - Example scripts demonstrating CAMS download, DTM generation, and L2A processing
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
   - /data/MAJA-metadata/GIPP
   - /data/MAJA-metadata/GSW
   - /data/MAJA-metadata/LUT
   - /data/MAJA-metadata/S2-L1C
   - /data/MAJA-metadata/S2-L2A
   - /data/MAJA-metadata/tmp

Additionally, a persistent Docker volume named maja-home stores /home/maja,
including the user’s ~/.cdsapirc.

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


- 5.1 CAMS Download Example

Run:
./1_camsdownload_example.sh
This script downloads CAMS data for a fixed date and requires a valid ~/.cdsapirc file.


- 5.2 DTM Generation Example

Run:
./2_dtmcreation_example.sh
This script uses the SAFE deployed by 0_seed_example_safe.sh and generates a DTM for tile T31TCJ
It writes outputs to:
    /data/MAJA-metadata/DTM/T31TCJ

- 5.3 MAJA L2A Processing Example

Run:
./3_startmaja_example.sh
This script performs an L2A processing workflow using:
   - folder.txt (MAJA configuration)
   - the example L1C SAFE
   - the generated DTM

Outputs are written to:
   /data/MAJA-metadata/S2-L2A




