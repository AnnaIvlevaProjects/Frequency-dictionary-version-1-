from __future__ import annotations

import csv
from pathlib import Path

from freqdict_project.export.wordforms import build_stage5_exports, build_stage5_wordforms


def _write_stage2_tokens(path: Path) -> None:
    rows = [
        {"surface": "Дом"},
        {"surface": "дом"},
        {"surface": "дом"},
        {"surface": "в"},
        {"surface": ","},
        {"surface": "Дом"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["surface"])
        writer.writeheader()
        writer.writerows(rows)


def test_build_stage5_wordforms(tmp_path: Path):
    tokens_csv = tmp_path / "tokens_stage2.csv"
    _write_stage2_tokens(tokens_csv)

    result = build_stage5_wordforms(tokens_csv, tmp_path, ipm_min=5.0)
    stage5 = tmp_path / "stage5"

    assert (stage5 / "dictionary_wordforms_alphabetic_ipm5.csv").exists()
    assert (stage5 / "stage5_report.csv").exists()
    assert result.report["wordforms_rows"] == 3

    with (stage5 / "dictionary_wordforms_alphabetic_ipm5.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]

    assert rows == [
        {"Словоформа": "в", "Частота (ipm)": "200000.0", "Капитализация": "lower"},
        {"Словоформа": "Дом", "Частота (ipm)": "400000.0", "Капитализация": "higher"},
        {"Словоформа": "дом", "Частота (ipm)": "400000.0", "Капитализация": "lower"},
    ]


def _write_global(path: Path) -> None:
    rows = [
        {"lemma_display": "дом", "pos_dict": "NOUN", "freq": "50", "ipm": "500.0"},
        {"lemma_display": "газета", "pos_dict": "NOUN", "freq": "20", "ipm": "200.0"},
        {"lemma_display": "роман", "pos_dict": "NOUN", "freq": "30", "ipm": "300.0"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_style(path: Path) -> None:
    rows = [
        {"lemma_display": "дом", "pos_dict": "NOUN", "style_3": "fiction", "freq": "25", "ipm": "600.0"},
        {"lemma_display": "газета", "pos_dict": "NOUN", "style_3": "publicistics", "freq": "15", "ipm": "500.0"},
        {"lemma_display": "роман", "pos_dict": "NOUN", "style_3": "nonfiction_other", "freq": "5", "ipm": "120.0"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_build_stage5_exports(tmp_path: Path):
    tokens_csv = tmp_path / "tokens_stage2.csv"
    global_csv = tmp_path / "lemma_stats_global.csv"
    style_csv = tmp_path / "lemma_stats_style.csv"

    _write_stage2_tokens(tokens_csv)
    _write_global(global_csv)
    _write_style(style_csv)

    result = build_stage5_exports(
        global_csv,
        style_csv,
        tokens_csv,
        tmp_path,
        style_limit=5,
        significant_limit=5,
        wordform_ipm_min=5.0,
    )

    stage5 = tmp_path / "stage5"
    assert (stage5 / "dictionary_style_fiction_5000.csv").exists()
    assert (stage5 / "dictionary_significant_fiction_1000.csv").exists()
    assert (stage5 / "dictionary_wordforms_alphabetic_ipm5.csv").exists()
    assert (stage5 / "stage5_dictionaries.xlsx").exists()
    assert (stage5 / "stage5_report.csv").exists()
    assert result.report["files_written"] >= 8
