"""Run Stage 4: build public dictionary CSVs from Stage 3 aggregates."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freqdict_project.export.dictionaries import build_stage4_dictionaries
from freqdict_project.utils.settings import load_settings


def _to_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def main() -> None:
    settings = load_settings(ROOT / "config" / "settings.yaml")
    output_root = Path(settings["paths"]["output_root"])

    global_csv = output_root / "stage3" / "lemma_stats_global.csv"
    style_csv = output_root / "stage3" / "lemma_stats_style.csv"
    stage2_tokens_csv = output_root / "stage2" / "tokens_stage2.csv"

    if not global_csv.exists():
        raise SystemExit(f"Stage 3 global stats not found: {global_csv}")
    if not style_csv.exists():
        raise SystemExit(f"Stage 3 style stats not found: {style_csv}")

    limits = settings.get("limits", {})
    stage4_settings = settings.get("stage4", {})
    result = build_stage4_dictionaries(
        global_csv,
        style_csv,
        output_root,
        stage2_tokens_csv=stage2_tokens_csv if stage2_tokens_csv.exists() else None,
        alphabetic_ipm_min=_to_float(stage4_settings.get("alphabetic_ipm_min", 0.4), 0.4),
        frequency_ipm_min=_to_float(stage4_settings.get("frequency_ipm_min", 2.6), 2.6),
        style_limit=_to_int(stage4_settings.get("style_limit", limits.get("style_limit", 5_000)), 5_000),
        wordform_ipm_min=_to_float(stage4_settings.get("wordform_ipm_min", 5.0), 5.0),
    )

    print("Stage 4 complete")
    print(result.report)


if __name__ == "__main__":
    main()
