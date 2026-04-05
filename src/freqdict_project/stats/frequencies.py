"""Frequency metrics."""

from __future__ import annotations


def calc_ipm(freq: int, total_tokens: int) -> float:
    if total_tokens <= 0:
        return 0.0
    return freq / total_tokens * 1_000_000


def calc_doc_percent(doc_hits: int, total_docs: int) -> float:
    if total_docs <= 0:
        return 0.0
    return 100.0 * doc_hits / total_docs
