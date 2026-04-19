from __future__ import annotations

import csv
from pathlib import Path

from freqdict_project.export.wordforms import build_stage5_wordforms


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
