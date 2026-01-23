#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Script Name          : 3_startmaja_example.sh
# Version              : 1.0
# Author               : Reda El Hirech - reda.el-hirech@expleogroup.com
# Date                 : 2025-12-10
# Purpose              : Example MAJA L2A processing using startmaja.
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
echo "===================================================="
echo "      Example: Running MAJA L2A with startmaja"
echo "===================================================="
echo

echo "This script demonstrates how to run startmaja using:"
echo " - A fixed tile        : T31TCJ"
echo " - An example zone     : Toulouse"
echo " - A fixed sensing date: 2025-11-22"
echo " - An example folder.txt (processing configuration)"
echo

startmaja \
  -f /opt/maja-workspace/folder.txt \
  -t T31TCJ \
  -s Toulouse \
  -d 2025-11-22 \
  -e 2025-11-23

echo
echo "Done. MAJA L2A processing has been executed."
echo "Check the output directory under:"
echo "  /data/MAJA-metadata/S2-L2A"
echo

