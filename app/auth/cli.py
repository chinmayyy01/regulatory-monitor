import argparse

from app.auth.passwords import hash_password
from app.db import apply_schema, connect


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a login for a tenant")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--tenant", required=True)
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)

    tenant = connection.execute("SELECT id FROM tenant WHERE name = %s", (args.tenant,)).fetchone()
    if tenant is None:
        raise SystemExit(f"tenant not found: {args.tenant}")

    connection.execute(
        """
        INSERT INTO app_user (email, password_hash, tenant_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
        """,
        (args.email.lower().strip(), hash_password(args.password), tenant[0]),
    )
    connection.commit()
    print(f"user {args.email} -> tenant {args.tenant}")
    connection.close()


if __name__ == "__main__":
    main()
