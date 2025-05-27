#!/usr/bin/env bash
set -euo pipefail

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
