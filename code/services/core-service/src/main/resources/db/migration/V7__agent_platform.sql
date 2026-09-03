-- M04 Agent-owned conversation, execution trace, result version and feedback data.
CREATE TABLE agent_conversation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    title VARCHAR(120) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DELETED')),
    current_intent VARCHAR(24),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_agent_conversation_owner_time
    ON agent_conversation(user_id, updated_at DESC) WHERE status = 'ACTIVE';

CREATE TABLE agent_message (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversation(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL CHECK (role IN ('USER', 'ASSISTANT', 'TOOL')),
    content TEXT NOT NULL CHECK (char_length(content) BETWEEN 1 AND 12000),
    sequence_number INTEGER NOT NULL CHECK (sequence_number > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (conversation_id, sequence_number)
);
CREATE INDEX idx_agent_message_conversation
    ON agent_message(conversation_id, sequence_number);

CREATE TABLE agent_task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversation(id) ON DELETE CASCADE,
    user_message_id UUID NOT NULL REFERENCES agent_message(id) ON DELETE CASCADE,
    intent VARCHAR(24) NOT NULL,
    status VARCHAR(24) NOT NULL CHECK (
        status IN ('RUNNING', 'NEEDS_INPUT', 'COMPLETED', 'DEGRADED', 'FAILED')),
    missing_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    error_code VARCHAR(64),
    request_id VARCHAR(80) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);
CREATE INDEX idx_agent_task_conversation_time
    ON agent_task(conversation_id, started_at DESC);

CREATE TABLE agent_tool_call (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES agent_task(id) ON DELETE CASCADE,
    tool_name VARCHAR(80) NOT NULL,
    tool_version VARCHAR(24) NOT NULL,
    arguments JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB,
    status VARCHAR(16) NOT NULL CHECK (status IN ('RUNNING', 'SUCCESS', 'DENIED', 'FAILED')),
    error_type VARCHAR(64),
    duration_ms INTEGER CHECK (duration_ms IS NULL OR duration_ms >= 0),
    request_id VARCHAR(80) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);
CREATE INDEX idx_agent_tool_call_task ON agent_tool_call(task_id, created_at);

CREATE TABLE agent_result_version (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES agent_task(id) ON DELETE CASCADE,
    assistant_message_id UUID NOT NULL REFERENCES agent_message(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL CHECK (version_number > 0),
    content TEXT NOT NULL,
    structured_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    basis JSONB NOT NULL DEFAULT '[]'::jsonb,
    limitations JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_name VARCHAR(120),
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (task_id, version_number)
);
CREATE INDEX idx_agent_result_task_version
    ON agent_result_version(task_id, version_number DESC);

CREATE TABLE agent_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_version_id UUID NOT NULL REFERENCES agent_result_version(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    category VARCHAR(16) NOT NULL CHECK (category IN ('HELPFUL', 'UNHELPFUL', 'INCORRECT', 'OUTDATED')),
    comment VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (result_version_id, user_id)
);
CREATE INDEX idx_agent_feedback_category_time
    ON agent_feedback(category, created_at DESC);
