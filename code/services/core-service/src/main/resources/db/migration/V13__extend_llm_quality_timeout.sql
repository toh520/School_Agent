-- Allow complete recommendation generation now that the application does not cap output tokens.
UPDATE system_config
SET payload = jsonb_set(
        payload,
        '{configValue}',
        to_jsonb(((payload->>'configValue')::jsonb || '{"timeoutSeconds":180}'::jsonb)::text)
    ),
    updated_at = CURRENT_TIMESTAMP
WHERE lower(code) = lower('LLM_RUNTIME')
  AND deleted_at IS NULL;
