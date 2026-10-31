import argparse
import os
import time

from app.config import MODEL_WORKER
from app.db import apply_schema, connect
from app.extract.llm import LlmError, chat_json
from app.extract.obligations import (
    BATCH_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    batch_results,
    build_batch_prompt,
    build_user_prompt,
    validate,
)

CANDIDATES = r"""
SELECT c.id, c.text, d.title, d.doc_type, d.date_issued
FROM reg_clause c
JOIN reg_doc d ON d.id = c.reg_doc_id
WHERE c.text ~* '\m(shall|must|may not|required to|permitted to|is to|are to)\M'
  AND NOT EXISTS (SELECT 1 FROM obligation o WHERE o.reg_clause_id = c.id)
ORDER BY d.date_issued DESC NULLS LAST, c.id
LIMIT %s
"""

INSERT = r"""
INSERT INTO obligation
    (reg_clause_id, ordinal, modality, actor, action, condition, scope_entities, valid_from, valid_to, model)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, %s)
ON CONFLICT (reg_clause_id, ordinal) DO NOTHING
"""

MAX_CONSECUTIVE_FAILURES = 5
TPM_LIMIT = int(os.getenv("GROQ_TPM_LIMIT", "8000"))


def pace(tokens_used: int, floor: float) -> None:
    time.sleep(max(floor, tokens_used * 60 / TPM_LIMIT))


def insert_records(connection, clause_id, records, dry_run) -> int:
    if dry_run:
        return len(records)
    for record in records:
        connection.execute(
            INSERT,
            (
                clause_id,
                record.ordinal,
                record.modality,
                record.actor,
                record.action,
                record.condition,
                record.scope_entities,
                record.valid_from,
                MODEL_WORKER,
            ),
        )
    connection.commit()
    return len(records)


def extract_one(connection, row, args) -> tuple[int, int]:
    clause_id, text, title, doc_type, date_issued = row
    payload, usage = chat_json(SYSTEM_PROMPT, build_user_prompt(title, doc_type, text))
    records = validate(payload, text, date_issued)
    return insert_records(connection, clause_id, records, args.dry_run), int(usage.get("total_tokens", 0))


def process(connection, rows, args) -> tuple[int, int, int]:
    stored = failed = tokens = 0
    consecutive = 0

    for start in range(0, len(rows), args.batch):
        chunk = rows[start : start + args.batch]
        entries = [(index, row[1]) for index, row in enumerate(chunk)]

        try:
            payload, usage = chat_json(BATCH_SYSTEM_PROMPT, build_batch_prompt(entries))
        except LlmError as error:
            print(f"  batch at {start} failed ({error}); retrying one by one", flush=True)
            for row in chunk:
                try:
                    count, used = extract_one(connection, row, args)
                except LlmError as inner:
                    failed += 1
                    consecutive += 1
                    print(f"  clause {row[0]} failed: {inner}", flush=True)
                    if consecutive >= MAX_CONSECUTIVE_FAILURES:
                        print("  too many consecutive failures, stopping", flush=True)
                        return stored, failed, tokens
                    continue
                consecutive = 0
                stored += count
                tokens += used
                pace(used, args.sleep)
            continue

        consecutive = 0
        tokens += int(usage.get("total_tokens", 0))
        results = batch_results(payload, len(chunk))

        for row, item in zip(chunk, results):
            records = validate(item, row[1], row[4])
            stored += insert_records(connection, row[0], records, args.dry_run)
            if args.dry_run and records:
                print(f"  [dry] {row[0]}: {len(records)} obligation(s) | {records[0].action[:70]}", flush=True)

        pace(int(usage.get("total_tokens", 0)), args.sleep)
        if tokens >= args.token_budget:
            print(f"  token budget reached ({tokens}), stopping. rerun tomorrow.", flush=True)
            break
        done = min(start + args.batch, len(rows))
        if done % 25 < args.batch or done == len(rows):
            print(
                f"  {done}/{len(rows)} clauses | {stored} obligations | {tokens} tokens",
                flush=True,
            )

    return stored, failed, tokens


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract obligations from stored clauses")
    parser.add_argument("--limit", type=int, default=100, help="max clauses to process")
    parser.add_argument("--dry-run", action="store_true", help="call the model, write nothing")
    parser.add_argument("--recompute", action="store_true", help="delete existing obligations first")
    parser.add_argument("--sleep", type=float, default=0.8, help="seconds between model calls")
    parser.add_argument("--batch", type=int, default=5, help="clauses per model call")
    parser.add_argument(
        "--token-budget",
        type=int,
        default=int(os.getenv("GROQ_TOKEN_BUDGET", "180000")),
        help="stop before exhausting the daily token quota",
    )
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)

    if args.recompute and not args.dry_run:
        connection.execute("DELETE FROM obligation")
        connection.commit()
        print("cleared obligation table", flush=True)

    rows = connection.execute(CANDIDATES, (args.limit,)).fetchall()
    print(f"{len(rows)} candidate clauses", flush=True)

    started = time.time()
    stored, failed, tokens = process(connection, rows, args)
    elapsed = time.time() - started

    print(
        f"done: {stored} obligations from {len(rows)} clauses | "
        f"{failed} failed | {tokens} tokens | {elapsed:.1f}s",
        flush=True,
    )
    connection.close()


if __name__ == "__main__":
    main()
