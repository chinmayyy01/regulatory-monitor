ALTER TABLE reg_clause ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS reg_clause_embedding_idx
    ON reg_clause USING hnsw (embedding vector_cosine_ops);
