import argparse
from datetime import datetime
from pathlib import Path

from app.db import apply_schema, connect

SEVERITY = {"satisfied": 0, "partial": 1, "missing": 2, "stale": 3}
VERDICT_BY_SEVERITY = {value: key for key, value in SEVERITY.items()}

RUNS = """
SELECT run_id, min(created_at) AS at
FROM mapping
WHERE tenant_id = %s
GROUP BY run_id
ORDER BY at DESC
LIMIT %s
"""

VERDICTS = """
SELECT obligation_id, verdict
FROM mapping
WHERE tenant_id = %s AND run_id = %s
"""

OBLIGATION_TEXT = "SELECT id, action FROM obligation WHERE id = ANY(%s)"

OUT_DIR = Path("data/change")


def verdict_map(rows) -> dict[int, str]:
    best: dict[int, int] = {}
    for obligation_id, verdict in rows:
        severity = SEVERITY.get(verdict)
        if severity is None:
            continue
        if obligation_id not in best or severity < best[obligation_id]:
            best[obligation_id] = severity
    return {key: VERDICT_BY_SEVERITY[value] for key, value in best.items()}


def diff(old: dict[int, str], new: dict[int, str]) -> list[dict]:
    changes = []
    for obligation_id in sorted(set(old) | set(new)):
        before = old.get(obligation_id)
        after = new.get(obligation_id)
        if before == after:
            continue
        if before is None:
            direction = "new"
        elif after is None:
            direction = "dropped"
        elif SEVERITY[after] > SEVERITY[before]:
            direction = "worsened"
        else:
            direction = "improved"
        changes.append(
            {
                "obligation_id": obligation_id,
                "before": before,
                "after": after,
                "direction": direction,
            }
        )
    return changes


def render(tenant: str, old_run: str, new_run: str, changes: list[dict], actions: dict[int, str]) -> str:
    lines = [
        f"# Change feed: {tenant}",
        "",
        f"Comparing run `{old_run}` with run `{new_run}`.",
        "",
    ]
    if not changes:
        lines.append("No verdicts changed between these runs.")
        return "\n".join(lines)

    counts: dict[str, int] = {}
    for change in changes:
        counts[change["direction"]] = counts.get(change["direction"], 0) + 1
    summary = ", ".join(f"{value} {key}" for key, value in sorted(counts.items()))
    lines.append(f"{len(changes)} changes: {summary}.")
    lines.append("")

    for change in changes:
        action = actions.get(change["obligation_id"], f"obligation {change['obligation_id']}")
        lines.append(
            f"- **{change['direction']}** ({change['before']} -> {change['after']}) {action[:160]}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Diff a tenant's verdicts between the last two runs")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--runs", type=int, default=2, help="number of runs to look back")
    parser.add_argument("--out", default=str(OUT_DIR))
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)

    row = connection.execute("SELECT id FROM tenant WHERE name = %s", (args.tenant,)).fetchone()
    if row is None:
        raise SystemExit(f"tenant not found: {args.tenant}")
    tenant_id = row[0]

    runs = connection.execute(RUNS, (tenant_id, max(args.runs, 2))).fetchall()
    if len(runs) < 2:
        print(f"need at least two runs for {args.tenant}, found {len(runs)}")
        return

    new_run, old_run = runs[0][0], runs[1][0]
    old = verdict_map(connection.execute(VERDICTS, (tenant_id, old_run)).fetchall())
    new = verdict_map(connection.execute(VERDICTS, (tenant_id, new_run)).fetchall())

    changes = diff(old, new)
    ids = [change["obligation_id"] for change in changes]
    actions = dict(connection.execute(OBLIGATION_TEXT, (ids,)).fetchall()) if ids else {}

    text = render(args.tenant, old_run, new_run, changes, actions)
    print(text)

    directory = Path(args.out)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{args.tenant}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    path.write_text(text + "\n", encoding="utf-8")
    print(f"\nwritten to {path}")
    connection.close()


if __name__ == "__main__":
    main()
