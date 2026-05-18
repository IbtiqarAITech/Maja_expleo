# -----------------------------------------------------------------------------
# Dockerfile  : maja-env
# Version     : 1.0.0
# Author      : Tarek ELOUARET - tarek.elouaret@expleogroup.com
# Date        : 2025-12-10
#
# Base Image  : ubuntu:20.04
#
# Description :
#   Docker image providing a ready-to-use MAJA 4.10.0 processing environment
#   for Sentinel-2 L2A generation. The image includes:
#     - MAJA 4.10.0 precompiled binaries
#     - Python 3.8 environment (MAJA internal) with updated certifi
#     - Geospatial Data Abstraction Library (GDAL) via MAJA environment
#     - Example scripts for:
#         * ENSO satellite image download
#         * DTM generation (DTMCreation.py)
#         * MAJA L2A processing (startmaja)
#
# Expected Host Volumes :
#   - /data/MAJA-metadata/CAMS   : CAMS auxiliary data (MAJA internal)
#   - /data/MAJA-metadata/CDF    : Path to folder where netcdf data are stored (can be considered as a temporary file)
#   - /data/MAJA-metadata/DEM    : DEM datasets
#   - /data/MAJA-metadata/DTM    : Generated DTM products
#   - /data/MAJA-metadata/ENSO   : Downloaded ENSO satellite images
#   - /data/MAJA-metadata/GIPP   : MAJA GIPP configuration files
#   - /data/MAJA-metadata/GSW    : Global Surface Water mask
#   - /data/MAJA-metadata/LUT    : MAJA LUT files
#   - /data/MAJA-metadata/S2-L1C : Sentinel-2 L1C input products
#   - /data/MAJA-metadata/S2-L2A : Sentinel-2 L2A output products
#   - /data/MAJA-metadata/tmp    : For temporary I/O during DTMCreation
#
# Runtime Notes :
#   - The container is intended to be launched via run_maja_wrapper.sh.
#   - The wrapper manages a persistent Docker volume "maja-home"
#     mounted on /home/maja to preserve user files (e.g. ~/.cdsapirc).
#
# Build Example :
#   docker build --build-arg IMAGE_VERSION=1.0.0 -t tareelou/maja-env:1.0.0 .
#
# -----------------------------------------------------------------------------

FROM ubuntu:20.04

LABEL maintainer="Tarek ELOUARET - tarek.elouaret@expleogroup.com"
LABEL maja.version="4.10.0"
LABEL description="MAJA 4.10.0 environment with Python 3.8 + GDAL + updated certifi. Ready for operational Sentinel-2 L2A processing."
LABEL org.opencontainers.image.title="MAJA Processing Environment"
LABEL org.opencontainers.image.version="4.10.0"
LABEL org.opencontainers.image.description="Processing environment for MAJA L2A atmospheric correction from CNES/MAJA, including utilities from StartMaja and full metadata structure."
LABEL org.opencontainers.image.source="https://gitlab.orfeo-toolbox.org/maja/maja"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL volumes_required='["/data/MAJA-metadata/CAMS", "/data/MAJA-metadata/CDF", "/data/MAJA-metadata/DEM", "/data/MAJA-metadata/DTM", "/data/MAJA-metadata/ENSO", "/data/MAJA-metadata/GIPP", "/data/MAJA-metadata/GSW", "/data/MAJA-metadata/LUT", "/data/MAJA-metadata/S2-L1C", "/data/MAJA-metadata/S2-L2A", "/data/MAJA-metadata/tmp"]'

# --------------------------------------------------------------
# 1) Install system standard dependencies
# --------------------------------------------------------------
ARG DEBIAN_FRONTEND=noninteractive
ARG IMAGE_VERSION=1.0.0
LABEL version="${IMAGE_VERSION}"
ENV MAJA_IMAGE_VERSION="${IMAGE_VERSION}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    curl \
    unzip \
    vim \
    bash-completion \
    bzip2 \
    file \
    lsof \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir pyyaml pytest && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# --------------------------------------------------------------
# 2) Create user + core directories
#    /opt   =>  SSD NVMe (MAJA env + workspace)
#    /data  =>  HDD for Auxiliary Data + L1C & L2A products
# --------------------------------------------------------------
RUN useradd -ms /bin/bash maja && \
    mkdir -p \
    /opt/maja-precompiled \
    /opt/maja-tmp \
    /opt/maja-workspace \
    /data/MAJA-metadata/CAMS \
    /data/MAJA-metadata/CDF \
    /data/MAJA-metadata/DEM \
    /data/MAJA-metadata/DTM \
    /data/MAJA-metadata/ENSO \
    /data/MAJA-metadata/GIPP \
    /data/MAJA-metadata/GSW \
    /data/MAJA-metadata/LUT \
    /data/MAJA-metadata/S2-L1C \
    /data/MAJA-metadata/S2-L2A \
    /data/MAJA-metadata/tmp \
    && chown -R maja:maja /opt /data/MAJA-metadata

USER maja
WORKDIR /opt/maja-workspace

RUN echo 'export PS1="maja@sentinel-2:\w\$ "' >> /home/maja/.bashrc

# 2.1 - Example Sentinel-2 L1C product for tile T31TCJ (Toulouse)
#       Included only for the MAJA 1.0.0 example image.

COPY --chown=maja:maja S2A_MSIL1C_20251122T105401_N0511_R051_T31TCJ_20251122T132206.SAFE \
  /opt/maja-workspace/example_data/S2-L1C/Toulouse/T31TCJ/S2A_MSIL1C_20251122T105401_N0511_R051_T31TCJ_20251122T132206.SAFE/

# --------------------------------------------------------------
# 3) Install MAJA precompiled binary
# --------------------------------------------------------------
COPY --chown=maja:maja MAJA-4.10.0.zip /tmp/MAJA-4.10.0.zip

RUN unzip /tmp/MAJA-4.10.0.zip -d /tmp/maja-installer && \
    chmod +x /tmp/maja-installer/MAJA-4.10.0.run && \
    /tmp/maja-installer/MAJA-4.10.0.run --target /opt/maja-precompiled && \
    rm -rf /tmp/MAJA-4.10.0.zip /tmp/maja-installer

# --------------------------------------------------------------
# 4) Prepare MAJA Python environment
# --------------------------------------------------------------

# Use bash for the following RUN instructions
SHELL ["/bin/bash", "-c"]

# 4.1 - Source MAJA env in maja's shell + update certifi
COPY --chown=maja:maja folder.txt /opt/maja-workspace

RUN echo 'source /opt/maja-precompiled/bin/.majaenv.sh' >> /home/maja/.bashrc && \
    /opt/maja-precompiled/bin/python3.8 -m pip install --upgrade certifi

# 4.2 - Install example scripts (enso download, dtmcreation, startmaja)

COPY --chown=maja:maja 0_seed_example_safe.sh /opt/maja-workspace/0_seed_example_safe.sh
COPY --chown=maja:maja 1_enso_download_example.sh /opt/maja-workspace/1_enso_download_example.sh
COPY --chown=maja:maja 2_dtmcreation_example.sh /opt/maja-workspace/2_dtmcreation_example.sh
COPY --chown=maja:maja 3_startmaja_example.sh /opt/maja-workspace/3_startmaja_example.sh
COPY --chown=maja:maja README_EXAMPLES.md /opt/maja-workspace/README_EXAMPLES.md

COPY --chown=maja:maja tools /opt/maja-workspace/tools
COPY --chown=maja:maja scripts /opt/maja-workspace/scripts
COPY --chown=maja:maja tests /opt/maja-workspace/tests
COPY --chown=maja:maja examples /opt/maja-workspace/examples

RUN chmod +x /opt/maja-workspace/*.sh

# 4.3 - Global MAJA banner
USER root

RUN echo "${IMAGE_VERSION}" > /etc/maja_image_version

RUN cat << 'EOF' >> /etc/bash.bashrc

if [ -t 1 ]; then
  echo
  echo "=========================================================="
  echo "==========[ 🌍 MAJA 4.10.0 + ENSO - Ready ]=========="
  echo "==============[ Image version : $(cat /etc/maja_image_version 2>/dev/null) ]=============="
  echo "=========================================================="
  echo
fi

EOF
RUN sed -i 's/\r$//' /etc/bash.bashrc

USER maja

# --------------------------------------------------------------
# 5) Default command
# --------------------------------------------------------------
CMD ["bash", "-i"]
