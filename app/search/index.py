import argparse

from app.db import apply_schema, connect
from app.search.embed import embed_texts, vector_literal

BATCH = 512

PENDING_REG = """
SELECT id, text FROM reg_clause WHERE embedding IS NULL ORDER BY id LIMIT %s
"""

PENDING_OBLIGATION = """
SELECT id, action FROM obligation WHERE embedding IS NULL ORDER BY id LIMIT %s
"""


def embed_regulation(connection, limit: int) -> int:
    done = 0
    while done < limit:
        rows = connection.execute(PENDING_REG, (min(BATCH, limit - done),)).fetchall()
        if not rows:
            break
        vectors = embed_texts([row[1] for row in rows])
        for (clause_id, _), vector in zip(rows, vectors):
            connection.execute(
                "UPDATE reg_clause SET embedding = %s::vector WHERE id = %s",
                (vector_literal(vector), clause_id),
            )
        connection.commit()
        done += len(rows)
        print(f"  regulation {done}", flush=True)
    return done


def embed_obligations(connection, limit: int) -> int:
    done = 0
    while done < limit:
        rows = connection.execute(PENDING_OBLIGATION, (min(BATCH, limit - done),)).fetchall()
        if not rows:
            break
        vectors = embed_texts([row[1] for row in rows])
        for (obligation_id, _), vector in zip(rows, vectors):
            connection.execute(
                "UPDATE obligation SET embedding = %s::vector WHERE id = %s",
                (vector_literal(vector), obligation_id),
            )
        connection.commit()
        done += len(rows)
        print(f"  obligations {done}", flush=True)
    return done


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed pending regulation clauses and obligations")
    parser.add_argument("--limit", type=int, default=100000)
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)
    regulations = embed_regulation(connection, args.limit)
    obligations = embed_obligations(connection, args.limit)
    print(f"done: {regulations} regulation clauses, {obligations} obligations")
    connection.close()


if __name__ == "__main__":
    main()
