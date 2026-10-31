CREATE TABLE IF NOT EXISTS reg_relation (
    id             BIGSERIAL PRIMARY KEY,
    src_doc_id     BIGINT NOT NULL REFERENCES reg_doc(id) ON DELETE CASCADE,
    dst_doc_id     BIGINT REFERENCES reg_doc(id) ON DELETE CASCADE,
    kind           TEXT NOT NULL CHECK (kind IN ('amends', 'repeals', 'supersedes', 'consolidates', 'clarifies')),
    clause_ref     TEXT,
    target_text    TEXT NOT NULL DEFAULT '',
    effective_from DATE,
    method         TEXT NOT NULL DEFAULT 'regex',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (src_doc_id, kind, clause_ref, dst_doc_id)
);

CREATE INDEX IF NOT EXISTS reg_relation_src_idx ON reg_relation (src_doc_id);
CREATE INDEX IF NOT EXISTS reg_relation_dst_idx ON reg_relation (dst_doc_id);
CREATE INDEX IF NOT EXISTS reg_relation_clause_idx ON reg_relation (dst_doc_id, clause_ref);

ALTER TABLE mapping ADD COLUMN IF NOT EXISTS regulation_span JSONB;
ALTER TABLE mapping ADD COLUMN IF NOT EXISTS policy_span JSONB;

CREATE OR REPLACE VIEW clause_in_force AS
SELECT
    c.id AS reg_clause_id,
    c.reg_doc_id,
    c.section_no,
    d.date_issued AS valid_from,
    (
        SELECT min(r.effective_from)
        FROM reg_relation r
        WHERE r.dst_doc_id = d.id
          AND r.clause_ref = c.section_no
          AND r.kind IN ('amends', 'repeals')
    ) AS valid_to
FROM reg_clause c
JOIN reg_doc d ON d.id = c.reg_doc_id;

ALTER TABLE mapping ADD COLUMN IF NOT EXISTS tenant_id BIGINT REFERENCES tenant(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS mapping_tenant_idx ON mapping (tenant_id, run_id);

ALTER TABLE mapping DROP CONSTRAINT IF EXISTS mapping_tenant_clause_id_fkey;
ALTER TABLE mapping ADD CONSTRAINT mapping_tenant_clause_id_fkey
    FOREIGN KEY (tenant_clause_id) REFERENCES tenant_clause(id) ON DELETE SET NULL;
