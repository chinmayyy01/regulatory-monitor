from datetime import date

IN_FORCE = """
SELECT reg_clause_id
FROM clause_in_force
WHERE valid_from <= %s AND (valid_to IS NULL OR valid_to > %s)
"""


def in_force_clause_ids(connection, as_of: date | None = None) -> set[int]:
    when = as_of or date.today()
    rows = connection.execute(IN_FORCE, (when, when)).fetchall()
    return {row[0] for row in rows}


def is_in_force(connection, clause_id: int, as_of: date | None = None) -> bool:
    return clause_id in in_force_clause_ids(connection, as_of)
