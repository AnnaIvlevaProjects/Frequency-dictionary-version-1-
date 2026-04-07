"""Log-likelihood for significant vocabulary."""

from __future__ import annotations

import math


def calc_ll(a: int, b: int, c: int, d: int) -> float | None:
    """Compute LL_score = 2(a ln(a/E1) + b ln(b/E2)), rounded to 3 decimals."""
    if a == 0:
        return None
    total = c + d
    if total == 0:
        return 0.0
    e1 = c * (a + b) / total
    e2 = d * (a + b) / total

    term_a = 0.0 if a == 0 or e1 == 0 else a * math.log(a / e1)
    term_b = 0.0 if b == 0 or e2 == 0 else b * math.log(b / e2)
    return round(2 * (term_a + term_b), 3)
