========================================================
MAJA Example Workflows
Location: /opt/maja-workspace
========================================================

This directory contains simple example scripts that demonstrate
how to use the MAJA processing environment inside the container.

These scripts are provided for demonstration and training only.
They use fixed parameters (date, tile, paths) and are NOT intended
for operational production.

--------------------------------------------------------
1. Prerequisites
--------------------------------------------------------

Before running the examples, please ensure that:

1) The required host volumes are mounted into the container (The run_maja_wrapper.sh script does this automatically) :

   - /data/MAJA-metadata/CAMS
   - /data/MAJA-metadata/CDF
   - /data/MAJA-metadata/DEM
   - /data/MAJA-metadata/DTM
   - /data/MAJA-metadata/GSW
   - /data/MAJA-metadata/GIPP
   - /data/MAJA-metadata/LUT
   - /data/MAJA-metadata/S2-L1C
   - /data/MAJA-metadata/S2-L2A
   - /data/MAJA-metadata/tmp

2) A valid ~/.cdsapirc file must be in /home/maja
   (on the persistent Docker volume "maja-home") if you want to
   download CAMS data from the Copernicus Climate Data Store.

3) The example Sentinel-2 L1C SAFE product must be deployed to the
   host-mounted directory. This is done by running:

       ./0_seed_example_safe.sh

   This script copies the example SAFE product from the Docker image
   into the host volume /data/MAJA-metadata/S2-L1C so it becomes
   visible to MAJA.

If these inputs are missing, the example scripts will fail.

--------------------------------------------------------
2. Files Provided
--------------------------------------------------------

/opt/maja-workspace contains:

   0_seed_example_safe.sh          → Deploys example .SAFE to the host
   1_camsdownload_example.sh       → Example CAMS download
   2_dtmcreation_example.sh        → Example DTM generation
   3_startmaja_example.sh          → Example MAJA L2A processing
   folder.txt                      → MAJA configuration file
   README_EXAMPLES.txt             → This documentation
   example_data/                   → Contains the embedded L1C SAFE structure

To list available scripts:

   ls -l /opt/maja-workspace

--------------------------------------------------------
3. Step 1 – Deploy the Example Sentinel-2 L1C SAFE
--------------------------------------------------------

Before running any processing script (DTM or L2A), deploy the example SAFE
product to the host-mounted directory by running:

   ./0_seed_example_safe.sh

This will copy:

   /opt/maja-workspace/example_data/S2-L1C/Toulouse/T31TCJ/<SAFE>/

into:

   /data/MAJA-metadata/S2-L1C/Toulouse/T31TCJ/

If the SAFE already exists on the host, nothing will be overwritten.

--------------------------------------------------------
4. Step 2 – CAMS data download
--------------------------------------------------------

Script  : 1_camsdownload_example.sh
Purpose : Demonstrate how to download CAMS data for a fixed date.

Command (inside container):

   ./1_camsdownload_example.sh

This script runs:

   camsdownload \
     -d 20251122 \
     -f 20251122 \
     -w /data/MAJA-metadata/CDF \
     -a /data/MAJA-metadata/CAMS \
     -p s2

Behaviour:

   - Downloads CAMS data for 2025-11-22.
   - Stores intermediate CDF files in:
       /data/MAJA-metadata/CDF
   - Stores CAMS (archive DBL) data in:
       /data/MAJA-metadata/CAMS

Note: A valid ~/.cdsapirc file is required to access the CDS API.
More Info: check /opt/maja-precompiled/lib/python/StartMaja/cams_download/ (inside container)
           Or run this command: camsdownload --help

--------------------------------------------------------
5. Step 3 – DTM generation (DTMCreation.py)
--------------------------------------------------------

Script  : 2_dtmcreation_example.sh
Purpose : Demonstrate how to generate a DTM from DEM + GSW using
          MAJA's DTMCreation.py tool.

Command (inside container):

   ./2_dtmcreation_example.sh

This script runs:

python3.8 /opt/maja-precompiled/lib/python/StartMaja/prepare_mnt/DTMCreation.py \
        -p /data/MAJA-metadata/S2-L1C/Toulouse/T31TCJ/S2A_MSIL1C_20251122T105401_N0511_R051_T31TCJ_20251122T132206.SAFE \
        -o /data/MAJA-metadata/DTM/T31TCJ \
        -d /data/MAJA-metadata/DEM \
        -w /data/MAJA-metadata/GSW \
        -t /data/MAJA-metadata/tmp \
        -c 120

Behaviour:

   - Ensures the output directory exists:
       /data/MAJA-metadata/DTM/T31TCJ
   - Uses:
       - DEM data from /data/MAJA-metadata/DEM: The path to the folder containing the downloaded DEM files/archives.If not existing, an attempt will be made to download them.
       - Global Surface Water data from /data/MAJA-metadata/GSW: The path to the folder containing the GSW occurence .tif-files.If not existing, an attempt will be made to download them.
       - Temporary files under /data/MAJA-metadata/tmp: The path to temp the folder.If not existing, it is set to a /tmp/ location.
   - Produces a DTM dedicated to tile T31TCJ under:
       /data/MAJA-metadata/DTM/T31TCJ

More Info: check /opt/maja-precompiled/lib/python/StartMaja/prepare_mnt/ (inside container)
           Or run this command: dtmcreation --help 

--------------------------------------------------------
6. Step 4 – MAJA L2A processing (startmaja)
--------------------------------------------------------

Script  : 3_startmaja_example.sh
Purpose : Demonstrate how to run MAJA L2A processing with startmaja
          for a single tile and a fixed date range (Init Mode).

Command (inside container):

   ./3_startmaja_example.sh

This script runs:

   startmaja \
     -f /opt/maja-workspace/folder.txt \
     -t T31TCJ \
     -s Toulouse \
     -d 2025-11-22 \
     -e 2025-11-23

Behaviour:

   - Uses folder.txt as the MAJA configuration file: Config/Folder-definition file used for all permanent paths.
   - Processes tile T31TCJ for the Toulouse area (T31TCJ is the tile number).
   - Uses Sentinel-2 L1C data in:
       /data/MAJA-metadata/S2-L1C
   - Writes Sentinel-2 L2A outputs to:
       /data/MAJA-metadata/S2-L2A

More Info: startmaja --help

--------------------------------------------------------
7. Important Notes
--------------------------------------------------------

- These scripts are EXAMPLES ONLY.
  They are not meant to be used as-is in production.

- In a real workflow, you would typically:
  - Parameterize the date(s), tiles and site name.
  - Use your own directory structure and GIPP configuration.

- You are encouraged to copy and adapt these scripts to create
  your own production-ready workflows.

========================================================
End of README_EXAMPLES.md
========================================================
