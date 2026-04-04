"""Run Stage 2: XML extraction + Stanza token analysis."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freqdict_project.nlp.stage2_service import load_stage1_documents, run_stage2, save_stage2_outputs
from freqdict_project.nlp.stanza_pipeline import get_stanza_pipeline
from freqdict_project.utils.settings import load_settings


def main() -> None:
    settings = load_settings(ROOT / "config" / "settings.yaml")

    stage1_documents = ROOT / "output" / "stage1" / "documents_stage1.csv"
    if not stage1_documents.exists():
        raise SystemExit(f"Stage 1 output not found: {stage1_documents}")

    try:
        nlp = get_stanza_pipeline(
            language=settings["nlp"]["language"],
            processors=settings["nlp"]["processors"],
        )
    except ModuleNotFoundError as exc:
        raise SystemExit("Stanza is not installed. Install stanza before running Stage 2.") from exc

    rows = load_stage1_documents(stage1_documents)
    limit_docs = settings.get("stage2", {}).get("limit_docs")
    result = run_stage2(rows, nlp, limit_docs=limit_docs)
    save_stage2_outputs(result, settings["paths"]["output_root"])

    print("Stage 2 complete")
    print(result.report)


if __name__ == "__main__":
    main()
