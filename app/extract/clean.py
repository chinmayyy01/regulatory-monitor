import argparse

from app.db import apply_schema, connect
from app.extract.obligations import FRAGMENT_RE, MIN_ACTION_CHARS

CANDIDATES = "SELECT id, action FROM obligation"
DELETE = "DELETE FROM obligation WHERE id = ANY(%s)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete fragmentary obligations")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)

    rows = connection.execute(CANDIDATES).fetchall()
    doomed = [
        row[0]
        for row in rows
        if len(row[1]) < MIN_ACTION_CHARS or FRAGMENT_RE.match(row[1])
    ]

    print(f"{len(rows)} obligations, {len(doomed)} fragmentary")
    for row in rows:
        if row[0] in set(doomed[:10]):
            print(f"  drop: {row[1][:70]}")

    if args.dry_run or not doomed:
        connection.close()
        return

    connection.execute(DELETE, (doomed,))
    connection.commit()
    print(f"deleted {len(doomed)}")
    connection.close()


if __name__ == "__main__":
    main()
