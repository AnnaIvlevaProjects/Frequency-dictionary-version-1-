"""Style classifier based on the `sphere` metadata field."""

from __future__ import annotations

FICTION = "fiction"
PUBLICISTICS = "publicistics"
NONFICTION_OTHER = "nonfiction_other"


def classify_style_3(sphere: str | None) -> str:
    raw = (sphere or "").lower()
    values = {part.strip() for part in raw.split("|") if part.strip()}
    if "художественная" in values:
        return FICTION
    if "публицистика" in values:
        return PUBLICISTICS
    return NONFICTION_OTHER
