"""Metadata loading and normalization utilities for Stage 1."""

from __future__ import annotations

import csv
from pathlib import Path

REQUIRED_COLUMNS = {
    "path",
    "created",
    "publ_year",
    "sphere",
    "style",
    "medium",
    "subcorpus",
}


def load_metadata_csv(metadata_csv: str | Path, encoding: str = "utf-8") -> tuple[list[dict[str, str]], list[str]]:
    path = Path(metadata_csv)
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return rows, fieldnames


def validate_required_columns(fieldnames: list[str]) -> None:
    missing = sorted(REQUIRED_COLUMNS.difference(set(fieldnames)))
    if missing:
        raise ValueError(f"Metadata CSV is missing required columns: {', '.join(missing)}")


def normalize_metadata_fields(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in rows:
        clean_row: dict[str, str] = {}
        for key, value in row.items():
            text = "" if value is None else str(value).strip()
            clean_row[key] = "" if text.lower() in {"nan", "none", "null"} else text
        normalized.append(clean_row)
    return normalized
