import argparse
import json
import time
from pathlib import Path

from app.config import MODEL_WORKER
from app.extract.llm import LlmError, chat_json
from app.extract.obligations import (
    BATCH_SYSTEM_PROMPT,
    batch_results,
    build_batch_prompt,
    validate,
)

DATASET = Path("evals/obligations.jsonl")


def load_rows() -> list[dict]:
    return [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure obligation extraction on the gold set")
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--batch", type=int, default=5)
    args = parser.parse_args()

    rows = load_rows()
    tp = fp = fn = tn = 0
    modality_hits = 0
    failures = 0

    for start in range(0, len(rows), args.batch):
        chunk = rows[start : start + args.batch]
        entries = [(index, row["text"]) for index, row in enumerate(chunk)]
        try:
            payload, _ = chat_json(BATCH_SYSTEM_PROMPT, build_batch_prompt(entries))
            results = batch_results(payload, len(chunk))
        except LlmError as error:
            failures += len(chunk)
            print(f"  batch at {start} failed: {error}")
            continue

        for row, item in zip(chunk, results):
            records = validate(item, row["text"])
            predicted = len(records) > 0
            gold = row["is_obligation"]

            if predicted and gold:
                tp += 1
                if records[0].modality == row["modality"]:
                    modality_hits += 1
            elif predicted and not gold:
                fp += 1
                print(f"  FP {row['clause_id']}: {records[0].action[:90]}")
            elif gold and not predicted:
                fn += 1
                print(f"  FN {row['clause_id']}: {row['text'][:90]}")
            else:
                tn += 1
        time.sleep(args.sleep)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    modality_accuracy = modality_hits / tp if tp else 0.0

    print()
    print(f"model: {MODEL_WORKER}")
    print(f"rows: {len(rows)}  failures: {failures}")
    print(f"tp={tp} fp={fp} fn={fn} tn={tn}")
    print(f"precision {precision:.3f}  recall {recall:.3f}  f1 {f1:.3f}")
    print(f"modality accuracy on true positives: {modality_accuracy:.3f}")


if __name__ == "__main__":
    main()
