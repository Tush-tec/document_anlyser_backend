import io
from dataclasses import dataclass
from pypdf import PdfReader
import docx

@dataclass
class ParsedDoc:
    pages: list[str]              # one string per page
    page_offsets: list[int]       # char offset in the concatenated text

def _join_pages(pages: list[str]) -> tuple[str, list[int]]:
    text, offsets, cursor = "", [], 0
    for p in pages:
        offsets.append(cursor)
        text += p + "\n"
        cursor = len(text)
    return text, offsets

def parse_pdf(data: bytes) -> ParsedDoc:
    reader = PdfReader(io.BytesIO(data))
    pages = [(pg.extract_text() or "").strip() for pg in reader.pages]
    _, offsets = _join_pages(pages)
    return ParsedDoc(pages=pages, page_offsets=offsets)

def parse_docx(data: bytes) -> ParsedDoc:
    d = docx.Document(io.BytesIO(data))
    # DOCX has no page concept — approximate one page per 3000 chars
    full = "\n".join(p.text for p in d.paragraphs)
    pages, buf = [], ""
    for line in full.splitlines(keepends=True):
        buf += line
        if len(buf) >= 3000:
            pages.append(buf); buf = ""
    if buf: pages.append(buf)
    _, offsets = _join_pages(pages)
    return ParsedDoc(pages=pages, page_offsets=offsets)

def parse_txt(data: bytes) -> ParsedDoc:
    full = data.decode("utf-8", errors="ignore")
    pages, buf = [], ""
    for line in full.splitlines(keepends=True):
        buf += line
        if len(buf) >= 3000:
            pages.append(buf); buf = ""
    if buf: pages.append(buf)
    _, offsets = _join_pages(pages)
    return ParsedDoc(pages=pages, page_offsets=offsets)

def parse(mime: str, data: bytes) -> ParsedDoc:
    if mime == "application/pdf": return parse_pdf(data)
    if mime in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",): return parse_docx(data)
    if mime.startswith("text/"): return parse_txt(data)
    raise ValueError(f"unsupported mime: {mime}")