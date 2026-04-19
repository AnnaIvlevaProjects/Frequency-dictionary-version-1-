"""Run Stage 5: wordform dictionary build (without consensus)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freqdict_project.export.wordforms import build_stage5_wordforms
from freqdict_project.utils.settings import load_settings


def _to_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def main() -> None:
    settings = load_settings(ROOT / "config" / "settings.yaml")
    output_root = Path(settings["paths"]["output_root"])
    tokens_csv = output_root / "stage2" / "tokens_stage2.csv"
    if not tokens_csv.exists():
        raise SystemExit(f"Stage 2 tokens file not found: {tokens_csv}")

    stage4_settings = settings.get("stage4", {})
    result = build_stage5_wordforms(
        tokens_csv,
        output_root,
        ipm_min=_to_float(stage4_settings.get("wordform_ipm_min", 5.0), 5.0),
    )

    print("Stage 5 complete")
    print(result.report)


if __name__ == "__main__":
    main()
