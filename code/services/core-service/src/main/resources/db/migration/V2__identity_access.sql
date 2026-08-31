-- M02 identity, personal data authorization and minimum auditable cleanup model.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE app_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(64) NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    role VARCHAR(32) NOT NULL CHECK (role IN ('STUDENT', 'INFO_ADMIN')),
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISABLED')),
    nickname VARCHAR(80) NOT NULL,
    avatar_url VARCHAR(500),
    contact VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_app_user_username UNIQUE (username)
);

CREATE TABLE user_preference (
    user_id UUID PRIMARY KEY REFERENCES app_user(id) ON DELETE CASCADE,
    tastes JSONB NOT NULL DEFAULT '[]'::jsonb,
    budget NUMERIC(10, 2),
    avoidances JSONB NOT NULL DEFAULT '[]'::jsonb,
    allergens JSONB NOT NULL DEFAULT '[]'::jsonb,
    dietary_goal VARCHAR(200),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (budget IS NULL OR budget >= 0)
);

CREATE TABLE data_authorization (
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    data_scope VARCHAR(32) NOT NULL CHECK (data_scope IN ('EXAMS', 'MASTERY', 'DIET', 'CHAT_HISTORY')),
    granted BOOLEAN NOT NULL DEFAULT FALSE,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, data_scope)
);

CREATE TABLE auth_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    refresh_token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMPTZ
);
CREATE INDEX idx_auth_session_user ON auth_session(user_id, expires_at);

CREATE TABLE user_long_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    data_scope VARCHAR(32) NOT NULL CHECK (data_scope IN ('EXAMS', 'MASTERY', 'DIET', 'CHAT_HISTORY')),
    content_summary VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_user_memory_owner_scope ON user_long_term_memory(user_id, data_scope);

CREATE TABLE data_cleanup_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    data_scope VARCHAR(32) NOT NULL,
    trigger_type VARCHAR(32) NOT NULL CHECK (trigger_type IN ('AUTHORIZATION_REVOKED', 'USER_REQUEST')),
    status VARCHAR(16) NOT NULL CHECK (status IN ('COMPLETED', 'FAILED')),
    deleted_records INTEGER NOT NULL DEFAULT 0,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);
CREATE INDEX idx_cleanup_record_user_time ON data_cleanup_record(user_id, requested_at DESC);

CREATE TABLE audit_event (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES app_user(id) ON DELETE SET NULL,
    actor_user_id UUID REFERENCES app_user(id) ON DELETE SET NULL,
    event_type VARCHAR(64) NOT NULL,
    module VARCHAR(32) NOT NULL,
    target_type VARCHAR(64),
    target_id VARCHAR(100),
    outcome VARCHAR(16) NOT NULL CHECK (outcome IN ('SUCCESS', 'DENIED', 'FAILED')),
    request_id VARCHAR(80),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_user_time ON audit_event(user_id, occurred_at DESC);
CREATE INDEX idx_audit_event_module_time ON audit_event(event_type, module, occurred_at DESC);

INSERT INTO app_user (id, username, password_hash, role, nickname)
VALUES
    ('10000000-0000-0000-0000-000000000001', 'student1', crypt('Student@123', gen_salt('bf', 10)), 'STUDENT', '学生用户一'),
    ('10000000-0000-0000-0000-000000000002', 'student2', crypt('Student@123', gen_salt('bf', 10)), 'STUDENT', '学生用户二'),
    ('20000000-0000-0000-0000-000000000001', 'admin1', crypt('Admin@123', gen_salt('bf', 10)), 'INFO_ADMIN', '信息资料管理员');

INSERT INTO user_preference (user_id)
SELECT id FROM app_user;

INSERT INTO data_authorization (user_id, data_scope, granted)
SELECT app_user.id, scope.data_scope, FALSE
FROM app_user
CROSS JOIN (VALUES ('EXAMS'), ('MASTERY'), ('DIET'), ('CHAT_HISTORY')) AS scope(data_scope);
