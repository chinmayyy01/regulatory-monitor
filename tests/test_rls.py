import os
import uuid

import pytest

from app.db import apply_schema, connect, connect_app

pytestmark = pytest.mark.skipif(
    not (os.getenv("DATABASE_URL") and os.getenv("DATABASE_URL_APP")),
    reason="DATABASE_URL and DATABASE_URL_APP are required",
)


@pytest.fixture(scope="module")
def tenants():
    suffix = uuid.uuid4().hex[:8]
    with connect() as connection:
        apply_schema(connection)
        ids = []
        for name in (f"rls a {suffix}", f"rls b {suffix}"):
            row = connection.execute(
                "INSERT INTO tenant (name, entity_type) VALUES (%s, 'nbfc') RETURNING id",
                (name,),
            ).fetchone()
            connection.execute(
                "INSERT INTO tenant_doc (tenant_id, title, doc_type, sha256) VALUES (%s, %s, 'policy', %s)",
                (row[0], f"doc for {name}", f"{suffix}-{name}"),
            )
            ids.append(row[0])
        connection.commit()
    yield ids
    with connect() as connection:
        connection.execute("DELETE FROM tenant WHERE id = ANY(%s)", (ids,))
        connection.commit()


def test_tenant_sees_only_its_own_documents(tenants):
    first, second = tenants
    with connect_app(first) as connection:
        seen = {
            row[0]
            for row in connection.execute("SELECT DISTINCT tenant_id FROM tenant_doc").fetchall()
        }
    assert seen == {first}


def test_cross_tenant_read_returns_nothing(tenants):
    first, second = tenants
    with connect_app(first) as connection:
        count = connection.execute(
            "SELECT count(*) FROM tenant_doc WHERE tenant_id = %s", (second,)
        ).fetchone()[0]
    assert count == 0


def test_cross_tenant_write_is_rejected(tenants):
    first, second = tenants
    with connect_app(first) as connection:
        with pytest.raises(Exception) as error:
            connection.execute(
                "INSERT INTO tenant_doc (tenant_id, title, doc_type, sha256) VALUES (%s, 'x', 'policy', %s)",
                (second, uuid.uuid4().hex),
            )
        assert "row-level security" in str(error.value).lower()


def test_no_tenant_set_sees_nothing(tenants):
    with connect_app() as connection:
        assert connection.execute("SELECT count(*) FROM tenant_doc").fetchone()[0] == 0
