import json
from collections import Counter
from pathlib import Path

LABELS = Path("evals/mapping-labels.jsonl")
VERDICTS = ["satisfied", "partial", "missing"]


def kappa(pairs: list[tuple[str, str]]) -> float:
    total = len(pairs)
    if not total:
        return 0.0
    observed = sum(1 for judge, human in pairs if judge == human) / total
    judge_counts = Counter(judge for judge, _ in pairs)
    human_counts = Counter(human for _, human in pairs)
    expected = sum(
        (judge_counts[verdict] / total) * (human_counts[verdict] / total)
        for verdict in VERDICTS
    )
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)


def main() -> None:
    rows = [json.loads(line) for line in LABELS.read_text().splitlines() if line.strip()]
    pairs = [(row["judge"], row["human"]) for row in rows]
    agreement = sum(1 for judge, human in pairs if judge == human)

    satisfied = [row for row in rows if row["judge"] == "satisfied"]
    false_satisfied = [row for row in satisfied if row["human"] != "satisfied"]
    partial = [row for row in rows if row["judge"] == "partial"]
    over_strict = [row for row in partial if row["human"] == "satisfied"]
    false_partial = [row for row in partial if row["human"] == "missing"]

    print(f"labelled rows        {len(rows)}")
    print(f"agreement            {agreement}/{len(rows)} = {agreement / len(rows):.3f}")
    print(f"cohen kappa          {kappa(pairs):.3f}")
    print(f"false satisfied      {len(false_satisfied)}/{len(satisfied)} = {len(false_satisfied) / max(len(satisfied), 1):.3f}")
    print(f"over strict          {len(over_strict)}/{max(len(partial), 1)}")
    print(f"false partial        {len(false_partial)}/{max(len(partial), 1)} = {len(false_partial) / max(len(partial), 1):.3f}")

    for row in false_satisfied:
        print(f"  false satisfied: mapping {row['mapping_id']}: {row['note']}")
    for row in false_partial:
        print(f"  false partial:   mapping {row['mapping_id']}: {row['note']}")


if __name__ == "__main__":
    main()
