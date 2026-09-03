-- Public, non-secret LLM runtime settings. The API key remains environment-only.
UPDATE system_config
SET name = '大模型运行配置',
    payload = jsonb_build_object(
        'configValue', '{"provider":"siliconflow","baseUrl":"https://api.siliconflow.cn/v1","model":"Qwen/Qwen3.5-4B","timeoutSeconds":60,"maxRetries":2}',
        'description', '管理端可切换模型和运行参数；API Key 仅由本机环境变量提供。'
    ),
    source = '智能服务运行配置',
    updated_at = CURRENT_TIMESTAMP
WHERE lower(code) = lower('LLM_RUNTIME') AND deleted_at IS NULL;

INSERT INTO system_config(code, name, payload, source, created_by, updated_by)
SELECT
    'LLM_RUNTIME',
    '大模型运行配置',
    '{"configValue":"{\"provider\":\"siliconflow\",\"baseUrl\":\"https://api.siliconflow.cn/v1\",\"model\":\"Qwen/Qwen3.5-4B\",\"timeoutSeconds\":60,\"maxRetries\":2}","description":"管理端可切换模型和运行参数；API Key 仅由本机环境变量提供。"}'::jsonb,
    '智能服务运行配置',
    '20000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001'
WHERE NOT EXISTS (
    SELECT 1 FROM system_config WHERE lower(code) = lower('LLM_RUNTIME') AND deleted_at IS NULL
);
