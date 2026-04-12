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


def main() -> None:
    settings = load_settings(ROOT / "config" / "settings.yaml")
    output_root = Path(settings["paths"]["output_root"])

    global_csv = output_root / "stage3" / "lemma_stats_global.csv"
    style_csv = output_root / "stage3" / "lemma_stats_style.csv"

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
        alphabetic_ipm_min=stage4_settings.get("alphabetic_ipm_min", 0.4),
        frequency_ipm_min=stage4_settings.get("frequency_ipm_min", 2.6),
        style_limit=stage4_settings.get("style_limit", limits.get("style_limit", 5_000)),
    )

    print("Stage 4 complete")
    print(result.report)


if __name__ == "__main__":
    main()
