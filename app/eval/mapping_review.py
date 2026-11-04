import json
import random
from pathlib import Path

from app.db import connect

LABELS = Path("evals/mapping-labels.jsonl")
OUTPUT = Path("notes/mapping-review-packet.md")
LABEL_TEMPLATE = Path("notes/mapping-review-response.jsonl")
TENANT_NAME = "demo-fintech"
PACKET_SIZE = 20
SEED = 20261104

CASES = """
SELECT m.id, o.modality, o.actor, o.action, o.condition, o.scope_entities,
       d.title, c.section_no, c.text
FROM mapping m
JOIN obligation o ON o.id = m.obligation_id
JOIN reg_clause c ON c.id = o.reg_clause_id
JOIN reg_doc d ON d.id = c.reg_doc_id
WHERE m.id = ANY(%s) AND m.tenant_id = %s
"""

POLICIES = """
SELECT td.title, tc.section_no, tc.text
FROM tenant_doc td
JOIN tenant_clause tc ON tc.tenant_doc_id = td.id
WHERE td.tenant_id = %s
ORDER BY td.title, tc.ordinal
"""


def select_mapping_ids(rows: list[dict], count: int = PACKET_SIZE, seed: int = SEED) -> list[int]:
    grouped = {verdict: [] for verdict in ("satisfied", "partial", "missing")}
    for row in rows:
        if row["judge"] in grouped:
            grouped[row["judge"]].append(row["mapping_id"])
    rng = random.Random(seed)
    targets = {"satisfied": 4, "partial": 8, "missing": 8}
    selected: list[int] = []
    for verdict, target in targets.items():
        selected.extend(rng.sample(grouped[verdict], min(target, len(grouped[verdict]))))
    remaining = [mapping_id for values in grouped.values() for mapping_id in values if mapping_id not in selected]
    if len(selected) + len(remaining) < count:
        raise ValueError(f"only {len(selected) + len(remaining)} labelled mappings are available")
    selected.extend(rng.sample(remaining, count - len(selected)))
    rng.shuffle(selected)
    return selected


def quote(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.splitlines())


def render_packet(tenant: dict, policies: list[tuple], cases: list[tuple]) -> str:
    lines = [
        "# Independent mapping review",
        "",
        "This is a blinded, stratified challenge sample, not a population estimate. It uses the seeded demo workspace and synthetic policy text. Do not treat it as customer validation or legal advice.",
        "",
        f"Workspace profile: {tenant['entity_type']}; products: {', '.join(tenant['products']) or 'none listed'}.",
        "",
        "For each requirement, compare it with the complete policy register below. Label `satisfied` only when the same requirement is fully covered; `partial` only when that same requirement is incompletely covered; otherwise label `missing`. Add a short reason for every non-obvious label.",
        "",
        "Do not infer coverage from a related topic. A missing candidate in the original run does not mean the full policy register has no match.",
        "",
        "## Cases",
        "",
    ]
    for index, case in enumerate(cases, start=1):
        mapping_id, modality, actor, action, condition, scope, title, section, text = case
        lines.extend(
            [
                f"### Case {index:02d} (record {mapping_id})",
                "",
                f"Requirement: {modality} {actor} {action}".strip(),
                f"Condition: {condition or 'none stated'}",
                f"Scope facets: {', '.join(scope or []) or 'not specified'}",
                f"Regulatory source: {title}; section {section or 'not specified'}",
                "",
                quote(text),
                "",
                "Reviewer label: `satisfied` / `partial` / `missing`",
                "Reason:",
                "",
            ]
        )
    lines.extend(["## Complete policy register", ""])
    for title, section, text in policies:
        lines.extend(
            [
                f"### {title}; section {section or 'not specified'}",
                "",
                quote(text),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    rows = [json.loads(line) for line in LABELS.read_text(encoding="utf-8").splitlines() if line.strip()]
    mapping_ids = select_mapping_ids(rows)
    with connect() as connection:
        tenant_row = connection.execute(
            "SELECT id, entity_type, products FROM tenant WHERE name = %s",
            (TENANT_NAME,),
        ).fetchone()
        if tenant_row is None:
            raise SystemExit(f"tenant not found: {TENANT_NAME}")
        tenant_id, entity_type, products = tenant_row
        cases = connection.execute(CASES, (mapping_ids, tenant_id)).fetchall()
        policies = connection.execute(POLICIES, (tenant_id,)).fetchall()
    if len(cases) != len(mapping_ids):
        raise SystemExit(f"only {len(cases)} of {len(mapping_ids)} mapping records were found")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        render_packet(
            {"entity_type": entity_type, "products": products},
            policies,
            cases,
        ),
        encoding="utf-8",
    )
    LABEL_TEMPLATE.write_text(
        "\n".join(
            json.dumps({"mapping_id": mapping_id, "human": "", "note": ""})
            for mapping_id in mapping_ids
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(cases)} blinded review cases to {OUTPUT}")
    print(f"wrote blank label template to {LABEL_TEMPLATE}")


if __name__ == "__main__":
    main()
