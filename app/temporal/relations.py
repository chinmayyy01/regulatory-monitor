import re
from dataclasses import dataclass
from datetime import date

AMEND_RE = re.compile(
    r"paragraph\s+(\d{1,3}(?:\.\d{1,3}){0,3})\s+(?:shall be|is|are)\s+"
    r"(amended|substituted|inserted|deleted|omitted)",
    re.IGNORECASE,
)
REPEAL_RE = re.compile(r"\b(?:stands?|is|are)\s+(?:hereby\s+)?repealed\b", re.IGNORECASE)
SUPERSEDE_RE = re.compile(r"shall\s+(?:supersede|stand superseded by)\b", re.IGNORECASE)

SENTENCE_END = re.compile(r"(?<=[.;])\s+")
MIN_SIMILARITY = 0.6
STOP_WORDS = {
    "the", "of", "and", "to", "in", "a", "an", "for", "on", "by", "with",
    "reserve", "bank", "india", "sebi", "directions", "direction", "circular",
    "amendments", "amendment", "2024", "2025", "2026",
}


@dataclass
class RelationCandidate:
    kind: str
    clause_ref: str | None
    target_text: str


def tokens(title: str) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    return {word for word in cleaned.split() if word not in STOP_WORDS and len(word) > 2}


def title_similarity(left: str, right: str) -> float:
    left_tokens, right_tokens = tokens(left), tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def sentence_around(text: str, match: re.Match) -> str:
    start = 0
    for boundary in SENTENCE_END.finditer(text[: match.start()]):
        start = boundary.end()
    end_match = SENTENCE_END.search(text, match.end())
    end = end_match.start() if end_match else len(text)
    return " ".join(text[start:end].split())[:400]


def extract(text: str) -> list[RelationCandidate]:
    found: list[RelationCandidate] = []
    seen: set[tuple[str, str | None]] = set()

    for match in AMEND_RE.finditer(text):
        clause_ref = match.group(1)
        key = ("amends", clause_ref)
        if key in seen:
            continue
        seen.add(key)
        found.append(RelationCandidate("amends", clause_ref, sentence_around(text, match)))

    if REPEAL_RE.search(text):
        match = REPEAL_RE.search(text)
        found.append(RelationCandidate("repeals", None, sentence_around(text, match)))

    match = SUPERSEDE_RE.search(text)
    if match:
        found.append(RelationCandidate("supersedes", None, sentence_around(text, match)))

    return found


def resolve_target(connection, target_text: str) -> int | None:
    rows = connection.execute("SELECT id, title FROM reg_doc").fetchall()
    scored = [(title_similarity(target_text, title), doc_id) for doc_id, title in rows]
    scored = [item for item in scored if item[0] >= MIN_SIMILARITY]
    if not scored:
        return None
    scored.sort(reverse=True)
    if len(scored) > 1 and scored[0][0] - scored[1][0] < 0.05:
        return None
    return scored[0][1]


INSERT = """
INSERT INTO reg_relation
    (src_doc_id, dst_doc_id, kind, clause_ref, target_text, effective_from, method)
VALUES (%s, %s, %s, %s, %s, %s, 'regex')
ON CONFLICT DO NOTHING
"""


EXISTS = """
SELECT 1 FROM reg_relation
WHERE src_doc_id = %s AND kind = %s AND clause_ref IS NOT DISTINCT FROM %s
"""


def store(connection, src_doc_id: int, dst_doc_id: int | None, candidate: RelationCandidate, effective_from: date | None) -> bool:
    existing = connection.execute(
        EXISTS, (src_doc_id, candidate.kind, candidate.clause_ref)
    ).fetchone()
    if existing:
        return False
    connection.execute(
        INSERT,
        (
            src_doc_id,
            dst_doc_id,
            candidate.kind,
            candidate.clause_ref,
            candidate.target_text,
            effective_from,
        ),
    )
    return True
