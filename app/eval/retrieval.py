import json
from pathlib import Path

from app.chat.retrieve import tsquery_from
from app.db import connect
from app.eval.constants import CHAT_EVAL_AS_OF

DATASET = Path("evals/chat.jsonl")
LIMIT = 60

LEXICAL = """
SELECT c.id, d.id
FROM reg_clause c
JOIN reg_doc d ON d.id = c.reg_doc_id
WHERE to_tsvector('english', c.text) @@ to_tsquery('english', %s)
  AND c.id IN (
      SELECT reg_clause_id FROM clause_in_force
      WHERE valid_from <= %s AND (valid_to IS NULL OR valid_to > %s)
  )
ORDER BY ts_rank_cd(to_tsvector('english', c.text), to_tsquery('english', %s)) DESC, c.id
LIMIT %s
"""


def summarize(rows: list[dict], candidates: dict[str, list[tuple[int, int]]]) -> dict:
    answerable = [row for row in rows if row["answerable"]]
    exact = 0
    same_document = 0
    for row in answerable:
        ranked = candidates.get(row["question"], [])
        exact += any(clause_id == row["gold_clause_id"] for clause_id, _ in ranked)
        same_document += any(doc_id == row["gold_doc_id"] for _, doc_id in ranked)
    total = len(answerable)
    return {
        "answerable": total,
        "as_of": CHAT_EVAL_AS_OF.isoformat(),
        "candidate_limit": LIMIT,
        "exact_clause_recall": round(exact / total, 3) if total else 0.0,
        "same_document_rate": round(same_document / total, 3) if total else 0.0,
        "no_candidates": sum(not candidates.get(row["question"]) for row in answerable),
    }


def main() -> None:
    rows = [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    candidates: dict[str, list[tuple[int, int]]] = {}
    with connect() as connection:
        for row in rows:
            if not row["answerable"]:
                continue
            query = tsquery_from(row["question"])
            ranked = (
                connection.execute(
                    LEXICAL,
                    (query, CHAT_EVAL_AS_OF, CHAT_EVAL_AS_OF, query, LIMIT),
                ).fetchall()
                if query
                else []
            )
            candidates[row["question"]] = ranked
    print(json.dumps(summarize(rows, candidates), indent=2))


if __name__ == "__main__":
    main()
