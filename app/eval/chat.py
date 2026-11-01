import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from app.chat.answer import ask_with_usage
from app.chat.retrieve import gather
from app.db import connect
from app.extract.llm import LlmError
from app.rate import TokenPacer

DATASET = Path("evals/chat.jsonl")
RAW = Path("data/eval/chat-raw.jsonl")
OUT_DIR = Path("data/eval")
TENANT = "demo-fintech"


def load_rows() -> list[dict]:
    return [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_raw() -> dict[str, dict]:
    if not RAW.exists():
        return {}
    return {
        item["question"]: item
        for item in (json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines() if line.strip())
    }


def save_raw(records: dict[str, dict]) -> None:
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in records.values()) + "\n",
        encoding="utf-8",
    )


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))
    return ordered[index]


def summarize(records: list[dict]) -> dict:
    answerable = [item for item in records if item["answerable"]]
    unanswerable = [item for item in records if not item["answerable"]]
    answered = [item for item in answerable if not item["insufficient"]]

    gold_hits = sum(1 for item in answered if item.get("gold_hit"))
    doc_hits = sum(1 for item in answered if item.get("doc_hit"))
    cited_total = sum(item.get("cited_count", 0) for item in answered)
    cited_gold = sum(item.get("cited_gold", 0) for item in answered)
    abstained_correct = sum(1 for item in unanswerable if item["insufficient"])
    latencies = [item["latency"] for item in records if item.get("latency")]

    return {
        "rows": len(records),
        "answerable": len(answerable),
        "answered": len(answered),
        "abstained_on_answerable": len(answerable) - len(answered),
        "gold_citation_recall": round(gold_hits / len(answerable), 3) if answerable else 0.0,
        "same_document_rate": round((gold_hits + doc_hits) / len(answerable), 3) if answerable else 0.0,
        "citation_precision": round(cited_gold / cited_total, 3) if cited_total else 0.0,
        "unanswerable": len(unanswerable),
        "abstention_accuracy": round(abstained_correct / len(unanswerable), 3) if unanswerable else 0.0,
        "claims_rejected": sum(item.get("rejected", 0) for item in records),
        "model_call_failures": sum(1 for item in records if item.get("error")),
        "latency_p50_s": round(percentile(latencies, 0.5), 2),
        "latency_p95_s": round(percentile(latencies, 0.95), 2),
    }


def failures(records: list[dict]) -> list[dict]:
    out = []
    for item in records:
        if item.get("error"):
            out.append({"question": item["question"], "reason": item["error"]})
        elif item["answerable"] and item["insufficient"]:
            out.append({"question": item["question"], "reason": "abstained"})
        elif item["answerable"] and not item.get("gold_hit") and not item.get("doc_hit"):
            out.append({"question": item["question"], "reason": "gold not cited"})
        elif not item["answerable"] and not item["insufficient"]:
            out.append({"question": item["question"], "reason": "answered an unanswerable question"})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure chat citation and abstention quality")
    parser.add_argument("--limit", type=int, default=0, help="process at most N unanswered rows")
    parser.add_argument("--redo", action="store_true", help="re-run rows that already have results")
    parser.add_argument("--summary-only", action="store_true", help="do not call the model")
    parser.add_argument("--floor", type=float, default=25.0, help="minimum seconds between calls")
    args = parser.parse_args()

    rows = load_rows()
    records = load_raw()

    if not args.summary_only:
        pending = [
            row
            for row in rows
            if args.redo
            or row["question"] not in records
            or records[row["question"]].get("error")
        ]
        if args.limit:
            pending = pending[: args.limit]

        connection = connect()
        tenant = connection.execute("SELECT id FROM tenant WHERE name = %s", (TENANT,)).fetchone()
        if tenant is None:
            raise SystemExit(f"tenant not found: {TENANT}")
        tenant_id = tenant[0]

        pacer = TokenPacer()
        for index, row in enumerate(pending, start=1):
            question = row["question"]
            started = time.time()
            try:
                sources = gather(connection, tenant_id, question)
                answer, tokens = ask_with_usage(question, sources)
            except LlmError as error:
                records[question] = {
                    **{key: row[key] for key in ("question", "answerable", "gold_clause_id", "gold_doc_id")},
                    "error": str(error)[:200],
                }
                save_raw(records)
                print(f"  {index}/{len(pending)} failed: {error}", flush=True)
                pacer.wait(2000, args.floor)
                continue

            cited = {
                citation.clause_id
                for claim in answer.claims
                for citation in claim.citations
                if citation.kind == "regulation"
            }
            doc_ids = set()
            if cited:
                doc_ids = {
                    doc_id
                    for _, doc_id in connection.execute(
                        "SELECT id, reg_doc_id FROM reg_clause WHERE id = ANY(%s)",
                        (list(cited),),
                    ).fetchall()
                }

            records[question] = {
                "question": question,
                "answerable": row["answerable"],
                "gold_clause_id": row["gold_clause_id"],
                "gold_doc_id": row["gold_doc_id"],
                "insufficient": answer.insufficient,
                "rejected": answer.rejected,
                "cited_count": len(cited),
                "cited_gold": 1 if row["answerable"] and row["gold_clause_id"] in cited else 0,
                "gold_hit": bool(row["answerable"] and row["gold_clause_id"] in cited),
                "doc_hit": bool(row["answerable"] and row["gold_doc_id"] in doc_ids),
                "latency": round(time.time() - started, 2),
            }
            save_raw(records)
            print(
                f"  {index}/{len(pending)} "
                f"{'abstain' if answer.insufficient else f'{len(answer.claims)} claims'} "
                f"{time.time()-started:.1f}s",
                flush=True,
            )
            pacer.wait(tokens, args.floor)

        connection.close()

    ordered = [records[row["question"]] for row in rows if row["question"] in records]
    summary = summarize(ordered)
    print(json.dumps(summary, indent=2))

    problems = failures(ordered)
    if problems:
        print("\nfailures:")
        for item in problems[:15]:
            print(f"  [{item['reason']}] {item['question'][:90]}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps({"summary": summary, "failures": problems}, indent=2), encoding="utf-8")
    print(f"\nwritten to {path}")


if __name__ == "__main__":
    main()
