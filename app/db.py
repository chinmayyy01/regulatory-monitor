import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is missing. Copy .env.example to .env and fill it in.")
    return url


def connect() -> psycopg.Connection:
    return psycopg.connect(database_url())


def connect_app(tenant_id: int | None = None) -> psycopg.Connection:
    url = os.getenv("DATABASE_URL_APP", "").strip() or database_url()
    connection = psycopg.connect(url)
    if tenant_id is not None:
        connection.execute("SELECT set_config('app.tenant_id', %s, false)", (str(tenant_id),))
    return connection


def apply_schema(connection: psycopg.Connection) -> None:
    for path in sorted(SQL_DIR.glob("*.sql")):
        connection.execute(path.read_text(encoding="utf-8"))
    connection.commit()


def main() -> None:
    with connect() as connection:
        apply_schema(connection)
    print(f"schema applied from {SQL_DIR}")


if __name__ == "__main__":
    main()
