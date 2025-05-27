#!/usr/bin/env bash
set -euo pipefail

################################################################################
# This script expects that you run the container with the host's Docker
# socket bind-mounted, e.g.:
#
#   docker run --rm -it \
#     -v /var/run/docker.sock:/var/run/docker.sock \
#     your-image:latest
#
# That way, Docker commands inside the container will talk to the host daemon.
################################################################################

export DEBIAN_FRONTEND=noninteractive

# Install prerequisites: Docker CLI, jq, curl, procps, findutils, Java runtime.
# Note: This installs 'docker.io' which provides the docker CLI on Ubuntu.
apt-get update
apt-get install -y --no-install-recommends \
    docker.io \
    jq \
    curl \
    procps \
    findutils \
    openjdk-11-jre-headless

# Verify that Docker is accessible through the bind-mounted socket.
echo "Checking if Docker is accessible..."
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Cannot communicate with Docker daemon."
    echo "Make sure you run this container with the Docker socket bind-mounted:"
    echo "  docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock your-image"
    exit 1
fi

# Pre-pull container images used by the project
images=(
    python:3.6
    python:3.7
    maven:3.8-openjdk-11
    vespaengine/vespa
)

for img in "${images[@]}"; do
    echo "Pulling image: $img"
    docker pull "$img"
done

echo "All done!"
exit 0
