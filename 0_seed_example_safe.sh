#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Script Name          : 0_seed_example_safe.sh
# Version              : 1.0
# Author               : Reda El Hirech - reda.el-hirech@expleogroup.com
# Date                 : 2025-12-10
# Purpose              : Copy the example Sentinel-2 L1C SAFE product from the image
#                        into the host-mounted directory /data/MAJA-metadata/S2-L1C.
#
# Notes:
#   - This script is intended for the MAJA 1.0.0 example image.
#   - It should be run from inside the container, after the Docker volume
#     /data/MAJA-metadata has been mounted by the wrapper.
#   - If the example SAFE already exists on the host, nothing is copied.
# -----------------------------------------------------------------------------

set -euo pipefail

TILE="T31TCJ"
SAFE_NAME="S2A_MSIL1C_20251122T105401_N0511_R051_T31TCJ_20251122T132206.SAFE"

SRC_SAFE_DIR="/opt/maja-workspace/example_data/S2-L1C/Toulouse/${TILE}/${SAFE_NAME}"
DST_SAFE_DIR="/data/MAJA-metadata/S2-L1C/Toulouse/${TILE}"
DST_SAFE_PATH="${DST_SAFE_DIR}/${SAFE_NAME}"


echo
echo "==============================================================="
echo "  Seeding example Sentinel-2 L1C SAFE product for tile ${TILE} "
echo "==============================================================="
echo

# Check if the SAFE example exists in the image
if [ ! -d "${SRC_SAFE_DIR}" ]; then
  echo "Error: example SAFE directory not found in the image:"
  echo "  ${SRC_SAFE_DIR}"
  echo "Please check that the image was built with the example data."
  echo
  exit 1
fi

# Check if the SAFE example already exists in /data/MAJA-metadata in the host
if [ -d "${DST_SAFE_PATH}" ]; then
  echo "Example SAFE already present on the host:"
  echo "  ${DST_SAFE_PATH}"
  echo "Nothing to do."
  echo
  exit 0
fi

echo "Creating destination directory:"
echo "  ${DST_SAFE_DIR}"
mkdir -p "${DST_SAFE_DIR}"

echo
echo "Copying example SAFE from:"
echo "  ${SRC_SAFE_DIR}"
echo "to:"
echo "  ${DST_SAFE_DIR}"
echo

cp -r "${SRC_SAFE_DIR}" "${DST_SAFE_DIR}/"

echo "Done. Example SAFE is now available under:"
echo "  ${DST_SAFE_PATH}"
echo
echo "You can now run the example scripts:"
echo "  ./1_enso_download_example.sh"
echo "  ./2_dtmcreation_example.sh"
echo "  ./3_startmaja_example.sh"
echo



