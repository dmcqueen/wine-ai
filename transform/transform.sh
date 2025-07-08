#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# transform.sh -- Convert Kaggle wine CSVs to Vespa JSON with rich progress
# ---------------------------------------------------------------------------

# ---[ Colour & formatting helpers ]-----------------------------------------
bold=$(tput bold)
cyan=$(tput setaf 6)
green=$(tput setaf 2)
yellow=$(tput setaf 3)
red=$(tput setaf 1)
reset=$(tput sgr0)

step() {
    printf "\n%s%s>> %s%s\n" "$bold" "$cyan" "$1" "$reset"
}

info() {
    printf "%s%s%s\n" "$green" "$1" "$reset"
}

warn() {
    printf "%s%s%s\n" "$yellow" "$1" "$reset"
}

error() {
    printf "%s%s%s\n" "$red" "$1" "$reset"
}

SECONDS=0

cleanup() {
    local exit_code=$?
    local runtime_min=$(( SECONDS / 60 ))
    local runtime_sec=$(( SECONDS % 60 ))
    if (( exit_code == 0 )); then
        step "Transformation finished in ${runtime_min}m ${runtime_sec}s"
    else
        error "Aborted after ${runtime_min}m ${runtime_sec}s (exit code ${exit_code})"
    fi
}
trap cleanup EXIT

# ---[ 1. Activate (or create) the Python virtual environment ]---------------
step "Preparing Python environment"
VENV_DIR=".venv"
CREATED_ENV=false
if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtual environment at $VENV_DIR"
    python -m venv "$VENV_DIR"
    CREATED_ENV=true
else
    info "Using existing virtual environment at $VENV_DIR"
fi
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# ---[ 2. Install dependencies (only first run) ]-----------------------------
step "Installing Python dependencies"
if [[ "$CREATED_ENV" == true ]]; then
    python -m pip install --upgrade pip
    python -m pip install sentence-transformers
else
    info "Dependencies already installed – skipping"
fi

# ---[ 3. Convert every CSV in data/ ]---------------------------------------
shopt -s nullglob
csv_files=(data/*.csv)
if (( ${#csv_files[@]} == 0 )); then
    warn "No CSV files found in data/"
else
    for csv in "${csv_files[@]}"; do
        step "Processing $(basename "$csv")"
        python transform/csv_to_vespa_json.py "$csv"
    done
fi

