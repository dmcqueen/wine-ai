#!/usr/bin/env python3
"""
csv_to_vespa_json.py
--------------------

Convert one or more CSV files of wine data to Vespa‑flavoured JSON.

Enhancements over the minimalist original:
    •  Clearer function and variable names
    •  Rich doc‑strings
    •  `argparse` for a friendlier CLI
    •  Basic logging of progress and errors
    •  Type hints for static analysis
    •  Graceful handling of missing or malformed rows
    •  Duplicate‑description detection limited to the
       first 128 tokens, mirroring the original intent
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import pathlib
import sys
from typing import Dict, List

from sentence_transformers import SentenceTransformer


# ──────────────────────────────────────────────────────────────────────────────
# Globals & constants
# ──────────────────────────────────────────────────────────────────────────────
# A single Sentence‑BERT model instance is reasonably heavy; load only once.
EMBEDDING_MODEL = SentenceTransformer("paraphrase-MiniLM-L6-v2")

# Store descriptions we have already ingested (keyed by 128‑token hash)
SEEN_DESCRIPTIONS: Dict[int, bool] = {}


# ──────────────────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────────────────
def _truncate_description(description: str, max_tokens: int = 128) -> str:
    """
    Keep only the first *max_tokens* space‑separated tokens.

    Parameters
    ----------
    description : str
        Full text description from the CSV row.
    max_tokens : int, optional
        Token limit (default is 128).

    Returns
    -------
    str
        Truncated description.
    """
    return " ".join(description.split(" ")[:max_tokens])


def _row_to_vespa_record(row: dict) -> dict | None:
    """
    Transform a single CSV row to a Vespa 'put' record.

    The function performs:
        •  Duplicate‑description filtering
        •  Embedding of the truncated description
        •  Safe casting of numeric fields
        •  Construction of the Vespa 'put' wrapper

    Returns
    -------
    dict | None
        Vespa record ready for JSON output, or None if the row was skipped.
    """
    truncated_desc = _truncate_description(row.get("description", ""))

    # Deduplicate by hash of the truncated description
    duplicate_key = hash(truncated_desc)
    if duplicate_key in SEEN_DESCRIPTIONS:
        logging.debug("Skipping duplicate description (row id=%s).", row.get("id"))
        return None
    SEEN_DESCRIPTIONS[duplicate_key] = True

    # Embed description
    try:
        row["desc_vector"] = {"values": EMBEDDING_MODEL.encode(truncated_desc).tolist()}
    except Exception as exc:
        logging.error("Failed to embed description for id=%s – %s", row.get("id"), exc)
        return None

    # Parse numeric fields with fallbacks
    for numeric_field, caster in [("price", float), ("points", int)]:
        raw_value = row.get(numeric_field, "")
        try:
            row[numeric_field] = caster(raw_value) if raw_value else caster(0)
        except ValueError:
            logging.warning(
                "Invalid %s '%s' for id=%s – replacing with 0",
                numeric_field,
                raw_value,
                row.get("id"),
            )
            row[numeric_field] = caster(0)

    # Wrap in Vespa 'put' directive
    vespa_id = f"id:wine:wine::{row.get('id', 'MISSING')}"
    return {"put": vespa_id, "fields": row}


def csv_file_to_json_records(csv_path: pathlib.Path) -> List[dict]:
    records: List[dict] = []
    truncated_descs: list[str] = []
    pending_rows: list[dict] = []

    with csv_path.open(newline="", encoding="utf‑8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            truncated = _truncate_description(row.get("description", ""))
            if hash(truncated) in SEEN_DESCRIPTIONS:
                logging.debug("Skipping duplicate description (row id=%s).", row.get("id"))
                continue
            SEEN_DESCRIPTIONS[hash(truncated)] = True

            truncated_descs.append(truncated)
            pending_rows.append(row)

    # ---- single vectorisation call ----
    vectors = EMBEDDING_MODEL.encode(
        truncated_descs,
        batch_size=32,              # tune to your GPU/CPU
        show_progress_bar= logging.getLogger().level <= logging.DEBUG
    )

    # ---- attach vectors and finish conversion ----
    for row, vec in zip(pending_rows, vectors):
        row["desc_vector"] = {"values": vec.tolist()}
        vespa_id = f"id:wine:wine::{row.get('id', 'MISSING')}"
        records.append({"put": vespa_id, "fields": row})

    logging.info("→ %d records written from %s", len(records), csv_path.name)
    return records


def write_json(records: List[dict], output_path: pathlib.Path) -> None:
    """
    Dump *records* to *output_path* (pretty‑printed JSON).

    Parameters
    ----------
    records : List[dict]
        The Vespa records to serialise.
    output_path : pathlib.Path
        Destination *.json file.
    """
    with output_path.open("w", encoding="utf‑8") as fp:
        json.dump(records, fp, indent=4)
    logging.info("Saved %s (%d lines).", output_path.name, len(records))


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────
def parse_cli_args(argv: List[str]) -> argparse.Namespace:
    """
    Set up and parse command‑line arguments.

    You can pass one or more space‑separated CSV paths, e.g.
        python csv_to_vespa_json.py wines1.csv wines2.csv
    """
    parser = argparse.ArgumentParser(
        description="Convert wine CSV files to Vespa JSON format."
    )
    parser.add_argument(
        "csv_files",
        nargs="+",
        type=pathlib.Path,
        help="One or more CSV files to convert.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug‑level logging.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    """
    Orchestrate CLI parsing, file conversion, and JSON writing.
    """
    args = parse_cli_args(argv or sys.argv[1:])

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    for csv_path in args.csv_files:
        if not csv_path.is_file():
            logging.error("✗ %s is not a readable file – skipping.", csv_path)
            continue

        try:
            json_records = csv_file_to_json_records(csv_path)
            output_path = csv_path.with_suffix(".json")
            write_json(json_records, output_path)
        except Exception as exc:  # Catch‑all so one bad file does not stop the run
            logging.exception("Unexpected failure while processing %s – %s", csv_path, exc)


if __name__ == "__main__":
    main()
