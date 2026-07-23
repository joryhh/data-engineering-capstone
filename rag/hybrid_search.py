from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

from bm25_search import build_bm25_index, tokenize
from chunking import build_all_chunks

CHROMA_PATH = str(Path(__file__).resolve().parent.parent / "data" / "chroma_db")
COLLECTION_NAME = "wafra_knowledge_base"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RRF_K = 60  # standard constant used in RRF literature


def dense_ranked_ids(query: str, model, collection, top_k: int = 10) -> list[str]:
    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)
    return results["ids"][0]  # already ranked best -> worst


def bm25_ranked_ids(query: str, bm25, chunks, top_k: int = 10) -> list[str]:
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [chunks[i].chunk_id for i in ranked_indices]


def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    """
    Fuses multiple ranked ID lists into one score per ID using RRF.
    Each list contributes 1 / (k + rank) to every ID it contains.
    """
    fused_scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)


def hybrid_search(query: str, top_k: int = 3):
    # ── set up both retrievers ──
    model = SentenceTransformer(EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION_NAME)
    bm25, chunks = build_bm25_index()
    chunk_lookup = {c.chunk_id: c for c in chunks}

    # ── get each ranked list separately ──
    dense_ids = dense_ranked_ids(query, model, collection)
    bm25_ids = bm25_ranked_ids(query, bm25, chunks)

    print(f"\nDense ranking:  {dense_ids}")
    print(f"BM25 ranking:   {bm25_ids}")

    # ── fuse with RRF ──
    fused = reciprocal_rank_fusion([dense_ids, bm25_ids])[:top_k]

    print(f"\n=== Hybrid (RRF) results for: '{query}' ===")
    for rank, (chunk_id, score) in enumerate(fused, start=1):
        chunk = chunk_lookup[chunk_id]
        print(f"{rank}. (rrf_score={score:.4f}) [{chunk_id}]")
        print(f"   {chunk.text[:100]}...")

    return fused


if __name__ == "__main__":
    hybrid_search("How do I get a refund on my Mada card?")
    hybrid_search("How fast is express delivery?")
