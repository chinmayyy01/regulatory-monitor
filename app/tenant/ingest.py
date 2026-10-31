import argparse
import hashlib
from datetime import date
from pathlib import Path

from psycopg.types.json import Jsonb

from app.db import apply_schema, connect
from app.ingest.pdf import parse_pdf
from app.ingest.segment import Clause, segment
from app.search.embed import embed_texts, vector_literal

EMBED_BATCH = 32

INSERT_CLAUSE = """
INSERT INTO tenant_clause
    (tenant_doc_id, ordinal, section_no, heading_path, text, page, bbox, spans)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

PENDING = """
SELECT tc.id, tc.text
FROM tenant_clause tc
JOIN tenant_doc td ON td.id = tc.tenant_doc_id
WHERE td.tenant_id = %s AND tc.embedding IS NULL
ORDER BY tc.id
LIMIT %s
"""


def ensure_tenant(
    connection,
    name: str,
    entity_type: str,
    products: list[str],
    license_type: str | None = None,
    asset_size_band: str | None = None,
) -> int:
    row = connection.execute(
        """
        INSERT INTO tenant (name, entity_type, license_type, products, asset_size_band)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET entity_type = EXCLUDED.entity_type
        RETURNING id
        """,
        (name, entity_type, license_type, products, asset_size_band),
    ).fetchone()
    connection.commit()
    return row[0]


def store_document(
    connection,
    tenant_id: int,
    title: str,
    doc_type: str,
    clauses: list[Clause],
    sha256: str,
    page_count: int,
    version: str | None = None,
    effective_from: date | None = None,
) -> int | None:
    row = connection.execute(
        """
        INSERT INTO tenant_doc (tenant_id, title, doc_type, version, effective_from, sha256, page_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tenant_id, sha256) DO NOTHING
        RETURNING id
        """,
        (tenant_id, title, doc_type, version, effective_from, sha256, page_count),
    ).fetchone()
    connection.commit()
    if row is None:
        return None

    document_id = row[0]
    for clause in clauses:
        connection.execute(
            INSERT_CLAUSE,
            (
                document_id,
                clause.ordinal,
                clause.section_no,
                clause.heading_path,
                clause.text,
                clause.page,
                Jsonb(clause.bbox),
                Jsonb(clause.spans),
            ),
        )
    connection.commit()
    return document_id


def ingest_pdf(
    connection,
    tenant_id: int,
    path: Path,
    doc_type: str = "policy",
    version: str | None = None,
    effective_from: date | None = None,
) -> int | None:
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    lines, pages = parse_pdf(payload)
    return store_document(
        connection,
        tenant_id,
        path.stem.replace("_", " ").replace("-", " ").title(),
        doc_type,
        segment(lines),
        digest,
        pages,
        version,
        effective_from,
    )


def embed_pending(connection, tenant_id: int, limit: int = 100000) -> int:
    done = 0
    while True:
        rows = connection.execute(PENDING, (tenant_id, EMBED_BATCH)).fetchall()
        if not rows:
            break
        vectors = embed_texts([row[1] for row in rows])
        for (clause_id, _), vector in zip(rows, vectors):
            connection.execute(
                "UPDATE tenant_clause SET embedding = %s::vector WHERE id = %s",
                (vector_literal(vector), clause_id),
            )
        connection.commit()
        done += len(rows)
        if done >= limit:
            break
    return done


def main() -> None:
    parser = argparse.ArgumentParser(description="Onboard a tenant and ingest its policy PDFs")
    parser.add_argument("--name", required=True)
    parser.add_argument("--entity-type", required=True)
    parser.add_argument("--products", default="", help="comma separated")
    parser.add_argument("--license-type", default=None)
    parser.add_argument("--dir", default=None, help="folder of *.pdf policies")
    parser.add_argument("--doc-type", default="policy")
    args = parser.parse_args()

    products = [item.strip() for item in args.products.split(",") if item.strip()]

    connection = connect()
    apply_schema(connection)
    tenant_id = ensure_tenant(connection, args.name, args.entity_type, products, args.license_type)
    print(f"tenant {args.name} -> id {tenant_id}", flush=True)

    if args.dir:
        for path in sorted(Path(args.dir).glob("*.pdf")):
            document_id = ingest_pdf(connection, tenant_id, path, args.doc_type)
            if document_id is None:
                print(f"  skip (already ingested): {path.name}", flush=True)
            else:
                print(f"  + {path.name}", flush=True)

    embedded = embed_pending(connection, tenant_id)
    print(f"embedded {embedded} clauses", flush=True)
    connection.close()


if __name__ == "__main__":
    main()
