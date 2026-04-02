from __future__ import annotations

from pathlib import Path

from freqdict_project.utils.settings import load_settings


def test_load_settings_from_yaml(tmp_path: Path):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        """
paths:
  corpus_root: "C:/corpus"
  output_root: "./output"
corpus:
  year_from: 2008
  year_to: 2022
rules:
  det_to_pron: true
  service_upos: ["ADP", "AUX"]
""".strip(),
        encoding="utf-8",
    )

    loaded = load_settings(cfg)
    assert loaded["paths"]["corpus_root"] == "C:/corpus"
    assert loaded["corpus"]["year_from"] == 2008
    assert loaded["rules"]["det_to_pron"] is True
    assert loaded["rules"]["service_upos"] == ["ADP", "AUX"]
