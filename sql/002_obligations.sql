CREATE TABLE IF NOT EXISTS obligation (
    id             BIGSERIAL PRIMARY KEY,
    reg_clause_id  BIGINT NOT NULL REFERENCES reg_clause(id) ON DELETE CASCADE,
    ordinal        INTEGER NOT NULL,
    modality       TEXT NOT NULL CHECK (modality IN ('shall', 'shall_not', 'may')),
    actor          TEXT NOT NULL DEFAULT '',
    action         TEXT NOT NULL,
    condition      TEXT NOT NULL DEFAULT '',
    scope_entities TEXT[] NOT NULL DEFAULT '{}',
    valid_from     DATE,
    valid_to       DATE,
    model          TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (reg_clause_id, ordinal)
);

CREATE INDEX IF NOT EXISTS obligation_clause_idx ON obligation (reg_clause_id);
CREATE INDEX IF NOT EXISTS obligation_valid_idx ON obligation (valid_from);
CREATE INDEX IF NOT EXISTS obligation_scope_idx ON obligation USING GIN (scope_entities);
