import json, time
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
import google.generativeai as genai
from app.core.config import settings
from app.schemas.query import Citation
from app.services.gemini_client import chat_model

SYSTEM = Path("app/prompts/system_qa.txt").read_text()

SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low", "insufficient"]},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "chunk_id": {"type": "string"},
                    "page": {"type": "integer"},
                    "quote": {"type": "string"},
                },
                "required": ["chunk_id", "page", "quote"],
            },
        },
    },
    "required": ["answer", "confidence", "citations"],
}

@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=16))
def _call_gemini(context: str, question: str) -> dict:
    model = genai.GenerativeModel(
        settings.GEMINI_CHAT_MODEL,
        system_instruction=SYSTEM,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": SCHEMA,
            "temperature": 0.1,
        },
    )
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    resp = model.generate_content(prompt)
    return json.loads(resp.text)

def build_context(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        parts.append(f"[CHUNK_ID:{c['chunk_id']}][PAGE:{c['page']}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)

def answer(question: str, chunks: list[dict]) -> tuple[str, list[Citation], str, int]:
    t0 = time.perf_counter()
    raw = _call_gemini(build_context(chunks), question)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    answer_text = raw.get("answer", "").strip()
    confidence = raw.get("confidence", "low")
    cits = [Citation(**c) for c in raw.get("citations", [])]
    return answer_text, cits, confidence, latency_ms