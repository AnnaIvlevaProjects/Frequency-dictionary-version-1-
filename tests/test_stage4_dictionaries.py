from __future__ import annotations

import csv
from pathlib import Path

from freqdict_project.export.dictionaries import build_stage4_dictionaries


def _write_global(path: Path) -> None:
    rows = [
        {
            "lemma_display": "делать",
            "pos_dict": "VERB",
            "freq": "30",
            "ipm": "300.0",
            "doc_hits": "2",
            "doc_percent": "100.0",
            "R": "2",
            "D": "100.0",
            "rank": "1",
        },
        {
            "lemma_display": "дом",
            "pos_dict": "NOUN",
            "freq": "20",
            "ipm": "200.0",
            "doc_hits": "2",
            "doc_percent": "100.0",
            "R": "2",
            "D": "100.0",
            "rank": "2",
        },
        {
            "lemma_display": "и",
            "pos_dict": "SERVICE",
            "freq": "10",
            "ipm": "100.0",
            "doc_hits": "2",
            "doc_percent": "100.0",
            "R": "2",
            "D": "100.0",
            "rank": "3",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_style(path: Path) -> None:
    rows = [
        {"lemma_display": "делать", "pos_dict": "VERB", "style_3": "fiction", "freq": "15", "ipm": "350.0"},
        {"lemma_display": "дом", "pos_dict": "NOUN", "style_3": "publicistics", "freq": "12", "ipm": "250.0"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_build_stage4_dictionaries(tmp_path: Path):
    global_csv = tmp_path / "lemma_stats_global.csv"
    style_csv = tmp_path / "lemma_stats_style.csv"
    _write_global(global_csv)
    _write_style(style_csv)

    result = build_stage4_dictionaries(
        global_csv,
        style_csv,
        tmp_path,
        alphabetic_limit=2,
        frequency_limit=2,
        style_limit=2,
    )

    stage4 = tmp_path / "stage4"
    assert (stage4 / "dictionary_alphabetic_50000.csv").exists()
    assert (stage4 / "dictionary_frequency_20000.csv").exists()
    assert (stage4 / "dictionary_new_lemmas.csv").exists()
    assert (stage4 / "dictionary_style_fiction.csv").exists()
    assert (stage4 / "dictionary_pos_nouns.csv").exists()
    assert (stage4 / "stage4_report.csv").exists()

    assert result.report["alphabetic_rows"] == 2
    assert result.report["frequency_rows"] == 2
