import os
import pymupdf4llm


def extract_text_from_pdf(file: str) -> dict:
    """Extract text as markdown (preserves tables, headings, reading order)."""
    # Per-page markdown so we can keep page numbers
    page_chunks = pymupdf4llm.to_markdown(
        file,
        page_chunks=True,       # returns list[dict], one per page
        show_progress=False,
    )

    pages: list[tuple[int, str]] = []
    for index, chunk in enumerate(page_chunks):
        page_text = (chunk.get("text") or "").strip()
        pages.append((index + 1, page_text))

    full_text = "\n\n".join(text for _, text in pages).strip()
    word_count = sum(len(text.split()) for _, text in pages)

    return {
        "text": full_text,
        "pages": pages,
        "page_count": len(pages),
        "word_count": word_count,
    }


def extract_text_from_txt(file: str) -> dict:
    with open(file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    return {
        "text": text,
        "pages": [(1, text)],
        "page_count": 1,
        "word_count": len(text.split()),
    }


def extract_text(file_path: str) -> dict:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    raise ValueError("Unsupported file type. Only PDF and TXT files are allowed")
