"""Run Stage 3: aggregate Stage 2 tokens into lemma-level statistics."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freqdict_project.stats.aggregation import run_stage3_aggregation, save_stage3_outputs
from freqdict_project.utils.settings import load_settings


def main() -> None:
    settings = load_settings(ROOT / "config" / "settings.yaml")
    output_root = Path(settings["paths"]["output_root"])

    tokens_path = output_root / "stage2" / "tokens_stage2.csv"
    stage1_docs_path = output_root / "stage1" / "documents_stage1.csv"

    if not tokens_path.exists():
        raise SystemExit(f"Stage 2 tokens file not found: {tokens_path}")
    if not stage1_docs_path.exists():
        raise SystemExit(f"Stage 1 documents file not found: {stage1_docs_path}")

    stage3_settings = settings.get("stage3", {})
    segments_n = stage3_settings.get("segments_n", settings.get("corpus", {}).get("segments_n", 100))
    progress_every = stage3_settings.get("progress_every", 500_000)
    lexical_only = stage3_settings.get("lexical_only", False)
    excluded_upos = stage3_settings.get("excluded_upos", ["PUNCT", "SYM", "X"])

    result = run_stage3_aggregation(
        tokens_path,
        stage1_docs_path,
        segments_n=segments_n,
        progress_every=progress_every,
        lexical_only=lexical_only,
        excluded_upos=excluded_upos,
    )
    save_stage3_outputs(result, output_root)

    print("Stage 3 complete")
    print(result.report)


if __name__ == "__main__":
    main()
