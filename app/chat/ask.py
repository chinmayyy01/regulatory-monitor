import argparse
import json
from datetime import date

from app.chat.answer import ask
from app.chat.retrieve import gather
from app.db import apply_schema, connect


def render(answer) -> str:
    if answer.insufficient:
        return (
            "Not enough evidence in the indexed documents.\n"
            f"({answer.rejected} claim(s) rejected by citation verification)"
        )
    lines = []
    for claim in answer.claims:
        lines.append(f"- {claim.text}")
        for citation in claim.citations:
            lines.append(
                f"    [{citation.kind} #{citation.clause_id}] \"{citation.quote}\""
            )
            lines.append(f"      source: {citation.label}")
    if answer.rejected:
        lines.append(f"\n({answer.rejected} claim(s) rejected by citation verification)")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question over regulation and tenant policy")
    parser.add_argument("question")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--as-of", default=None, help="YYYY-MM-DD, defaults to today")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)

    row = connection.execute("SELECT id FROM tenant WHERE name = %s", (args.tenant,)).fetchone()
    if row is None:
        raise SystemExit(f"tenant not found: {args.tenant}")

    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    sources = gather(connection, row[0], args.question, as_of)
    answer = ask(args.question, sources)

    if args.json:
        print(json.dumps(
            {
                "insufficient": answer.insufficient,
                "rejected": answer.rejected,
                "claims": [
                    {
                        "text": claim.text,
                        "citations": [
                            {
                                "kind": citation.kind,
                                "clause_id": citation.clause_id,
                                "quote": citation.quote,
                                "span": citation.span,
                                "label": citation.label,
                            }
                            for citation in claim.citations
                        ],
                    }
                    for claim in answer.claims
                ],
            },
            indent=2,
        ))
    else:
        print(render(answer))
    connection.close()


if __name__ == "__main__":
    main()
