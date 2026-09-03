-- Expand the single-library demo with 50 searchable books and matching holdings.
WITH catalog(code, name, isbn, authors, publisher, published_year, language, category, tags, summary) AS (
    VALUES
    ('BOOK-ONE-HUNDRED-YEARS', '百年孤独', '9780060883287', ARRAY['加西亚·马尔克斯'], 'Harper Perennial', 2006, '中文', '名著', ARRAY['魔幻现实主义','家族史诗','拉美文学'], '布恩迪亚家族七代人的传奇映照马孔多从建立到消逝的百年历史。'),
    ('BOOK-KITE-RUNNER', '追风筝的人', '9781594631931', ARRAY['卡勒德·胡赛尼'], 'Riverhead Books', 2013, '中文', '小说', ARRAY['成长','救赎','友情'], '以阿富汗社会变迁为背景，讲述一段关于友谊、背叛与自我救赎的故事。'),
    ('BOOK-TO-LIVE', '活着', '9781408856488', ARRAY['余华'], 'Anchor Books', 2014, '中文', '名著', ARRAY['中国文学','苦难','生命'], '普通人福贵在时代与命运的重压下经历失去，仍以朴素意志继续生活。'),
    ('BOOK-FORTRESS-BESIEGED', '围城', '9780141187860', ARRAY['钱钟书'], 'Penguin Classics', 2006, '中文', '名著', ARRAY['讽刺','婚姻','知识分子'], '以幽默讽刺的语言描绘青年知识分子的爱情、婚姻与人生困境。'),
    ('BOOK-ORDINARY-WORLD', '平凡的世界', '9787530216781', ARRAY['路遥'], '北京十月文艺出版社', 2017, '中文', '小说', ARRAY['现实主义','奋斗','乡土'], '通过孙少安、孙少平等人的生活展现普通人在社会变迁中的奋斗与选择。'),
    ('BOOK-DREAM-RED-MANSIONS', '红楼梦', '9787119006430', ARRAY['曹雪芹','高鹗'], '外文出版社', 2010, '中文', '名著', ARRAY['古典文学','家族','爱情'], '围绕贾府兴衰与宝黛爱情，描绘广阔细腻的中国古代社会生活。'),
    ('BOOK-CALL-TO-ARMS', '呐喊', '9787533949746', ARRAY['鲁迅'], '浙江文艺出版社', 2017, '中文', '名著', ARRAY['短篇小说','社会批判','中国文学'], '收录多篇现代文学经典，以冷峻笔触审视旧社会中的国民精神。'),
    ('BOOK-OLD-MAN-SEA', '老人与海', '9780684801223', ARRAY['欧内斯特·海明威'], 'Scribner', 1995, '中文', '名著', ARRAY['勇气','海洋','经典'], '老渔夫独自在海上与大鱼搏斗，展现人在困境中的尊严与坚韧。'),
    ('BOOK-MOCKINGBIRD', '杀死一只知更鸟', '9780061120084', ARRAY['哈珀·李'], 'Harper Perennial', 2006, '中文', '名著', ARRAY['成长','正义','社会'], '从儿童视角讲述一场充满偏见的审判，讨论正义、勇气与同理心。'),
    ('BOOK-MOON-SIXPENCE', '月亮与六便士', '9780099284765', ARRAY['威廉·萨默塞特·毛姆'], 'Vintage Classics', 1999, '中文', '名著', ARRAY['艺术','理想','人生选择'], '一名中年人离开安稳生活追求绘画理想，探索天才、欲望与世俗价值。'),
    ('BOOK-THE-STRANGER', '局外人', '9780679720201', ARRAY['阿尔贝·加缪'], 'Vintage International', 1989, '中文', '名著', ARRAY['存在主义','荒诞','法国文学'], '默尔索以疏离姿态面对生活与审判，呈现荒诞世界中的个体处境。'),
    ('BOOK-UNBEARABLE-LIGHTNESS', '不能承受的生命之轻', '9780060932138', ARRAY['米兰·昆德拉'], 'Harper Perennial', 1999, '中文', '名著', ARRAY['爱情','哲思','欧洲文学'], '通过几位人物的情感与选择，思考轻与重、偶然与责任。'),
    ('BOOK-AND-THEN-NONE', '无人生还', '9780062073488', ARRAY['阿加莎·克里斯蒂'], 'William Morrow', 2011, '中文', '小说', ARRAY['悬疑','推理','孤岛','反转'], '十名陌生人被困孤岛并接连死亡，谜题紧凑且真相出人意料。'),
    ('BOOK-SHERLOCK-HOLMES', '福尔摩斯探案全集', '9780553328257', ARRAY['阿瑟·柯南·道尔'], 'Bantam Classics', 1986, '中文', '小说', ARRAY['悬疑','推理','侦探','经典'], '收录福尔摩斯与华生破解奇案的故事，重视观察、证据与逻辑推演。'),
    ('BOOK-DEVOTION-SUSPECT-X', '嫌疑人X的献身', '9781250097685', ARRAY['东野圭吾'], 'Minotaur Books', 2016, '中文', '小说', ARRAY['悬疑','推理','爱情','反转'], '数学天才为保护邻居设计精密骗局，侦探与嫌疑人展开智力较量。'),
    ('BOOK-JOURNEY-UNDER-MIDNIGHT-SUN', '白夜行', '9780312376428', ARRAY['东野圭吾'], 'St. Martin''s Press', 2008, '中文', '小说', ARRAY['悬疑','犯罪','人性'], '一桩旧案将两个人的命运长期连接，逐步揭示黑暗而复杂的人性。'),
    ('BOOK-DA-VINCI-CODE', '达·芬奇密码', '9780307474278', ARRAY['丹·布朗'], 'Anchor Books', 2009, '中文', '小说', ARRAY['悬疑','密码','艺术','冒险'], '符号学家沿着艺术与历史线索破解谜团，展开节奏快速的追踪冒险。'),
    ('BOOK-GONE-GIRL', '消失的爱人', '9780307588371', ARRAY['吉莉安·弗琳'], 'Crown Publishing', 2012, '中文', '小说', ARRAY['悬疑','婚姻','心理','反转'], '妻子离奇失踪后丈夫成为嫌疑人，叙述视角不断翻转婚姻真相。'),
    ('BOOK-THREE-BODY', '三体', '9780765382030', ARRAY['刘慈欣'], 'Tor Books', 2014, '中文', '科幻', ARRAY['硬科幻','宇宙','文明'], '人类发现外星文明后面临跨越数百年的危机与文明抉择。'),
    ('BOOK-FOUNDATION', '银河帝国：基地', '9780553293357', ARRAY['艾萨克·阿西莫夫'], 'Bantam Spectra', 1991, '中文', '科幻', ARRAY['太空歌剧','帝国','未来史'], '心理史学家预见帝国衰亡并建立基地，试图缩短漫长的文明黑暗期。'),
    ('BOOK-DUNE', '沙丘', '9780441172719', ARRAY['弗兰克·赫伯特'], 'Ace', 1990, '中文', '科幻', ARRAY['太空歌剧','政治','生态'], '少年保罗在沙漠星球卷入家族、帝国与宗教力量的宏大斗争。'),
    ('BOOK-HYPERION', '海伯利安', '9780553283686', ARRAY['丹·西蒙斯'], 'Bantam Spectra', 1990, '中文', '科幻', ARRAY['太空歌剧','时间','群像'], '七名朝圣者在星际战争前讲述各自经历，共同走向神秘的时间冢。'),
    ('BOOK-STORIES-YOUR-LIFE', '你一生的故事', '9781101972120', ARRAY['特德·姜'], 'Vintage', 2016, '中文', '科幻', ARRAY['短篇小说','语言','时间','哲思'], '以严谨构思探索语言、自由意志、数学与技术对人类经验的影响。'),
    ('BOOK-ANDROID-DREAM', '仿生人会梦见电子羊吗？', '9780345404473', ARRAY['菲利普·迪克'], 'Del Rey', 1996, '中文', '科幻', ARRAY['赛博朋克','人工智能','人性'], '赏金猎人在追捕仿生人的过程中不断追问何为真实的人类与同理心。'),
    ('BOOK-GUNS-GERMS-STEEL', '枪炮、病菌与钢铁', '9780393354324', ARRAY['贾雷德·戴蒙德'], 'W. W. Norton', 2017, '中文', '历史', ARRAY['文明史','地理','人类学'], '从地理环境和资源条件解释不同大陆社会发展道路的巨大差异。'),
    ('BOOK-WANLI-1587', '万历十五年', '9787108009821', ARRAY['黄仁宇'], '生活·读书·新知三联书店', 1997, '中文', '历史', ARRAY['明史','制度','人物'], '以1587年前后的人物与事件切入，分析明代制度运行的深层困境。'),
    ('BOOK-GLOBAL-HISTORY', '全球通史', '9780139238970', ARRAY['L. S. Stavrianos'], 'Prentice Hall', 1998, '中文', '历史', ARRAY['世界史','文明','通史'], '从全球互动视角梳理人类文明从早期社会到现代世界的发展。'),
    ('BOOK-FROM-SOIL', '乡土中国', '9787301174821', ARRAY['费孝通'], '北京大学出版社', 2012, '中文', '社会科学', ARRAY['社会学','乡土社会','中国'], '用差序格局等概念分析传统中国乡土社会的结构与运行逻辑。'),
    ('BOOK-THE-CROWD', '乌合之众', '9780486419565', ARRAY['古斯塔夫·勒庞'], 'Dover Publications', 2002, '中文', '社会科学', ARRAY['群体心理','社会学','传播'], '讨论群体中的心理变化、情绪传播和意见形成机制。'),
    ('BOOK-CHRYSANTHEMUM-SWORD', '菊与刀', '9780618619597', ARRAY['鲁思·本尼迪克特'], 'Mariner Books', 2006, '中文', '社会科学', ARRAY['文化人类学','日本文化','社会'], '从文化模式角度观察日本社会中的礼仪、义务、羞耻与价值体系。'),
    ('BOOK-BRIEF-HISTORY-TIME', '时间简史', '9780553380163', ARRAY['斯蒂芬·霍金'], 'Bantam', 1998, '中文', '科普', ARRAY['宇宙','物理','时间'], '以通俗语言介绍宇宙起源、黑洞、时间箭头和现代宇宙学问题。'),
    ('BOOK-SELFISH-GENE', '自私的基因', '9780198788607', ARRAY['理查德·道金斯'], 'Oxford University Press', 2016, '中文', '科普', ARRAY['进化','生物学','基因'], '从基因视角解释自然选择、合作行为与生命演化。'),
    ('BOOK-ORIGIN-SPECIES', '物种起源', '9780451529060', ARRAY['查尔斯·达尔文'], 'Signet Classics', 2003, '中文', '科普', ARRAY['进化论','生物学','科学经典'], '系统阐述自然选择与物种演化思想，是现代生物学的重要基础著作。'),
    ('BOOK-COSMOS', '宇宙', '9780345539434', ARRAY['卡尔·萨根'], 'Ballantine Books', 2013, '中文', '科普', ARRAY['天文学','宇宙','科学史'], '从行星、恒星到生命与文明，以富有想象力的方式讲述宇宙探索。'),
    ('BOOK-SEX-IN-SEA', '海洋中的爱与性', '9781476768878', ARRAY['Marah J. Hardt'], 'St. Martin''s Press', 2016, '中文', '科普', ARRAY['海洋生物','动物行为','生态'], '介绍海洋生物多样而奇特的繁殖策略及其生态意义。'),
    ('BOOK-OTHER-MINDS', '其他心灵', '9780374537197', ARRAY['Peter Godfrey-Smith'], 'Farrar, Straus and Giroux', 2017, '中文', '科普', ARRAY['章鱼','动物智能','海洋生命'], '结合潜水观察与认知科学，探索章鱼等头足类动物独特的心智演化。'),
    ('BOOK-BEAUTY-MATH', '数学之美', '9787115537973', ARRAY['吴军'], '人民邮电出版社', 2020, '中文', '科普', ARRAY['数学','信息技术','自然语言处理'], '用通俗案例解释搜索、通信和人工智能背后的数学方法。'),
    ('BOOK-THINKING-FAST-SLOW', '思考，快与慢', '9780374533557', ARRAY['丹尼尔·卡尼曼'], 'Farrar, Straus and Giroux', 2013, '中文', '心理学', ARRAY['认知偏差','决策','行为科学'], '通过快思考与慢思考两个系统解释判断、选择和认知偏差。'),
    ('BOOK-INFLUENCE', '影响力', '9780062937650', ARRAY['罗伯特·西奥迪尼'], 'Harper Business', 2021, '中文', '心理学', ARRAY['说服','社会心理','决策'], '分析互惠、承诺、社会认同等影响人们判断与行动的心理原则。'),
    ('BOOK-COURAGE-DISLIKED', '被讨厌的勇气', '9781501197277', ARRAY['岸见一郎','古贺史健'], 'Atria Books', 2018, '中文', '心理学', ARRAY['阿德勒心理学','成长','人际关系'], '以对话形式讨论课题分离、自我接纳以及获得自由与幸福的勇气。'),
    ('BOOK-FROG-THERAPY', '蛤蟆先生去看心理医生', '9787201161693', ARRAY['罗伯特·戴博德'], '天津人民出版社', 2020, '中文', '心理学', ARRAY['心理咨询','情绪','治愈'], '通过蛤蟆先生的咨询过程介绍自我状态、情绪觉察与心理成长。'),
    ('BOOK-FLOW', '心流', '9780061339202', ARRAY['米哈里·契克森米哈赖'], 'Harper Perennial', 2008, '中文', '心理学', ARRAY['专注','幸福','积极心理学'], '解释人在挑战与能力平衡时产生的全情投入体验及其生活价值。'),
    ('BOOK-CSAPP', '深入理解计算机系统', '9780134092669', ARRAY['Randal E. Bryant','David R. O''Hallaron'], 'Pearson', 2015, '中文', '计算机', ARRAY['计算机系统','操作系统','体系结构'], '从程序员视角贯通数据表示、汇编、处理器、存储、链接与并发。'),
    ('BOOK-CLRS', '算法导论', '9780262046305', ARRAY['Thomas H. Cormen','Charles E. Leiserson','Ronald L. Rivest','Clifford Stein'], 'MIT Press', 2022, '中文', '计算机', ARRAY['算法','数据结构','教材'], '系统讲解算法设计、正确性证明、复杂度分析及经典数据结构。'),
    ('BOOK-DESIGN-PATTERNS', '设计模式', '9780201633610', ARRAY['Erich Gamma','Richard Helm','Ralph Johnson','John Vlissides'], 'Addison-Wesley', 1994, '中文', '计算机', ARRAY['软件设计','面向对象','架构'], '总结可复用的面向对象设计模式及其适用场景、结构与协作方式。'),
    ('BOOK-REFACTORING', '重构：改善既有代码的设计', '9780134757599', ARRAY['Martin Fowler'], 'Addison-Wesley', 2018, '中文', '计算机', ARRAY['重构','软件工程','代码质量'], '通过小步、安全的代码变换改善既有软件的结构与可维护性。'),
    ('BOOK-SICP', '计算机程序的构造和解释', '9780262510875', ARRAY['Harold Abelson','Gerald Jay Sussman'], 'MIT Press', 1996, '中文', '计算机', ARRAY['编程语言','抽象','计算机科学'], '借助程序设计探索抽象、递归、解释器和计算模型等核心思想。'),
    ('BOOK-PYTHON-CRASH', 'Python编程：从入门到实践', '9781718502703', ARRAY['Eric Matthes'], 'No Starch Press', 2023, '中文', '计算机', ARRAY['Python','编程入门','项目实践'], '从基础语法逐步进入数据可视化、Web应用等完整项目实践。'),
    ('BOOK-DEEP-LEARNING', '深度学习', '9780262035613', ARRAY['Ian Goodfellow','Yoshua Bengio','Aaron Courville'], 'MIT Press', 2016, '中文', '计算机', ARRAY['深度学习','神经网络','机器学习'], '系统介绍深度神经网络的数学基础、优化方法、模型与研究方向。'),
    ('BOOK-AIMA', '人工智能：一种现代的方法', '9780134610993', ARRAY['Stuart Russell','Peter Norvig'], 'Pearson', 2020, '中文', '计算机', ARRAY['人工智能','机器学习','智能体','教材'], '从智能体出发全面介绍搜索、推理、学习、规划、感知与机器人技术。')
)
INSERT INTO book(code, name, payload, source)
SELECT code,
       name,
       jsonb_build_object(
           'isbn', isbn,
           'authors', to_jsonb(authors),
           'publisher', publisher,
           'edition', '馆藏版',
           'publishedYear', published_year,
           'language', language,
           'category', category,
           'tags', to_jsonb(tags),
           'summary', summary,
           'coverImage', 'https://covers.openlibrary.org/b/isbn/' || isbn || '-L.jpg?default=false'
       ),
       '智慧图书馆扩充数据'
FROM catalog
ON CONFLICT DO NOTHING;

INSERT INTO library_holding(code, name, parent_code, payload, source)
SELECT 'HOLD-' || substring(book.code from 6),
       book.name || '馆藏',
       book.code,
       jsonb_build_object(
           'callNumber', CASE book.payload->>'category'
               WHEN '计算机' THEN 'TP3/' || upper(right(md5(book.code), 4))
               WHEN '科普' THEN 'N4/' || upper(right(md5(book.code), 4))
               WHEN '历史' THEN 'K1/' || upper(right(md5(book.code), 4))
               WHEN '社会科学' THEN 'C0/' || upper(right(md5(book.code), 4))
               WHEN '心理学' THEN 'B8/' || upper(right(md5(book.code), 4))
               WHEN '科幻' THEN 'I247/' || upper(right(md5(book.code), 4))
               ELSE 'I5/' || upper(right(md5(book.code), 4))
           END,
           'location', CASE book.payload->>'category'
               WHEN '计算机' THEN '二层科技书架'
               WHEN '科普' THEN '二层科技书架'
               WHEN '历史' THEN '三层人文书架'
               WHEN '社会科学' THEN '三层人文书架'
               WHEN '心理学' THEN '三层人文书架'
               ELSE '一层文学书架'
           END,
           'totalCount', 2 + mod(abs(hashtext(book.code)), 4),
           'availableCount', 2 + mod(abs(hashtext(book.code)), 4),
           'availabilityStatus', 'AVAILABLE'
       ),
       '智慧图书馆扩充数据'
FROM book
WHERE book.source = '智慧图书馆扩充数据'
  AND book.deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1
      FROM library_holding holding
      WHERE holding.parent_code = book.code
        AND holding.deleted_at IS NULL
  );
