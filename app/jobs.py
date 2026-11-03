from types import SimpleNamespace

from app.config import MODEL_CHEAP
from app.db import connect_app
from app.mapping.run import run as run_mapping


def start(connection, tenant_id: int, kind: str) -> int:
    row = connection.execute(
        "INSERT INTO job (tenant_id, kind) VALUES (%s, %s) RETURNING id",
        (tenant_id, kind),
    ).fetchone()
    connection.commit()
    return row[0]


def run_map_job(job_id: int, tenant_id: int, limit: int, candidates: int = 5) -> None:
    with connect_app(tenant_id) as connection:
        connection.execute(
            "UPDATE job SET status = 'running', updated_at = now() WHERE id = %s",
            (job_id,),
        )
        connection.commit()

        try:
            row = connection.execute(
                "SELECT name FROM tenant WHERE id = %s", (tenant_id,)
            ).fetchone()
            if row is None:
                raise RuntimeError("tenant not found")

            options = SimpleNamespace(
                limit=limit,
                candidates=candidates,
                sleep=0.2,
                dry_run=False,
                ids=None,
                model=MODEL_CHEAP,
            )
            mapped, rejected, applicable = run_mapping(connection, row[0], options)
            connection.execute(
                """
                UPDATE job
                SET status = 'done', mapped = %s, detail = %s, updated_at = now()
                WHERE id = %s
                """,
                (mapped, f"{rejected} rejected, {applicable} applicable", job_id),
            )
        except Exception as error:
            connection.rollback()
            connection.execute(
                "UPDATE job SET status = 'failed', detail = %s, updated_at = now() WHERE id = %s",
                (str(error)[:300], job_id),
            )
        connection.commit()
