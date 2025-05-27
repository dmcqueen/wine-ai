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

# Pre-pull container images used in the README steps

#docker pull python:3.6

#docker pull python:3.7

#docker pull maven:3.8-openjdk-11

#docker pull vespaengine/vespa

