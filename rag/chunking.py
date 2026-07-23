from pathlib import Path
from dataclasses import dataclass

DOCS_DIR = Path(__file__).parent / "documents"
CHUNK_SIZE = 200       # characters per chunk
CHUNK_OVERLAP = 40     # overlap between consecutive chunks


@dataclass
class Chunk:
    chunk_id: str
    source_doc: str
    text: str


def chunk_text(text: str, source_doc: str, chunk_size: int, overlap: int) -> list[Chunk]:
    """Simple sliding-window character chunker with overlap."""
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + chunk_size
        piece = text[start:end].strip()
        if piece:
            chunks.append(Chunk(
                chunk_id=f"{source_doc}_chunk{idx}",
                source_doc=source_doc,
                text=piece,
            ))
            idx += 1
        start += chunk_size - overlap  # slide window forward with overlap
    return chunks


def build_all_chunks() -> list[Chunk]:
    all_chunks = []
    for doc_path in sorted(DOCS_DIR.glob("*.txt")):
        text = doc_path.read_text(encoding="utf-8")
        all_chunks.extend(chunk_text(text, doc_path.name, CHUNK_SIZE, CHUNK_OVERLAP))
    return all_chunks


if __name__ == "__main__":
    chunks = build_all_chunks()
    print(f"Total chunks created: {len(chunks)}\n")
    for c in chunks:
        print(f"[{c.chunk_id}] ({len(c.text)} chars)")
        print(f"  {c.text[:80]}...")
        print()
