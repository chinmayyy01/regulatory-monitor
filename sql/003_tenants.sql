CREATE TABLE IF NOT EXISTS tenant (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    entity_type     TEXT NOT NULL,
    license_type    TEXT,
    products        TEXT[] NOT NULL DEFAULT '{}',
    asset_size_band TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_doc (
    id             BIGSERIAL PRIMARY KEY,
    tenant_id      BIGINT NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    title          TEXT NOT NULL,
    doc_type       TEXT NOT NULL,
    version        TEXT,
    effective_from DATE,
    sha256         TEXT NOT NULL,
    pdf_url        TEXT,
    page_count     INTEGER NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, sha256)
);

CREATE TABLE IF NOT EXISTS tenant_clause (
    id            BIGSERIAL PRIMARY KEY,
    tenant_doc_id BIGINT NOT NULL REFERENCES tenant_doc(id) ON DELETE CASCADE,
    ordinal       INTEGER NOT NULL,
    section_no    TEXT,
    heading_path  TEXT[] NOT NULL DEFAULT '{}',
    text          TEXT NOT NULL,
    page          INTEGER NOT NULL DEFAULT 1,
    bbox          JSONB,
    spans         JSONB NOT NULL DEFAULT '[]',
    embedding     vector(384),
    UNIQUE (tenant_doc_id, ordinal)
);

CREATE INDEX IF NOT EXISTS tenant_clause_doc_idx ON tenant_clause (tenant_doc_id);
CREATE INDEX IF NOT EXISTS tenant_clause_embedding_idx
    ON tenant_clause USING hnsw (embedding vector_cosine_ops);

ALTER TABLE obligation ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS obligation_embedding_idx
    ON obligation USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS mapping (
    id                   BIGSERIAL PRIMARY KEY,
    obligation_id        BIGINT NOT NULL REFERENCES obligation(id) ON DELETE CASCADE,
    tenant_clause_id     BIGINT REFERENCES tenant_clause(id) ON DELETE CASCADE,
    verdict              TEXT NOT NULL CHECK (verdict IN ('satisfied', 'partial', 'missing', 'stale')),
    confidence           REAL NOT NULL DEFAULT 0,
    evidence_regulation  TEXT NOT NULL DEFAULT '',
    evidence_policy      TEXT NOT NULL DEFAULT '',
    reason               TEXT NOT NULL DEFAULT '',
    model                TEXT NOT NULL,
    run_id               TEXT NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (obligation_id, tenant_clause_id, run_id)
);

CREATE INDEX IF NOT EXISTS mapping_obligation_idx ON mapping (obligation_id);
CREATE INDEX IF NOT EXISTS mapping_clause_idx ON mapping (tenant_clause_id);
