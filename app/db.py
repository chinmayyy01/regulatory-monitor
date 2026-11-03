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


MIGRATION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename   TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


def migrate(connection: psycopg.Connection) -> list[str]:
    connection.execute(MIGRATION_TABLE)
    applied = {
        row[0]
        for row in connection.execute("SELECT filename FROM schema_migrations").fetchall()
    }
    newly_applied: list[str] = []
    for path in sorted(SQL_DIR.glob("*.sql")):
        if path.name in applied:
            continue
        connection.execute(path.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO schema_migrations (filename) VALUES (%s) ON CONFLICT DO NOTHING",
            (path.name,),
        )
        connection.commit()
        newly_applied.append(path.name)
    return newly_applied


def apply_schema(connection: psycopg.Connection) -> None:
    migrate(connection)


def main() -> None:
    with connect() as connection:
        applied = migrate(connection)
    if applied:
        print("applied: " + ", ".join(applied))
    else:
        print("schema up to date")


if __name__ == "__main__":
    main()
