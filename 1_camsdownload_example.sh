#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Script Name          : 1_camsdownload_example.sh (DEPRECATED)
# Version              : 1.0
# Author               : Tarek ELOUARET - tarek.elouaret@expleogroup.com
# Date                 : 2025-12-10
# Purpose              : Example CAMS download for MAJA (fixed parameters).
# Tile area            : Toulouse, Haute-Garonne, FRANCE
# Maja version         : 4.10.0
# Docker image version : 1.0.0
#
# Notes:
#   - DEPRECATED in favour of 1_enso_download_example.sh.
#   - Kept for backward compatibility only.
#   - No parameters are taken.
# -----------------------------------------------------------------------------

set -euo pipefail

echo
echo "================================================="
echo "   [DEPRECATED] CAMS data download for MAJA      "
echo "================================================="
echo

echo "NOTE: This script is deprecated."
echo "Please use 1_enso_download_example.sh instead."
echo

echo "Downloading CAMS data for fixed example date..."
echo

camsdownload \
  -d 20251122 \
  -f 20251122 \
  -w /data/MAJA-metadata/CDF \
  -a /data/MAJA-metadata/CAMS \
  -p s2

echo
echo "Done. CAMS data saved under:"
echo "  /data/MAJA-metadata/CDF"
echo "  /data/MAJA-metadata/CAMS"
echo
