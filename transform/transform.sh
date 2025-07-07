#!/usr/bin/env bash
set -euo pipefail

# 1. Activate (or create) a local virtual environment -------------------------
VENV_DIR=".venv"
if [[ ! -d "$VENV_DIR" ]]; then
  python -m venv "$VENV_DIR"
fi
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# 2. Keep tools up to date, but inside the venv --------------------------------
python -m pip install --upgrade pip sentence-transformers

# 3. Convert every CSV safely --------------------------------------------------
shopt -s nullglob                 # empty glob ⇒ empty list, not the literal pattern
for csv in data/*.csv; do
  python transform/csv_to_vespa_json.py "$csv"
done
