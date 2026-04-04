"""Stage 2 pipeline: XML text -> Stanza tokens -> normalized token rows."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from freqdict_project.corpus.xml_reader import extract_clean_text
from freqdict_project.nlp.morph_postprocess import process_token


@dataclass(slots=True)
class Stage2Result:
    tokens: list[dict[str, Any]]
    report: dict[str, Any]


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes"}


def load_stage1_documents(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _build_token_rows(row: dict[str, str], stanza_doc: Any) -> list[dict[str, Any]]:
    token_rows: list[dict[str, Any]] = []
    for sent_index, sentence in enumerate(stanza_doc.sentences, start=1):
        for token_index, word in enumerate(sentence.words, start=1):
            processed = process_token(
                surface=word.text,
                lemma=word.lemma or word.text,
                upos=word.upos or "X",
                feats=word.feats,
            )
            token_rows.append(
                {
                    "path": row.get("path", ""),
                    "year": row.get("year", ""),
                    "style_3": row.get("style_3", ""),
                    "sent_id": sent_index,
                    "token_id": token_index,
                    "surface": word.text,
                    "lemma_raw": processed.lemma_raw,
                    "lemma_norm": processed.lemma_norm,
                    "lemma_display": processed.lemma_display,
                    "pos_ud": processed.pos_ud,
                    "pos_dict": processed.pos_dict,
                    "feats": word.feats or "",
                    "is_propn": processed.is_propn,
                    "is_abbrev": processed.is_abbrev,
                    "is_participle": processed.is_participle,
                }
            )
    return token_rows


def run_stage2(stage1_rows: list[dict[str, str]], nlp_pipeline: Any, *, limit_docs: int | None = None) -> Stage2Result:
    tokens: list[dict[str, Any]] = []
    docs_total = 0
    docs_processed = 0
    docs_failed = 0
    docs_empty_text = 0

    for row in stage1_rows:
        if not _as_bool(row.get("xml_exists")):
            continue
        docs_total += 1
        if limit_docs is not None and docs_processed >= limit_docs:
            break

        xml_path = row.get("xml_abs_path", "")
        try:
            text = extract_clean_text(xml_path)
            if not text:
                docs_empty_text += 1
                continue
            stanza_doc = nlp_pipeline(text)
            tokens.extend(_build_token_rows(row, stanza_doc))
            docs_processed += 1
        except Exception:
            docs_failed += 1

    report = {
        "docs_total_with_xml": docs_total,
        "docs_processed": docs_processed,
        "docs_failed": docs_failed,
        "docs_empty_text": docs_empty_text,
        "tokens_total": len(tokens),
        "propn_tokens": sum(1 for t in tokens if t["is_propn"]),
        "participle_tokens": sum(1 for t in tokens if t["is_participle"]),
        "pron_tokens": sum(1 for t in tokens if t["pos_dict"] == "PRON"),
    }
    return Stage2Result(tokens=tokens, report=report)


def save_stage2_outputs(result: Stage2Result, output_root: str | Path) -> None:
    out = Path(output_root) / "stage2"
    out.mkdir(parents=True, exist_ok=True)

    csv_path = out / "tokens_stage2.csv"
    if not result.tokens:
        csv_path.write_text("", encoding="utf-8")
    else:
        keys: list[str] = []
        seen: set[str] = set()
        for row in result.tokens:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=keys)
            writer.writeheader()
            writer.writerows(result.tokens)

    (out / "stage2_report.json").write_text(
        json.dumps(result.report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
