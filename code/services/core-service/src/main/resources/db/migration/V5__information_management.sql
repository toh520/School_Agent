-- M03 unified information management entities. Domain tables stay separate while
-- payload keeps optional course-project fields extensible without schema churn.
CREATE TABLE canteen (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(40) NOT NULL,
    name VARCHAR(120) NOT NULL,
    parent_code VARCHAR(40),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    source VARCHAR(300) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_by UUID REFERENCES app_user(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES app_user(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ
);

CREATE TABLE food_stall (LIKE canteen INCLUDING ALL);
CREATE TABLE ingredient (LIKE canteen INCLUDING ALL);
CREATE TABLE dish (LIKE canteen INCLUDING ALL);
CREATE TABLE book (LIKE canteen INCLUDING ALL);
CREATE TABLE library_holding (LIKE canteen INCLUDING ALL);
CREATE TABLE knowledge_document (LIKE canteen INCLUDING ALL);
CREATE TABLE system_config (LIKE canteen INCLUDING ALL);

ALTER TABLE canteen ADD CONSTRAINT uk_canteen_code_raw UNIQUE(code);
ALTER TABLE food_stall ADD CONSTRAINT uk_food_stall_code_raw UNIQUE(code);
ALTER TABLE book ADD CONSTRAINT uk_book_code_raw UNIQUE(code);

ALTER TABLE food_stall
    ADD CONSTRAINT fk_food_stall_canteen
    FOREIGN KEY (parent_code) REFERENCES canteen(code);
ALTER TABLE dish
    ADD CONSTRAINT fk_dish_stall
    FOREIGN KEY (parent_code) REFERENCES food_stall(code);
ALTER TABLE library_holding
    ADD CONSTRAINT fk_holding_book
    FOREIGN KEY (parent_code) REFERENCES book(code);

CREATE UNIQUE INDEX uk_canteen_code ON canteen(lower(code)) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uk_food_stall_code ON food_stall(lower(code)) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uk_ingredient_code ON ingredient(lower(code)) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uk_dish_code ON dish(lower(code)) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uk_book_code ON book(lower(code)) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uk_holding_code ON library_holding(lower(code)) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uk_knowledge_code ON knowledge_document(lower(code)) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uk_system_config_code ON system_config(lower(code)) WHERE deleted_at IS NULL;

CREATE INDEX idx_canteen_search ON canteen(status, name) WHERE deleted_at IS NULL;
CREATE INDEX idx_stall_search ON food_stall(status, name) WHERE deleted_at IS NULL;
CREATE INDEX idx_ingredient_search ON ingredient(status, name) WHERE deleted_at IS NULL;
CREATE INDEX idx_dish_search ON dish(status, name) WHERE deleted_at IS NULL;
CREATE INDEX idx_book_search ON book(status, name) WHERE deleted_at IS NULL;
CREATE INDEX idx_holding_search ON library_holding(status, name) WHERE deleted_at IS NULL;
CREATE INDEX idx_knowledge_search ON knowledge_document(status, name) WHERE deleted_at IS NULL;
CREATE INDEX idx_config_search ON system_config(status, name) WHERE deleted_at IS NULL;
CREATE INDEX idx_dish_payload ON dish USING GIN(payload);
CREATE INDEX idx_book_payload ON book USING GIN(payload);
CREATE INDEX idx_knowledge_payload ON knowledge_document USING GIN(payload);

CREATE TABLE admin_operation_log (
    id BIGSERIAL PRIMARY KEY,
    actor_user_id UUID REFERENCES app_user(id) ON DELETE SET NULL,
    action VARCHAR(32) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DEACTIVATE', 'IMPORT', 'ACCOUNT_STATUS')),
    resource_type VARCHAR(32) NOT NULL,
    resource_id VARCHAR(100),
    resource_code VARCHAR(80),
    summary VARCHAR(300) NOT NULL,
    request_id VARCHAR(80),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_admin_operation_time ON admin_operation_log(occurred_at DESC, id DESC);
CREATE INDEX idx_admin_operation_actor ON admin_operation_log(actor_user_id, occurred_at DESC);

-- Sanitized starter records exercise every downstream data contract.
INSERT INTO canteen(code, name, payload, source, created_by, updated_by)
VALUES ('CANTEEN-NORTH', '北区食堂', '{"location":"北区生活区","openingHours":"06:30-20:30","description":"校内综合食堂"}', '校内公开资料', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001');

INSERT INTO food_stall(code, name, parent_code, payload, source, created_by, updated_by)
VALUES ('STALL-NORTH-01', '家常菜窗口', 'CANTEEN-NORTH', '{"location":"一层东侧","openingHours":"10:30-19:30"}', '校内公开资料', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001');

INSERT INTO ingredient(code, name, payload, source, created_by, updated_by)
VALUES ('ING-TOMATO', '番茄', '{"category":"蔬菜","taste":"酸甜","nutritionKcal":18,"nutritionProtein":0.9,"allergens":[]}', '公开食品资料', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001');

INSERT INTO dish(code, name, parent_code, payload, source, created_by, updated_by)
VALUES ('DISH-TOMATO-EGG', '番茄炒蛋', 'STALL-NORTH-01', '{"price":10.00,"availabilityStatus":"AVAILABLE","tastes":["酸甜"],"ingredientCodes":["ING-TOMATO"],"nutritionKcal":180,"nutritionProtein":9.5,"allergens":["蛋类"],"supplyPeriods":["午餐","晚餐"]}', '食堂公示信息', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001');

INSERT INTO book(code, name, payload, source, created_by, updated_by)
VALUES ('BOOK-CS-001', '计算机科学导论', '{"isbn":"9780000000001","authors":["示例作者"],"publisher":"示例出版社","edition":"第1版","publishedYear":2024,"language":"中文","summary":"计算机科学基础入门资料。","tags":["计算机","入门"],"difficulty":"基础"}', '图书馆公开书目', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001');

INSERT INTO library_holding(code, name, parent_code, payload, source, created_by, updated_by)
VALUES ('HOLD-CS-001', '计算机科学导论馆藏', 'BOOK-CS-001', '{"callNumber":"TP3/001","location":"主馆二层","totalCount":3,"availableCount":2,"availabilityStatus":"AVAILABLE"}', '图书馆公开馆藏', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001');

INSERT INTO knowledge_document(code, name, payload, source, created_by, updated_by)
VALUES ('DOC-CAMPUS-001', '校园服务指南', '{"body":"校园公共服务基础说明。","category":"校园服务","ownerDepartment":"信息中心","audiences":["学生"],"publishedOn":"2026-08-01","validUntil":"2027-07-31","version":"1.0","permissionLevel":"PUBLIC","reviewStatus":"APPROVED"}', '学校公开信息', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001');

INSERT INTO system_config(code, name, payload, source, created_by, updated_by)
VALUES ('PUBLIC-SERVICE-NOTICE', '公共服务说明', '{"configValue":"校园服务信息以责任部门最新发布为准。","description":"学生端公共提示，不包含密钥或口令"}', '项目配置基线', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001');
