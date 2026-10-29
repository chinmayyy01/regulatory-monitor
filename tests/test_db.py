import os
import uuid
from datetime import date

import pytest
from psycopg.types.json import Jsonb

from app.db import apply_schema, connect

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not set"
)


def test_schema_roundtrip():
    suffix = uuid.uuid4().hex
    with connect() as connection:
        apply_schema(connection)
        doc = connection.execute(
            """
            INSERT INTO reg_doc (url, title, doc_type, date_issued, pdf_url, sha256, page_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                f"https://example.test/{suffix}",
                "Test circular",
                "notification",
                date(2026, 1, 1),
                None,
                suffix,
                3,
            ),
        ).fetchone()
        doc_id = doc[0]
        connection.execute(
            """
            INSERT INTO reg_clause (reg_doc_id, ordinal, section_no, heading_path, text, page, bbox, spans)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                doc_id,
                0,
                "1",
                ["1. Scope"],
                "1. Scope\nThe entity shall comply.",
                1,
                Jsonb([40.0, 40.0, 500.0, 60.0]),
                Jsonb([{"page": 1, "bbox": [40.0, 40.0, 500.0, 60.0]}]),
            ),
        )

        count = connection.execute(
            "SELECT count(*) FROM reg_clause WHERE reg_doc_id = %s", (doc_id,)
        ).fetchone()[0]
        assert count == 1

        connection.execute("DELETE FROM reg_doc WHERE id = %s", (doc_id,))
