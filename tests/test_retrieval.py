import numpy as np
import pytest

from kobi_asistan.data.parsing import Document, Section
from kobi_asistan.retrieval.chunking import fixed_size, section_aware
from kobi_asistan.retrieval.dense import DenseIndex, Hit
from kobi_asistan.retrieval.evaluation import build_report, score_question
from kobi_asistan.retrieval.lexical import BM25Index, HybridIndex, tokenize


def _doc() -> Document:
    return Document(
        doc_id="shop-help",
        title="Help",
        sections=[
            Section("faq-1", "İade süresi", "Ürünü 14 gün içinde iade edebilirsiniz."),
            Section("faq-2", "Kargo", "Kargo firması satıcıya göre değişir."),
            Section("faq-3", "Ödeme", "Kredi kartı ve banka kartı kabul edilir."),
        ],
    )


class BagOfWordsEmbedder:
    """Tiny stand-in for a real model: one dimension per vocabulary word."""

    def __init__(self, vocabulary: list[str]):
        self.vocab = {w: i for i, w in enumerate(vocabulary)}

    def _embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), len(self.vocab)))
        for row, text in enumerate(texts):
            for word in text.lower().split():
                if word.strip(".?,") in self.vocab:
                    out[row, self.vocab[word.strip(".?,")]] += 1
        return out

    embed_queries = embed_passages = _embed


def test_fixed_size_chunks_track_the_sections_they_overlap():
    chunks = fixed_size([_doc()], words=8, overlap=2)
    assert [c.chunk_id for c in chunks][:2] == ["shop-help::0", "shop-help::1"]
    # Section 1 has 2 + 7 = 9 words, so the first 8-word chunk is entirely faq-1
    assert chunks[0].section_keys == ("shop-help#faq-1",)
    # The next chunk starts 6 words later and crosses into faq-2
    assert chunks[1].section_keys == ("shop-help#faq-1", "shop-help#faq-2")
    # Every word ends up in some chunk
    covered = {k for c in chunks for k in c.section_keys}
    assert covered == {"shop-help#faq-1", "shop-help#faq-2", "shop-help#faq-3"}


def test_fixed_size_rejects_bad_overlap():
    with pytest.raises(ValueError):
        fixed_size([_doc()], words=10, overlap=10)


def test_dense_index_ranks_the_matching_chunk_first():
    chunks = fixed_size([_doc()], words=9, overlap=0)
    index = DenseIndex(chunks, BagOfWordsEmbedder(["iade", "kargo", "kredi", "gün"]))
    hits = index.search("kargo kim taşıyor?", k=2)
    assert "shop-help#faq-2" in hits[0].chunk.section_keys
    assert hits[0].score >= hits[1].score


def test_metrics_recall_and_mrr():
    chunks = fixed_size([_doc()], words=9, overlap=0)
    index = DenseIndex(chunks, BagOfWordsEmbedder(["iade", "kargo", "kredi", "gün"]))
    questions = [
        {  # found at rank 1
            "id": "a",
            "category": "single_source",
            "question": "kargo",
            "supporting_section_ids": ["shop-help#faq-2"],
        },
        {  # needs two sections; only one can be found in the top 1
            "id": "b",
            "category": "multi_evidence",
            "question": "iade gün",
            "supporting_section_ids": ["shop-help#faq-1", "shop-help#faq-3"],
        },
    ]
    results = [score_question(q, index.search(q["question"], k=1)) for q in questions]
    report = build_report(results)
    assert results[0].first_hit_rank == 1
    assert results[1].first_hit_rank == 1 and not results[1].all_gold_found
    assert report.overall.recall_any == 1.0
    assert report.overall.recall_all == 0.5
    assert report.overall.mrr == 1.0
    assert report.failures == []


def test_section_aware_makes_one_chunk_per_short_section():
    chunks = section_aware([_doc()], max_words=50, overlap=5)
    assert [c.chunk_id for c in chunks] == [
        "shop-help::faq-1",
        "shop-help::faq-2",
        "shop-help::faq-3",
    ]
    assert chunks[0].section_keys == ("shop-help#faq-1",)
    assert chunks[0].text.startswith("İade süresi\n")


def test_section_aware_splits_long_sections_and_repeats_the_title():
    long_doc = Document(
        doc_id="law",
        title="Law",
        sections=[Section("article-1", "Cayma hakkı", " ".join(f"w{i}" for i in range(25)))],
    )
    chunks = section_aware([long_doc], max_words=10, overlap=2)
    assert [c.chunk_id for c in chunks] == [
        "law::article-1.0",
        "law::article-1.1",
        "law::article-1.2",
    ]
    assert all(c.text.startswith("Cayma hakkı\n") for c in chunks)
    assert all(c.section_keys == ("law#article-1",) for c in chunks)
    # Windows start every 8 words and the last one reaches the end of the text
    assert chunks[1].text.split()[2] == "w8"
    assert chunks[-1].text.split()[-1] == "w24"


def test_section_aware_rejects_bad_overlap():
    with pytest.raises(ValueError):
        section_aware([_doc()], max_words=10, overlap=10)


def test_tokenize_handles_turkish_case_diacritics_and_suffixes():
    assert tokenize("İADE Işık şöyle", prefix=None) == ["iade", "isik", "soyle"]
    # Customers often type without Turkish characters; both sides must match
    assert tokenize("kulaklığı açtım") == tokenize("kulakligi actim")
    # Prefix stemming maps inflected forms to the same term
    assert tokenize("değişim değişimi")[0] == tokenize("degisimler")[0] == "degis"


def test_bm25_ranks_the_keyword_match_first():
    chunks = section_aware([_doc()], max_words=50, overlap=5)
    index = BM25Index(chunks)
    assert index.search("kargo firmasi hangisi", k=1)[0].chunk.section_keys == ("shop-help#faq-2",)
    assert index.search("KREDİ KARTI", k=1)[0].chunk.section_keys == ("shop-help#faq-3",)


class _FixedRetriever:
    def __init__(self, chunks):
        self.chunks = chunks

    def search(self, query, k=5):
        return [Hit(c, 1.0) for c in self.chunks[:k]]


def test_hybrid_rewards_chunks_ranked_well_by_both_retrievers():
    a, b, c = section_aware([_doc()], max_words=50, overlap=5)
    hybrid = HybridIndex([_FixedRetriever([a, b, c]), _FixedRetriever([b, c, a])], rrf_k=1)
    # b: 1/3 + 1/2, a: 1/2 + 1/4, c: 1/4 + 1/3
    assert [h.chunk.chunk_id for h in hybrid.search("x", k=3)] == [
        b.chunk_id,
        a.chunk_id,
        c.chunk_id,
    ]
