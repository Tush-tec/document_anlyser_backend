import json
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from app.services.gemini_client import chat_model

RERANK_PROMPT = """You are a reranker. Given a question and N passages, return the
indices of the {keep} most relevant passages in order, as a JSON array of ints.
Only output JSON, nothing else.

Question: {q}

Passages:
{passages}
"""

@retry(stop=stop_after_attempt(2), wait=wait_exponential_jitter(initial=1, max=8))
def _call(q: str, passages: list[str], keep: int) -> list[int]:
    numbered = "\n".join(f"[{i}] {p[:600]}" for i, p in enumerate(passages))
    prompt = RERANK_PROMPT.format(q=q, passages=numbered, keep=keep)
    resp = chat_model().generate_content(prompt)
    raw = resp.text.strip().strip("`").replace("json\n", "")
    try:
        idxs = json.loads(raw)
        return [i for i in idxs if isinstance(i, int) and 0 <= i < len(passages)][:keep]
    except Exception:
        return list(range(min(keep, len(passages))))

def rerank(q: str, items: list[dict], keep: int = 5) -> list[dict]:
    if len(items) <= keep:
        return items
    idxs = _call(q, [it["text"] for it in items], keep)
    if not idxs:
        return items[:keep]
    return [items[i] for i in idxs]