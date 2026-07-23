from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

from chunking import build_all_chunks

CHROMA_PATH = str(Path(__file__).resolve().parent.parent / "data" / "chroma_db")
COLLECTION_NAME = "wafra_knowledge_base"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # small, fast, good quality


def build_vector_store():
    print(f"Loading embedding model '{EMBEDDING_MODEL}' ...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Building chunks from documents ...")
    chunks = [c for c in build_all_chunks() if len(c.text) >= 20]  # skip tiny fragments
    print(f"Using {len(chunks)} chunks (tiny fragments filtered out)\n")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # Fresh collection each run, so re-running this script stays repeatable
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    texts = [c.text for c in chunks]
    ids = [c.chunk_id for c in chunks]
    metadatas = [{"source_doc": c.source_doc} for c in chunks]

    print("Encoding chunks into embeddings ...")
    embeddings = model.encode(texts).tolist()

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"✅ Vector store built -> {CHROMA_PATH}")
    print(f"   Collection '{COLLECTION_NAME}' now has {collection.count()} vectors.\n")

    return collection, model


def semantic_search(query: str, top_k: int = 3):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION_NAME)
    model = SentenceTransformer(EMBEDDING_MODEL)

    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    print(f"\n=== Dense/semantic search results for: '{query}' ===")
    for i, (doc, dist, meta) in enumerate(zip(
        results["documents"][0], results["distances"][0], results["metadatas"][0]
    )):
        print(f"{i+1}. (score={1 - dist:.3f}, source={meta['source_doc']})")
        print(f"   {doc[:100]}...")


if __name__ == "__main__":
    build_vector_store()
    semantic_search("How do I get a refund?")
    semantic_search("What are the delivery times?")
