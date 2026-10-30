import sys
from datetime import date, timedelta
from types import SimpleNamespace

import requests

from app.db import apply_schema, connect
from app.ingest.run import ingest_rbi_month, ingest_sebi

OPTIONS = SimpleNamespace(dry_run=False, limit=0, sleep=2.0)


def months_to_check(today: date) -> list[tuple[int, int]]:
    previous = today.replace(day=1) - timedelta(days=1)
    return [(today.year, today.month), (previous.year, previous.month)]


def main() -> int:
    connection = connect()
    apply_schema(connection)
    session = requests.Session()

    total = 0
    for year, month in months_to_check(date.today()):
        try:
            total += ingest_rbi_month(connection, session, year, month, OPTIONS)
        except Exception as error:
            connection.rollback()
            print(f"[rbi {year}-{month:02d}] failed: {error}", flush=True)

    try:
        total += ingest_sebi(connection, session, OPTIONS)
    except Exception as error:
        connection.rollback()
        print(f"[sebi] failed: {error}", flush=True)

    print(f"daily run finished: {total} new documents", flush=True)
    connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
