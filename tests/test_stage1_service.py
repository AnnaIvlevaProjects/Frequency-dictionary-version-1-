from __future__ import annotations

import csv
import json
from pathlib import Path

from freqdict_project.metadata.loader import load_metadata_csv, normalize_metadata_fields, validate_required_columns
from freqdict_project.metadata.stage1_service import (
    Stage1Result,
    add_style_3,
    add_xml_paths,
    build_stage1_report,
    enrich_years,
    filter_year_range,
    save_stage1_outputs,
    split_problem_tables,
)


def _write_metadata_csv(path: Path) -> None:
    rows = [
        {
            "path": "a.xml",
            "created": "2010|2011",
            "publ_year": "",
            "sphere": "художественная",
            "style": "",
            "medium": "print",
            "subcorpus": "main",
        },
        {
            "path": "b.xml",
            "created": "invalid",
            "publ_year": "2009",
            "sphere": "публицистика",
            "style": "",
            "medium": "web",
            "subcorpus": "main",
        },
        {
            "path": "",
            "created": "invalid",
            "publ_year": "",
            "sphere": "наука",
            "style": "",
            "medium": "web",
            "subcorpus": "main",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_loader_and_stage1_pipeline(tmp_path: Path):
    metadata_csv = tmp_path / "source.csv"
    _write_metadata_csv(metadata_csv)

    rows, columns = load_metadata_csv(metadata_csv)
    validate_required_columns(columns)
    rows = normalize_metadata_fields(rows)

    rows_years = enrich_years(rows)
    rows_filtered = filter_year_range(rows_years, 2008, 2022)
    rows_filtered = add_style_3(rows_filtered)

    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    (corpus_root / "a.xml").write_text("<doc/>", encoding="utf-8")

    rows_filtered = add_xml_paths(rows_filtered, corpus_root)
    problem_dates, missing_xml = split_problem_tables(rows_years, rows_filtered)
    report = build_stage1_report(rows_years, rows_filtered, problem_dates, missing_xml)

    assert len(rows_years) == 3
    assert len(rows_filtered) == 2
    assert any(r["style_3"] == "fiction" for r in rows_filtered)
    assert any(r["style_3"] == "publicistics" for r in rows_filtered)
    assert len(problem_dates) == 1
    assert len(missing_xml) == 1
    assert report["rows_total"] == 3
    assert report["rows_in_year_range"] == 2

    result = Stage1Result(
        documents=rows_filtered,
        problem_dates=problem_dates,
        missing_xml=missing_xml,
        report=report,
    )
    out_root = tmp_path / "output"
    save_stage1_outputs(result, out_root)

    assert (out_root / "stage1" / "documents_stage1.csv").exists()
    assert (out_root / "stage1" / "problem_dates.csv").exists()
    assert (out_root / "stage1" / "missing_xml.csv").exists()
    report_path = out_root / "stage1" / "stage1_report.json"
    assert report_path.exists()

    parsed_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert parsed_report["style_distribution"]["fiction"] == 1


def test_add_xml_paths_resolves_extensionless_metadata_path(tmp_path: Path):
    rows = [{"path": "post1950/archive/doc1"}]
    target = tmp_path / "post1950" / "archive"
    target.mkdir(parents=True)
    (target / "doc1.xml").write_text("<doc/>", encoding="utf-8")

    enriched = add_xml_paths(rows, tmp_path)
    assert enriched[0]["xml_exists"] is True
    assert str(enriched[0]["xml_abs_path"]).endswith("doc1.xml")
