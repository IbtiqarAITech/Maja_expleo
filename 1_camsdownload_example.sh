#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Script Name          : 1_camsdownload_example.sh
# Version              : 1.0
# Author               : Reda El Hirech - reda.el-hirech@expleogroup.com 
# Date                 : 2025-12-10
# Purpose              : Example CAMS download for MAJA (fixed parameters).
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
echo "================================================="
echo "   Example: CAMS data download for MAJA 4.10.0   "
echo "================================================="
echo

echo "This script downloads CAMS data for a fixed example date."
echo "It is provided as a demonstration of camsdownload usage."
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
