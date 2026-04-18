"""Range (R) and Juilland's D metrics."""

from __future__ import annotations

from math import sqrt


def calc_r(segment_freqs: list[int]) -> int:
    return sum(1 for value in segment_freqs if value > 0)


def calc_d(segment_freqs: list[int]) -> float:
    n = len(segment_freqs)
    if n < 2:
        return 0.0
    mu = sum(segment_freqs) / n
    if mu == 0:
        return 0.0
    variance = sum((x - mu) ** 2 for x in segment_freqs) / n
    sigma = variance**0.5
    d = 100 * (1 - sigma / (mu * sqrt(n - 1)))
    return max(0.0, round(d, 6))
