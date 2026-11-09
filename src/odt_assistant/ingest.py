from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

# __file__ means “this Python file.” Starting from src/odt_assistant/ingest.py, parents[2] resolves to the project root regardless of its folder name.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Document list: which URL page it fetches
DOCUMENTS = [
    {
        "name": "rest-endpoints",
        "url": (
            "https://docs.oracle.com/en/database/data-integration/"
            "data-transforms/dtapi/rest-endpoints.html"
        ),
    },
]


# Fetching the page
def fetch_page(url: str) -> bytes:
    host = urlsplit(url).hostname # It extracts the hostname (domain name) from a URL ex: docs.oracle.com from https://docs.oracle.com/en/database/data-integration/...
    if host != "docs.oracle.com":
        raise ValueError(f"Only docs.oracle.com URLs are allowed: {url}")

    # It requests the page and reads the response bytes. timeout=30 means it won’t wait forever if the site doesn’t respond
    request = Request(
        url,
        headers={"User-Agent": "ODT-Documentation-Learning-Project/0.1"},
    )
    with urlopen(request, timeout=30) as response:
        return response.read()

# Extracting readable text
def extract_text(html: bytes) -> tuple[str, str]:
    # Beautiful Soup reads the HTML structure so we can find its title and text.
    soup = BeautifulSoup(html, "html.parser")

    # It gets the page title. If the HTML has no title, it uses “Untitled page.”
    title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled page"

    # This removes page elements that are usually not useful as documentation evidence: scripts, style definitions, navigation, and footers.
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    # This gets the remaining text and cleans it line by line. It collapses extra spaces and skips a few page controls and the JavaScript notice that appeared in our first extraction.
    lines = []
    for line in soup.get_text("\n").splitlines():
        line = " ".join(line.split())
        if line and line not in {"Previous", "Next", "Sort by"}:
            if "JavaScript must be enabled" not in line:
                lines.append(line)

    # The function returns two things: the page title and the cleaned text. We keep the title separately because it helps identify the document.
    return title, "\n".join(lines)

# Running the ingestion
def main() -> None:
    # This defines the main task. These lines ensure the two folders exist. exist_ok=True means the script won’t fail if they already exist.
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # For every entry in the document list, it fetches the page, then extracts its title and text.
    for document in DOCUMENTS:
        html = fetch_page(document["url"])
        title, text = extract_text(html)

        # This saves the original HTML. Keeping it lets us process the downloaded page again later without fetching it again.
        (RAW_DIR / f"{document['name']}.html").write_bytes(html)

        # This prepares the processed file. It keeps the title, source URL, and retrieval time alongside the text. The source URL will be useful later when the assistant cites its evidence.
        processed = (
            f"Title: {title}\n"
            f"Source: {document['url']}\n"
            f"Retrieved: {datetime.now(timezone.utc).isoformat()}\n\n"
            f"{text}\n"
        )
        (PROCESSED_DIR / f"{document['name']}.txt").write_text(
            processed,
            encoding="utf-8",
        )

        print(f"Saved {document['name']}: {len(text)} text characters")


# Starting the script
if __name__ == "__main__":
    main()
