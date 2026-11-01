import argparse
import json
import re
from pathlib import Path

from app.db import connect
from app.rate import TokenPacer
from app.extract.llm import chat_json

OUT = Path("evals/chat.jsonl")

CANDIDATES = """
SELECT DISTINCT ON (d.id)
       c.id, c.text, c.section_no, d.id AS doc_id, d.title
FROM reg_clause c
JOIN reg_doc d ON d.id = c.reg_doc_id
WHERE c.embedding IS NOT NULL
  AND length(c.text) BETWEEN 220 AND 900
  AND c.text ~* '\\m(shall|must|is|are|means|includes)\\M'
  AND c.id IN (
      SELECT reg_clause_id FROM clause_in_force
      WHERE valid_from <= current_date AND (valid_to IS NULL OR valid_to > current_date)
  )
ORDER BY d.id, c.id
LIMIT %s
"""

UNANSWERABLE = [
    "What is our policy on cryptocurrency trading and virtual digital assets?",
    "How many employees does the company have in its Pune office?",
    "What is our internal escalation matrix for IT incidents?",
    "What did the board decide about executive bonuses this year?",
    "What is our marketing spend for the current quarter?",
    "Which external law firm do we retain for litigation?",
    "What is our policy on remote work for engineering staff?",
    "How much capital did we raise in our last funding round?",
]

SYSTEM = """You write evaluation questions for a regulatory search system.

You get numbered clauses. For each clause, write the question a compliance officer would ask whose
answer is that clause.

Rules:
- Ask about the obligation, the procedure, the threshold, the definition, or the deadline.
- Never ask about the document itself: no "which circular", "what authority", "who issued",
  "what does this notification cover", no titles, no circular numbers.
- The question must be answerable from that clause alone.
- Do not copy any phrase longer than six words from the clause.
- Maximum 20 words.
- Return JSON only: {"results": [{"index": 0, "question": "..."}]}
- Return one result per index, in order.
"""

META = re.compile(
    r"\b(which circular|what circular|under what authority|what authority|who issues|who issued|"
    r"what does .* cover|circular no|notification no|document title|which notification)\b",
    re.IGNORECASE,
)
STOP = {"the", "a", "an", "of", "to", "in", "for", "on", "and", "or", "is", "are", "be", "by", "with", "that", "this"}


def words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP}


def similar(left: str, right: str, threshold: float = 0.7) -> bool:
    a, b = words(left), words(right)
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= threshold


def build_prompt(rows) -> str:
    blocks = []
    for index, row in enumerate(rows):
        text = " ".join(row[1].split())[:900]
        blocks.append(f"[{index}] {text}")
    return "\n\n".join(blocks)


def select_clauses(connection, limit: int):
    rows = connection.execute(CANDIDATES, (limit,)).fetchall()
    chosen, titles = [], []
    for row in rows:
        title = row[4]
        if any(similar(title, kept, 0.6) for kept in titles):
            continue
        chosen.append(row)
        titles.append(title)
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a chat evaluation set from the corpus")
    parser.add_argument("--answerable", type=int, default=40)
    parser.add_argument("--batch", type=int, default=3)
    args = parser.parse_args()

    connection = connect()
    rows = select_clauses(connection, args.answerable * 2)
    connection.close()

    pacer = TokenPacer()
    records = []
    for start in range(0, len(rows), args.batch):
        chunk = rows[start : start + args.batch]
        payload, usage = chat_json(
            SYSTEM, build_prompt(chunk), max_completion_tokens=2048
        )
        pacer.wait(int(usage.get("total_tokens", 0)), 10)
        results = payload.get("results") if isinstance(payload, dict) else payload
        if not isinstance(results, list):
            results = []
        by_index = {
            item.get("index"): item.get("question")
            for item in results
            if isinstance(item, dict)
        }
        for index, row in enumerate(chunk):
            question = by_index.get(index)
            if not question:
                continue
            question = " ".join(question.split())
            if META.search(question):
                continue
            if any(similar(question, item["question"]) for item in records):
                continue
            if len(records) >= args.answerable:
                break
            records.append(
                {
                    "question": question,
                    "gold_clause_id": row[0],
                    "gold_doc_id": row[3],
                    "gold_title": row[4],
                    "answerable": True,
                }
            )
        print(f"  generated {len(records)}/{len(rows)}", flush=True)

    for question in UNANSWERABLE:
        records.append(
            {
                "question": question,
                "gold_clause_id": None,
                "gold_doc_id": None,
                "gold_title": None,
                "answerable": False,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} rows to {OUT}")


if __name__ == "__main__":
    main()
