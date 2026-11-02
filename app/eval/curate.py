import argparse
import json
import re
from pathlib import Path

from app.config import MODEL_CHEAP
from app.db import connect
from app.extract.llm import chat_json

DATASET = Path("evals/chat.jsonl")

META = re.compile(
    r"\b(which circular|what circular|which notification|what notification|"
    r"under what authority|what authority|under which (?:legal )?provisions?|"
    r"under which powers?|under which sections?|who issues|who issued|"
    r"what does .* cover|which directions and provisions|"
    r"purpose of the .* direction|what is the scope of the ongoing review)\b",
    re.IGNORECASE,
)

META_CLAUSE = re.compile(
    r"(in exercise of the powers|under the provisions of|these directions (?:are|have been) issued|"
    r"shall be read (?:along )?with|read with the|issued under section|by virtue of|"
    r"hereby issues?|come into force|comes into effect)",
    re.IGNORECASE,
)

BAD_QUESTION = re.compile(
    r"\b(notification|circular|powers?|provisions?|read along|read with|these directions|"
    r"legal|authority|section|issued|purpose|guidelines?|document|master direction)\b",
    re.IGNORECASE,
)

SYSTEM = """You write evaluation questions for a regulatory search system.

You get one clause. Write the question a compliance officer would ask whose answer is that clause.

Rules:
- Ask about the duty, the threshold, the deadline, the definition, or the procedure.
- Never mention a notification, circular, direction, section, power, provision, legal basis or purpose.
- Never ask what should be read with something.
- The question must be answerable from that clause alone.
- Maximum 20 words, one question mark.
- Return JSON only: {"question": "..."}
"""

STOP = {"the", "a", "an", "of", "to", "in", "for", "on", "and", "or", "is", "are", "be", "by", "with", "that", "this", "must", "should", "what", "which", "does", "do"}


def words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP}


def similar(left: str, right: str, threshold: float = 0.7) -> bool:
    a, b = words(left), words(right)
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= threshold


def acceptable(question: str, kept: list[str]) -> bool:
    if not question or META.search(question) or BAD_QUESTION.search(question):
        return False
    if len(question.split()) > 24:
        return False
    return not any(similar(question, other) for other in kept)


def rewrite(clause_text: str, kept: list[str]) -> str | None:
    for _ in range(2):
        payload, _usage = chat_json(
            SYSTEM,
            f"CLAUSE:\n{clause_text[:900]}",
            model=MODEL_CHEAP,
            max_completion_tokens=256,
        )
        question = payload.get("question") if isinstance(payload, dict) else None
        if isinstance(question, str):
            question = " ".join(question.split())
            if acceptable(question, kept):
                return question
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Replace document-identity questions in the eval set")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--top-up", type=int, default=0, help="add N new questions from fresh clauses")
    args = parser.parse_args()

    rows = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    answerable = [row for row in rows if row["answerable"]]

    connection = connect()
    kept: list[str] = []
    replaced = dropped = 0
    out: list[dict] = []

    for row in answerable:
        question = row["question"]
        duplicate = any(similar(question, other) for other in kept)
        if not META.search(question) and not duplicate:
            kept.append(question)
            out.append(row)
            continue

        clause = connection.execute("SELECT text FROM reg_clause WHERE id = %s", (row["gold_clause_id"],)).fetchone()
        if clause is None or META_CLAUSE.search(clause[0]):
            dropped += 1
            print(f"  drop (clause is a legal basis or reference) {question[:60]}")
            continue
        new_question = rewrite(clause[0], kept)
        if new_question is None:
            dropped += 1
            print(f"  drop  {question[:70]}")
            continue
        replaced += 1
        kept.append(new_question)
        out.append({**row, "question": new_question})
        print(f"  old: {question[:80]}")
        print(f"  new: {new_question}")

    added = 0
    if args.top_up:
        used = {row["gold_clause_id"] for row in out}
        candidates = connection.execute(
            """
            SELECT DISTINCT ON (d.id) c.id, c.text, d.id
            FROM reg_clause c
            JOIN reg_doc d ON d.id = c.reg_doc_id
            WHERE c.embedding IS NOT NULL
              AND length(c.text) BETWEEN 220 AND 900
              AND c.text ~* '\\m(shall|must|is|are|means|includes)\\M'
              AND c.id IN (
                  SELECT reg_clause_id FROM clause_in_force
                  WHERE valid_from <= current_date AND (valid_to IS NULL OR valid_to > current_date)
              )
            ORDER BY d.id, random()
            LIMIT 200
            """,
        ).fetchall()
        for clause_id, text, _doc in candidates:
            if added >= args.top_up:
                break
            if clause_id in used or META_CLAUSE.search(text):
                continue
            question = rewrite(text, kept)
            if question is None:
                continue
            kept.append(question)
            used.add(clause_id)
            out.append(
                {
                    "question": question,
                    "gold_clause_id": clause_id,
                    "gold_doc_id": _doc,
                    "gold_title": None,
                    "answerable": True,
                }
            )
            added += 1
            print(f"  add   {question}")

    connection.close()
    print(f"\nreplaced {replaced}, dropped {dropped}, added {added}, kept {len(out) - replaced}")

    if args.dry_run:
        return

    unanswerable = [row for row in rows if not row["answerable"]]
    DATASET.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in out + unanswerable) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(out) + len(unanswerable)} rows to {DATASET}")


if __name__ == "__main__":
    main()
