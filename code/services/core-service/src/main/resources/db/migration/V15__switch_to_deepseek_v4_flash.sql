-- Make the higher-quality reasoning model the active default while keeping API keys environment-only.
UPDATE system_config
SET payload = jsonb_set(
        payload,
        '{configValue}',
        to_jsonb(((payload->>'configValue')::jsonb ||
            '{"provider":"siliconflow","baseUrl":"https://api.siliconflow.cn/v1","model":"deepseek-ai/DeepSeek-V4-Flash","timeoutSeconds":180,"maxRetries":2}'::jsonb
        )::text)
    ),
    updated_at = CURRENT_TIMESTAMP
WHERE lower(code) = lower('LLM_RUNTIME')
  AND deleted_at IS NULL;
