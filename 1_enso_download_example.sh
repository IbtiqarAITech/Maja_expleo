#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Script Name          : 1_enso_download_example.sh
# Version              : 1.0
# Author               : Reda El Hirech - reda.el-hirech@expleogroup.com
# Date                 : 2025-12-10
# Purpose              : Example ENSO satellite image download (fixed parameters).
# Source               : https://ddp.csum.umontpellier.fr/rob1e/photos
# Maja version         : 4.10.0
# Docker image version : 1.0.0
#
# Notes:
#   - This is only a demonstration script.
#   - No parameters are taken.
#   - Downloads the latest curated ROB1E (ENSO) satellite photos.
# -----------------------------------------------------------------------------

set -euo pipefail

ENSO_SOURCE="https://ddp.csum.umontpellier.fr/rob1e/photos"
ENSO_DIR="/data/MAJA-metadata/ENSO"

echo
echo "================================================="
echo "  Example: ENSO satellite image download         "
echo "================================================="
echo

echo "This script downloads ENSO (ROB1E) satellite photos"
echo "from the CNES/UMR server for demonstration purposes."
echo

# Create destination
mkdir -p "${ENSO_DIR}"

# Download the page listing and extract all .jpg image URLs
# Handles both absolute (/static/ddp/...) and relative paths
echo "Fetching image listing from:"
echo "  ${ENSO_SOURCE}"
echo

IMAGES=$(wget -q -O - "${ENSO_SOURCE}" \
  | grep -o 'href="[^"]*\.jpg"' \
  | cut -d'"' -f2 \
  | sort -u)

COUNT=$(echo "${IMAGES}" | grep -c . || true)

if [ "${COUNT}" -eq 0 ]; then
  echo "No images found. The server may have changed."
  echo "Check manually: ${ENSO_SOURCE}"
  echo
  exit 0
fi

echo "Found ${COUNT} image(s). Downloading to:"
echo "  ${ENSO_DIR}"
echo

DOWNLOADED=0
while IFS= read -r img; do
  if [ -z "${img}" ]; then
    continue
  fi
  # Construct full URL
  if [[ "${img}" == /* ]]; then
    url="https://ddp.csum.umontpellier.fr${img}"
  else
    url="${ENSO_SOURCE}/${img}"
  fi
  fname=$(basename "${img}")
  if [ -f "${ENSO_DIR}/${fname}" ]; then
    echo "  EXISTS: ${fname}"
  else
    echo -n "  DOWNLOAD: ${fname} ... "
    if wget -q -O "${ENSO_DIR}/${fname}" "${url}"; then
      echo "OK"
      DOWNLOADED=$((DOWNLOADED + 1))
    else
      echo "FAILED"
    fi
  fi
done <<< "${IMAGES}"

echo
echo "Done. Downloaded ${DOWNLOADED} new image(s)."
echo "Total ENSO images saved under:"
echo "  ${ENSO_DIR}"
echo
echo "You can now proceed to DTM generation:"
echo "  ./2_dtmcreation_example.sh"
echo
