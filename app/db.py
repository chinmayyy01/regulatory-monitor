import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "001_init.sql"


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is missing. Copy .env.example to .env and fill it in.")
    return url


def connect() -> psycopg.Connection:
    return psycopg.connect(database_url())


def apply_schema(connection: psycopg.Connection) -> None:
    connection.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
    connection.commit()


def main() -> None:
    with connect() as connection:
        apply_schema(connection)
    print(f"schema applied from {SCHEMA_PATH.name}")


if __name__ == "__main__":
    main()
