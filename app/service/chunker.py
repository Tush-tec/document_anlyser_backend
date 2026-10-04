from core.config import settings


def chunk_page(text: str, page_number: int,
               size: int | None = None, overlap: int | None = None) -> list[dict]:
    """Split ONE page into overlapping word windows.

    Input : text of a page, its page number
    Output: [{"text": "...", "page": 3}, ...]
    No Mongo, no vectors here - it only splits text.
    Chunks never cross page boundaries, so every chunk has exactly one page number.
    """
    size = size or settings.CHUNK_WORDS
    overlap = overlap if overlap is not None else settings.CHUNK_OVERLAP_WORDS

    words = text.split()
    if not words:
        return []

    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        window = words[start:start + size]
        chunks.append({"text": " ".join(window), "page": page_number})
        if start + size >= len(words):
            break
    return chunks
