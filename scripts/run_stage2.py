"""Run Stage 2: XML extraction + Stanza token analysis."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freqdict_project.nlp.stage2_service import load_stage1_documents, run_stage2_parallel, save_stage2_outputs
from freqdict_project.utils.settings import load_settings


def main() -> None:
    settings = load_settings(ROOT / "config" / "settings.yaml")

    stage1_documents = ROOT / "output" / "stage1" / "documents_stage1.csv"
    if not stage1_documents.exists():
        raise SystemExit(f"Stage 1 output not found: {stage1_documents}")

    rows = load_stage1_documents(stage1_documents)
    stage2_settings = settings.get("stage2", {})
    limit_docs = stage2_settings.get("limit_docs")
    workers = stage2_settings.get("workers", 1)
    chunksize = stage2_settings.get("chunksize", 1)
    try:
        result = run_stage2_parallel(
            rows,
            language=settings["nlp"]["language"],
            processors=settings["nlp"]["processors"],
            limit_docs=limit_docs,
            workers=workers,
            chunksize=chunksize,
        )
    except ModuleNotFoundError as exc:
        raise SystemExit("Stanza is not installed. Install stanza before running Stage 2.") from exc
    save_stage2_outputs(result, settings["paths"]["output_root"])

    print("Stage 2 complete")
    print(result.report)


if __name__ == "__main__":
    main()
