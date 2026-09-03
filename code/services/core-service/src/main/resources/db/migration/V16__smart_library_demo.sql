-- M07 smart library demo: one holding row per book and simple borrow/return history.
CREATE UNIQUE INDEX IF NOT EXISTS uk_holding_active_book
    ON library_holding(lower(parent_code)) WHERE deleted_at IS NULL;

CREATE TABLE library_loan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    book_id UUID NOT NULL REFERENCES book(id) ON DELETE RESTRICT,
    holding_id UUID NOT NULL REFERENCES library_holding(id) ON DELETE RESTRICT,
    status VARCHAR(16) NOT NULL DEFAULT 'BORROWED'
        CHECK (status IN ('BORROWED', 'RETURNED')),
    borrowed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    returned_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK ((status = 'BORROWED' AND returned_at IS NULL)
        OR (status = 'RETURNED' AND returned_at IS NOT NULL))
);

CREATE UNIQUE INDEX uk_library_loan_current_user_book
    ON library_loan(user_id, book_id) WHERE status = 'BORROWED';
CREATE INDEX idx_library_loan_user_time
    ON library_loan(user_id, borrowed_at DESC);
CREATE INDEX idx_library_loan_holding_status
    ON library_loan(holding_id, status);

-- The single-library demo derives availability from counts and no longer uses difficulty.
UPDATE book
SET payload = (payload - 'difficulty')
    || jsonb_build_object(
        'category', COALESCE(NULLIF(payload->>'category', ''), '计算机'),
        'coverImage', COALESCE(payload->>'coverImage', '')
    );

INSERT INTO book(code, name, payload, source)
VALUES
('BOOK-1984', '1984', '{"isbn":"9780451524935","authors":["乔治·奥威尔"],"publisher":"Signet Classic","edition":"平装版","publishedYear":1950,"language":"中文","category":"小说","tags":["反乌托邦","社会思考","经典"],"summary":"一部以极权社会为背景，讨论权力、语言与个人自由的经典小说。","coverImage":"https://covers.openlibrary.org/b/isbn/9780451524935-L.jpg"}', '智慧图书馆演示数据'),
('BOOK-ORIENT-EXPRESS', '东方快车谋杀案', '{"isbn":"9780062693662","authors":["阿加莎·克里斯蒂"],"publisher":"William Morrow","edition":"平装版","publishedYear":2017,"language":"中文","category":"小说","tags":["悬疑","推理","密室","经典"],"summary":"波洛在被大雪困住的列车上调查一桩谋杀案，线索密集且结局富有反转。","coverImage":"https://covers.openlibrary.org/b/isbn/9780062693662-L.jpg"}', '智慧图书馆演示数据'),
('BOOK-PRIDE', '傲慢与偏见', '{"isbn":"9780141439518","authors":["简·奥斯汀"],"publisher":"Penguin Classics","edition":"经典版","publishedYear":2003,"language":"中文","category":"名著","tags":["爱情","成长","英国文学","经典"],"summary":"围绕伊丽莎白与达西的相识和改变，描绘情感、家庭与社会偏见。","coverImage":"https://covers.openlibrary.org/b/isbn/9780141439518-L.jpg"}', '智慧图书馆演示数据'),
('BOOK-LITTLE-PRINCE', '小王子', '{"isbn":"9780156012195","authors":["安托万·德·圣埃克苏佩里"],"publisher":"Mariner Books","edition":"平装版","publishedYear":2000,"language":"中文","category":"名著","tags":["童话","成长","哲思","治愈"],"summary":"借一段星际旅行讲述友谊、责任和看见事物本质的方式。","coverImage":"https://covers.openlibrary.org/b/isbn/9780156012195-L.jpg"}', '智慧图书馆演示数据'),
('BOOK-CLEAN-CODE', '代码整洁之道', '{"isbn":"9780132350884","authors":["Robert C. Martin"],"publisher":"Prentice Hall","edition":"第1版","publishedYear":2008,"language":"中文","category":"计算机","tags":["编程","软件工程","代码质量"],"summary":"通过原则与案例介绍如何编写更清晰、易维护的软件代码。","coverImage":"https://covers.openlibrary.org/b/isbn/9780132350884-L.jpg"}', '智慧图书馆演示数据'),
('BOOK-COMPUTER-NETWORKS', '计算机网络', '{"isbn":"9780132126953","authors":["Andrew S. Tanenbaum","David J. Wetherall"],"publisher":"Pearson","edition":"第5版","publishedYear":2010,"language":"中文","category":"计算机","tags":["网络","计算机基础","教材"],"summary":"系统介绍计算机网络分层结构、协议原理与典型网络技术。","coverImage":"https://covers.openlibrary.org/b/isbn/9780132126953-L.jpg"}', '智慧图书馆演示数据'),
('BOOK-SAPIENS', '人类简史', '{"isbn":"9780062316097","authors":["尤瓦尔·赫拉利"],"publisher":"Harper","edition":"平装版","publishedYear":2015,"language":"中文","category":"历史","tags":["人类学","历史","社会思考"],"summary":"从认知革命、农业革命等视角梳理人类社会长期演化。","coverImage":"https://covers.openlibrary.org/b/isbn/9780062316097-L.jpg"}', '智慧图书馆演示数据'),
('BOOK-GATSBY', '了不起的盖茨比', '{"isbn":"9780743273565","authors":["F. Scott Fitzgerald"],"publisher":"Scribner","edition":"平装版","publishedYear":2004,"language":"中文","category":"名著","tags":["美国文学","爱情","社会","经典"],"summary":"通过盖茨比对理想与爱情的追逐，描绘爵士时代的繁华与幻灭。","coverImage":"https://covers.openlibrary.org/b/isbn/9780743273565-L.jpg"}', '智慧图书馆演示数据')
ON CONFLICT DO NOTHING;

INSERT INTO library_holding(code, name, parent_code, payload, source)
SELECT 'HOLD-' || substring(code from 6), name || '馆藏', code,
       jsonb_build_object(
           'callNumber', CASE
               WHEN payload->>'category' = '计算机' THEN 'TP3/' || right(code, 4)
               WHEN payload->>'category' = '历史' THEN 'K0/' || right(code, 4)
               ELSE 'I5/' || right(code, 4)
           END,
           'location', CASE
               WHEN payload->>'category' = '计算机' THEN '二层科技书架'
               WHEN payload->>'category' = '历史' THEN '三层人文书架'
               ELSE '一层文学书架'
           END,
           'totalCount', 3,
           'availableCount', 3,
           'availabilityStatus', 'AVAILABLE'
       ),
       '智慧图书馆演示数据'
FROM book
WHERE code LIKE 'BOOK-%'
  AND deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM library_holding holding
      WHERE holding.parent_code = book.code AND holding.deleted_at IS NULL
  );
