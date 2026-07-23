import os
from dotenv import load_dotenv
from groq import Groq

from reranker import rerank

load_dotenv()  # reads GROQ_API_KEY from the .env file at project root

LLM_MODEL = "llama-3.1-8b-instant"


def build_context_block(retrieved: list[tuple[str, str]]) -> str:
    """Formats retrieved chunks into a labeled context block for grounding."""
    lines = []
    for chunk_id, text in retrieved:
        lines.append(f"[Source: {chunk_id}]\n{text}")
    return "\n\n".join(lines)


def answer_question(query: str) -> str:
    retrieved = rerank(query, top_k_hybrid=5, top_k_final=2)
    context = build_context_block(retrieved)

    system_prompt = (
        "You are a customer support assistant. Answer ONLY using the provided "
        "context below. If the context does not contain the answer, say you "
        "don't have enough information. Always cite the source chunk id(s) "
        "you used in square brackets at the end of your answer."
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}"

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    query = "How do I get a refund on my Mada card?"
    print(f"\n{'='*60}\nQUESTION: {query}\n{'='*60}")
    answer = answer_question(query)
    print(f"\nANSWER:\n{answer}")
