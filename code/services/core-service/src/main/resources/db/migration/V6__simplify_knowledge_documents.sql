-- Align existing M03 records with the simplified announcement-text contract.
-- RAG indexing and vector storage remain deferred to M08.
UPDATE knowledge_document
SET payload = jsonb_build_object(
        'category', COALESCE(payload -> 'category', '"校园公告"'::jsonb),
        'keywords', COALESCE(
            payload -> 'keywords',
            jsonb_build_array(COALESCE(payload ->> 'category', '校园公告'))
        ),
        'body', COALESCE(payload -> 'body', '""'::jsonb)
    ),
    updated_at = CURRENT_TIMESTAMP;
