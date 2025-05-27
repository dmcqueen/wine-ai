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


# Start the Docker daemon and pre-pull container images so that tests
# depending on Docker can run without requiring network access.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -x "$SCRIPT_DIR/init.sh" ]; then
    bash "$SCRIPT_DIR/init.sh"
fi

