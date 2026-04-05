from __future__ import annotations

from pathlib import Path

from freqdict_project.metadata.loader import load_metadata_csv, validate_required_columns


def test_load_metadata_semicolon_and_header_case(tmp_path: Path):
    csv_path = tmp_path / "source.csv"
    csv_path.write_text(
        "PATH;CREATED;PUBL_YEAR;SPHERE;STYLE;MEDIUM;SUBCORPUS\n"
        "docs/a.xml;2010|2011;;художественная;;print;main\n",
        encoding="utf-8",
    )

    rows, fieldnames = load_metadata_csv(csv_path)
    validate_required_columns(fieldnames)

    assert fieldnames[0] == "path"
    assert rows[0]["path"] == "docs/a.xml"
    assert rows[0]["created"] == "2010|2011"
