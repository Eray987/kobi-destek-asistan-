from pathlib import Path

import pytest

from kobi_asistan.veri.ayristirma import ayristir, html_main, idefix_sss, markdown_yaz, mevzuat

FIXTURES = Path(__file__).parent / "fixtures"


def _oku(ad: str) -> str:
    return (FIXTURES / ad).read_text(encoding="utf-8")


def test_idefix_sss_her_kategori_ayri_dokuman():
    doks = idefix_sss(_oku("idefix_sss_ornek.html"))
    assert [d.doc_id for d in doks] == ["idefix-teslimat", "idefix-iade-ve-degisim"]
    assert [b.id for b in doks[0].bolumler] == ["faq-64", "faq-65"]


def test_idefix_sss_html_etiketleri_ve_nbsp_temizlenir():
    bolum = idefix_sss(_oku("idefix_sss_ornek.html"))[0].bolumler[0]
    assert bolum.metin == "Örnek cevap: ödeme sayfasında görünür."
    assert "<" not in bolum.metin


def test_idefix_sss_next_data_yoksa_anlasilir_hata():
    with pytest.raises(ValueError, match="__NEXT_DATA__"):
        idefix_sss("<html><body>boş</body></html>")


def test_mevzuat_maddeleri_ayri_bolum_ve_baslikli():
    dok = mevzuat(_oku("mevzuat_ornek.html"), "ornek")[0]
    assert [b.id for b in dok.bolumler] == ["madde-1", "madde-9", "gecici-madde-1"]
    madde9 = dok.bolumler[1]
    assert madde9.baslik == "Cayma hakkı"
    assert "(2) Süre teslim günü başlar." in madde9.metin
    # Bir sonraki maddenin başlığı bu maddenin metnine karışmamalı
    assert not madde9.metin.endswith("Geçiş hükmü")


def test_html_main_script_ve_nav_atilir():
    html = (
        "<html><head><title>İade</title></head><body><nav>Menü</nav>"
        "<main><p>İade 14 gün.</p><script>x()</script></main></body></html>"
    )
    dok = html_main(html, "ornek-iade")[0]
    assert dok.bolumler[0].metin == "İade 14 gün."


def test_markdown_kaynak_bilgisi_ve_bolum_kimligi_icerir():
    dok = ayristir("idefix_sss", _oku("idefix_sss_ornek.html"), "idefix-sss")[0]
    md = markdown_yaz(dok, {"url": "https://ornek", "erisim": "2026-11-22", "lisans": "sirket"})
    assert md.startswith("---\ndoc_id: idefix-teslimat\n")
    assert "## [faq-64] Kargo ücreti nedir?" in md
