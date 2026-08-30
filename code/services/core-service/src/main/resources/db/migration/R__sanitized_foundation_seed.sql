-- Repeatable seed contains no account, personal, health or credential data.
INSERT INTO schema_metadata (metadata_key, metadata_value)
VALUES ('seed_classification', 'SANITIZED_FOUNDATION_ONLY')
ON CONFLICT (metadata_key) DO UPDATE
SET metadata_value = EXCLUDED.metadata_value,
    updated_at = CURRENT_TIMESTAMP;
