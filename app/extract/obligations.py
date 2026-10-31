import re
from dataclasses import dataclass, field
from datetime import date, datetime

CUE_RE = re.compile(
    r"\b(shall|must|shall not|may not|required to|permitted to|is to|are to)\b",
    re.IGNORECASE,
)

FACETS = {
    "payments_bank": r"payments? bank",
    "small_finance_bank": r"small finance bank",
    "cooperative_bank": r"co-?operative bank|\bucbs?\b|urban co-?operative bank",
    "bank": r"\bbanks?\b|banking compan",
    "nbfc": r"\bnbfcs?\b|non[- ]banking financial compan",
    "aifi": r"all india financial institution",
    "housing_finance": r"housing finance compan|\bhfcs?\b",
    "payment_system_operator": r"payment system operator|\bps[os]\b",
    "prepaid_instrument": r"prepaid payment instrument|\bppis?\b",
    "mutual_fund": r"mutual fund",
    "stock_broker": r"stock broker",
    "depository": r"depositor(?:y|ies)",
    "investment_adviser": r"investment advis",
    "research_analyst": r"research analyst",
    "debenture_trustee": r"debenture trustee",
    "aif": r"alternative investment fund|\baifs?\b",
    "invit": r"\binvits?\b",
    "reit": r"\breits?\b",
    "regulated_entity": r"regulated entit",
}

EFFECTIVE_RE = re.compile(
    r"(?:with effect from|w\.?\s?e\.?\s?f\.?|effective from|come into force (?:on|from)|"
    r"comes into force (?:on|from)|come into effect (?:on|from)|comes into effect (?:on|from)|"
    r"shall (?:come into|be in) (?:force|effect) (?:on|from))"
    r"\s*(?:the\s*)?"
    r"(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s*\d{4}|[A-Za-z]+\s+\d{1,2},?\s*\d{4}|\d{2}[-/]\d{2}[-/]\d{4})",
    re.IGNORECASE,
)

DATE_FORMATS = ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y", "%d-%m-%Y", "%d/%m/%Y")

MODALITIES = {"shall", "shall_not", "may"}
NON_OBLIGATION_ACTION_RE = re.compile(
    r"\b(come into (force|effect)|be in (force|effect)|be deemed|be construed|"
    r"be subject to the provisions|be read with|be applicable to the extent|"
    r"be called|be referred to|\bsupersed|\brepeal|\bamended? the)\b",
    re.IGNORECASE,
)
MAX_ACTION_CHARS = 400
MAX_TEXT_CHARS = 6000

RULES = """Rules:
- modality is "shall" for a duty, "shall_not" for a prohibition, "may" for an explicit permission.
- actor is who must act, as written (for example "regulated entity", "banks", "NBFCs").
- action is the required behaviour in plain words. Do not add facts that are not in the text.
- condition is the trigger, deadline or scope, or "" when there is none.
- If the text states no obligation (definitions, explanations, references, headings), use an empty list.
- Never invent obligations. Never cite clause numbers. Return at most 4 obligations per text.
- Commencement and definition text is NOT an obligation. If the only content is when the
  directions take effect, what a term means, what a document is called, or that something
  "shall be deemed" or "shall be construed" in a certain way, use an empty list.
- An obligation must describe a concrete thing an actor must do, stop doing, or may do.
- The regulator is not the actor. Statements where RBI or SEBI issues, supersedes, amends or
  repeals something are NOT obligations, and neither are bare statements that a rule "shall apply".

Examples of correct answers:
Text: "2. Every bank shall submit the return by the 10th day of the following month."
{"obligations": [{"is_obligation": true, "modality": "shall", "actor": "every bank", "action": "submit the return by the 10th day of the following month", "condition": ""}]}

Text: "These directions shall come into force on April 01, 2025."
{"obligations": []}

Text: "For the purposes of these directions, customer means a person who holds an account."
{"obligations": []}

Text: "Entities shall not share customer data with third parties without consent."
{"obligations": [{"is_obligation": true, "modality": "shall_not", "actor": "entities", "action": "share customer data with third parties without consent", "condition": ""}]}
"""

SYSTEM_PROMPT = f"""You extract obligations from Indian financial regulation written by RBI or SEBI.

Reply with JSON only, shaped exactly like:
{{"obligations": [{{"is_obligation": true, "modality": "shall", "actor": "...", "action": "...", "condition": "..."}}]}}

{RULES}"""

BATCH_SYSTEM_PROMPT = f"""You extract obligations from Indian financial regulation written by RBI or SEBI.

You will receive several numbered texts, each introduced by a line like [0], [1], [2].
Reply with JSON only, shaped exactly like:
{{"results": [{{"index": 0, "obligations": [{{"is_obligation": true, "modality": "shall", "actor": "...", "action": "...", "condition": "..."}}]}}]}}

Return exactly one result object per input index, in the same order, even when a text has none.

{RULES}"""


@dataclass
class ObligationRecord:
    ordinal: int
    modality: str
    actor: str
    action: str
    condition: str
    scope_entities: list[str] = field(default_factory=list)
    valid_from: date | None = None


def is_candidate(text: str) -> bool:
    return bool(CUE_RE.search(text))


def extract_facets(text: str) -> list[str]:
    scrubbed = re.sub(r"\breserve bank(?: of india)?\b|\brbi\b", " ", text, flags=re.IGNORECASE)
    return [
        name
        for name, pattern in FACETS.items()
        if re.search(pattern, scrubbed, re.IGNORECASE)
    ]


def parse_valid_from(text: str) -> date | None:
    match = EFFECTIVE_RE.search(text)
    if match is None:
        return None
    raw = match.group(1).strip()
    variants = {raw, re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", raw)}
    variants |= {variant.replace(",", "") for variant in list(variants)}
    for variant in variants:
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(variant, fmt).date()
            except ValueError:
                continue
    return None


def clean(value) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:MAX_ACTION_CHARS]


def validate(payload, text: str, source_date: date | None = None) -> list[ObligationRecord]:
    raw = payload if isinstance(payload, list) else payload.get("obligations")
    if not isinstance(raw, list):
        return []

    facets = extract_facets(text)
    valid_from = parse_valid_from(text) or source_date
    records: list[ObligationRecord] = []
    seen: set[str] = set()

    for item in raw:
        if not isinstance(item, dict) or not item.get("is_obligation"):
            continue
        modality = str(item.get("modality", "")).strip().lower()
        actor = clean(item.get("actor"))
        action = clean(item.get("action"))
        if modality not in MODALITIES or not action:
            continue
        key = action.lower()
        if len(action) < 12:
            continue
        if NON_OBLIGATION_ACTION_RE.search(action):
            continue
        if re.search(r"\b(reserve bank|rbi|sebi|board)\b", actor, re.IGNORECASE):
            continue
        if key in seen:
            continue
        seen.add(key)
        records.append(
            ObligationRecord(
                ordinal=len(records),
                modality=modality,
                actor=actor,
                action=action,
                condition=clean(item.get("condition")),
                scope_entities=facets,
                valid_from=valid_from,
            )
        )
    return records


def build_user_prompt(title: str, doc_type: str, text: str) -> str:
    return (
        f"Document type: {doc_type}\n"
        f"Document title: {title}\n"
        f"Text:\n{text[:MAX_TEXT_CHARS]}"
    )


def build_batch_prompt(entries: list[tuple[int, str]]) -> str:
    return "\n\n".join(f"[{index}]\n{text[:MAX_TEXT_CHARS]}" for index, text in entries)


def batch_results(payload, count: int) -> list[dict]:
    raw = payload if isinstance(payload, list) else payload.get("results")
    if not isinstance(raw, list):
        return [{} for _ in range(count)]
    by_index = {}
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("index"), int):
            by_index[item["index"]] = item
    return [by_index.get(index, {}) for index in range(count)]
