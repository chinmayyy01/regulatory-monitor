CREATE TABLE IF NOT EXISTS app_user (
    id            BIGSERIAL PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    role          TEXT NOT NULL DEFAULT 'owner',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS session_token (
    token_hash TEXT PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS session_token_user_idx ON session_token (user_id);
