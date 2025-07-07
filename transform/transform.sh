#!/usr/bin/env bash
set -euo pipefail

# 1. Activate (or create) a local virtual environment -------------------------
VENV_DIR=".venv"
CREATED_ENV=false
if [[ ! -d "$VENV_DIR" ]]; then
  python -m venv "$VENV_DIR"
  CREATED_ENV=true
fi
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# 2. Install dependencies only when the venv is first created ------------------
if [[ "$CREATED_ENV" == true ]]; then
  python -m pip install --upgrade pip
  python -m pip install sentence-transformers
fi

# 3. Convert every CSV safely --------------------------------------------------
shopt -s nullglob                 # empty glob ⇒ empty list, not the literal pattern
for csv in data/*.csv; do
  python transform/csv_to_vespa_json.py "$csv"
done
