"""Corpus segmentation into approximately equal lexical-token chunks."""

from __future__ import annotations


def assign_segments(doc_token_counts: list[int], segments_n: int = 100) -> list[int]:
    if not doc_token_counts:
        return []
    total = sum(max(0, c) for c in doc_token_counts)
    if total == 0:
        return [0 for _ in doc_token_counts]

    target = total / segments_n
    segment = 0
    acc = 0.0
    result: list[int] = []

    for count in doc_token_counts:
        result.append(segment)
        acc += max(0, count)
        if acc >= target and segment < segments_n - 1:
            segment += 1
            acc = 0.0
    return result
