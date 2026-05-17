#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Script Name          : 2_dtmcreation_example.sh
# Version              : 1.0
# Author               : Tarek ELOUARET - tarek.elouaret@expleogroup.com
# Date                 : 2025-12-10
# Purpose              : Example DEM → DTM generation using DTMCreation.py (fixed paths).
# Tile area            : Toulouse, Haute-Garonne, FRANCE
# Maja version         : 4.10.0
# Docker image version : 1.0.0
#
# Notes:
#   - This is only a demonstration script.
#   - No parameters are taken.
# -----------------------------------------------------------------------------

set -euo pipefail

echo
echo "============================================="
echo "   Example: DTM generation for MAJA 4.10.0   "
echo "============================================="
echo

echo "This script demonstrates how to run DTMCreation.py with"
echo "a fixed example Sentinel-2 L1C product and fixed output paths."
echo

TILE="T31TCJ"
OUTPUT_DIR="/data/MAJA-metadata/DTM/${TILE}"

if [ ! -d "${OUTPUT_DIR}" ]; then
	echo "Output directory does not exist. Creating: ${OUTPUT_DIR}"
	mkdir -p "${OUTPUT_DIR}"
else
	echo "Output directory already exists: ${OUTPUT_DIR}"
fi

if [ ! -f /opt/maja-precompiled/lib/python/StartMaja/prepare_mnt/DTMCreation.py ]; then
	echo "ERROR: MAJA is not installed in this image. DTMCreation.py not found."
	echo "Install MAJA first (see Dockerfile section 3) and rebuild."
	exit 1
fi

python3.8 /opt/maja-precompiled/lib/python/StartMaja/prepare_mnt/DTMCreation.py \
	-p /data/MAJA-metadata/S2-L1C/Toulouse/T31TCJ/S2A_MSIL1C_20251122T105401_N0511_R051_T31TCJ_20251122T132206.SAFE \
	-o /data/MAJA-metadata/DTM/T31TCJ \
	-d /data/MAJA-metadata/DEM \
	-w /data/MAJA-metadata/GSW \
	-t /data/MAJA-metadata/tmp \
	-c 120

echo
echo "Done. DEM-based DTM saved under:"
echo "  /data/MAJA-metadata/DTM/T31TCJ"
echo

