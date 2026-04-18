from __future__ import annotations

from pathlib import Path

from freqdict_project.nlp.stage2_service import load_stage1_documents, run_stage2, save_stage2_outputs


class _Word:
    def __init__(self, text: str, lemma: str, upos: str, feats: str = ""):
        self.text = text
        self.lemma = lemma
        self.upos = upos
        self.feats = feats


class _Sentence:
    def __init__(self, words: list[_Word]):
        self.words = words


class _Doc:
    def __init__(self, sentences: list[_Sentence]):
        self.sentences = sentences


class _FakePipeline:
    def __call__(self, text: str):
        assert text
        return _Doc(
            [
                _Sentence(
                    [
                        _Word("Этот", "этот", "DET", "PronType=Dem"),
                        _Word("сделанный", "сделать", "VERB", "VerbForm=Part"),
                        _Word("ТЕСТ", "ТЕСТ", "PROPN", "_"),
                    ]
                )
            ]
        )


def test_run_stage2_and_save_outputs(tmp_path: Path):
    xml_path = tmp_path / "doc1.xml"
    xml_path.write_text("<doc><p>Этот сделанный ТЕСТ</p></doc>", encoding="utf-8")

    stage1_csv = tmp_path / "documents_stage1.csv"
    stage1_csv.write_text(
        "path,year,style_3,xml_abs_path,xml_exists\n"
        f"doc1.xml,2014,fiction,{xml_path},True\n",
        encoding="utf-8",
    )

    rows = load_stage1_documents(stage1_csv)
    result = run_stage2(rows, _FakePipeline())

    assert result.report["docs_processed"] == 1
    assert result.report["tokens_total"] == 3
    assert result.report["pron_tokens"] == 1
    assert result.report["participle_tokens"] == 1
    assert result.report["propn_tokens"] == 1
    assert result.tokens[1]["lemma_display"] == "сделать*"

    save_stage2_outputs(result, tmp_path)
    assert (tmp_path / "stage2" / "tokens_stage2.csv").exists()
    assert (tmp_path / "stage2" / "stage2_report.json").exists()
