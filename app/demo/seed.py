import argparse
import hashlib
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from app.auth.passwords import hash_password
from app.config import MODEL_WORKER
from app.db import apply_schema, connect
from app.demo.policies import build as build_policies
from app.ingest.pdf import parse_pdf
from app.ingest.segment import segment
from app.mapping.run import run as run_mapping
from app.tenant.ingest import embed_pending, ensure_tenant, store_document


def reset_tenant(connection, tenant_id: int) -> None:
    connection.execute("DELETE FROM mapping WHERE tenant_id = %s", (tenant_id,))
    connection.execute("DELETE FROM tenant_doc WHERE tenant_id = %s", (tenant_id,))
    connection.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a demo tenant with policies and verdicts")
    parser.add_argument("--tenant", default="demo-fintech")
    parser.add_argument("--entity-type", default="commercial_bank")
    parser.add_argument("--products", default="lending")
    parser.add_argument("--email", default="demo@regintel.dev")
    parser.add_argument("--password", default="correct-horse-battery-staple")
    parser.add_argument("--map", type=int, default=20, help="obligations to map (0 = skip)")
    parser.add_argument("--reset", action="store_true", help="delete existing documents and verdicts")
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)

    tenant_id = ensure_tenant(
        connection,
        args.tenant,
        args.entity_type,
        [item for item in args.products.split(",") if item],
    )
    print(f"tenant {args.tenant} -> {tenant_id}", flush=True)

    if args.reset:
        reset_tenant(connection, tenant_id)
        print("  reset existing documents and verdicts", flush=True)

    connection.execute(
        """
        INSERT INTO app_user (email, password_hash, tenant_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash,
                                         tenant_id = EXCLUDED.tenant_id
        """,
        (args.email.lower(), hash_password(args.password), tenant_id),
    )
    connection.commit()

    for path in build_policies():
        payload = path.read_bytes()
        lines, pages = parse_pdf(payload)
        document_id = store_document(
            connection,
            tenant_id,
            path.stem.replace("_", " ").title(),
            "policy",
            segment(lines),
            hashlib.sha256(payload).hexdigest(),
            pages,
            effective_from=date.today(),
        )
        print(f"  {'+' if document_id else '='} {path.name}", flush=True)

    embedded = embed_pending(connection, tenant_id)
    print(f"  embedded {embedded} clauses", flush=True)

    if args.map > 0:
        options = SimpleNamespace(
            limit=args.map,
            candidates=5,
            sleep=0.2,
            dry_run=False,
            ids=None,
            model=MODEL_WORKER,
        )
        mapped, rejected, applicable = run_mapping(connection, args.tenant, options)
        print(f"  mapped {mapped}, rejected {rejected}, applicable {applicable}", flush=True)

    print(f"\nlogin: {args.email} / {args.password}")
    connection.close()


if __name__ == "__main__":
    main()
