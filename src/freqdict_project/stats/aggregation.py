"""Stage 3 aggregation utilities: lemma-level statistics from Stage 2 tokens."""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from freqdict_project.stats.frequencies import calc_doc_percent, calc_ipm
from freqdict_project.stats.range_dispersion import calc_d, calc_r
from freqdict_project.stats.segmentation import assign_segments


@dataclass(slots=True)
class Stage3Result:
    global_rows: list[dict[str, Any]]
    style_rows: list[dict[str, Any]]
    report: dict[str, Any]


def _print_progress(stage: str, processed: int, started_at: float, every: int) -> None:
    if every <= 0 or processed <= 0 or processed % every != 0:
        return
    elapsed = time.time() - started_at
    speed = processed / elapsed if elapsed > 0 else 0.0
    print(f"[{stage}] processed={processed:,} rows | {speed:,.0f} rows/s", flush=True)


def _token_key(row: dict[str, str]) -> tuple[str, str]:
    return row.get("lemma_display", ""), row.get("pos_dict", "")


def _load_stage1_doc_order(path: str | Path) -> list[str]:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        ordered_paths: list[str] = []
        for row in reader:
            xml_exists = str(row.get("xml_exists", "")).strip().lower() in {"1", "true", "yes"}
            if xml_exists:
                ordered_paths.append(row.get("path", ""))
    return ordered_paths


def run_stage3_aggregation(
    tokens_csv: str | Path,
    stage1_documents_csv: str | Path,
    *,
    segments_n: int = 100,
    progress_every: int = 500_000,
) -> Stage3Result:
    tokens_path = Path(tokens_csv)
    started_pass1 = time.time()

    global_freq: dict[tuple[str, str], int] = {}
    key_doc_hits: dict[tuple[str, str], set[str]] = {}
    style_freq: dict[tuple[str, str, str], int] = {}
    style_totals: dict[str, int] = {}
    doc_token_counts: dict[str, int] = {}
    token_rows_count = 0

    with tokens_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            token_rows_count += 1
            _print_progress("Stage3-pass1", token_rows_count, started_pass1, progress_every)

            key = _token_key(row)
            doc_path = row.get("path", "")
            style = row.get("style_3", "")

            global_freq[key] = global_freq.get(key, 0) + 1
            doc_token_counts[doc_path] = doc_token_counts.get(doc_path, 0) + 1

            if key not in key_doc_hits:
                key_doc_hits[key] = set()
            key_doc_hits[key].add(doc_path)

            style_key = (key[0], key[1], style)
            style_freq[style_key] = style_freq.get(style_key, 0) + 1
            style_totals[style] = style_totals.get(style, 0) + 1

    total_tokens = sum(global_freq.values())
    total_docs = len(doc_token_counts)

    doc_order_stage1 = _load_stage1_doc_order(stage1_documents_csv)
    doc_order = [path for path in doc_order_stage1 if path in doc_token_counts]
    doc_counts = [doc_token_counts[path] for path in doc_order]
    segment_ids = assign_segments(doc_counts, segments_n=segments_n)
    doc_to_segment = {path: seg for path, seg in zip(doc_order, segment_ids)}

    started_pass2 = time.time()
    lemma_segment_counts: dict[tuple[str, str], dict[int, int]] = {}
    token_rows_count_pass2 = 0

    with tokens_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            token_rows_count_pass2 += 1
            _print_progress("Stage3-pass2", token_rows_count_pass2, started_pass2, progress_every)

            key = _token_key(row)
            doc_path = row.get("path", "")
            segment = doc_to_segment.get(doc_path)
            if segment is None:
                continue
            if key not in lemma_segment_counts:
                lemma_segment_counts[key] = {}
            lemma_segment_counts[key][segment] = lemma_segment_counts[key].get(segment, 0) + 1

    global_rows: list[dict[str, Any]] = []
    for key, freq in global_freq.items():
        segment_map = lemma_segment_counts.get(key, {})
        segment_freqs = [segment_map.get(i, 0) for i in range(segments_n)]
        doc_hits = len(key_doc_hits.get(key, set()))
        global_rows.append(
            {
                "lemma_display": key[0],
                "pos_dict": key[1],
                "freq": freq,
                "ipm": calc_ipm(freq, total_tokens),
                "doc_hits": doc_hits,
                "doc_percent": calc_doc_percent(doc_hits, total_docs),
                "R": calc_r(segment_freqs),
                "D": calc_d(segment_freqs),
            }
        )

    global_rows.sort(key=lambda row: row["ipm"], reverse=True)
    for index, row in enumerate(global_rows, start=1):
        row["rank"] = index

    style_rows: list[dict[str, Any]] = []
    for (lemma_display, pos_dict, style), freq in style_freq.items():
        style_total = style_totals.get(style, 0)
        style_rows.append(
            {
                "lemma_display": lemma_display,
                "pos_dict": pos_dict,
                "style_3": style,
                "freq": freq,
                "ipm": calc_ipm(freq, style_total),
            }
        )
    style_rows.sort(key=lambda row: (row["style_3"], -row["ipm"]))

    report = {
        "tokens_total": total_tokens,
        "documents_total": total_docs,
        "lemmas_total": len(global_rows),
        "styles_total": len(style_totals),
        "segments_n": segments_n,
    }
    return Stage3Result(global_rows=global_rows, style_rows=style_rows, report=report)


def save_stage3_outputs(result: Stage3Result, output_root: str | Path) -> None:
    out = Path(output_root) / "stage3"
    out.mkdir(parents=True, exist_ok=True)

    def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        fieldnames = list(rows[0].keys())
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    write_csv(out / "lemma_stats_global.csv", result.global_rows)
    write_csv(out / "lemma_stats_style.csv", result.style_rows)
    (out / "stage3_report.json").write_text(
        json.dumps(result.report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
