# Frequency Dictionary (NКРЯ 2008–2022) — Starter Implementation

This repository now contains a production-oriented project skeleton for the technical specification in `TZ`:

- modular Python package under `src/freqdict_project/`;
- configurable settings (`config/settings.yaml`);
- core linguistic rules implemented as reusable functions;
- Stage 1 pipeline implementation for metadata loading/filtering;
- metadata CSV loader supports common delimiters (`,`, `;`, `\t`) and header normalization to lowercase.
- XML resolver supports metadata paths without extension by trying `<path>`, `<path>.xml`, `<path>.xml.gz`.
- XML resolver also handles duplicated leading corpus segment in metadata paths (e.g. `post1950/...` with `corpus_root` already ending in `post1950`).
- XML resolver can also resolve metadata paths that point to a sibling corpus directory (e.g. `pre1950/...` when `corpus_root` is `.../post1950`).
- baseline unit tests for acceptance-critical calculations.

## Quick start

```bash
python -m pip install -e .
python -m pytest
```

## Run Stage 1

```bash
python scripts/run_full_build.py
```

Outputs are written into `output/stage1/`:

- `documents_stage1.csv`
- `problem_dates.csv`
- `missing_xml.csv`
- `stage1_report.json`

## Run Stage 2

```bash
python scripts/run_stage2.py
```

`run_stage2.py` reads `output/stage1/documents_stage1.csv`, runs XML extraction + Stanza analysis, and writes:

- `output/stage2/tokens_stage2.csv`
- `output/stage2/stage2_report.json`

Optional Stage 2 settings in `config/settings.yaml`:

- `stage2.limit_docs` — limit documents for test runs
- `stage2.workers` — number of processes (use `1` for single-process mode)
- `stage2.chunksize` — task chunk size for multiprocessing
- `stage2.progress_every` — print progress line every N processed documents

If Stage 2 finishes too quickly with `docs_failed` close to total, first re-run with:

- `stage2.workers: 1`

to verify single-process behavior and inspect the reported `failed_error_samples`.

## Run Stage 3

```bash
python scripts/run_stage3.py
```

`run_stage3.py` reads:

- `output/stage2/tokens_stage2.csv`
- `output/stage1/documents_stage1.csv`

and writes:

- `output/stage3/lemma_stats_global.csv`
- `output/stage3/lemma_stats_style.csv`
- `output/stage3/stage3_report.json`

Optional Stage 3 settings in `config/settings.yaml`:

- `stage3.segments_n` — number of corpus segments (default `100`)
- `stage3.progress_every` — progress print interval in processed token rows

## Windows / PyCharm troubleshooting

If you see `collected 0 items`, check the following:

1. Ensure your local clone includes the `tests/` directory and test files.
2. Run tests from the repository root (where `pyproject.toml` is located).
3. Prefer module invocation to avoid PATH issues:

```bash
python -m pytest -q
```

The project config explicitly points pytest to the `tests` folder.
