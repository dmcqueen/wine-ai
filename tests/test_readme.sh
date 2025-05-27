#!/usr/bin/env bash
set -euo pipefail

# Ensure Docker is available. Attempt to start it using the repo's init script
# if `docker info` fails. Fail the test if Docker still isn't available so that
# README steps always execute when possible.
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if ! docker info >/dev/null 2>&1; then
    if [ -x "$REPO_DIR/codex/init.sh" ]; then
        bash "$REPO_DIR/codex/init.sh" || true
    fi
    if ! docker info >/dev/null 2>&1; then
        echo "Docker daemon not available; failing README integration test." >&2
        exit 1
    fi
fi

# Integration test that follows the README instructions
# Start Vespa and model servers using Docker
bin/deploy_servers.sh

# Clean up containers on exit
cleanup() {
    docker rm -f vespa models >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Wait for Vespa container to report ApplicationStatus
timeout 120 bash -c 'until curl -s --head http://localhost:19071/ApplicationStatus | grep "200 OK"; do sleep 2; done'

# Build and deploy the Vespa application
bin/build_vespa_app.sh

# Wait for application to be available
timeout 120 bash -c 'until curl -s --head http://localhost:8080/ApplicationStatus | grep "200 OK"; do sleep 2; done'

# Transform the wine review data
bin/transform_data.sh

# Load the transformed documents
bin/load_data.sh

# Run the sample query from the README
bin/get_wines.sh "goes with asian food"
