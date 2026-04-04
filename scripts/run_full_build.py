"""Entry point for full corpus processing."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

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
from freqdict_project.utils.settings import load_settings


def main() -> None:
    settings = load_settings(ROOT / "config" / "settings.yaml")

    try:
        rows, columns = load_metadata_csv(settings["paths"]["metadata_csv"])
    except FileNotFoundError as exc:
        raise SystemExit(f"Metadata file not found: {exc.filename}") from exc
    validate_required_columns(columns)

    rows = normalize_metadata_fields(rows)
    rows_years = enrich_years(rows, fallback_to_publ_year=True)

    rows_filtered = filter_year_range(
        rows_years,
        year_from=settings["corpus"]["year_from"],
        year_to=settings["corpus"]["year_to"],
    )
    rows_filtered = add_style_3(rows_filtered)
    rows_filtered = add_xml_paths(rows_filtered, settings["paths"]["corpus_root"])

    problem_dates, missing_xml = split_problem_tables(rows_years, rows_filtered)
    report = build_stage1_report(rows_years, rows_filtered, problem_dates, missing_xml)

    result = Stage1Result(
        documents=rows_filtered,
        problem_dates=problem_dates,
        missing_xml=missing_xml,
        report=report,
    )
    save_stage1_outputs(result, settings["paths"]["output_root"])

    print("Stage 1 complete")
    print(report)


if __name__ == "__main__":
    main()
