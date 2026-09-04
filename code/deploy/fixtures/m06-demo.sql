-- Synthetic local-only fixtures. No personal database rows or credentials are exported.
-- Apply after Flyway migrations; repeated runs do not overwrite existing records.
BEGIN;
INSERT INTO exam_record(id,user_id,subject,exam_date,start_time,end_time,location) VALUES
('60000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000001','数据结构',CURRENT_DATE+14,'09:00','11:00','演示教室A'),
('60000000-0000-0000-0000-000000000002','10000000-0000-0000-0000-000000000001','算法设计与分析',CURRENT_DATE+21,'14:00','16:00','演示教室B'),
('60000000-0000-0000-0000-000000000003','10000000-0000-0000-0000-000000000001','计算机网络',CURRENT_DATE+28,'09:00','11:00','演示教室C')
ON CONFLICT (id) DO NOTHING;

INSERT INTO practice_item(id,user_id,course,knowledge_point,question_type,difficulty,prompt,standard_answer,step_analysis,test_cases,source_type,source_label,validation_status) VALUES
('60000000-0000-0000-0000-000000000010','10000000-0000-0000-0000-000000000001','数据结构','二叉树遍历','FILL','BASIC','根A，左孩子B，右孩子C，B和C均为叶子。求前序遍历。','ABC','1. 先访问根A。2. 遍历左子树B。3. 遍历右子树C，得到ABC。','[]','AI_GENERATED','AI生成标识演示：人工构造的合成测试题','PARTIAL')
ON CONFLICT (id) DO NOTHING;

INSERT INTO practice_attempt(id,user_id,practice_id,work_process,final_answer,correct,score,diagnosis,duration_seconds) VALUES
('60000000-0000-0000-0000-000000000011','10000000-0000-0000-0000-000000000001','60000000-0000-0000-0000-000000000010','先访问左孩子B，再根A，最后右孩子C。','BAC',FALSE,30,'{"items":["第1步误用中序规则，前序应先根后左后右。"],"causeType":"CONCEPT","correctedConclusion":"ABC","reviewSuggestion":"重新按根、左、右各写一步。"}',60),
('60000000-0000-0000-0000-000000000012','10000000-0000-0000-0000-000000000001','60000000-0000-0000-0000-000000000010','先访问根A，再左孩子B，最后右孩子C。','ABC',TRUE,100,'{"items":[],"causeType":"NONE","correctedConclusion":"ABC","reviewSuggestion":"继续练习不同结构的树。"}',45)
ON CONFLICT (id) DO NOTHING;

INSERT INTO mistake_record(id,user_id,attempt_id,course,knowledge_point,cause_type,corrected_conclusion,review_suggestion,mastered) VALUES
('60000000-0000-0000-0000-000000000013','10000000-0000-0000-0000-000000000001','60000000-0000-0000-0000-000000000011','数据结构','二叉树遍历','CONCEPT','ABC','重新按根、左、右各写一步。',FALSE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO learning_activity(id,user_id,activity_type,course,knowledge_point,summary,related_entity_id) VALUES
('60000000-0000-0000-0000-000000000014','10000000-0000-0000-0000-000000000001','PRACTICE','数据结构','二叉树遍历','合成数据：用于验证练习与作答历史回看。','60000000-0000-0000-0000-000000000010')
ON CONFLICT (id) DO NOTHING;
COMMIT;
