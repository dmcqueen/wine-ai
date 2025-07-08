#!/bin/bash
# This script sets up and runs the Wine AI application using Vespa and Docker.
# Ensure the script is run from the root directory of the project
set -e

# Launch Vespa & model‑server containers
bin/deploy_servers.sh

# Build Vespa application
bin/build_vespa_app.sh

# Deploy Vespa application
bin/deploy_vespa_app.sh

# Transform CSV → Vespa JSON with embeddings
bin/transform_data.sh

# Feed documents into Vespa
bin/load_data.sh

# Search for wines that go with poultry using the vector search
bin/search_wines.sh "goes with poultry" vector