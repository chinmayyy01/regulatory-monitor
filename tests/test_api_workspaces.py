import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import apply_schema, connect
from api import main as api_main

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not set")


def test_demo_mode_can_create_workspace_without_a_session_cookie(monkeypatch):
    suffix = uuid.uuid4().hex[:12]
    seed_name = f"workspace create seed {suffix}"
    workspace_name = f"workspace create probe {suffix}"
    actor_email = f"workspace-create-{suffix}@example.test"

    with connect() as connection:
        apply_schema(connection)
        connection.execute(
            "INSERT INTO tenant (name, entity_type, products) VALUES (%s, %s, %s)",
            (seed_name, "nbfc", ["lending"]),
        )
        seed_id = connection.execute(
            "SELECT id FROM tenant WHERE name = %s", (seed_name,)
        ).fetchone()[0]
        connection.execute(
            "INSERT INTO app_user (email, password_hash, tenant_id) VALUES (%s, %s, %s)",
            (actor_email, "test-only-unused-hash", seed_id),
        )
        actor_id, actor_tenant_id = connection.execute(
            "SELECT id, tenant_id FROM app_user ORDER BY id LIMIT 1"
        ).fetchone()

    try:
        monkeypatch.setattr(api_main, "AUTH_DISABLED", True)
        with TestClient(api_main.app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/tenants",
                json={"name": workspace_name, "entity_type": "nbfc", "products": ["lending"]},
            )

        assert response.status_code == 201, response.text
        assert response.json()["name"] == workspace_name
    finally:
        with connect() as connection:
            connection.execute(
                "UPDATE app_user SET tenant_id = %s WHERE id = %s",
                (actor_tenant_id, actor_id),
            )
            connection.execute("DELETE FROM app_user WHERE email = %s", (actor_email,))
            connection.execute(
                "DELETE FROM tenant WHERE name IN (%s, %s)",
                (seed_name, workspace_name),
            )
