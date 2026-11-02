CREATE TABLE IF NOT EXISTS membership (
    user_id    BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    tenant_id  BIGINT NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    role       TEXT NOT NULL DEFAULT 'owner',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, tenant_id)
);

INSERT INTO membership (user_id, tenant_id, role)
SELECT id, tenant_id, role FROM app_user
ON CONFLICT DO NOTHING;

GRANT SELECT, INSERT, UPDATE, DELETE ON membership TO regintel_app;
