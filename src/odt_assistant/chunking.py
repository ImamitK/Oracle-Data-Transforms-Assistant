import json # json saves chunks in a structured format that another part of the app can read later.
from pathlib import Path # Path builds paths to the input and output files.

# project folder based on its own location, then points to the processed text it will read and the JSON file it will create.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "rest-endpoints.txt"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "rest-endpoints.chunks.json"

# SECTION_NAMES lists the API group headings in this page, such as Connection, Project, and Workflow.
SECTION_NAMES = {
    "About",
    "Authentication",
    "Connection",
    "DataFlow",
    "DataLoad",
    "DesignMigration",
    "Folder",
    "Job",
    "Project",
    "Schedule",
    "Variable",
    "Workflow",
}

# The function reads the cleaned document line by line. It ignores lines until it reaches a known section heading, which skips the page title and table controls.
# When it reaches another section heading, it closes the current chunk and starts a new one.
# At the end, it saves the final section.
def split_into_chunks(lines: list[str]) -> list[str]:
    chunks = []
    current_lines = []

    for line in lines:
        if line in SECTION_NAMES:
            if current_lines:
                chunks.append("\n".join(current_lines))
            current_lines = [line]
        elif current_lines:
            current_lines.append(line)

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Processed document not found: {INPUT_FILE}")

    # Reads the processed text file and separates its metadata—title, source URL, retrieval time—from the documentation body. partition uses the first blank line as the boundary
    document = INPUT_FILE.read_text(encoding="utf-8")
    header, separator, body = document.partition("\n\n")

    if not separator:
        raise ValueError("Expected document metadata followed by a blank line.")

    metadata = {}
    for line in header.splitlines():
        key, colon, value = line.partition(":")
        if colon:
            metadata[key.strip().lower()] = value.strip()

    body_lines = [line.strip() for line in body.splitlines() if line.strip()]
    chunk_texts = split_into_chunks(body_lines)

    # Carries some ending lines into the next chunk to preserve context at the boundary. So the chunks overlap; they aren’t strictly separate pieces.
    chunks = []
    for number, chunk_text in enumerate(chunk_texts, start=1):
        chunks.append(
            {
                "chunk_id": f"rest-endpoints-{number:03d}",
                "title": metadata.get("title", "Untitled document"),
                "source_url": metadata.get("source", ""),
                "retrieved_at": metadata.get("retrieved", ""),
                "text": chunk_text,
            }
        )

    # Saves each chunk as JSON with its own ID and the original source URL. Later, retrieval can return that URL with matching evidence.
    OUTPUT_FILE.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Created {len(chunks)} chunks in {OUTPUT_FILE.name}")
    for chunk in chunks:
        print(f"{chunk['chunk_id']}: {len(chunk['text'])} characters")


if __name__ == "__main__":
    main()
