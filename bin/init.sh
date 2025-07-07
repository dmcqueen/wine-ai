#!/usr/bin/env bash
set -euo pipefail

# Start the Docker daemon if it is not already running
if ! pgrep dockerd > /dev/null 2>&1; then
    nohup dockerd > /tmp/dockerd.log 2>&1 &
    # Wait until Docker is ready
    timeout 30 bash -c 'until docker info >/dev/null 2>&1; do sleep 1; done'
fi

# Pre-pull container images used by the project
images=(
    python:3.12.4
    maven:3.8-openjdk-11
    vespaengine/vespa
)

for img in "${images[@]}"; do
    docker pull "$img"
done
