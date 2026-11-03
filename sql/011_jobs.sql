CREATE TABLE IF NOT EXISTS job (
    id         BIGSERIAL PRIMARY KEY,
    tenant_id  BIGINT NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    kind       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'queued',
    detail     TEXT NOT NULL DEFAULT '',
    mapped     INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS job_tenant_idx ON job (tenant_id, created_at DESC);

ALTER TABLE job ENABLE ROW LEVEL SECURITY;
ALTER TABLE job FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS job_isolation ON job;
CREATE POLICY job_isolation ON job
    USING (tenant_id = current_setting('app.tenant_id', true)::bigint)
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::bigint);

GRANT SELECT, INSERT, UPDATE, DELETE ON job TO regintel_app;
GRANT USAGE, SELECT ON SEQUENCE job_id_seq TO regintel_app;
