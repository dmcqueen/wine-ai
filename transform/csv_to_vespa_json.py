#!/usr/bin/env python3
"""
csv_to_vespa_json.py
--------------------

Convert one or more CSV files of wine data to Vespa‑flavoured JSON.

"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import pathlib
import re
import sys
import unicodedata
from typing import Dict, List, Tuple

import hashlib
from sentence_transformers import SentenceTransformer


# ──────────────────────────────────────────────────────────────────────────────
# Globals & constants
# ──────────────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Store de‑duplication keys (128‑bit hashes) already seen in this run
SEEN_DESCRIPTIONS: Dict[str, bool] = {}


# ──────────────────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────────────────
def _truncate_description(description: str, max_tokens: int = 128) -> str:
    """
    Keep only the first *max_tokens* space‑separated tokens.
    """
    return " ".join(description.split(" ")[:max_tokens])


def _dedup_key(description: str, max_tokens: int = 128) -> str:
    """
    Return a **stable 32‑character hex string** that uniquely represents the
    first *max_tokens* tokens of *description*.

    Normalisation makes the hash insensitive to case, accents and
    runs of whitespace so near‑duplicates fold together.
    """
    truncated = _truncate_description(description, max_tokens)
    normalised = unicodedata.normalize("NFKC", truncated).lower()
    normalised = re.sub(r"\s+", " ", normalised).strip()

    # 128‑bit BLAKE2 → extremely low collision probability
    return hashlib.blake2b(normalised.encode("utf‑8"), digest_size=16).hexdigest()


def _progress_bar(current: int, total: int, width: int = 30) -> str:
    """Return a textual progress bar string."""
    if total <= 0:
        total = 1
    fraction = min(max(current / total, 0.0), 1.0)
    filled = int(width * fraction)
    bar = "█" * filled + "-" * (width - filled)
    percent = math.floor(fraction * 100)
    return f"[{bar}] {percent:3d}%"


def _row_to_vespa_record(row: dict) -> dict | None:
    """
    Transform a single CSV row to a Vespa 'put' record.

    The function performs:
        • Duplicate‑description filtering (hash‑based)
        • Embedding of the truncated description
        • Safe casting of numeric fields
        • Construction of the Vespa 'put' wrapper
    """
    dup_key = _dedup_key(row.get("description", ""))

    if dup_key in SEEN_DESCRIPTIONS:
        logging.debug("Skipping duplicate description (row id=%s).", row.get("id"))
        return None
    SEEN_DESCRIPTIONS[dup_key] = True

    # Create embedding from the same truncated block used for the key
    truncated_desc = _truncate_description(row.get("description", ""))
    try:
        row["description_vector"] = {"values": EMBEDDING_MODEL.encode(truncated_desc).tolist()}
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

    # Use the de‑duplication key as the Vespa document ID
    vespa_id = f"id:wine:wine::{dup_key}"
    return {"put": vespa_id, "fields": row}


def csv_file_to_json_records(csv_path: pathlib.Path) -> List[dict]:
    """
    Read *csv_path*, filter duplicates, embed descriptions in a batch and
    return a list of Vespa records.
    """
    records: List[dict] = []
    truncated_descs: List[str] = []
    pending_rows: List[Tuple[dict, str]] = []

    with csv_path.open(newline="", encoding="utf-8") as fp:
        total_rows = max(sum(1 for _ in fp) - 1, 0)

    if total_rows == 0:
        logging.info("→ 0 unique records in %s (no data).", csv_path.name)
        return records

    progress_interval = max(1, total_rows // 20)
    processed = 0

    with csv_path.open(newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            dup_key = _dedup_key(row.get("description", ""))
            if dup_key in SEEN_DESCRIPTIONS:
                logging.debug("Skipping duplicate description (row id=%s).", row.get("id"))
                continue
            SEEN_DESCRIPTIONS[dup_key] = True

            truncated_desc = _truncate_description(row.get("description", ""))
            truncated_descs.append(truncated_desc)
            pending_rows.append((row, dup_key))

            processed += 1
            if processed % progress_interval == 0 or processed == total_rows:
                logging.info("%s %s", csv_path.name, _progress_bar(processed, total_rows))

    if not pending_rows:
        logging.info("→ 0 unique records in %s (all duplicates).", csv_path.name)
        return records

    # ---- single vectorisation call ----
    vectors = EMBEDDING_MODEL.encode(
        truncated_descs,
        batch_size=32,              # tune to your GPU/CPU
        show_progress_bar=logging.getLogger().level <= logging.DEBUG,
    )

    # ---- attach vectors and finish conversion ----
    progress_interval_out = max(1, len(pending_rows) // 20)
    for idx, ((row, dup_key), vec) in enumerate(zip(pending_rows, vectors), 1):
        row["description_vector"] = {"values": vec.tolist()}

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

        vespa_id = f"id:wine:wine::{dup_key}"
        records.append({"put": vespa_id, "fields": row})

        if idx % progress_interval_out == 0 or idx == len(pending_rows):
            logging.info("%s %s", csv_path.name, _progress_bar(idx, len(pending_rows)))

    logging.info("→ %d records written from %s", len(records), csv_path.name)
    return records


def write_json(records: List[dict], output_path: pathlib.Path) -> None:
    """
    Dump *records* to *output_path* (pretty‑printed JSON).
    """
    with output_path.open("w", encoding="utf‑8") as fp:
        json.dump(records, fp, indent=4)
    logging.info("Saved %s (%d lines).", output_path.name, len(records))


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────
def parse_cli_args(argv: List[str]) -> argparse.Namespace:
    """
    Configure and parse command‑line arguments.
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
