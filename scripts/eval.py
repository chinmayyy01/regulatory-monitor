import json
import sys
from pathlib import Path

EVAL_DIR = Path("evals")
DATASETS = {
    "applicability.jsonl": "obligation x tenant profile -> applies / does not apply",
    "mapping.jsonl": "obligation x tenant clause -> satisfied / partial / missing / stale",
    "chat.jsonl": "question -> answer plus gold citation spans",
}
EXIT_NOT_READY = 2


def count_rows(path: Path) -> int:
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            json.loads(line)
            total += 1
    return total


def main() -> int:
    print("RegIntel eval harness (W0 gate)")
    print(f"datasets dir: {EVAL_DIR.resolve()}")

    missing = [name for name in DATASETS if not (EVAL_DIR / name).exists()]
    for name, purpose in DATASETS.items():
        path = EVAL_DIR / name
        if name in missing:
            print(f"  MISSING  {name:24} {purpose}")
        else:
            print(f"  ok       {name:24} {count_rows(path)} rows")

    print()
    print("FAIL: scoring is not implemented yet.")
    print("This target is supposed to fail until W2.")
    return EXIT_NOT_READY


if __name__ == "__main__":
    sys.exit(main())
