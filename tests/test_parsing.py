from pathlib import Path

import pytest

from kobi_asistan.data.parsing import html_main, idefix_faq, legislation, parse, to_markdown

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_idefix_faq_one_document_per_category():
    docs = idefix_faq(_read("idefix_faq_sample.html"))
    assert [d.doc_id for d in docs] == ["idefix-teslimat", "idefix-iade-ve-degisim"]
    assert [s.id for s in docs[0].sections] == ["faq-64", "faq-65"]


def test_idefix_faq_strips_html_and_nbsp():
    section = idefix_faq(_read("idefix_faq_sample.html"))[0].sections[0]
    assert section.text == "Örnek cevap: ödeme sayfasında görünür."
    assert "<" not in section.text


def test_idefix_faq_without_next_data_gives_clear_error():
    with pytest.raises(ValueError, match="__NEXT_DATA__"):
        idefix_faq("<html><body>empty</body></html>")


def test_legislation_articles_become_titled_sections():
    doc = legislation(_read("legislation_sample.html"), "sample")[0]
    assert [s.id for s in doc.sections] == ["article-1", "article-9", "temporary-article-1"]
    article9 = doc.sections[1]
    assert article9.title == "Cayma hakkı"
    assert "(2) Süre teslim günü başlar." in article9.text
    # The next article's title must not leak into this article's text
    assert not article9.text.endswith("Geçiş hükmü")


def test_html_main_drops_scripts_and_navigation():
    html = (
        "<html><head><title>İade</title></head><body><nav>Menü</nav>"
        "<main><p>İade 14 gün.</p><script>x()</script></main></body></html>"
    )
    doc = html_main(html, "sample-returns")[0]
    assert doc.sections[0].text == "İade 14 gün."


def test_markdown_contains_source_metadata_and_section_ids():
    doc = parse("idefix_faq", _read("idefix_faq_sample.html"), "idefix-faq")[0]
    md = to_markdown(
        doc, {"url": "https://example", "accessed": "2026-11-22", "license": "company"}
    )
    assert md.startswith("---\ndoc_id: idefix-teslimat\n")
    assert "## [faq-64] Kargo ücreti nedir?" in md
