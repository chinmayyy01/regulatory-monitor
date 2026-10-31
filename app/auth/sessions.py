import hashlib
import secrets
from datetime import datetime, timedelta, timezone

SESSION_DAYS = 7


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(connection, user_id: int, user_agent: str = "") -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    connection.execute(
        "INSERT INTO session_token (token_hash, user_id, expires_at, user_agent) "
        "VALUES (%s, %s, %s, %s)",
        (_digest(token), user_id, expires_at, user_agent[:300]),
    )
    connection.commit()
    return token


def user_for_token(connection, token: str):
    if not token:
        return None
    return connection.execute(
        """
        SELECT u.id, u.email, u.tenant_id, u.role
        FROM session_token s
        JOIN app_user u ON u.id = s.user_id
        WHERE s.token_hash = %s AND s.expires_at > now()
        """,
        (_digest(token),),
    ).fetchone()


def delete_session(connection, token: str) -> None:
    if not token:
        return
    connection.execute("DELETE FROM session_token WHERE token_hash = %s", (_digest(token),))
    connection.commit()


def list_sessions(connection, user_id: int):
    return connection.execute(
        """
        SELECT id, created_at, expires_at, user_agent
        FROM session_token
        WHERE user_id = %s AND expires_at > now()
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()


def revoke_session(connection, user_id: int, session_id: int) -> int:
    removed = connection.execute(
        "DELETE FROM session_token WHERE id = %s AND user_id = %s",
        (session_id, user_id),
    ).rowcount
    connection.commit()
    return removed


def revoke_all(connection, user_id: int) -> int:
    removed = connection.execute(
        "DELETE FROM session_token WHERE user_id = %s", (user_id,)
    ).rowcount
    connection.commit()
    return removed


def purge_expired(connection) -> int:
    removed = connection.execute("DELETE FROM session_token WHERE expires_at <= now()").rowcount
    connection.commit()
    return removed
