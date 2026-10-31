import argparse

from app.db import apply_schema, connect
from app.temporal.relations import extract, resolve_target, store

SCAN = r"""
SELECT c.id, c.reg_doc_id, c.text, d.date_issued
FROM reg_clause c
JOIN reg_doc d ON d.id = c.reg_doc_id
WHERE c.text ~* 'shall be (amended|substituted|inserted|deleted|omitted)'
   OR c.text ~* '\mrepealed\M'
   OR c.text ~* 'shall supersede'
ORDER BY d.date_issued, c.id
LIMIT %s
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract amendment and repeal relations")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)

    rows = connection.execute(SCAN, (args.limit,)).fetchall()
    print(f"{len(rows)} clauses mention an amendment or repeal", flush=True)

    stored = 0
    for clause_id, doc_id, text, date_issued in rows:
        for candidate in extract(text):
            target = resolve_target(connection, candidate.target_text) if candidate.target_text else None
            if args.dry_run:
                print(
                    f"  [dry] doc {doc_id} {candidate.kind} clause={candidate.clause_ref} "
                    f"target={target} :: {candidate.target_text[:70]}",
                    flush=True,
                )
                continue
            if store(connection, doc_id, target, candidate, date_issued):
                stored += 1
                print(
                    f"  + {candidate.kind} clause={candidate.clause_ref} "
                    f"doc={doc_id} target={target}",
                    flush=True,
                )
        connection.commit()

    print(f"done: {stored} relations stored")
    connection.close()


if __name__ == "__main__":
    main()
