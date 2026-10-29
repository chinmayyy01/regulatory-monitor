CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS reg_doc (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT NOT NULL UNIQUE,
    title       TEXT NOT NULL,
    doc_type    TEXT NOT NULL,
    date_issued DATE,
    pdf_url     TEXT,
    sha256      TEXT NOT NULL UNIQUE,
    page_count  INTEGER NOT NULL DEFAULT 0,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reg_clause (
    id           BIGSERIAL PRIMARY KEY,
    reg_doc_id   BIGINT NOT NULL REFERENCES reg_doc(id) ON DELETE CASCADE,
    ordinal      INTEGER NOT NULL,
    section_no   TEXT,
    heading_path TEXT[] NOT NULL DEFAULT '{}',
    text         TEXT NOT NULL,
    page         INTEGER NOT NULL,
    bbox         JSONB,
    spans        JSONB NOT NULL DEFAULT '[]',
    UNIQUE (reg_doc_id, ordinal)
);

CREATE INDEX IF NOT EXISTS reg_clause_doc_idx ON reg_clause (reg_doc_id);
CREATE INDEX IF NOT EXISTS reg_doc_date_idx ON reg_doc (date_issued);
