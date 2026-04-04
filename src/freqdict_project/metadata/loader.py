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


def _open_with_fallback(path: Path) -> tuple[str, str]:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError("Failed to read metadata CSV")


def _detect_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        class _Fallback(csv.Dialect):
            delimiter = ","
            quotechar = '"'
            doublequote = True
            skipinitialspace = False
            lineterminator = "\n"
            quoting = csv.QUOTE_MINIMAL

        return _Fallback


def load_metadata_csv(metadata_csv: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    path = Path(metadata_csv)
    content, _ = _open_with_fallback(path)
    sample = content[:4096] or "path,created,publ_year,sphere,style,medium,subcorpus\n"
    dialect = _detect_dialect(sample)

    reader = csv.DictReader(content.splitlines(), dialect=dialect)
    fieldnames = [name.strip().lower() for name in (reader.fieldnames or [])]

    rows: list[dict[str, str]] = []
    for row in reader:
        rows.append({str(k).strip().lower(): v for k, v in row.items() if k is not None})
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
