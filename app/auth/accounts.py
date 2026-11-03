from app.auth.passwords import hash_password

DEFAULT_PRODUCTS = ["lending"]


class EmailTaken(Exception):
    pass


class WorkspaceTaken(Exception):
    pass


def create_account(
    connection,
    email: str,
    password: str,
    workspace: str,
    entity_type: str,
    products: list[str] | None = None,
):
    email = email.lower().strip()
    workspace = workspace.strip()
    password_hash = hash_password(password)

    if connection.execute("SELECT 1 FROM app_user WHERE email = %s", (email,)).fetchone():
        raise EmailTaken(email)

    row = connection.execute(
        """
        INSERT INTO tenant (name, entity_type, products)
        VALUES (%s, %s, %s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id
        """,
        (workspace, entity_type, products or DEFAULT_PRODUCTS),
    ).fetchone()
    if row is None:
        raise WorkspaceTaken(workspace)
    tenant_id = row[0]

    user = connection.execute(
        """
        INSERT INTO app_user (email, password_hash, tenant_id)
        VALUES (%s, %s, %s)
        RETURNING id, email, tenant_id, role
        """,
        (email, password_hash, tenant_id),
    ).fetchone()

    connection.execute(
        "INSERT INTO membership (user_id, tenant_id, role) VALUES (%s, %s, 'owner') "
        "ON CONFLICT DO NOTHING",
        (user[0], tenant_id),
    )
    connection.commit()
    return user
