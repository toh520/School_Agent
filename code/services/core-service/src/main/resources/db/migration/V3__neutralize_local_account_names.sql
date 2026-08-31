-- Replace development-only labels with neutral user-facing account names.
UPDATE app_user
SET nickname = '学生用户一', updated_at = CURRENT_TIMESTAMP
WHERE id = '10000000-0000-0000-0000-000000000001';

UPDATE app_user
SET nickname = '学生用户二', updated_at = CURRENT_TIMESTAMP
WHERE id = '10000000-0000-0000-0000-000000000002';
