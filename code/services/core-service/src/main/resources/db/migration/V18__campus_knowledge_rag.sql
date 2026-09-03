-- Store independently replaceable text chunks for local semantic retrieval.
CREATE TABLE knowledge_chunk (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_document(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    content TEXT NOT NULL CHECK (length(trim(content)) > 0),
    content_hash VARCHAR(64) NOT NULL,
    document_updated_at TIMESTAMPTZ NOT NULL,
    embedding vector(512) NOT NULL,
    indexed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_knowledge_chunk_document ON knowledge_chunk(document_id);
CREATE INDEX idx_knowledge_chunk_embedding
    ON knowledge_chunk USING hnsw (embedding vector_cosine_ops);

-- Existing generic records remain valid, while new writes use the simplified contract.
UPDATE knowledge_document
SET source = '校园知识库管理',
    payload = jsonb_build_object(
        'category', COALESCE(NULLIF(payload->>'category', ''), '校园服务'),
        'body', COALESCE(payload->>'body', '')
    ),
    updated_at = CURRENT_TIMESTAMP
WHERE deleted_at IS NULL;
