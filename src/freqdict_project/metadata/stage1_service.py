"""Stage 1 pipeline: metadata preparation and corpus filtering."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from freqdict_project.metadata.style_classifier import classify_style_3
from freqdict_project.metadata.year_parser import parse_document_year


@dataclass(slots=True)
class Stage1Result:
    documents: list[dict[str, object]]
    problem_dates: list[dict[str, object]]
    missing_xml: list[dict[str, object]]
    report: dict[str, object]


def enrich_years(rows: list[dict[str, str]], fallback_to_publ_year: bool = True) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for row in rows:
        parsed = parse_document_year(
            created=row.get("created"),
            publ_year=row.get("publ_year"),
            fallback_to_publ_year=fallback_to_publ_year,
        )
        enriched = dict(row)
        enriched["year"] = parsed.year
        enriched["year_source"] = parsed.source
        enriched["is_problem_date"] = parsed.year is None
        enriched["problem_reason"] = parsed.problem or ""
        result.append(enriched)
    return result


def filter_year_range(rows: list[dict[str, object]], year_from: int, year_to: int) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    for row in rows:
        year = row.get("year")
        if isinstance(year, int) and year_from <= year <= year_to:
            filtered.append(dict(row))
    return filtered


def add_style_3(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    with_style: list[dict[str, object]] = []
    for row in rows:
        updated = dict(row)
        updated["style_3"] = classify_style_3(str(row.get("sphere", "")))
        with_style.append(updated)
    return with_style


def _resolve_xml_path(root: Path, rel_path: str) -> Path:
    base = root / rel_path

    # If metadata path already starts with the same folder as corpus_root (e.g.
    # root=.../post1950 and rel_path=post1950/... ), avoid duplicate segment.
    parts = [p for p in rel_path.split("/") if p]
    if parts and root.name.lower() == parts[0].lower():
        alt_rel = "/".join(parts[1:])
        alt_base = root / alt_rel
    else:
        alt_base = None

    candidates = [base, Path(f"{base}.xml"), Path(f"{base}.xml.gz")]
    if alt_base is not None:
        candidates.extend([alt_base, Path(f"{alt_base}.xml"), Path(f"{alt_base}.xml.gz")])

    # If metadata points to a sibling corpus directory (e.g. rel_path starts with
    # pre1950 while root is .../post1950), try root.parent / rel_path.
    sibling_base = root.parent / rel_path if root.parent != root else None
    if sibling_base is not None:
        candidates.extend([sibling_base, Path(f"{sibling_base}.xml"), Path(f"{sibling_base}.xml.gz")])

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return base


def add_xml_paths(rows: list[dict[str, object]], corpus_root: str | Path) -> list[dict[str, object]]:
    root = Path(corpus_root)
    output: list[dict[str, object]] = []
    for row in rows:
        rel_path = str(row.get("path", "")).replace("\\", "/").strip("/")
        resolved = _resolve_xml_path(root, rel_path) if rel_path else root
        updated = dict(row)
        updated["xml_abs_path"] = str(resolved)
        updated["xml_exists"] = rel_path != "" and resolved.exists()
        updated["is_empty_path"] = rel_path == ""
        output.append(updated)
    return output


def split_problem_tables(all_rows: list[dict[str, object]], filtered_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    problem_dates = [row for row in all_rows if bool(row.get("is_problem_date"))]
    missing_xml = [row for row in filtered_rows if not bool(row.get("xml_exists"))]
    return problem_dates, missing_xml


def build_stage1_report(all_rows: list[dict[str, object]], filtered_rows: list[dict[str, object]], problem_dates: list[dict[str, object]], missing_xml: list[dict[str, object]]) -> dict[str, object]:
    by_style: dict[str, int] = {}
    for row in filtered_rows:
        style = str(row.get("style_3", ""))
        by_style[style] = by_style.get(style, 0) + 1
    return {
        "rows_total": len(all_rows),
        "rows_in_year_range": len(filtered_rows),
        "problem_dates": len(problem_dates),
        "missing_xml": len(missing_xml),
        "style_distribution": by_style,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    keys: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                keys.append(key)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def save_stage1_outputs(result: Stage1Result, output_root: str | Path) -> None:
    out = Path(output_root) / "stage1"
    out.mkdir(parents=True, exist_ok=True)
    _write_csv(out / "documents_stage1.csv", result.documents)
    _write_csv(out / "problem_dates.csv", result.problem_dates)
    _write_csv(out / "missing_xml.csv", result.missing_xml)
    (out / "stage1_report.json").write_text(
        json.dumps(result.report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
