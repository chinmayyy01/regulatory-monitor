import argparse
from types import SimpleNamespace

from app.change.feed import OBLIGATION_TEXT, RUNS, VERDICTS, diff, verdict_map
from app.config import MODEL_WORKER
from app.db import apply_schema, connect
from app.mapping.run import run as run_mapping

POLICY = "Priority Sector Lending Policy"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate a policy being withdrawn and show what changed"
    )
    parser.add_argument("--tenant", default="demo-fintech")
    parser.add_argument("--policy", default=POLICY)
    parser.add_argument("--map", type=int, default=20)
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)

    tenant = connection.execute("SELECT id FROM tenant WHERE name = %s", (args.tenant,)).fetchone()
    if tenant is None:
        raise SystemExit(f"tenant not found: {args.tenant}")
    tenant_id = tenant[0]

    removed = connection.execute(
        "DELETE FROM tenant_doc WHERE tenant_id = %s AND title = %s",
        (tenant_id, args.policy),
    ).rowcount
    connection.commit()
    print(f"withdrew {removed} document(s) titled {args.policy!r}", flush=True)

    options = SimpleNamespace(
        limit=args.map, candidates=5, sleep=0.2, dry_run=False, ids=None, model=MODEL_WORKER
    )
    mapped, rejected, applicable = run_mapping(connection, args.tenant, options)
    print(f"remapped: {mapped} stored, {rejected} rejected, {applicable} applicable", flush=True)

    runs = connection.execute(RUNS, (tenant_id, 2)).fetchall()
    if len(runs) < 2:
        print("need two runs to diff")
        return

    to_run, from_run = runs[0][0], runs[1][0]
    old = verdict_map(connection.execute(VERDICTS, (tenant_id, from_run)).fetchall())
    new = verdict_map(connection.execute(VERDICTS, (tenant_id, to_run)).fetchall())
    changes = diff(old, new)

    ids = [item["obligation_id"] for item in changes]
    actions = dict(connection.execute(OBLIGATION_TEXT, (ids,)).fetchall()) if ids else {}

    print(f"\n{len(changes)} change(s) between {from_run} and {to_run}:")
    for item in changes:
        print(
            f"  {item['direction']:9} {item['before']} -> {item['after']} "
            f"| {actions.get(item['obligation_id'], '')[:70]}"
        )
    connection.close()


if __name__ == "__main__":
    main()
