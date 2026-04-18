"""Stage 5 exports: wordforms, style dictionaries and significant vocabulary."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape

from freqdict_project.stats.likelihood import calc_ll


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


def _to_int(value: Any) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _build_style_frequency(style_rows: list[dict[str, str]], *, style_limit: int) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for style in ["fiction", "publicistics", "nonfiction_other"]:
        rows = [
            {
                "Лемма": row.get("lemma_display", ""),
                "Часть речи": row.get("pos_dict", ""),
                "Частота в подкорпусе (ipm)": _to_float(row.get("ipm", 0)),
                "freq_style": _to_int(row.get("freq", 0)),
            }
            for row in style_rows
            if row.get("style_3", "") == style
        ]
        rows.sort(key=lambda row: row["Частота в подкорпусе (ipm)"], reverse=True)
        out[style] = rows[:style_limit]
    return out


def _build_significant(
    global_rows: list[dict[str, str]],
    style_rows: list[dict[str, str]],
    *,
    significant_limit: int,
) -> dict[str, list[dict[str, Any]]]:
    global_by_key = {
        (row.get("lemma_display", ""), row.get("pos_dict", "")): row for row in global_rows
    }
    global_total = sum(_to_int(row.get("freq", 0)) for row in global_rows)

    style_totals: dict[str, int] = {}
    style_counts: dict[str, dict[tuple[str, str], int]] = {}
    for row in style_rows:
        style = row.get("style_3", "")
        key = (row.get("lemma_display", ""), row.get("pos_dict", ""))
        freq = _to_int(row.get("freq", 0))
        if style not in style_counts:
            style_counts[style] = {}
        style_counts[style][key] = freq
        style_totals[style] = style_totals.get(style, 0) + freq

    out: dict[str, list[dict[str, Any]]] = {}
    for style in ["fiction", "publicistics", "nonfiction_other"]:
        style_total = style_totals.get(style, 0)
        other_total = max(0, global_total - style_total)
        rows: list[dict[str, Any]] = []
        for key, a in style_counts.get(style, {}).items():
            global_row = global_by_key.get(key)
            if not global_row:
                continue
            global_freq = _to_int(global_row.get("freq", 0))
            b = max(0, global_freq - a)
            ll = calc_ll(a, b, style_total, other_total)
            if ll is None:
                continue
            rows.append(
                {
                    "Лемма": key[0],
                    "Часть речи": key[1],
                    "Частота в корпусе (ipm)": _to_float(global_row.get("ipm", 0)),
                    "Частота в подкорпусе (ipm)": (a / style_total * 1_000_000) if style_total > 0 else 0.0,
                    "LL-score": ll,
                }
            )
        rows.sort(key=lambda row: row["LL-score"], reverse=True)
        out[style] = rows[:significant_limit]
    return out


def _xlsx_cell(value: Any) -> str:
    if value is None:
        return "<c/>"
    if isinstance(value, (int, float)):
        return f"<c t=\"n\"><v>{value}</v></c>"
    text = escape(str(value))
    return f"<c t=\"inlineStr\"><is><t>{text}</t></is></c>"


def _write_simple_xlsx(path: Path, sheets: list[tuple[str, list[dict[str, Any]]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    content_types = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">",
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>",
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>",
        "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>",
        "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>",
    ]
    for idx in range(1, len(sheets) + 1):
        content_types.append(
            f"<Override PartName=\"/xl/worksheets/sheet{idx}.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
        )
    content_types.append("</Types>")

    rels_root = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>
</Relationships>"""

    workbook_sheets = []
    workbook_rels = []
    for idx, (name, _) in enumerate(sheets, start=1):
        safe_name = escape(name)
        workbook_sheets.append(f"<sheet name=\"{safe_name}\" sheetId=\"{idx}\" r:id=\"rId{idx}\"/>")
        workbook_rels.append(
            f"<Relationship Id=\"rId{idx}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet{idx}.xml\"/>"
        )

    workbook_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        "<sheets>"
        + "".join(workbook_sheets)
        + "</sheets></workbook>"
    )

    workbook_rels_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        + "".join(workbook_rels)
        + "</Relationships>"
    )

    styles_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">
  <fonts count=\"1\"><font><sz val=\"11\"/><name val=\"Calibri\"/></font></fonts>
  <fills count=\"1\"><fill><patternFill patternType=\"none\"/></fill></fills>
  <borders count=\"1\"><border/></borders>
  <cellStyleXfs count=\"1\"><xf/></cellStyleXfs>
  <cellXfs count=\"1\"><xf xfId=\"0\"/></cellXfs>
</styleSheet>"""

    with ZipFile(path, "w", compression=ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "".join(content_types))
        zf.writestr("_rels/.rels", rels_root)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        zf.writestr("xl/styles.xml", styles_xml)

        for idx, (_, rows) in enumerate(sheets, start=1):
            headers = list(rows[0].keys()) if rows else []
            xml_rows: list[str] = []
            if headers:
                xml_rows.append("<row>" + "".join(_xlsx_cell(h) for h in headers) + "</row>")
                for row in rows:
                    xml_rows.append("<row>" + "".join(_xlsx_cell(row.get(h, "")) for h in headers) + "</row>")
            sheet_xml = (
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
                "<sheetData>"
                + "".join(xml_rows)
                + "</sheetData></worksheet>"
            )
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml)


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


def build_stage5_exports(
    global_csv: str | Path,
    style_csv: str | Path,
    tokens_csv: str | Path,
    output_root: str | Path,
    *,
    style_limit: int = 5_000,
    significant_limit: int = 1_000,
    wordform_ipm_min: float = 5.0,
) -> Stage5Result:
    global_rows = _read_csv(global_csv)
    style_rows = _read_csv(style_csv)
    token_rows = _read_csv(tokens_csv)

    style_freq = _build_style_frequency(style_rows, style_limit=style_limit)
    significant = _build_significant(global_rows, style_rows, significant_limit=significant_limit)
    wordforms = wordforms_alphabetic_by_ipm(token_rows, ipm_min=wordform_ipm_min)

    out = Path(output_root) / "stage5"
    written: list[str] = []

    wordforms_path = out / "dictionary_wordforms_alphabetic_ipm5.csv"
    _write_csv(wordforms_path, wordforms)
    written.append(str(wordforms_path))

    style_name_map = {
        "fiction": "fiction",
        "publicistics": "publicistics",
        "nonfiction_other": "nonfiction_other",
    }
    for style, suffix in style_name_map.items():
        p = out / f"dictionary_style_{suffix}_5000.csv"
        _write_csv(p, style_freq.get(style, []))
        written.append(str(p))

    for style, suffix in style_name_map.items():
        p = out / f"dictionary_significant_{suffix}_1000.csv"
        _write_csv(p, significant.get(style, []))
        written.append(str(p))

    xlsx_path = out / "stage5_dictionaries.xlsx"
    sheets: list[tuple[str, list[dict[str, Any]]]] = [
        ("wordforms", wordforms),
        ("style_fiction", style_freq.get("fiction", [])),
        ("style_publicistics", style_freq.get("publicistics", [])),
        ("style_nonfiction", style_freq.get("nonfiction_other", [])),
        ("significant_fiction", significant.get("fiction", [])),
        ("significant_public", significant.get("publicistics", [])),
        ("significant_nonfiction", significant.get("nonfiction_other", [])),
    ]
    _write_simple_xlsx(xlsx_path, sheets)
    written.append(str(xlsx_path))

    report = {
        "global_rows": len(global_rows),
        "style_rows": len(style_rows),
        "tokens_rows": len(token_rows),
        "wordforms_rows": len(wordforms),
        "style_fiction_rows": len(style_freq.get("fiction", [])),
        "style_publicistics_rows": len(style_freq.get("publicistics", [])),
        "style_nonfiction_rows": len(style_freq.get("nonfiction_other", [])),
        "significant_fiction_rows": len(significant.get("fiction", [])),
        "significant_publicistics_rows": len(significant.get("publicistics", [])),
        "significant_nonfiction_rows": len(significant.get("nonfiction_other", [])),
        "style_limit": style_limit,
        "significant_limit": significant_limit,
        "wordform_ipm_min": wordform_ipm_min,
        "files_written": len(written),
    }

    report_path = out / "stage5_report.csv"
    _write_csv(report_path, [report])
    written.append(str(report_path))

    return Stage5Result(files_written=written, report=report)
