#!/usr/bin/env bash
set -euo pipefail

# Install prerequisites to run the example application.
# Tools: docker, jq, curl, watch, xargs, and Java runtime.

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
    docker.io \
    jq \
    curl \
    procps \
    findutils \
    openjdk-11-jre-headless

# Start the Docker daemon if it is not already running
if ! pgrep dockerd > /dev/null 2>&1; then
    nohup dockerd > /tmp/dockerd.log 2>&1 &
    # Wait until Docker is ready
    timeout 30 bash -c 'until docker info >/dev/null 2>&1; do sleep 1; done'
fi

# Pre-pull container images used by the project
images=(
    python:3.6
    python:3.7
    maven:3.8-openjdk-11
    vespaengine/vespa
)

for img in "${images[@]}"; do
    docker pull "$img"
done

