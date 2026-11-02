from app.config import MODEL_CHEAP
from app.extract.llm import chat_json

SYSTEM = """You check whether a quoted sentence supports a claim.

You get a CLAIM and a QUOTE. The quote is the only evidence allowed.

Reply with JSON only: {"supported": true, "reason": "..."}

Rules:
- supported is true only if the quote, on its own, states or directly implies the claim.
- A quote that merely mentions the topic does not support a claim about a duty, a threshold, a
  deadline, or a consequence.
- If the claim drops a condition in the quote (for example a time limit, an applicability clause, a
  threshold), supported is false.
- If the claim is broader than the quote, supported is false.
- Do not use outside knowledge. Be strict.
"""


def supported(claim: str, quote: str) -> tuple[bool, int]:
    if not claim or not quote:
        return False, 0
    payload, usage = chat_json(
        SYSTEM,
        f"CLAIM:\n{claim}\n\nQUOTE:\n{quote}",
        model=MODEL_CHEAP,
        max_completion_tokens=256,
    )
    tokens = int(usage.get("total_tokens", 0))
    if not isinstance(payload, dict):
        return False, tokens
    return payload.get("supported") is True, tokens
