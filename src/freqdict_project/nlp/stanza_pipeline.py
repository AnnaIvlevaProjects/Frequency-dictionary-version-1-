"""Stanza pipeline factory with one-time initialization per process."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def get_stanza_pipeline(language: str = "ru", processors: str = "tokenize,pos,lemma"):
    import stanza

    stanza.download(language)
    return stanza.Pipeline(language, processors=processors)
