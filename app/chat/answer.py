from dataclasses import dataclass

from app.config import MODEL_WORKER
from app.extract.llm import chat_json
from app.search.span import find_span

SYSTEM_PROMPT = """You answer questions about Indian financial regulation and a company's own policies.

You get numbered SOURCES. Use only those sources. Never use outside knowledge.

Reply with JSON only:
{"insufficient": false, "claims": [{"text": "...", "citations": [{"source": 0, "quote": "..."}]}]}

Rules:
- Each claim is one sentence, in plain language.
- Every claim must cite at least one source by its number.
- "quote" must be copied word for word from that source. No paraphrasing inside a quote.
- If the sources answer only part of the question, answer that part and leave the rest out.
- Set "insufficient": true only when nothing in the sources supports an answer. Do not pad with
  general knowledge to avoid saying you do not know.
- Never cite a source you did not quote from.
- Do not give legal advice. State what the sources say.
"""


@dataclass
class Citation:
    source: int
    kind: str
    clause_id: int
    label: str
    quote: str
    span: dict


@dataclass
class Claim:
    text: str
    citations: list[Citation]


@dataclass
class Answer:
    claims: list[Claim]
    insufficient: bool
    rejected: int


def build_prompt(question: str, sources) -> str:
    blocks = [f"QUESTION:\n{question}", "", "SOURCES:"]
    for index, source in enumerate(sources):
        blocks.append(f"[{index}] ({source.kind}) {source.label}\n{source.text[:1200]}")
    return "\n\n".join(blocks)


def _clean(value) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:800]


def parse(payload, sources) -> Answer:
    if not isinstance(payload, dict):
        return Answer([], True, 0)

    raw_claims = payload.get("claims")
    if not isinstance(raw_claims, list):
        raw_claims = []

    claims: list[Claim] = []
    rejected = 0

    for item in raw_claims:
        if not isinstance(item, dict):
            rejected += 1
            continue
        text = _clean(item.get("text"))
        citations = item.get("citations")
        if not text or not isinstance(citations, list) or not citations:
            rejected += 1
            continue

        verified: list[Citation] = []
        for citation in citations:
            if not isinstance(citation, dict):
                continue
            try:
                index = int(citation.get("source", -1))
            except (TypeError, ValueError):
                continue
            if index < 0 or index >= len(sources):
                continue
            quote = _clean(citation.get("quote"))
            if not quote:
                continue
            source = sources[index]
            span = find_span(source.text, quote)
            if span is None:
                continue
            verified.append(
                Citation(index, source.kind, source.clause_id, source.label, quote, span)
            )

        if not verified:
            rejected += 1
            continue
        claims.append(Claim(text, verified))

    insufficient = bool(payload.get("insufficient")) or not claims
    return Answer(claims, insufficient, rejected)


def ask(question: str, sources) -> Answer:
    if not sources:
        return Answer([], True, 0)
    payload, _usage = chat_json(SYSTEM_PROMPT, build_prompt(question, sources), model=MODEL_WORKER)
    if isinstance(payload, list):
        payload = payload[0] if payload and isinstance(payload[0], dict) else {}
    return parse(payload, sources)
