-- M01 foundation only: enable vector support and record schema metadata.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schema_metadata (
    metadata_key VARCHAR(100) PRIMARY KEY,
    metadata_value VARCHAR(500) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_metadata (metadata_key, metadata_value)
VALUES ('foundation_version', 'M01-V1')
ON CONFLICT (metadata_key) DO UPDATE
SET metadata_value = EXCLUDED.metadata_value,
    updated_at = CURRENT_TIMESTAMP;
