"""Stage 4 dictionary builders from Stage 3 aggregates."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Stage4Result:
    files_written: list[str]
    report: dict[str, Any]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _global_ranked(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: _to_int(row.get("rank", "0")))


def _global_by_freq(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: _to_float(row.get("ipm", "0")), reverse=True)


def _sort_alpha(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (str(row.get("lemma_display", "")).lower(), str(row.get("pos_dict", ""))))


def build_stage4_dictionaries(
    global_csv: str | Path,
    style_csv: str | Path,
    output_root: str | Path,
    *,
    alphabetic_limit: int = 50_000,
    frequency_limit: int = 20_000,
    style_limit: int = 5_000,
) -> Stage4Result:
    global_rows = _read_csv(global_csv)
    style_rows = _read_csv(style_csv)

    ranked = _global_ranked(global_rows)
    by_freq = _global_by_freq(global_rows)

    top_alphabetic_source = ranked[:alphabetic_limit]
    alphabetic = _sort_alpha(top_alphabetic_source)
    frequency = by_freq[:frequency_limit]

    top_key_set = {(row["lemma_display"], row["pos_dict"]) for row in top_alphabetic_source}
    new_lemmas = _sort_alpha([row for row in ranked if (row["lemma_display"], row["pos_dict"]) not in top_key_set])

    styles = ["fiction", "publicistics", "nonfiction_other"]
    style_files: dict[str, list[dict[str, str]]] = {}
    for style in styles:
        filtered = [row for row in style_rows if row.get("style_3") == style]
        filtered.sort(key=lambda row: _to_float(row.get("ipm", "0")), reverse=True)
        style_files[style] = filtered[:style_limit]

    pos_groups = {
        "nouns": ["NOUN"],
        "verbs": ["VERB", "PARTICIPLE"],
        "adjectives": ["ADJ"],
        "adverbs": ["ADV"],
        "pronouns": ["PRON"],
        "numerals": ["NUM"],
        "service": ["SERVICE"],
        "propn_abbrev": ["PROPN_ABBREV"],
    }
    pos_files: dict[str, list[dict[str, str]]] = {}
    for group, values in pos_groups.items():
        filtered = [row for row in by_freq if row.get("pos_dict") in values]
        pos_files[group] = filtered[:1000]

    out = Path(output_root) / "stage4"
    written: list[str] = []

    main_files = {
        "dictionary_alphabetic_50000.csv": alphabetic,
        "dictionary_frequency_20000.csv": frequency,
        "dictionary_new_lemmas.csv": new_lemmas,
    }
    for filename, rows in main_files.items():
        path = out / filename
        _write_csv(path, rows)
        written.append(str(path))

    for style, rows in style_files.items():
        path = out / f"dictionary_style_{style}.csv"
        _write_csv(path, rows)
        written.append(str(path))

    for group, rows in pos_files.items():
        path = out / f"dictionary_pos_{group}.csv"
        _write_csv(path, rows)
        written.append(str(path))

    report = {
        "global_rows": len(global_rows),
        "style_rows": len(style_rows),
        "alphabetic_rows": len(alphabetic),
        "frequency_rows": len(frequency),
        "new_lemmas_rows": len(new_lemmas),
        "files_written": len(written),
    }
    _write_csv(out / "stage4_report.csv", [report])
    written.append(str(out / "stage4_report.csv"))

    return Stage4Result(files_written=written, report=report)
