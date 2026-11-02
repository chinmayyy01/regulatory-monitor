CREATE TABLE IF NOT EXISTS clause_extraction (
    reg_clause_id BIGINT PRIMARY KEY REFERENCES reg_clause(id) ON DELETE CASCADE,
    model         TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO clause_extraction (reg_clause_id, model)
SELECT DISTINCT o.reg_clause_id, o.model
FROM obligation o
ON CONFLICT DO NOTHING;
