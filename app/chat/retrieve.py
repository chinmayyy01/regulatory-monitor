import re
from dataclasses import dataclass
from datetime import date

from app.search.embed import embed_texts, vector_literal

RRF_K = 60
STOP_WORDS = {
    "the", "and", "for", "that", "this", "with", "from", "what", "when",
    "does", "are", "was", "were", "have", "has", "our", "their", "which",
    "how", "who", "why", "can", "should", "must", "into", "about", "any",
}

IN_FORCE_FILTER = """
c.id IN (
    SELECT reg_clause_id FROM clause_in_force
    WHERE valid_from <= %s AND (valid_to IS NULL OR valid_to > %s)
)
"""

DENSE_REGULATION = f"""
SELECT c.id, c.text, d.title, c.section_no
FROM reg_clause c
JOIN reg_doc d ON d.id = c.reg_doc_id
WHERE c.embedding IS NOT NULL AND {IN_FORCE_FILTER}
ORDER BY c.embedding <=> %s::vector
LIMIT %s
"""

LEXICAL_REGULATION = f"""
SELECT c.id, c.text, d.title, c.section_no
FROM reg_clause c
JOIN reg_doc d ON d.id = c.reg_doc_id
WHERE to_tsvector('english', c.text) @@ to_tsquery('english', %s) AND {IN_FORCE_FILTER}
ORDER BY ts_rank_cd(to_tsvector('english', c.text), to_tsquery('english', %s)) DESC
LIMIT %s
"""

DENSE_POLICY = """
SELECT tc.id, tc.text, td.title, tc.section_no
FROM tenant_clause tc
JOIN tenant_doc td ON td.id = tc.tenant_doc_id
WHERE td.tenant_id = %s AND tc.embedding IS NOT NULL
ORDER BY tc.embedding <=> %s::vector
LIMIT %s
"""

LEXICAL_POLICY = """
SELECT tc.id, tc.text, td.title, tc.section_no
FROM tenant_clause tc
JOIN tenant_doc td ON td.id = tc.tenant_doc_id
WHERE td.tenant_id = %s
  AND to_tsvector('english', tc.text) @@ to_tsquery('english', %s)
ORDER BY ts_rank_cd(to_tsvector('english', tc.text), to_tsquery('english', %s)) DESC
LIMIT %s
"""


@dataclass
class Source:
    kind: str
    clause_id: int
    label: str
    text: str


def tsquery_from(question: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]{4,}", question.lower())
    keep = [word for word in words if word not in STOP_WORDS]
    if not keep:
        keep = words
    return " | ".join(dict.fromkeys(keep))


def reciprocal_rank_fusion(ranked_lists: list[list[tuple]], limit: int) -> list[tuple]:
    scores: dict[int, float] = {}
    items: dict[int, tuple] = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            key = item[0]
            items[key] = item
            scores[key] = scores.get(key, 0.0) + 1 / (RRF_K + rank + 1)
    ordered = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
    return [items[key] for key, _ in ordered[:limit]]


def _label(kind: str, title: str, section_no: str | None) -> str:
    section = f" · s.{section_no}" if section_no else ""
    return f"{kind} · {title[:70]}{section}"


def regulation_sources(connection, question: str, embedding: list[float], as_of: date | None, limit: int = 6) -> list[Source]:
    when = as_of or date.today()
    literal = vector_literal(embedding)
    dense = connection.execute(DENSE_REGULATION, (when, when, literal, limit * 2)).fetchall()
    lexical = connection.execute(
        LEXICAL_REGULATION, (tsquery_from(question), when, when, tsquery_from(question), limit * 2)
    ).fetchall()
    merged = reciprocal_rank_fusion([dense, lexical], limit)
    return [
        Source("regulation", row[0], _label("regulation", row[2], row[3]), row[1])
        for row in merged
    ]


def policy_sources(connection, tenant_id: int, question: str, embedding: list[float], limit: int = 6) -> list[Source]:
    literal = vector_literal(embedding)
    dense = connection.execute(DENSE_POLICY, (tenant_id, literal, limit * 2)).fetchall()
    lexical = connection.execute(
        LEXICAL_POLICY, (tenant_id, tsquery_from(question), tsquery_from(question), limit * 2)
    ).fetchall()
    merged = reciprocal_rank_fusion([dense, lexical], limit)
    return [
        Source("policy", row[0], _label("policy", row[2], row[3]), row[1])
        for row in merged
    ]


def gather(connection, tenant_id: int, question: str, as_of: date | None = None) -> list[Source]:
    embedding = embed_texts([question])[0]
    return regulation_sources(connection, question, embedding, as_of) + policy_sources(
        connection, tenant_id, question, embedding
    )
