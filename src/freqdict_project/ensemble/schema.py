from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AnalyzerToken:
    text: str
    lemma: Optional[str]
    pos: Optional[str]
    feats: Optional[str] = None
    raw_pos: Optional[str] = None
    source: Optional[str] = None


@dataclass
class BaseToken:
    doc_id: str
    sent_id: int
    token_id: int
    text: str
    stanza_lemma: Optional[str]
    stanza_pos: Optional[str]
    stanza_feats: Optional[str] = None
