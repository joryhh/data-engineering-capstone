from sentence_transformers import CrossEncoder

from hybrid_search import hybrid_search
from chunking import build_all_chunks

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def rerank(query: str, top_k_hybrid: int = 5, top_k_final: int = 3):
    chunks = [c for c in build_all_chunks() if len(c.text) >= 20]
    chunk_lookup = {c.chunk_id: c for c in chunks}

    # ── Stage 1: fast hybrid retrieval (recall-focused) ──
    hybrid_results = hybrid_search(query, top_k=top_k_hybrid)
    candidate_ids = [cid for cid, _ in hybrid_results]

    # ── Stage 2: precise cross-encoder reranking (precision-focused) ──
    print(f"\nLoading cross-encoder '{RERANKER_MODEL}' ...")
    cross_encoder = CrossEncoder(RERANKER_MODEL)

    pairs = [(query, chunk_lookup[cid].text) for cid in candidate_ids]
    rerank_scores = cross_encoder.predict(pairs)

    reranked = sorted(zip(candidate_ids, rerank_scores), key=lambda x: x[1], reverse=True)[:top_k_final]

    print(f"\n=== Cross-encoder reranked results for: '{query}' ===")
    for rank, (cid, score) in enumerate(reranked, start=1):
        chunk = chunk_lookup[cid]
        print(f"{rank}. (cross_encoder_score={score:.4f}) [{cid}]")
        print(f"   {chunk.text[:100]}...")

    return [(cid, chunk_lookup[cid].text) for cid, _ in reranked]


if __name__ == "__main__":
    rerank("How do I get a refund on my Mada card?")
