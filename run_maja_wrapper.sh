#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# Script Name : run_maja_wrapper.sh
# Version     : 1.0
# Author      : Reda El Hirech - reda.el-hirech@expleogroup.com
# Date        : 2025-12-10
#
# Description:
#   Robust launcher for the MAJA processing environment.
#   This wrapper provides a clean and user-friendly interface to run MAJA
#   inside a persistent Docker container.
#
# Features:
#   - Automatically creates the persistent Docker volume "maja-home".
#   - Ensures /home/maja survives container restarts (for ~/.cdsapirc, logs…).
#   - Re-attaches to an existing container if it is already running.
#   - Starts an exited container when needed.
#   - Creates a brand-new MAJA container if none exists.
#
# User Workflow:
#   - First launch: container + volume are created automatically.
#   - Next launches: user is reattached seamlessly (docker exec / start).
#
# Important:
#   - Do NOT delete the "maja-home" Docker volume.
#
# Usage: ./run_maja_wrapper.sh

set -euo pipefail

IMAGE_NAME="tareelou/maja-env:latest"
CONTAINER_NAME="maja-run"

HOST_METADATA="/data/MAJA-metadata"
ETC_LOCAL_TIME="/etc/localtime"
ETC_TIME_ZONE="/etc/timezone"
PERSISTENT_HOME="maja-home"

# Default command: bash if nothing is provided
if [ "$#" -eq 0 ]; then
	CMD=("bash")
else
	CMD=("$@")
fi

# Check that Docker is available
if ! command -v docker >/dev/null 2>&1; then
	echo "Error: Docker is not available in the PATH." >&2
	exit 1
fi

# Check if there is a MAJA image installed locally
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "MAJA image not found locally: $IMAGE_NAME"
  echo "Please run: ./maja_setup.sh to get the latest version"
  exit 20
fi

# Ensure that the persistent volume for /home/maja exists
if ! docker volume inspect "${PERSISTENT_HOME}" >/dev/null 2>&1; then
	echo "Creating Docker volume '${PERSISTENT_HOME}' for /home/maja..."
	docker volume create "${PERSISTENT_HOME}" >/dev/null
fi

# Check if the container already exists
if docker ps -a --format '{{.Names}}' | grep "${CONTAINER_NAME}"; then
	# Container exists, check its state
	state="$(docker inspect -f '{{.State.Status}}' "${CONTAINER_NAME}")"

	if [ "${state}" = "running" ]; then
		echo "MAJA container '${CONTAINER_NAME}' is already running. Attaching with docker exec..."
		docker exec -it "${CONTAINER_NAME}" "${CMD[@]}"
	else
	        echo "Starting existing MAJA container '${CONTAINER_NAME}'..."
		docker start -ai "${CONTAINER_NAME}"	
	fi
else
	# Container does not exist yet: create it
	echo "Creating and starting new MAJA container '${CONTAINER_NAME}'..."
	docker run --pull=never -it \
		--name "${CONTAINER_NAME}" \
		-v "${HOST_METADATA}":/data/MAJA-metadata \
		-v "${ETC_LOCAL_TIME}:${ETC_LOCAL_TIME}":ro \
		-v "${ETC_TIME_ZONE}:${ETC_TIME_ZONE}":ro \
		-v "${PERSISTENT_HOME}":/home/maja \
		"$IMAGE_NAME" "${CMD[@]}"
fi
