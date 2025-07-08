#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# run.sh -- Orchestrate the full Wine‑AI demo
# -----------------------------------------------------------------------------
#  * Spins up the Vespa search engine and embedding model server
#  * Builds and deploys the Vespa application package
#  * Transforms the Wine Enthusiast CSV data to Vespa feed format
#  * Loads all documents and performs a sample search
# -----------------------------------------------------------------------------
set -euo pipefail

# ---[ Colour & formatting helpers ]-------------------------------------------
bold=$(tput bold)
cyan=$(tput setaf 6)
green=$(tput setaf 2)
yellow=$(tput setaf 3)
reset=$(tput sgr0)

step() {
    printf "\n%s%s>> %s%s\n" "$bold" "$cyan" "$1" "$reset"
}

info() {
    printf "%s%s%s\n" "$green" "$1" "$reset"
}

note() {
    printf "%s%s%s\n" "$yellow" "$1" "$reset"
}

SECONDS=0

step "Wine‑AI demo starting"
info "See README.md for a detailed overview of the architecture."

# ---[ 1. Launch Docker services ]--------------------------------------------
step "1/6 Starting Vespa and Tensor Server containers"
note "bin/deploy_servers.sh builds tensor_server and starts Vespa." \
     "Tensor Server serves embeddings via FastAPI while Vespa handles search."
bin/deploy_servers.sh

# ---[ 2. Build Vespa application ]-------------------------------------------
step "2/6 Building Vespa application with Maven"
note "Sources live in vespa_app/ with schema and ranking profiles."
bin/build_vespa_app.sh

# ---[ 3. Deploy Vespa application ]------------------------------------------
step "3/6 Deploying application to the Vespa cluster"
bin/deploy_vespa_app.sh

# ---[ 4. Transform Wine CSV data ]------------------------------------------
step "4/6 Converting CSV to Vespa JSON with embeddings"
note "transform/csv_to_vespa_json.py deduplicates rows and embeds descriptions." \
     "This may take a while for the full dataset."
bin/transform_data.sh

# ---[ 5. Feed documents into Vespa ]----------------------------------------
step "5/6 Feeding documents into Vespa"
bin/load_data.sh

# ---[ 6. Example semantic search ]-----------------------------------------
step "6/6 Performing sample vector search"
bin/search_wines.sh "goes with poultry" vector

runtime_min=$(( SECONDS / 60 ))
runtime_sec=$(( SECONDS % 60 ))
step "Wine‑AI demo finished in ${runtime_min}m ${runtime_sec}s"
