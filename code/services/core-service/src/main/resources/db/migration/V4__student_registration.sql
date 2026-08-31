-- Add normalized student identity fields and case-insensitive account uniqueness.
ALTER TABLE app_user
    ADD COLUMN student_number VARCHAR(20),
    ADD COLUMN real_name VARCHAR(50),
    ADD COLUMN phone VARCHAR(11);

UPDATE app_user
SET student_number = '2026000001', real_name = '学生用户一', phone = '13900000001'
WHERE id = '10000000-0000-0000-0000-000000000001';

UPDATE app_user
SET student_number = '2026000002', real_name = '学生用户二', phone = '13900000002'
WHERE id = '10000000-0000-0000-0000-000000000002';

ALTER TABLE app_user DROP CONSTRAINT uk_app_user_username;
CREATE UNIQUE INDEX uk_app_user_username_ci ON app_user (lower(username));
CREATE UNIQUE INDEX uk_app_user_student_number ON app_user (student_number)
    WHERE student_number IS NOT NULL;
CREATE UNIQUE INDEX uk_app_user_phone ON app_user (phone)
    WHERE phone IS NOT NULL;

ALTER TABLE app_user
    ADD CONSTRAINT ck_student_identity_required CHECK (
        role <> 'STUDENT'
        OR (student_number IS NOT NULL AND real_name IS NOT NULL AND phone IS NOT NULL)
    ),
    ADD CONSTRAINT ck_student_number_format CHECK (
        student_number IS NULL OR student_number ~ '^[0-9]{6,20}$'
    ),
    ADD CONSTRAINT ck_phone_format CHECK (
        phone IS NULL OR phone ~ '^1[3-9][0-9]{9}$'
    );

CREATE INDEX idx_app_user_role_status ON app_user (role, status);
CREATE INDEX idx_audit_actor_time ON audit_event (actor_user_id, occurred_at DESC);
