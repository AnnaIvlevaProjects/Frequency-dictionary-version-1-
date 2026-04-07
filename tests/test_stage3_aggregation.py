from __future__ import annotations

import csv
import json
from pathlib import Path

from freqdict_project.stats.aggregation import run_stage3_aggregation, save_stage3_outputs


def _write_stage1_docs(path: Path) -> None:
    rows = [
        {"path": "doc1.xml", "xml_exists": "True"},
        {"path": "doc2.xml", "xml_exists": "True"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "xml_exists"])
        writer.writeheader()
        writer.writerows(rows)


def _write_stage2_tokens(path: Path) -> None:
    rows = [
        {"path": "doc1.xml", "style_3": "fiction", "lemma_display": "делать", "pos_dict": "VERB"},
        {"path": "doc1.xml", "style_3": "fiction", "lemma_display": "делать", "pos_dict": "VERB"},
        {"path": "doc2.xml", "style_3": "publicistics", "lemma_display": "делать", "pos_dict": "VERB"},
        {"path": "doc2.xml", "style_3": "publicistics", "lemma_display": "дом", "pos_dict": "NOUN"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "style_3", "lemma_display", "pos_dict"])
        writer.writeheader()
        writer.writerows(rows)


def test_stage3_aggregation_and_outputs(tmp_path: Path):
    stage1_path = tmp_path / "documents_stage1.csv"
    stage2_tokens = tmp_path / "tokens_stage2.csv"
    _write_stage1_docs(stage1_path)
    _write_stage2_tokens(stage2_tokens)

    result = run_stage3_aggregation(stage2_tokens, stage1_path, segments_n=2, progress_every=0)
    assert result.report["tokens_total"] == 4
    assert result.report["documents_total"] == 2
    assert result.report["lemmas_total"] == 2

    top = result.global_rows[0]
    assert top["lemma_display"] == "делать"
    assert top["freq"] == 3
    assert top["rank"] == 1
    assert top["doc_hits"] == 2
    assert top["R"] >= 1

    save_stage3_outputs(result, tmp_path)
    assert (tmp_path / "stage3" / "lemma_stats_global.csv").exists()
    assert (tmp_path / "stage3" / "lemma_stats_style.csv").exists()
    report_path = tmp_path / "stage3" / "stage3_report.json"
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["segments_n"] == 2
