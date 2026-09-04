-- M06 exam assistant: deterministic exam records, review plans, learning evidence, and course RAG.
CREATE TABLE exam_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    subject VARCHAR(120) NOT NULL,
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (btrim(subject) <> ''),
    CHECK (btrim(location) <> ''),
    CHECK (end_time > start_time)
);

CREATE INDEX idx_exam_record_user_time
    ON exam_record(user_id, exam_date, start_time);

CREATE TABLE review_plan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    title VARCHAR(160) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'ARCHIVED')),
    input_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    priority_explanation TEXT NOT NULL DEFAULT '',
    assumptions TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    limitations TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    total_minutes INTEGER NOT NULL CHECK (total_minutes >= 0),
    model_name VARCHAR(160),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_review_plan_user_time ON review_plan(user_id, created_at DESC);

CREATE TABLE review_plan_exam (
    plan_id UUID NOT NULL REFERENCES review_plan(id) ON DELETE CASCADE,
    exam_id UUID NOT NULL REFERENCES exam_record(id) ON DELETE CASCADE,
    priority_score NUMERIC(8, 3) NOT NULL DEFAULT 0,
    PRIMARY KEY (plan_id, exam_id)
);

CREATE TABLE review_plan_stage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES review_plan(id) ON DELETE CASCADE,
    stage_index INTEGER NOT NULL CHECK (stage_index >= 0),
    name VARCHAR(120) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    subject VARCHAR(120) NOT NULL,
    knowledge_points TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    objective TEXT NOT NULL,
    suggested_minutes INTEGER NOT NULL CHECK (suggested_minutes >= 0),
    method TEXT NOT NULL DEFAULT '',
    CHECK (end_date >= start_date),
    UNIQUE (plan_id, stage_index)
);

CREATE TABLE study_material (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course VARCHAR(120) NOT NULL,
    relative_path TEXT NOT NULL UNIQUE,
    file_type VARCHAR(16) NOT NULL,
    byte_size BIGINT NOT NULL CHECK (byte_size >= 0),
    modified_at TIMESTAMPTZ NOT NULL,
    sha256 CHAR(64) NOT NULL,
    parse_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (parse_status IN ('PENDING', 'INDEXED', 'FAILED', 'INACTIVE')),
    parse_error TEXT,
    parser_version VARCHAR(40) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    indexed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_study_material_course_active ON study_material(course, active);

CREATE TABLE study_material_chunk (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES study_material(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    locator VARCHAR(120) NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    content_hash CHAR(64) NOT NULL,
    embedding vector(512) NOT NULL,
    UNIQUE (material_id, chunk_index)
);

CREATE INDEX idx_study_material_chunk_material ON study_material_chunk(material_id);
CREATE INDEX idx_study_material_chunk_embedding
    ON study_material_chunk USING hnsw (embedding vector_cosine_ops);

CREATE TABLE learning_attachment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    original_name VARCHAR(255) NOT NULL,
    media_type VARCHAR(120) NOT NULL,
    relative_path TEXT NOT NULL UNIQUE,
    byte_size BIGINT NOT NULL CHECK (byte_size >= 0),
    sha256 CHAR(64) NOT NULL,
    extracted_text TEXT,
    parse_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (parse_status IN ('PENDING', 'READY', 'FAILED')),
    parse_error TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learning_attachment_user_time
    ON learning_attachment(user_id, created_at DESC);

CREATE TABLE practice_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    course VARCHAR(120) NOT NULL,
    knowledge_point VARCHAR(160) NOT NULL,
    question_type VARCHAR(20) NOT NULL
        CHECK (question_type IN ('CHOICE', 'FILL', 'CALCULATION', 'PROOF', 'PROGRAMMING')),
    difficulty VARCHAR(16) NOT NULL CHECK (difficulty IN ('BASIC', 'MEDIUM', 'HARD')),
    prompt TEXT NOT NULL,
    standard_answer TEXT NOT NULL,
    step_analysis TEXT NOT NULL,
    test_cases JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('MATERIAL', 'AI_GENERATED')),
    source_label VARCHAR(500),
    validation_status VARCHAR(20) NOT NULL
        CHECK (validation_status IN ('VERIFIED', 'PARTIAL', 'UNVERIFIED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_practice_item_user_course
    ON practice_item(user_id, course, created_at DESC);

CREATE TABLE practice_attempt (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    practice_id UUID NOT NULL REFERENCES practice_item(id) ON DELETE CASCADE,
    work_process TEXT NOT NULL,
    final_answer TEXT NOT NULL DEFAULT '',
    correct BOOLEAN,
    score NUMERIC(5, 2) CHECK (score IS NULL OR (score >= 0 AND score <= 100)),
    diagnosis JSONB NOT NULL DEFAULT '{}'::jsonb,
    duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_practice_attempt_user_time
    ON practice_attempt(user_id, created_at DESC);

CREATE TABLE mistake_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    attempt_id UUID NOT NULL UNIQUE REFERENCES practice_attempt(id) ON DELETE CASCADE,
    course VARCHAR(120) NOT NULL,
    knowledge_point VARCHAR(160) NOT NULL,
    cause_type VARCHAR(32) NOT NULL,
    corrected_conclusion TEXT NOT NULL,
    review_suggestion TEXT NOT NULL,
    mastered BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mistake_record_user_mastery
    ON mistake_record(user_id, mastered, created_at DESC);

CREATE TABLE knowledge_mastery (
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    course VARCHAR(120) NOT NULL,
    knowledge_point VARCHAR(160) NOT NULL,
    mastery_score NUMERIC(5, 2) NOT NULL DEFAULT 0
        CHECK (mastery_score >= 0 AND mastery_score <= 100),
    evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
    correct_count INTEGER NOT NULL DEFAULT 0 CHECK (correct_count >= 0),
    last_studied_at TIMESTAMPTZ,
    next_review_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, course, knowledge_point),
    CHECK (correct_count <= evidence_count)
);

CREATE TABLE learning_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    activity_type VARCHAR(24) NOT NULL
        CHECK (activity_type IN ('EXPLANATION', 'SOLUTION', 'DIAGNOSIS', 'PRACTICE', 'PLAN')),
    course VARCHAR(120) NOT NULL,
    knowledge_point VARCHAR(160),
    summary TEXT NOT NULL,
    related_entity_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learning_activity_user_time
    ON learning_activity(user_id, created_at DESC);
