import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from chunking import build_all_chunks

DOCS_DIR = Path(__file__).parent / "documents"


def tokenize(text: str) -> list[str]:
    """Simple lowercase word tokenizer."""
    return re.findall(r"\b\w+\b", text.lower())


def build_bm25_index():
    chunks = [c for c in build_all_chunks() if len(c.text) >= 20]
    tokenized_corpus = [tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, chunks


def keyword_search(query: str, top_k: int = 3):
    bm25, chunks = build_bm25_index()
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    # rank chunk indices by score, descending
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    print(f"\n=== BM25 keyword search results for: '{query}' ===")
    for rank, i in enumerate(ranked_indices, start=1):
        print(f"{rank}. (score={scores[i]:.3f}, source={chunks[i].source_doc})")
        print(f"   {chunks[i].text[:100]}...")

    return [(chunks[i].chunk_id, scores[i]) for i in ranked_indices]


if __name__ == "__main__":
    keyword_search("Mada refund payment")
    keyword_search("express shipping fee")
