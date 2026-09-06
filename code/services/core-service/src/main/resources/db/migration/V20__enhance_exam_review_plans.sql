-- M06 review-plan versioning and traceability. Existing V19 learning data is preserved.
ALTER TABLE review_plan
    ADD COLUMN plan_group_id UUID,
    ADD COLUMN version_number INTEGER NOT NULL DEFAULT 1 CHECK (version_number > 0),
    ADD COLUMN is_current BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN data_as_of TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN target VARCHAR(300) NOT NULL DEFAULT '',
    ADD COLUMN constraints_text VARCHAR(1000) NOT NULL DEFAULT '',
    ADD COLUMN supersedes_id UUID REFERENCES review_plan(id) ON DELETE SET NULL;

UPDATE review_plan SET plan_group_id = id WHERE plan_group_id IS NULL;
ALTER TABLE review_plan ALTER COLUMN plan_group_id SET NOT NULL;

CREATE UNIQUE INDEX uq_review_plan_group_version
    ON review_plan(user_id, plan_group_id, version_number);
CREATE UNIQUE INDEX uq_review_plan_current_group
    ON review_plan(user_id, plan_group_id) WHERE is_current;

ALTER TABLE review_plan_exam
    ADD COLUMN source_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN allocated_minutes INTEGER NOT NULL DEFAULT 0 CHECK (allocated_minutes >= 0);

UPDATE review_plan_exam target
SET source_updated_at = exam.updated_at
FROM exam_record exam
WHERE exam.id = target.exam_id;

ALTER TABLE review_plan_stage
    ADD COLUMN phase VARCHAR(20) NOT NULL DEFAULT 'FOUNDATION'
        CHECK (phase IN ('FOUNDATION', 'PRACTICE', 'SPRINT')),
    ADD COLUMN rationale TEXT NOT NULL DEFAULT '';
