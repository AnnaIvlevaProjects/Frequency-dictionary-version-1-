"""Stage 5: wordform dictionaries without morphological consensus."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Stage5Result:
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


def capitalization_variant(surface: str) -> str:
    for ch in surface:
        if ch.isalpha():
            return "higher" if ch.isupper() else "lower"
    return "lower"


def wordforms_alphabetic_by_ipm(tokens_rows: list[dict[str, str]], *, ipm_min: float) -> list[dict[str, Any]]:
    normalized: list[tuple[str, str]] = []
    for row in tokens_rows:
        surface = str(row.get("surface", "")).strip()
        if not surface:
            continue
        if not any(ch.isalpha() for ch in surface):
            continue
        capitalization = capitalization_variant(surface)
        normalized.append((surface, capitalization))

    total = len(normalized)
    if total <= 0:
        return []

    counts: Counter[tuple[str, str]] = Counter(normalized)
    out: list[dict[str, Any]] = []
    for (surface, capitalization), count in counts.items():
        ipm = (count / total) * 1_000_000
        if ipm < ipm_min:
            continue
        out.append(
            {
                "Словоформа": surface,
                "Частота (ipm)": round(ipm, 6),
                "Капитализация": capitalization,
            }
        )

    out.sort(key=lambda row: (str(row["Словоформа"]).lower(), str(row["Капитализация"])))
    return out


def build_stage5_wordforms(tokens_csv: str | Path, output_root: str | Path, *, ipm_min: float = 5.0) -> Stage5Result:
    tokens_rows = _read_csv(tokens_csv)
    wordforms = wordforms_alphabetic_by_ipm(tokens_rows, ipm_min=ipm_min)

    out = Path(output_root) / "stage5"
    dictionary_path = out / "dictionary_wordforms_alphabetic_ipm5.csv"
    report_path = out / "stage5_report.csv"
    _write_csv(dictionary_path, wordforms)
    _write_csv(
        report_path,
        [
            {
                "source_tokens_rows": len(tokens_rows),
                "wordforms_rows": len(wordforms),
                "wordform_ipm_min": ipm_min,
            }
        ],
    )

    return Stage5Result(
        files_written=[str(dictionary_path), str(report_path)],
        report={
            "source_tokens_rows": len(tokens_rows),
            "wordforms_rows": len(wordforms),
            "wordform_ipm_min": ipm_min,
            "files_written": 2,
        },
    )
