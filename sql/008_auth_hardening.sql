ALTER TABLE session_token ADD COLUMN IF NOT EXISTS id BIGSERIAL;
ALTER TABLE session_token ADD COLUMN IF NOT EXISTS user_agent TEXT NOT NULL DEFAULT '';
CREATE UNIQUE INDEX IF NOT EXISTS session_token_id_idx ON session_token (id);

CREATE TABLE IF NOT EXISTS login_attempt (
    id        BIGSERIAL PRIMARY KEY,
    email     TEXT NOT NULL,
    ip        TEXT NOT NULL DEFAULT '',
    succeeded BOOLEAN NOT NULL DEFAULT true,
    at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS login_attempt_email_idx ON login_attempt (email, at DESC);

CREATE TABLE IF NOT EXISTS auth_event (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    email      TEXT NOT NULL DEFAULT '',
    kind       TEXT NOT NULL,
    ip         TEXT NOT NULL DEFAULT '',
    user_agent TEXT NOT NULL DEFAULT '',
    at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS auth_event_user_idx ON auth_event (user_id, at DESC);

GRANT SELECT, INSERT, UPDATE, DELETE ON login_attempt, auth_event TO regintel_app;
GRANT USAGE, SELECT ON SEQUENCE login_attempt_id_seq, auth_event_id_seq TO regintel_app;
GRANT INSERT ON session_token TO regintel_app;
