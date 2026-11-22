"""Turns HTML pages into structured documents.

Each parser takes raw HTML and returns a list of `Document`s. Parsers do no network
access, so they can be tested with small sample HTML files (tests/fixtures).

A document is made of `Section`s. Section IDs (e.g. `faq-64`, `article-12`) are the
stable IDs that test-set evidence points to.
"""

import json
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass
class Section:
    id: str
    title: str
    text: str


@dataclass
class Document:
    doc_id: str
    title: str
    sections: list[Section] = field(default_factory=list)


def _clean(text: str) -> str:
    """Collapses extra whitespace and blank lines."""
    text = text.replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    return text.strip()


def _html_to_text(html: str) -> str:
    return _clean(BeautifulSoup(html or "", "html.parser").get_text(" "))


def _slug(path: str) -> str:
    """'/yardim/iade-ve-degisim-6' -> 'iade-ve-degisim'"""
    last = path.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"-\d+$", "", last)


def idefix_faq(html: str, doc_id_prefix: str = "idefix") -> list[Document]:
    """idefix help centre: FAQs are embedded in the page's __NEXT_DATA__ JSON.

    The visible HTML only contains the questions; answers are rendered by JavaScript,
    so we read them from the embedded data instead of the HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    if tag is None:
        raise ValueError("__NEXT_DATA__ not found: the page structure may have changed")
    data = json.loads(tag.string)
    categories = data["props"]["pageProps"]["faqs"]

    documents = []
    for category in categories:
        doc = Document(doc_id=f"{doc_id_prefix}-{_slug(category['slug'])}", title=category["name"])
        for faq in category["faqs"]:
            doc.sections.append(
                Section(
                    id=f"faq-{faq['id']}",
                    title=_clean(faq["title"]),
                    text=_html_to_text(faq.get("message", "")),
                )
            )
        documents.append(doc)
    return documents


def html_main(html: str, doc_id: str) -> list[Document]:
    """Generic page: takes the text inside <main> as a single section."""
    soup = BeautifulSoup(html, "html.parser")
    for unwanted in soup(["script", "style", "noscript", "nav", "header", "footer"]):
        unwanted.decompose()
    body = soup.find("main") or soup.body or soup
    title = _clean(soup.title.get_text()) if soup.title else doc_id
    text = _clean(body.get_text("\n"))
    return [Document(doc_id=doc_id, title=title, sections=[Section("all", title, text)])]


# Turkish legal texts number articles as "MADDE 12 –" and transitional ones as "GEÇİCİ MADDE 1 –"
_ARTICLE = re.compile(r"^(?:GEÇİCİ\s+)?MADDE\s+(\d+)\s*[–-]", re.IGNORECASE)


def legislation(html: str, doc_id: str) -> list[Document]:
    """mevzuat.gov.tr text: every article becomes a section (article-1, article-2, ...).

    The line right above an article (e.g. "Cayma hakkı") is used as its title.
    """
    lines = _clean(BeautifulSoup(html, "html.parser").get_text("\n")).split("\n")
    doc = Document(doc_id=doc_id, title=lines[0] if lines else doc_id)

    current: Section | None = None
    previous = ""
    for line in lines:
        match = _ARTICLE.match(line)
        if match:
            prefix = "temporary-" if line.upper().startswith("GEÇİCİ") else ""
            current = Section(id=f"{prefix}article-{match.group(1)}", title=previous, text=line)
            doc.sections.append(current)
        elif current is not None:
            current.text += "\n" + line
        previous = line

    # The next article's title line was appended to the previous article; strip it.
    for i in range(len(doc.sections) - 1):
        next_title = doc.sections[i + 1].title
        if next_title and doc.sections[i].text.endswith("\n" + next_title):
            doc.sections[i].text = doc.sections[i].text[: -len(next_title) - 1]
    return [doc]


PARSERS = {"idefix_faq", "html_main", "legislation"}


def parse(parser: str, html: str, doc_id: str) -> list[Document]:
    if parser == "idefix_faq":
        return idefix_faq(html, doc_id_prefix=doc_id.split("-")[0])
    if parser == "html_main":
        return html_main(html, doc_id)
    if parser == "legislation":
        return legislation(html, doc_id)
    raise ValueError(f"Unknown parser: {parser}")


def to_markdown(doc: Document, source: dict) -> str:
    """Renders a document as Markdown with the source metadata as front matter."""
    header = [
        "---",
        f"doc_id: {doc.doc_id}",
        f"title: {json.dumps(doc.title, ensure_ascii=False)}",
        f"url: {source['url']}",
        f"accessed: {source['accessed']}",
        f"license: {source['license']}",
        "---",
        "",
        f"# {doc.title}",
        "",
    ]
    body = [f"## [{s.id}] {s.title}\n\n{s.text}\n" for s in doc.sections]
    return "\n".join(header) + "\n".join(body)
