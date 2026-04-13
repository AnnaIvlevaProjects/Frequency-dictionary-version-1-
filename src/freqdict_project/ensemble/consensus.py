from __future__ import annotations

from collections import defaultdict
from typing import Any

ALL_ANALYZERS = ["natasha", "spacy", "pymystem", "deeppavlov", "stanza", "udpipe"]
PARTICIPLE_ANALYZERS = ["stanza", "deeppavlov", "udpipe"]


def normalize_pos(tag: str | None, analyzer_name: str) -> str | None:
    if tag is None:
        return None
    tag = tag.strip()
    if analyzer_name == "pymystem" and tag == "CONJ":
        return "CCONJ"
    if analyzer_name == "deeppavlov" and tag == "PREP":
        return "ADP"
    return tag


def estimate_pos_simple(pos_candidates: dict[str, str]) -> tuple[str | None, float]:
    if not pos_candidates:
        return None, 0.0
    counts: dict[str, int] = {}
    for value in pos_candidates.values():
        counts[value] = counts.get(value, 0) + 1
    winner = max(counts.items(), key=lambda item: item[1])[0]
    confidence = counts[winner] / len(pos_candidates)
    return winner, confidence


def calculate_pos_consensus(row: dict[str, Any], pos_weights: dict[str, dict[str, float]], analyzer_performance: dict[str, dict[str, float]]) -> tuple[str | None, float]:
    pos_candidates: dict[str, str] = {}
    for analyzer in ALL_ANALYZERS:
        pos_value = row.get(f"{analyzer}_pos")
        if pos_value is not None:
            norm = normalize_pos(str(pos_value), analyzer)
            if norm is not None:
                pos_candidates[analyzer] = norm
    if not pos_candidates:
        return None, 0.0
    if len(pos_candidates) < 2:
        return row.get("stanza_pos"), 0.0

    initial_pos, _ = estimate_pos_simple(pos_candidates)
    votes = defaultdict(float)
    total_weight = 0.0
    for analyzer, pos_value in pos_candidates.items():
        if initial_pos:
            weight = pos_weights.get(analyzer, {}).get(initial_pos, 0.5)
        else:
            weight = analyzer_performance.get(analyzer, {}).get("overall_pos", 0.5)
        votes[pos_value] += weight
        total_weight += weight
    winner = max(votes.items(), key=lambda item: item[1])[0]
    confidence = votes[winner] / total_weight if total_weight > 0 else 0.0
    return winner, confidence


def calculate_lemma_consensus(
    row: dict[str, Any],
    lemma_weights: dict[str, dict[str, float]],
    analyzer_performance: dict[str, dict[str, float]],
    estimated_pos: str | None = None,
) -> tuple[str | None, float]:
    lemma_candidates: dict[str, str] = {}
    pos_candidates: dict[str, str] = {}

    for analyzer in ALL_ANALYZERS:
        lemma_value = row.get(f"{analyzer}_lemma")
        pos_value = row.get(f"{analyzer}_pos")
        if lemma_value is not None:
            lemma_candidates[analyzer] = str(lemma_value).strip().lower()
        if pos_value is not None:
            norm = normalize_pos(str(pos_value), analyzer)
            if norm is not None:
                pos_candidates[analyzer] = norm

    if not lemma_candidates:
        return None, 0.0
    if len(lemma_candidates) < 2:
        return row.get("stanza_lemma"), 0.0
    if estimated_pos is None and pos_candidates:
        estimated_pos, _ = estimate_pos_simple(pos_candidates)

    votes = defaultdict(float)
    total_weight = 0.0
    for analyzer, lemma_value in lemma_candidates.items():
        if estimated_pos:
            weight = lemma_weights.get(analyzer, {}).get(estimated_pos, 0.5)
        else:
            weight = analyzer_performance.get(analyzer, {}).get("overall_lemma", 0.5)
        votes[lemma_value] += weight
        total_weight += weight

    winner = max(votes.items(), key=lambda item: item[1])[0]
    confidence = votes[winner] / total_weight if total_weight > 0 else 0.0
    return winner, confidence


def has_verbform_part(pos_value: str | None, feats_value: str | None) -> bool:
    if pos_value != "VERB":
        return False
    if not feats_value:
        return False
    value = str(feats_value)
    return "VerbForm=Part" in value or "PartForm" in value


def participle_votes(row: dict[str, Any]) -> int:
    votes = 0
    if has_verbform_part(row.get("stanza_pos"), row.get("stanza_feats")):
        votes += 1
    if has_verbform_part(row.get("deeppavlov_pos"), row.get("deeppavlov_feats")):
        votes += 1
    if has_verbform_part(row.get("udpipe_pos"), row.get("udpipe_feats")):
        votes += 1
    return votes


def is_participle_by_override(row: dict[str, Any]) -> bool:
    return participle_votes(row) >= 2


def calculate_participle_lemma(
    row: dict[str, Any],
    lemma_weights: dict[str, dict[str, float]],
    analyzer_performance: dict[str, dict[str, float]],
) -> tuple[str | None, float]:
    estimated_pos = "VERB"
    votes = defaultdict(float)
    total_weight = 0.0
    for analyzer in PARTICIPLE_ANALYZERS:
        lemma_value = row.get(f"{analyzer}_lemma")
        if not lemma_value:
            continue
        normalized = str(lemma_value).strip().lower()
        weight = lemma_weights.get(analyzer, {}).get(
            estimated_pos, analyzer_performance.get(analyzer, {}).get("overall_lemma", 0.5)
        )
        votes[normalized] += weight
        total_weight += weight

    if not votes:
        base_lemma = row.get("stanza_lemma") or row.get("deeppavlov_lemma") or row.get("udpipe_lemma")
        if not base_lemma:
            return None, 0.0
        return f"{str(base_lemma).lower()}*", 0.0

    winner = max(votes.items(), key=lambda item: item[1])[0]
    confidence = votes[winner] / total_weight if total_weight > 0 else 0.0
    return f"{winner}*", confidence
