from dataclasses import dataclass

from app.chat.entail import supported
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
    unsupported: int = 0


def build_prompt(question: str, sources) -> str:
    blocks = [f"QUESTION:\n{question}", "", "SOURCES:"]
    for index, source in enumerate(sources):
        blocks.append(f"[{index}] ({source.kind}) {source.label}\n{source.text[:900]}")
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


def ask_with_usage(question: str, sources) -> tuple[Answer, int]:
    if not sources:
        return Answer([], True, 0), 0
    payload, usage = chat_json(
        SYSTEM_PROMPT,
        build_prompt(question, sources),
        model=MODEL_WORKER,
        max_completion_tokens=1024,
    )
    if isinstance(payload, list):
        payload = payload[0] if payload and isinstance(payload[0], dict) else {}
    answer = parse(payload, sources)

    tokens = int(usage.get("total_tokens", 0))
    kept: list[Claim] = []
    unsupported = 0
    for claim in answer.claims:
        ok = False
        for citation in claim.citations:
            passes, used = supported(claim.text, citation.quote)
            tokens += used
            ok = ok or passes
        if ok:
            kept.append(claim)
        else:
            unsupported += 1

    return (
        Answer(kept, answer.insufficient or not kept, answer.rejected, unsupported),
        tokens,
    )


def ask(question: str, sources) -> Answer:
    return ask_with_usage(question, sources)[0]
