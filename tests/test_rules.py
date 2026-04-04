from __future__ import annotations

from pathlib import Path

from freqdict_project.corpus.xml_reader import extract_clean_text
from freqdict_project.metadata.style_classifier import classify_style_3
from freqdict_project.metadata.year_parser import parse_document_year
from freqdict_project.nlp.morph_postprocess import process_token
from freqdict_project.stats.frequencies import calc_ipm
from freqdict_project.stats.likelihood import calc_ll
from freqdict_project.stats.range_dispersion import calc_d, calc_r


def test_extract_year_from_created_pipe():
    result = parse_document_year("2011|2012", None)
    assert result.year == 2011
    assert result.source == "created"


def test_fallback_to_publ_year():
    result = parse_document_year("unknown", "2010")
    assert result.year == 2010
    assert result.source == "publ_year"


def test_style_classifier_priority():
    assert classify_style_3("публицистика|художественная") == "fiction"
    assert classify_style_3("наука|публицистика") == "publicistics"
    assert classify_style_3("наука") == "nonfiction_other"


def test_xml_text_extraction(tmp_path: Path):
    xml = tmp_path / "sample.xml"
    xml.write_text("<doc><p>Привет <hi>мир</hi></p><p>!</p></doc>", encoding="utf-8")
    assert extract_clean_text(xml) == "Привет мир !"


def test_det_maps_to_pron():
    token = process_token(surface="этот", lemma="этот", upos="DET", feats="PronType=Dem")
    assert token.pos_dict == "PRON"


def test_participle_gets_star_and_participle_pos():
    token = process_token(surface="сделанный", lemma="сделать", upos="VERB", feats="VerbForm=Part|Tense=Past")
    assert token.pos_dict == "PARTICIPLE"
    assert token.lemma_display == "сделать*"


def test_yo_normalized_after_lemmatization():
    token = process_token(surface="всё", lemma="всё", upos="PRON", feats="_")
    assert token.lemma_raw == "всё"
    assert token.lemma_norm == "все"


def test_ipm():
    assert calc_ipm(50, 10_000) == 5000.0


def test_r_and_d():
    freqs = [3, 0, 2, 1]
    assert calc_r(freqs) == 3
    assert 0 <= calc_d(freqs) <= 100


def test_ll():
    score = calc_ll(a=30, b=10, c=1000, d=1000)
    assert isinstance(score, float)
    assert score > 0
