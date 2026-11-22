from collections import Counter
from pathlib import Path

from kobi_asistan.veri.test_seti import hatalari_bul, oku

TEST_SETI = Path(__file__).parent.parent / "data" / "test_seti" / "sorular_v0.jsonl"


def test_test_seti_kurallara_uyuyor():
    assert hatalari_bul(oku(TEST_SETI)) == []


def test_en_az_bes_cevaplanamaz_soru_var():
    sorular = oku(TEST_SETI)
    assert sum(not s["answerable"] for s in sorular) >= 5


def test_kategoriler_dengeli_dagiliyor():
    sayilar = Counter(s["category"] for s in oku(TEST_SETI))
    for kategori in ["tek_belge", "cevapsiz", "gunluk_dil", "prompt_injection"]:
        assert sayilar[kategori] >= 1, f"{kategori} kategorisinde hiç soru yok"


def test_kontrol_hatali_satiri_yakalar():
    hatali = {
        "id": "x1",
        "store": "s",
        "question": "Soru?",
        "category": "cevapsiz",
        "difficulty": "kolay",
        "answerable": False,
        "expected_answer": "Yok.",
        "supporting_doc_ids": ["d"],
        "supporting_section_ids": ["d#b"],
        "verified": False,
    }
    assert any("boş olmalı" in h for h in hatalari_bul([hatali]))
