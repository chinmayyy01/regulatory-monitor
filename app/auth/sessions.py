import hashlib
import secrets
from datetime import datetime, timedelta, timezone

SESSION_DAYS = 7


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    connection.execute(
        "INSERT INTO session_token (token_hash, user_id, expires_at) VALUES (%s, %s, %s)",
        (_digest(token), user_id, expires_at),
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


def purge_expired(connection) -> int:
    removed = connection.execute("DELETE FROM session_token WHERE expires_at <= now()").rowcount
    connection.commit()
    return removed
