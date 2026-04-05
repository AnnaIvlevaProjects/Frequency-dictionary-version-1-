"""Year extraction rules for NКРЯ metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

YEAR_RE = re.compile(r"(19|20)\d{2}")


@dataclass(slots=True)
class YearParseResult:
    year: int | None
    source: str
    problem: str | None = None


def _extract_year_candidate(value: str) -> int | None:
    if "|" in value:
        value = value.split("|", 1)[0]
    match = YEAR_RE.search(value)
    return int(match.group(0)) if match else None


def parse_document_year(
    created: Any,
    publ_year: Any,
    *,
    fallback_to_publ_year: bool = True,
) -> YearParseResult:
    """Parse document year using primary `created` and optional fallback `publ_year`."""

    created_str = "" if created is None else str(created).strip()
    year = _extract_year_candidate(created_str) if created_str else None
    if year is not None:
        return YearParseResult(year=year, source="created")

    if fallback_to_publ_year:
        publ_str = "" if publ_year is None else str(publ_year).strip()
        fallback_year = _extract_year_candidate(publ_str) if publ_str else None
        if fallback_year is not None:
            return YearParseResult(year=fallback_year, source="publ_year")

    return YearParseResult(
        year=None,
        source="none",
        problem="Failed to extract reliable 4-digit year from created/publ_year",
    )
