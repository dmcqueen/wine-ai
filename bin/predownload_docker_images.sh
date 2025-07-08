#!/usr/bin/env bash
#
# bin/predownload_docker_images.sh
#
# Preconditions:
#   • The Docker CLI is on PATH.
#   • The Docker daemon is already running and reachable.
#
# Behaviour:
#   • Verifies the above conditions.
#   • Pulls the container images defined in the IMAGES array.
#
# Optional environment variable:
#   DOCKERD_TIMEOUT (seconds) – gives the user a chance to shorten or lengthen
#   the probe loop; default is 30 s.

set -euo pipefail

#--------------------------------------------------------------------
# Configuration
#--------------------------------------------------------------------
DOCKERD_TIMEOUT="${DOCKERD_TIMEOUT:-30}"
IMAGES=(
    python:3.12.4
    maven:3.9.8-eclipse-temurin-17
    vespaengine/vespa
)

#--------------------------------------------------------------------
# 1. Ensure the Docker CLI is installed
#--------------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    echo "❌  Docker CLI not found in PATH." >&2
    echo "    Install Docker Desktop / Docker Engine and try again." >&2
    exit 127
fi

#--------------------------------------------------------------------
# 2. Probe the daemon
#--------------------------------------------------------------------
echo "⏳  Checking whether the Docker daemon is reachable…" >&2
deadline=$((SECONDS + DOCKERD_TIMEOUT))
until docker info --format '{{json .}}' >/dev/null 2>&1; do
    (( SECONDS >= deadline )) && {
        echo "❌  Docker daemon did not respond within ${DOCKERD_TIMEOUT}s." >&2
        echo "    Start the daemon (e.g., open Docker Desktop) and re‑run." >&2
        exit 1
    }
    sleep 1
done
echo "✅  Docker daemon is healthy." >&2

#--------------------------------------------------------------------
# 3. Pre‑pull images
#--------------------------------------------------------------------
echo "⬇️  Pulling container images…" >&2
for img in "${IMAGES[@]}"; do
    echo "   • $img" >&2
    docker pull "$img"
done
echo "🏁  All images pulled successfully." >&2
