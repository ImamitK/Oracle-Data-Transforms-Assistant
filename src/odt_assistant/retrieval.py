import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "rest-endpoints.chunks.json"

STOP_WORDS = {
    "a", "an", "the", "how", "do", "i", "to", "what", "is", "can", "all",
}

# tokenize lowercases text and breaks it into words, ignoring common words such as “how” and “the.”
def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in STOP_WORDS}


# retrieve counts how many question words each chunk shares, then ranks chunks by that count.
def retrieve(question: str, top_k: int = 3) -> list[dict]:
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Chunks file not found: {CHUNKS_FILE}")

    question_terms = tokenize(question)
    if not question_terms:
        return []

    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    ranked_results = []

    for chunk in chunks:
        chunk_terms = tokenize(chunk["text"])
        matched_terms = question_terms & chunk_terms

        if matched_terms:
            ranked_results.append(
                {
                    "score": len(matched_terms),
                    "matched_terms": sorted(matched_terms),
                    "chunk": chunk,
                }
            )

    ranked_results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )
    return ranked_results[:top_k]


# main() asks for a question and prints up to three matching chunks.
def main() -> None:
    question = input("Enter a documentation question: ").strip()
    results = retrieve(question)

    if not results:
        print("No chunks matched the question's keywords.")
        return

    # The result keeps the chunk’s source URL so the app can later show where its evidence came from.
    for result in results:
        chunk = result["chunk"]
        print(
            f"\n{chunk['chunk_id']} "
            f"(score: {result['score']}; "
            f"matched: {', '.join(result['matched_terms'])})"
        )
        print(f"Source: {chunk['source_url']}")
        print(chunk["text"])


if __name__ == "__main__":
    main()
