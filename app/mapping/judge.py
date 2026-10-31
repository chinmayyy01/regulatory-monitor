import re
from dataclasses import dataclass

from app.config import MODEL_JUDGE
from app.extract.llm import chat_json
from app.search.span import find_span

VERDICTS = {"satisfied", "partial", "missing"}
COMMITMENT_RE = re.compile(
    r"\b(?:shall|must|will)\b|\bwe\s+(?:ensure|verify|conduct|obtain|maintain|report|retain|appoint|review)\b",
    re.IGNORECASE,
)
MAX_CANDIDATES = 5

SYSTEM_PROMPT = """You compare one regulatory obligation with a company's own policy clauses.

You get the obligation, then numbered policy clauses. Decide whether the policy already commits to
what the regulation requires.

Reply with JSON only:
{"clause_index": 0, "verdict": "satisfied", "confidence": 0.0, "evidence_regulation": "...", "evidence_policy": "...", "reason": "..."}

Rules:
- verdict "satisfied": a clause covers the requirement, in substance, not just in topic.
- verdict "partial": a clause covers part of it, or covers it with a gap (no timeline, no owner, weaker duty).
- verdict "missing": no clause covers it. Use clause_index -1 and empty quotes.
- evidence_regulation must be an exact quote from the obligation text.
- evidence_policy must be an exact quote from the chosen clause. Never paraphrase.
- If you cannot quote it, you cannot claim it. Prefer "missing" over a guessed match.
- Be strict. A policy that mentions a topic without a duty is not "satisfied".
"""


@dataclass
class Judgment:
    clause_index: int
    verdict: str
    confidence: float
    evidence_regulation: str
    evidence_policy: str
    reason: str
    regulation_span: dict | None = None
    policy_span: dict | None = None


def validate(payload: dict, obligation_text: str, candidates: list[str]) -> Judgment | None:
    verdict = str(payload.get("verdict", "")).strip().lower()
    if verdict not in VERDICTS:
        return None

    try:
        index = int(payload.get("clause_index", -1))
    except (TypeError, ValueError):
        index = -1

    if verdict == "missing":
        return Judgment(-1, "missing", _confidence(payload.get("confidence")), "", "", _reason(payload))

    if index < 0 or index >= len(candidates):
        return None

    regulation_quote = _clean(payload.get("evidence_regulation"))
    policy_quote = _clean(payload.get("evidence_policy"))
    if not regulation_quote or not policy_quote:
        return None

    regulation_span = find_span(obligation_text, regulation_quote)
    policy_span = find_span(candidates[index], policy_quote)
    if regulation_span is None or policy_span is None:
        return None

    reason = _reason(payload)
    if verdict == "satisfied" and not COMMITMENT_RE.search(policy_quote):
        verdict = "partial"
        reason = f"{reason} [downgraded: evidence describes a practice, not a commitment]"

    return Judgment(
        index,
        verdict,
        _confidence(payload.get("confidence")),
        regulation_quote,
        policy_quote,
        reason,
        regulation_span,
        policy_span,
    )


def _clean(value) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:600]


def _confidence(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def _reason(payload: dict) -> str:
    return _clean(payload.get("reason"))[:400]


def build_prompt(obligation_text: str, candidates: list[str]) -> str:
    blocks = [
        f"OBLIGATION:\n{obligation_text}",
        "",
        "POLICY CLAUSES:",
    ]
    for index, text in enumerate(candidates):
        blocks.append(f"[{index}] {text[:1200]}")
    return "\n".join(blocks)


def judge(obligation_text: str, candidates: list[str]) -> Judgment | None:
    if not candidates:
        return Judgment(-1, "missing", 1.0, "", "", "no policy clauses available")
    payload, _usage = chat_json(SYSTEM_PROMPT, build_prompt(obligation_text, candidates), model=MODEL_JUDGE)
    if isinstance(payload, list):
        payload = payload[0] if payload and isinstance(payload[0], dict) else {}
    return validate(payload, obligation_text, candidates)
