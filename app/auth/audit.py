FAILURE_WINDOW_MINUTES = 15


def record_attempt(connection, email: str, ip: str, succeeded: bool) -> None:
    connection.execute(
        "INSERT INTO login_attempt (email, ip, succeeded) VALUES (%s, %s, %s)",
        (email, ip[:64], succeeded),
    )
    connection.commit()


def recent_failures(connection, email: str) -> int:
    row = connection.execute(
        """
        SELECT count(*) FROM login_attempt
        WHERE email = %s AND NOT succeeded
          AND at > now() - make_interval(mins => %s)
        """,
        (email, FAILURE_WINDOW_MINUTES),
    ).fetchone()
    return row[0] if row else 0


def clear_failures(connection, email: str) -> None:
    connection.execute("DELETE FROM login_attempt WHERE email = %s", (email,))
    connection.commit()


def record_event(
    connection,
    kind: str,
    user_id: int | None = None,
    email: str = "",
    ip: str = "",
    user_agent: str = "",
) -> None:
    connection.execute(
        "INSERT INTO auth_event (user_id, email, kind, ip, user_agent) VALUES (%s, %s, %s, %s, %s)",
        (user_id, email[:200], kind, ip[:64], user_agent[:300]),
    )
    connection.commit()
