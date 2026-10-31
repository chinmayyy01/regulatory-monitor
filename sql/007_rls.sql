CREATE INDEX IF NOT EXISTS tenant_doc_tenant_idx ON tenant_doc (tenant_id);

ALTER TABLE tenant_doc    ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_clause ENABLE ROW LEVEL SECURITY;
ALTER TABLE mapping       ENABLE ROW LEVEL SECURITY;

ALTER TABLE tenant_doc    FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_clause FORCE ROW LEVEL SECURITY;
ALTER TABLE mapping       FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_doc_isolation ON tenant_doc;
CREATE POLICY tenant_doc_isolation ON tenant_doc
    USING (tenant_id = current_setting('app.tenant_id', true)::bigint)
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::bigint);

DROP POLICY IF EXISTS tenant_clause_isolation ON tenant_clause;
CREATE POLICY tenant_clause_isolation ON tenant_clause
    USING (
        EXISTS (
            SELECT 1 FROM tenant_doc d
            WHERE d.id = tenant_clause.tenant_doc_id
              AND d.tenant_id = current_setting('app.tenant_id', true)::bigint
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM tenant_doc d
            WHERE d.id = tenant_clause.tenant_doc_id
              AND d.tenant_id = current_setting('app.tenant_id', true)::bigint
        )
    );

DROP POLICY IF EXISTS mapping_isolation ON mapping;
CREATE POLICY mapping_isolation ON mapping
    USING (tenant_id = current_setting('app.tenant_id', true)::bigint)
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::bigint);

GRANT USAGE ON SCHEMA public TO regintel_app;
GRANT SELECT ON reg_doc, reg_clause, reg_relation, obligation, clause_in_force TO regintel_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant, tenant_doc, tenant_clause, mapping TO regintel_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON app_user, session_token TO regintel_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO regintel_app;

GRANT UPDATE (embedding) ON obligation TO regintel_app;
