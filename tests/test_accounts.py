import os
import uuid

import pytest

from app.auth.accounts import EmailTaken, WorkspaceTaken, create_account
from app.db import apply_schema, connect

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not set")


def test_create_account_wires_user_membership_and_tenant():
    suffix = uuid.uuid4().hex[:8]
    workspace = f"test workspace {suffix}"
    email = f"owner-{suffix}@example.test"

    with connect() as connection:
        apply_schema(connection)
        user = create_account(connection, email, "a-long-enough-password", workspace, "nbfc")

        tenant_id = connection.execute(
            "SELECT id FROM tenant WHERE name = %s", (workspace,)
        ).fetchone()[0]
        membership = connection.execute(
            "SELECT role FROM membership WHERE user_id = %s AND tenant_id = %s",
            (user[0], tenant_id),
        ).fetchone()

        assert user[1] == email
        assert user[2] == tenant_id
        assert membership[0] == "owner"

        connection.execute("DELETE FROM tenant WHERE id = %s", (tenant_id,))


def test_duplicate_email_is_rejected():
    suffix = uuid.uuid4().hex[:8]
    email = f"dupe-{suffix}@example.test"
    workspace = f"dupe workspace {suffix}"

    with connect() as connection:
        apply_schema(connection)
        user = create_account(connection, email, "a-long-enough-password", workspace, "nbfc")
        tenant_id = user[2]

        with pytest.raises(EmailTaken):
            create_account(connection, email, "a-long-enough-password", f"{workspace} 2", "nbfc")

        connection.execute("DELETE FROM tenant WHERE id = %s", (tenant_id,))


def test_duplicate_workspace_is_rejected():
    suffix = uuid.uuid4().hex[:8]
    workspace = f"shared workspace {suffix}"

    with connect() as connection:
        apply_schema(connection)
        user = create_account(connection, f"a-{suffix}@example.test", "a-long-enough-password", workspace, "nbfc")
        tenant_id = user[2]

        with pytest.raises(WorkspaceTaken):
            create_account(connection, f"b-{suffix}@example.test", "a-long-enough-password", workspace, "nbfc")

        connection.execute("DELETE FROM tenant WHERE id = %s", (tenant_id,))


def test_short_password_is_rejected_before_any_write():
    suffix = uuid.uuid4().hex[:8]
    workspace = f"short password {suffix}"

    with connect() as connection:
        apply_schema(connection)
        with pytest.raises(ValueError):
            create_account(connection, f"c-{suffix}@example.test", "short", workspace, "nbfc")

        assert connection.execute(
            "SELECT 1 FROM tenant WHERE name = %s", (workspace,)
        ).fetchone() is None
