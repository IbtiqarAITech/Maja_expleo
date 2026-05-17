#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# Script Name : maja_setup.sh
# Version     : 1.0
# Author      : Reda El Hirech - reda.el-hirech@expleogroup.com
# Maintainer  : Reda El Hirech
# Date        : 2025-12-18
#
# Description :  Setup and validation script for MAJA Docker environment.
#                - Checks CPU, RAM and disk for host system
#                - Checks Docker availability and permissions
#                - Prepares host metadata directory structure
#                - Manages MAJA Docker image (latest)
#
# Requirements :
#   - Docker installed
#   - User authorized to access Docker daemon
#   - /data directory available and writable
#
# Notes :
#   This script does NOT use sudo.
#   Administrative actions must be performed beforehand.
#

cpu_info() {
	echo
	echo "[MAJA-SETUP] === CPU informations ==="
	echo
	
        # Architecture
	local arch
	arch="$(uname -m)"
	echo "[MAJA-SETUP] Architecture        : ${arch}"

	# CPU Model
	local model
	model="$(grep "model name" /proc/cpuinfo | head -n 1 | cut -d':' -f2 | sed 's/^ *//')"
	echo "[MAJA-SETUP] CPU model           : ${model}"

	# Number of logical cores
	local cores
	cores="$(nproc)"
	echo "[MAJA-SETUP] Logical cores       : ${cores}"

	# CPU Frequency
	local cpu_freq_cap
	cpu_freq_cap=$(echo "$model" | grep -o '@ .*GHz' | sed 's/@ //')
	echo "[MAJA-SETUP] CPU Freq            : ${cpu_freq_cap}"
}

ram_info() {
	echo
	echo "[MAJA-SETUP] === RAM informations ==="
	echo

	# Memory total (kB)
        local mem_total_kb
        mem_total_kb="$(grep "MemTotal" /proc/meminfo | cut -d':' -f2 | sed 's/^ *//' | cut -d' ' -f1)"

	# Memory total (GB)
        local mem_total_gb
        mem_total_gb=$(( mem_total_kb / 1024 / 1024 ))
        echo "[MAJA-SETUP] RAM total           : ${mem_total_gb} GB"

	local mem_avail_kb
        mem_avail_kb="$(grep "MemAvailable" /proc/meminfo | cut -d':' -f2 | sed 's/^ *//' | cut -d' ' -f1)"

        local mem_avail_gb
        mem_avail_gb=$(( mem_avail_kb / 1024 / 1024 ))

        echo "[MAJA-SETUP] RAM available       : ${mem_avail_gb} GB"
}

disk_info() {
	echo
        echo "[MAJA-SETUP] === Disk informations ==="
	echo

        local lineDf
        lineDf="$(df -hP / | tail -n 1)"

        local filesystem size used avail usepct mountpoint
        filesystem="$(echo "$lineDf" | awk '{print $1}')"
        size="$(echo "$lineDf" | awk '{print $2}')"
        used="$(echo "$lineDf" | awk '{print $3}')"
        avail="$(echo "$lineDf" | awk '{print $4}')"
        usepct="$(echo "$lineDf" | awk '{print $5}')"
        mountpoint="$(echo "$lineDf" | awk '{print $6}')"

        echo "[MAJA-SETUP] Filesystem          : $filesystem"
        echo "[MAJA-SETUP] Mount point         : $mountpoint"
        echo "[MAJA-SETUP] Size                : $size"
        echo "[MAJA-SETUP] Used                : $used ($usepct)"
        echo "[MAJA-SETUP] Available           : $avail"
		
        # Detect disk type (SSD / HDD)
        local disk_type="Unknown"
        local disk_name

	disk_name="$(lsblk -no PKNAME "$filesystem" 2>/dev/null || true)"

        if lsblk -d -o NAME,ROTA 2>/dev/null | grep -q "^${disk_name} *0"; then
                disk_type="SSD"
        elif lsblk -d -o NAME,ROTA 2>/dev/null | grep -q "^${disk_name} *1"; then
                disk_type="HDD"
        fi
	
	echo "[MAJA-SETUP] Disk type           : $disk_type"
}

docker_info() {
	echo
	echo "[MAJA-SETUP] === Docker informations ==="
        echo

	# Check Docker install
        if ! command -v docker >/dev/null 2>&1; then
                echo "[MAJA-SETUP][ERROR] Docker is not installed (docker command not found)."
		echo "[MAJA-SETUP][INFO] Please follow the official installation instructions:"
		echo "[MAJA-SETUP][INFO] https://docs.docker.com/engine/install/"
		echo
		return 1
	fi

	# Check daemon access
	if ! docker info >/dev/null 2>&1; then
		echo "[MAJA-SETUP][INFO] Docker is installed but you do not have access to the Docker daemon."
		echo "[MAJA-SETUP][INFO] Ask an administrator to run:"
		echo "  sudo usermod -aG docker $USER"
		echo
		echo "[MAJA-SETUP][INFO] Then you MUST log out and log back in (or reconnect via SSH) for changes to apply."
		echo
		return 1
	fi

	echo "[MAJA-SETUP] Docker version      : $(docker --version)"
}

get_local_digest() {
        # Returns: sha256:... or empty
        #docker inspect --format='{{index .RepoDigests 0}}' "$1" 2>/dev/null | sed 's/.*@sha256://'

	local ref="$1"
	local digest

	digest="$(docker inspect --format='{{index .RepoDigests 0}}' "$ref" 2>/dev/null \
                | sed -n 's/.*sha256:\([0-9a-f]\{64\}\).*/\1/ip')"

	if [ -n "$digest" ]; then
		echo "$digest"
		return 0
	fi

	digest="$(docker inspect --format='{{.Id}}' "$ref" 2>/dev/null \
		| sed -n 's/.*sha256:\([0-9a-f]\{64\}\).*/\1/ip')"

	echo "$digest"
}

get_remote_digest() {
        # Returns: sha256:... or empty
	docker manifest inspect --verbose "$1" 2>/dev/null \
		| grep -i -m 1 '"Digest".*sha256:' \
		| sed -n 's/.*sha256:\([0-9a-f]\{64\}\).*/\1/ip'
}

maja_check_update_latest() {
        echo "[MAJA-SETUP] === MAJA image update check (latest) ==="
	echo

        local image="tareelou/maja-env:latest"
        local local_digest remote_digest

        remote_digest="$(get_remote_digest "$image")" 
	if [ -z "$remote_digest" ]; then
                return 1 # Error, cannot check MAJA image in Docker Hub
        fi

        local_digest="$(get_local_digest "$image")"
	if [ -z "$local_digest" ]; then
                echo "[MAJA-SETUP] No local image found for $image"
                echo "[MAJA-SETUP] Remote image digest : $remote_digest"
                return 20 # MAJA not found in local => to pull
        fi

	echo "[MAJA-SETUP] Local image digest  : $local_digest"
        echo "[MAJA-SETUP] Remote image digest : $remote_digest"

	if [ "$local_digest" = "$remote_digest" ]; then
		return 0 # Up to date, nothing to pull
	else
		return 10 # New image available
        fi
}

maja_container_info() {
	local image_name="tareelou/maja-env:latest"
        container_info="$(docker ps -a \
                --filter "name=^maja-run$" \
                --format "{{.Names}}\t{{.ID}}\t{{.Status}}\t{{.Image}}" \
		| head -n 1)"

	echo "[MAJA-SETUP] Checking if there is any existing MAJA container..."
	sleep 1
        if [ -z "$container_info" ]; then
                echo "[MAJA-SETUP] No existing MAJA container found."
                return 0
        fi
   
	local name id status image image_id
        IFS=$'\t' read -r name id status image <<< "$container_info"

        echo "[MAJA-SETUP] Existing MAJA container found:"
        echo "[MAJA-SETUP]  =>  Name         : $name"
        echo "[MAJA-SETUP]  =>  Container ID : $id"
        echo "[MAJA-SETUP]  =>  Status       : $status"
	echo "[MAJA-SETUP]  =>  Image (tag)  : $image"
	image_id="$(docker inspect -f '{{.Image}}' "$name" 2>/dev/null)"
        echo "[MAJA-SETUP]  =>  Image ID     : $image_id"
        echo
        echo "[MAJA-SETUP][INFO] To remove this container (ONLY if no MAJA processing is running), run this command: docker rm $name"
        echo "[MAJA-SETUP][WARNING] ⚠️ Do NOT remove this container while MAJA processing is running."
        echo "[MAJA-SETUP][WARNING] ⚠️ Make sure no MAJA process is active inside this container."
}

maja_create_metadata_tree() {
	echo
	echo "[MAJA-SETUP] === MAJA metadata directory structure ==="
	echo

	# Check if /data exist
	if [ ! -d "/data" ]; then
		echo "[MAJA-SETUP] [ERROR] Base directory /data does not exist."
		echo "[MAJA-SETUP] [INFO] Please create it or ask an administrator."
		echo
		return 1		
	fi

	# Check if USER can write on /data
	if [ ! -w "/data" ]; then
		echo "[MAJA-SETUP][ERROR] Base directory /data exists but is not writable for user ${USER}"
		echo "[MAJA-SETUP][INFO] Please ask an administrator to grant write permissions on /data."
		echo
		return 1
	fi

	local base_dir="/data/MAJA-metadata"
	
        # Create ${base_dir}
	if [ ! -d "${base_dir}" ]; then
		echo "[MAJA-SETUP] Creating base directory: ${base_dir}"
		mkdir -p "${base_dir}" || return 1
	else
		echo "[MAJA-SETUP] Base directory already exists: ${base_dir} => OK"
	fi
	
	local base_dir_subdirs=(
    CAMS
    CDF
    DEM
    DTM
    ENSO
    GIPP
    GSW
    LUT
    S2-L1C
    S2-L2A
    tmp
        )

	for subdir in "${base_dir_subdirs[@]}"; do
		if [ ! -d "${base_dir}/${subdir}" ]; then
			echo "[MAJA-SETUP] Creating directory: ${base_dir}/${subdir}"
			mkdir -p "${base_dir}/${subdir}" || return 1
		else
			echo "[MAJA-SETUP] Directory already exists: ${base_dir}/${subdir} => OK"
		fi
	done

	echo
	echo "[MAJA-SETUP] MAJA metada directory structure is ready."
	echo
}


cpu_info
ram_info
disk_info
docker_info || exit 1
maja_create_metadata_tree || exit 1
maja_check_update_latest
update_status=$?
image_name="tareelou/maja-env:latest"

if [ "$update_status" -gt 1 ]; then # A pull has to be done
	if [ "$update_status" -eq 20 ]; then # First install
		# Ask user if he want to install MAJA image
		if [ -t 0 ]; then # Interactive mode
			echo
			read -r -p "[MAJA-SETUP] MAJA not installed! Do you want to pull MAJA image now? (y/N): " answer
			case "$answer" in
				y|Y|yes|YES)
					echo "[MAJA-SETUP] Pulling: ${image_name}"
					docker pull "${image_name}"
					echo "[MAJA-SETUP] Pull done."
					echo "[MAJA-SETUP] Run run_maja_wrapper.sh to start using MAJA environment."
					echo
					;;
				*)
					echo "[MAJA-SETUP] Pull skipped by user."
					echo
					;;
			esac
		else
			echo "[MAJA-SETUP] Non-interactive mode detected. Pull skipped."
			echo "[MAJA-SETUP] For this first install, run manually: docker pull ${image_name}"
			echo
		fi
	else # Update MAJA image : new version
		echo "[MAJA-SETUP] Status              : A newer MAJA image is available on Docker Hub."
		echo "[MAJA-SETUP][INFO] Pulling a new image does NOT affect running or stopped MAJA containers."
		echo "[MAJA-SETUP][INFO] Any existing MAJA container will continue using the image it was created with."
		echo

		# Ask user if he want to pull the new image
		if [ -t 0 ]; then # Interactive mode
			read -r -p "[MAJA-SETUP] Do you want to pull the latest MAJA image now? (y/N): " answer
			case "$answer" in
				y|Y|yes|YES)
					echo "[MAJA-SETUP] Pulling: ${image_name}"
					docker pull "${image_name}"
					echo "[MAJA-SETUP] Pull done."
					echo "[MAJA-SETUP][INFO] To start using this new image, any existing MAJA container must be removed and recreated."
					echo "[MAJA-SETUP][INFO] This must be done ONLY after the pull has completed."
                                        maja_container_info
					echo
					;;
				*)
					echo "[MAJA-SETUP] Pull skipped by user."
					echo
					;;
			esac
		else
			echo "[MAJA-SETUP] Non-interactive mode detected. Pull skipped."
			echo "[MAJA-SETUP] [INFO] To update MAJA environment, run manually: docker pull ${image_name}"
			echo
		fi
	fi 
elif [ "$update_status" -eq 1 ]; then
        echo "[MAJA-SETUP][ERROR] Unable to read remote digest from Docker Hub (docker manifest inspect failed)."
        echo "[MAJA-SETUP][ERROR] Unable to check MAJA image update."
	echo
	exit 1
else
	echo "[MAJA-SETUP] MAJA image status   : Up to date => OK (Nothing to do)."
	echo
	exit 0
fi


