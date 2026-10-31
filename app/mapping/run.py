import argparse
import os
import time
import uuid

from psycopg.types.json import Jsonb

from app.config import MODEL_JUDGE
from app.db import apply_schema, connect
from app.extract.llm import LlmError
from app.mapping.applicability import applies, tenant_facets
from app.mapping.judge import judge
from app.search.embed import embed_texts, parse_vector, vector_literal

TPM_LIMIT = int(os.getenv("GROQ_TPM_LIMIT", "8000"))
MAX_CONSECUTIVE_FAILURES = 4

TENANT = "SELECT id, entity_type, products FROM tenant WHERE name = %s"

OBLIGATIONS = """
SELECT o.id, o.action, o.condition, o.scope_entities, o.embedding
FROM obligation o
WHERE o.embedding IS NOT NULL
  AND (%s::bigint[] IS NULL OR o.id = ANY(%s))
  AND NOT EXISTS (
      SELECT 1 FROM mapping m WHERE m.obligation_id = o.id AND m.run_id = %s
  )
ORDER BY o.id
LIMIT %s
"""

CANDIDATES = """
SELECT tc.id, tc.text, 1 - (tc.embedding <=> %s::vector) AS score
FROM tenant_clause tc
JOIN tenant_doc td ON td.id = tc.tenant_doc_id
WHERE td.tenant_id = %s AND tc.embedding IS NOT NULL
ORDER BY tc.embedding <=> %s::vector
LIMIT %s
"""

INSERT = """
INSERT INTO mapping
    (obligation_id, tenant_clause_id, verdict, confidence,
     evidence_regulation, evidence_policy, reason, model, run_id,
     regulation_span, policy_span, tenant_id)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (obligation_id, tenant_clause_id, run_id) DO NOTHING
"""


def pace(tokens_used: int, floor: float) -> None:
    time.sleep(max(floor, tokens_used * 60 / TPM_LIMIT))


def embedding_pending(connection, limit: int = 500) -> int:
    rows = connection.execute(
        "SELECT id, action FROM obligation WHERE embedding IS NULL ORDER BY id LIMIT %s",
        (limit,),
    ).fetchall()
    if not rows:
        return 0
    vectors = embed_texts([f"{action}" for _, action in rows])
    for (obligation_id, _), vector in zip(rows, vectors):
        connection.execute(
            "UPDATE obligation SET embedding = %s::vector WHERE id = %s",
            (vector_literal(vector), obligation_id),
        )
    connection.commit()
    return len(rows)


def run(connection, tenant_name: str, args) -> tuple[int, int, int]:
    tenant = connection.execute(TENANT, (tenant_name,)).fetchone()
    if tenant is None:
        raise SystemExit(f"tenant not found: {tenant_name}")

    tenant_id, entity_type, products = tenant
    facets = tenant_facets(entity_type, products or [])
    run_id = uuid.uuid4().hex[:12]

    rows = connection.execute(OBLIGATIONS, (args.ids, args.ids, run_id, args.limit)).fetchall()
    applicable = [row for row in rows if applies(row[3] or [], facets)]
    print(
        f"tenant {tenant_name} ({entity_type}) facets={sorted(facets)} | "
        f"{len(rows)} obligations, {len(applicable)} applicable | run {run_id}",
        flush=True,
    )

    mapped = 0
    failed = 0
    consecutive = 0

    for obligation_id, action, condition, _scope, embedding in applicable:
        obligation_text = f"{action}. {condition}".strip(". ") if condition else action
        literal = vector_literal(parse_vector(embedding))
        candidates = connection.execute(
            CANDIDATES, (literal, tenant_id, literal, args.candidates)
        ).fetchall()

        if not candidates:
            print(f"  {obligation_id}: no policy clauses to compare", flush=True)
            continue

        try:
            result = judge(obligation_text, [row[1] for row in candidates])
        except LlmError as error:
            failed += 1
            consecutive += 1
            print(f"  {obligation_id}: judge failed: {error}", flush=True)
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                print("  too many failures, stopping", flush=True)
                break
            continue

        consecutive = 0
        if result is None:
            failed += 1
            print(f"  {obligation_id}: rejected (unverifiable quote or bad verdict)", flush=True)
            pace(3000, args.sleep)
            continue

        clause_id = candidates[result.clause_index][0] if result.clause_index >= 0 else None
        if args.dry_run:
            score = candidates[result.clause_index][2] if clause_id else 0.0
            print(
                f"  [dry] {result.verdict:9} sim={score:.3f} | {action[:60]}",
                flush=True,
            )
        else:
            connection.execute(
                INSERT,
                (
                    obligation_id,
                    clause_id,
                    result.verdict,
                    result.confidence,
                    result.evidence_regulation,
                    result.evidence_policy,
                    result.reason,
                    MODEL_JUDGE,
                    run_id,
                    Jsonb(result.regulation_span),
                    Jsonb(result.policy_span),
                    tenant_id,
                ),
            )
            connection.commit()
            mapped += 1
            print(f"  {result.verdict:9} | {action[:60]}", flush=True)

        pace(3000, args.sleep)

    return mapped, failed, len(applicable)


def main() -> None:
    parser = argparse.ArgumentParser(description="Map applicable obligations to a tenant's policies")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--limit", type=int, default=25, help="obligations to consider")
    parser.add_argument("--candidates", type=int, default=5, help="policy clauses per obligation")
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--obligation-ids", default=None, help="comma separated ids")
    args = parser.parse_args()

    args.ids = (
        [int(value) for value in args.obligation_ids.split(",") if value.strip()]
        if args.obligation_ids
        else None
    )

    connection = connect()
    apply_schema(connection)

    embedded = embedding_pending(connection)
    if embedded:
        print(f"embedded {embedded} obligations", flush=True)

    mapped, failed, applicable = run(connection, args.tenant, args)
    print(f"done: {mapped} mappings stored, {failed} rejected, {applicable} applicable")
    connection.close()


if __name__ == "__main__":
    main()
