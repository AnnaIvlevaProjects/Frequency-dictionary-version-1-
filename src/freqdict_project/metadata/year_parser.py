"""Year extraction rules for NКРЯ metadata."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import re

YEAR_ANY_RE = re.compile(r"\b(1[7-9]\d{2}|20\d{2}|2100)\b")
YEAR_RE = re.compile(r"(19|20)\d{2}")


@dataclass(slots=True)
class YearParseResult:
    year: int | None
    source: str
    problem: str | None = None




def _extract_year_candidate(value: str) -> int | None:
    if value is None:
        return None

    date_str = str(value).strip()
    if not date_str or date_str.lower() in {"nan", "none", "null"}:
        return None

    # 1) приоритет: часть до '|'
    if "|" in date_str:
        left = date_str.split("|", 1)[0].strip()
        if left.isdigit() and len(left) == 4:
            y = int(left)
            if 1700 <= y <= 2100:
                return y
        m = YEAR_ANY_RE.search(left)
        if m:
            return int(m.group(0))

    # 2) fallback: найти год в любой части строки created
    m = YEAR_ANY_RE.search(date_str)
    if m:
        return int(m.group(0))

    return None


def parse_document_year(
    created: Any,
    publ_year: Any,
    *,
    fallback_to_publ_year: bool = False,
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
