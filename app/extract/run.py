import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import MODEL_CHEAP, MODEL_WORKER, estimate_cost
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
  AND NOT EXISTS (SELECT 1 FROM clause_extraction x WHERE x.reg_clause_id = c.id)
ORDER BY d.date_issued DESC NULLS LAST, c.id
LIMIT %s
"""

MARK = "INSERT INTO clause_extraction (reg_clause_id, model) VALUES (%s, %s) ON CONFLICT DO NOTHING"

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


def insert_records(connection, clause_id, records, dry_run, model: str = MODEL_WORKER) -> int:
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
                model,
            ),
        )
    connection.commit()
    return len(records)


def extract_one(connection, row, args) -> tuple[int, int]:
    clause_id, text, title, doc_type, date_issued = row
    payload, usage = chat_json(SYSTEM_PROMPT, build_user_prompt(title, doc_type, text), model=args.model)
    records = validate(payload, text, date_issued)
    return insert_records(connection, clause_id, records, args.dry_run, args.model), int(usage.get("total_tokens", 0))


def call_batch(chunk, args):
    entries = [(index, row[1]) for index, row in enumerate(chunk)]
    return chat_json(
        BATCH_SYSTEM_PROMPT, build_batch_prompt(entries), model=args.model
    )


def process_parallel(connection, rows, args) -> tuple[int, int, int, float]:
    stored = failed = tokens = 0
    cost = 0.0
    chunks = [rows[index : index + args.batch] for index in range(0, len(rows), args.batch)]
    queue = iter(chunks)
    inflight = {}
    stopped = False
    done_batches = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for _ in range(args.workers * 2):
            chunk = next(queue, None)
            if chunk is None:
                break
            inflight[pool.submit(call_batch, chunk, args)] = chunk

        while inflight:
            for future in as_completed(list(inflight)):
                chunk = inflight.pop(future)
                try:
                    payload, usage = future.result()
                except LlmError as error:
                    failed += len(chunk)
                    print(f"  batch failed: {error}", flush=True)
                else:
                    tokens += int(usage.get("total_tokens", 0))
                    cost += estimate_cost(args.model, usage)
                    results = batch_results(payload, len(chunk))
                    for row, item in zip(chunk, results):
                        records = validate(item, row[1], row[4])
                        connection.execute(MARK, (row[0], args.model))
                        stored += insert_records(
                            connection, row[0], records, args.dry_run, args.model
                        )
                    connection.commit()
                    done_batches += 1
                    print(
                        f"  {done_batches}/{len(chunks)} batches "
                        f"| {stored} obligations | ${cost:.3f}",
                        flush=True,
                    )

                if args.budget_usd and cost >= args.budget_usd and not stopped:
                    stopped = True
                    print(f"  budget reached (${cost:.3f}), draining", flush=True)
                if not stopped:
                    following = next(queue, None)
                    if following is not None:
                        inflight[pool.submit(call_batch, following, args)] = following
                break

    return stored, failed, tokens, cost


def process(connection, rows, args) -> tuple[int, int, int, float]:
    stored = failed = tokens = 0
    cost = 0.0
    consecutive = 0

    for start in range(0, len(rows), args.batch):
        chunk = rows[start : start + args.batch]
        entries = [(index, row[1]) for index, row in enumerate(chunk)]

        try:
            payload, usage = chat_json(
                BATCH_SYSTEM_PROMPT, build_batch_prompt(entries), model=args.model
            )
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
                        return stored, failed, tokens, cost
                    continue
                consecutive = 0
                stored += count
                tokens += used
                pace(used, args.sleep)
            continue

        consecutive = 0
        tokens += int(usage.get("total_tokens", 0))
        cost += estimate_cost(args.model, usage)
        results = batch_results(payload, len(chunk))

        for row, item in zip(chunk, results):
            records = validate(item, row[1], row[4])
            stored += insert_records(connection, row[0], records, args.dry_run, args.model)
            if args.dry_run and records:
                print(f"  [dry] {row[0]}: {len(records)} obligation(s) | {records[0].action[:70]}", flush=True)

        pace(int(usage.get("total_tokens", 0)), args.sleep)
        if tokens >= args.token_budget:
            print(f"  token budget reached ({tokens}), stopping.", flush=True)
            break
        if args.budget_usd and cost >= args.budget_usd:
            print(f"  dollar budget reached (${cost:.3f}), stopping.", flush=True)
            break
        done = min(start + args.batch, len(rows))
        if done % 25 < args.batch or done == len(rows):
            print(
                f"  {done}/{len(rows)} clauses | {stored} obligations | {tokens} tokens",
                flush=True,
            )

    return stored, failed, tokens, cost


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
        default=int(os.getenv("GROQ_TOKEN_BUDGET", "2000000")),
        help="stop after this many tokens",
    )
    parser.add_argument("--model", default=MODEL_CHEAP, help="model for extraction")
    parser.add_argument("--workers", type=int, default=1, help="parallel model calls")
    parser.add_argument(
        "--budget-usd",
        type=float,
        default=float(os.getenv("EXTRACT_BUDGET_USD", "0.8")),
        help="stop when estimated spend reaches this amount",
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
    runner = process_parallel if args.workers > 1 else process
    stored, failed, tokens, cost = runner(connection, rows, args)
    elapsed = time.time() - started

    print(
        f"done: {stored} obligations from {len(rows)} clauses | "
        f"{failed} failed | {tokens} tokens | ${cost:.3f} | {elapsed:.1f}s",
        flush=True,
    )
    connection.close()


if __name__ == "__main__":
    main()
