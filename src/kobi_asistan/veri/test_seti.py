"""Test seti (JSONL) okuma ve tutarlılık kontrolü.

Bir test setindeki hatalar, deney sonuçlarını sessizce bozar. Bu yüzden her satırı
kurallara göre kontrol ediyoruz; `pytest` her çalıştığında bu kontroller de çalışır.
"""

import json
from pathlib import Path

KATEGORILER = {
    "tek_belge",  # cevap tek bir bölümde
    "cok_kanit",  # cevap için birden fazla bölüm gerekir
    "gunluk_dil",  # günlük dil, yazım hatası, Türkçe karakter eksikliği
    "mevzuat",  # cevap kanun/yönetmelikte
    "cevapsiz",  # cevap dokümanlarda yok -> temsilciye aktarılmalı
    "prompt_injection",  # talimat manipülasyonu
    "konu_disi",  # mağazayla ilgisiz
}
ZORLUKLAR = {"kolay", "orta", "zor"}
ALANLAR = {
    "id",
    "store",
    "question",
    "category",
    "difficulty",
    "answerable",
    "expected_answer",
    "supporting_doc_ids",
    "supporting_section_ids",
    "verified",
}


def oku(yol: Path) -> list[dict]:
    satirlar = []
    for no, satir in enumerate(yol.read_text(encoding="utf-8").splitlines(), start=1):
        if satir.strip():
            try:
                satirlar.append(json.loads(satir))
            except json.JSONDecodeError as hata:
                raise ValueError(f"{yol.name}:{no} geçerli JSON değil: {hata}") from hata
    return satirlar


def hatalari_bul(sorular: list[dict]) -> list[str]:
    """Kurallara uymayan satırlar için okunabilir hata mesajları döndürür."""
    hatalar = []
    gorulen = set()
    for s in sorular:
        sid = s.get("id", "?")
        if set(s) != ALANLAR:
            hatalar.append(
                f"{sid}: alanlar hatalı, eksik={ALANLAR - set(s)} fazla={set(s) - ALANLAR}"
            )
            continue
        if sid in gorulen:
            hatalar.append(f"{sid}: id tekrar ediyor")
        gorulen.add(sid)
        if s["category"] not in KATEGORILER:
            hatalar.append(f"{sid}: bilinmeyen kategori {s['category']!r}")
        if s["difficulty"] not in ZORLUKLAR:
            hatalar.append(f"{sid}: bilinmeyen zorluk {s['difficulty']!r}")
        if not s["question"].strip() or not s["expected_answer"].strip():
            hatalar.append(f"{sid}: soru veya beklenen cevap boş")

        kanitlar = s["supporting_section_ids"]
        if s["answerable"]:
            if not kanitlar:
                hatalar.append(f"{sid}: cevaplanabilir soru için kanıt bölümü yok")
        elif kanitlar or s["supporting_doc_ids"]:
            hatalar.append(f"{sid}: cevaplanamaz sorunun kanıt alanları boş olmalı")

        for kanit in kanitlar:
            if "#" not in kanit:
                hatalar.append(f"{sid}: kanıt '{kanit}' 'doc_id#bolum_id' biçiminde değil")
            elif kanit.split("#")[0] not in s["supporting_doc_ids"]:
                hatalar.append(f"{sid}: kanıt '{kanit}' supporting_doc_ids içinde değil")
    return hatalar
