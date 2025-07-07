#!/usr/bin/env bash
# search-wine.sh
# Usage: ./search-wine.sh "pinot noir red" default|default_2|vector

set -euo pipefail  # fail fast on any error, unset var, or pipe failure

# ──────────────────────────────────
# 1. Argument parsing & sanity check
# ──────────────────────────────────
if (( $# != 2 )); then
  echo "Usage: $0 \"SEARCH TERMS\" RANKING_MODE (default|default_2|vector)" >&2
  exit 1
fi

QUERY=$1          # free‑text search phrase
RANK_MODE=$2      # default | default_2 | vector

SEARCH_ENDPOINT="http://localhost:8080/search/"
EMBED_ENDPOINT="http://localhost:8088/"

# ──────────────────────────────────
# 2. Helper functions
# ──────────────────────────────────
build_default_payload() {
  local IFS=' '                      # split on spaces only
  local words=($QUERY)
  local cond=""

  for w in "${words[@]}"; do
    cond+="description contains \\\"$w\\\" or "
  done
  cond=${cond%" or "}                # ← portable trim

  cat <<JSON
{
  "yql": "select id,winery,variety,description \
           from wine where $cond limit 10 offset 0;",
  "ranking": "$RANK_MODE"
}
JSON
}

build_vector_payload() {
  # Generate embedding
  local vector
  vector=$(curl -sS \
            -H "Content-Type: application/json" \
            --data "$(jq -nc --arg t "$QUERY" '{text:$t}')" \
            "$EMBED_ENDPOINT" | jq -r '."paraphrase-MiniLM-L6-v2"')

  cat <<JSON
{
  "yql": "select id,winery,variety,description from wine where ([{\\"targetHits\\":1000}]nearestNeighbor(description_vector, query_vector)) limit 10 offset 0;",
  "input.query(query_vector)": "$vector",
  "ranking": "vector"
}
JSON
}

# ──────────────────────────────────
# 3. Build request payload
# ──────────────────────────────────
case "$RANK_MODE" in
  default|default_2)  PAYLOAD=$(build_default_payload) ;;
  vector)             PAYLOAD=$(build_vector_payload)  ;;
  *)
    echo "Invalid ranking mode: $RANK_MODE" >&2
    exit 2
    ;;
esac

# ──────────────────────────────────
# 4. Execute search & pretty‑print
# ──────────────────────────────────
# 4. Execute search & pretty‑print
curl -sS -H "Content-Type: application/json" \
     --data "$PAYLOAD" \
     "$SEARCH_ENDPOINT" | jq '
       # Collect every hit’s “fields” object into one JSON array
       (.root.children[]?.fields | [.winery, .variety, .description]) 
     '

