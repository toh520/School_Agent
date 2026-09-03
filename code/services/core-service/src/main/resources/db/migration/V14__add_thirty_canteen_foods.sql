-- Thirty additional menu records for broader recommendation and constraint testing.
WITH menu(code, name, price, category, meal_role, description, tastes, ingredients,
          energy_level, protein_level, carb_level, oil_level, allergens, spice_level,
          portion_size, suitable_tags, featured) AS (
    VALUES
    ('FOOD-MIXED-RICE', '五谷杂粮饭', 3.50, 'STAPLE', 'STAPLE', '大米、糙米与杂粮共同蒸制，谷香丰富。', ARRAY['清淡','谷香'], ARRAY['大米','糙米','燕麦'], 'MEDIUM','LOW','HIGH','LOW', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['粗粮','饱腹'], 'YES'),
    ('FOOD-BEEF-DUMPLING', '牛肉水饺', 12.00, 'STAPLE', 'STAPLE', '牛肉大葱馅水饺，现煮供应。', ARRAY['咸鲜','面香'], ARRAY['小麦面粉','牛肉','大葱'], 'HIGH','HIGH','HIGH','MEDIUM', ARRAY['麸质'], 'NONE','LARGE', ARRAY['饱腹','高蛋白'], 'YES'),
    ('FOOD-SCALLION-NOODLE', '葱油拌面', 8.00, 'STAPLE', 'STAPLE', '面条拌入葱油与酱汁，香气浓郁。', ARRAY['葱香','咸鲜'], ARRAY['小麦面粉','葱','酱油'], 'HIGH','LOW','HIGH','HIGH', ARRAY['麸质','大豆'], 'NONE','STANDARD', ARRAY['快捷','饱腹'], 'NO'),
    ('FOOD-SWEET-POTATO', '蒸红薯', 3.00, 'STAPLE', 'STAPLE', '整块红薯蒸熟，自然软糯香甜。', ARRAY['香甜','清淡'], ARRAY['红薯'], 'MEDIUM','LOW','HIGH','LOW', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['粗粮','素食','低脂'], 'NO'),
    ('FOOD-PORK-BUN', '鲜肉包', 3.00, 'STAPLE', 'STAPLE', '松软面皮包裹猪肉蔬菜馅。', ARRAY['咸鲜','面香'], ARRAY['小麦面粉','猪肉','卷心菜'], 'MEDIUM','MEDIUM','HIGH','MEDIUM', ARRAY['麸质'], 'NONE','SMALL', ARRAY['早餐','饱腹'], 'YES'),
    ('FOOD-YUXIANG-PORK', '鱼香肉丝', 13.00, 'MEAT', 'MAIN', '猪里脊配木耳与笋丝，酸甜微辣。', ARRAY['鱼香','酸甜','微辣'], ARRAY['猪肉','木耳','竹笋','辣椒'], 'MEDIUM','HIGH','MEDIUM','MEDIUM', ARRAY[]::text[], 'MILD','STANDARD', ARRAY['下饭','高蛋白'], 'YES'),
    ('FOOD-PEPPER-PORK', '青椒肉丝', 12.00, 'MEAT', 'MAIN', '猪肉丝与青椒大火快炒，鲜香爽口。', ARRAY['咸鲜','清香'], ARRAY['猪肉','青椒'], 'MEDIUM','HIGH','LOW','MEDIUM', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['高蛋白','下饭'], 'NO'),
    ('FOOD-COLA-WINGS', '可乐鸡翅', 16.00, 'MEAT', 'MAIN', '鸡翅以可乐和酱汁焖制，咸甜入味。', ARRAY['咸甜','酱香'], ARRAY['鸡翅','可乐','酱油'], 'HIGH','HIGH','MEDIUM','HIGH', ARRAY['大豆'], 'NONE','STANDARD', ARRAY['高蛋白','浓味'], 'YES'),
    ('FOOD-SALTED-DUCK', '盐水鸭', 18.00, 'MEAT', 'MAIN', '鸭肉盐卤后切片，皮香肉嫩。', ARRAY['咸鲜','卤香'], ARRAY['鸭肉','盐','香料'], 'HIGH','HIGH','LOW','HIGH', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['高蛋白','冷盘'], 'NO'),
    ('FOOD-BLACKPEPPER-BEEF', '黑椒牛柳', 19.00, 'MEAT', 'MAIN', '牛柳配洋葱和彩椒，以黑胡椒快炒。', ARRAY['黑椒','咸香'], ARRAY['牛肉','洋葱','彩椒','黑胡椒'], 'HIGH','HIGH','LOW','HIGH', ARRAY[]::text[], 'MILD','STANDARD', ARRAY['高蛋白','下饭'], 'YES'),
    ('FOOD-BOILED-PORK', '水煮肉片', 17.00, 'MEAT', 'MAIN', '猪肉片与蔬菜浸入麻辣汤汁。', ARRAY['麻辣','浓香'], ARRAY['猪肉','豆芽','辣椒','花椒'], 'HIGH','HIGH','LOW','HIGH', ARRAY[]::text[], 'HOT','LARGE', ARRAY['重口味','高蛋白'], 'YES'),
    ('FOOD-SHRIMP', '清炒虾仁', 20.00, 'MEAT', 'MAIN', '虾仁配黄瓜与胡萝卜清炒，鲜嫩少油。', ARRAY['鲜香','清淡'], ARRAY['虾仁','黄瓜','胡萝卜'], 'LOW','HIGH','LOW','LOW', ARRAY['甲壳类'], 'NONE','STANDARD', ARRAY['高蛋白','低脂','清淡'], 'YES'),
    ('FOOD-EGG-CUSTARD', '蒸鸡蛋羹', 7.00, 'MEAT', 'MAIN', '鸡蛋加水蒸制，细嫩易入口。', ARRAY['鲜香','清淡'], ARRAY['鸡蛋'], 'LOW','MEDIUM','LOW','LOW', ARRAY['蛋类'], 'NONE','SMALL', ARRAY['清淡','易消化'], 'NO'),
    ('FOOD-CUMIN-LAMB', '孜然羊肉', 21.00, 'MEAT', 'MAIN', '羊肉片与洋葱、孜然炒制，香气突出。', ARRAY['孜然','咸香'], ARRAY['羊肉','洋葱','孜然'], 'HIGH','HIGH','LOW','HIGH', ARRAY[]::text[], 'MILD','STANDARD', ARRAY['高蛋白','浓味'], 'YES'),
    ('FOOD-CABBAGE', '手撕包菜', 7.00, 'VEGETABLE', 'SIDE', '包菜手撕后快炒，爽脆微辣。', ARRAY['爽脆','微辣'], ARRAY['卷心菜','辣椒'], 'LOW','LOW','LOW','MEDIUM', ARRAY[]::text[], 'MILD','STANDARD', ARRAY['素食','下饭'], 'NO'),
    ('FOOD-LOTUS-ROOT', '清炒藕片', 8.00, 'VEGETABLE', 'SIDE', '莲藕薄片清炒，清脆爽口。', ARRAY['清淡','清脆'], ARRAY['莲藕','葱'], 'LOW','LOW','MEDIUM','LOW', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['素食','低脂'], 'NO'),
    ('FOOD-GREEN-BEAN', '干煸四季豆', 9.00, 'VEGETABLE', 'SIDE', '四季豆煸炒至入味，带有椒香。', ARRAY['咸香','椒香'], ARRAY['四季豆','辣椒'], 'MEDIUM','LOW','LOW','HIGH', ARRAY[]::text[], 'MEDIUM','STANDARD', ARRAY['素食','下饭'], 'YES'),
    ('FOOD-HOME-TOFU', '家常豆腐', 9.00, 'VEGETABLE', 'MAIN', '煎豆腐配木耳和彩椒烧制。', ARRAY['家常','咸鲜'], ARRAY['豆腐','木耳','彩椒'], 'MEDIUM','MEDIUM','LOW','MEDIUM', ARRAY['大豆'], 'NONE','STANDARD', ARRAY['素食','植物蛋白'], 'YES'),
    ('FOOD-POTATO-SLICE', '酸辣土豆丝', 7.00, 'VEGETABLE', 'SIDE', '土豆切丝快炒，酸辣爽脆。', ARRAY['酸辣','爽脆'], ARRAY['土豆','辣椒','香醋'], 'MEDIUM','LOW','HIGH','MEDIUM', ARRAY[]::text[], 'MEDIUM','STANDARD', ARRAY['素食','开胃'], 'YES'),
    ('FOOD-BABY-CABBAGE', '上汤娃娃菜', 10.00, 'VEGETABLE', 'SIDE', '娃娃菜以清鲜高汤煨制。', ARRAY['鲜香','清淡'], ARRAY['娃娃菜','高汤'], 'LOW','LOW','LOW','LOW', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['清淡','低热量'], 'NO'),
    ('FOOD-GARLIC-EGGPLANT', '蒜蓉茄子', 8.00, 'VEGETABLE', 'SIDE', '蒸茄子浇上蒜蓉调味汁。', ARRAY['蒜香','咸鲜'], ARRAY['茄子','蒜'], 'MEDIUM','LOW','LOW','MEDIUM', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['素食','下饭'], 'NO'),
    ('FOOD-LOTUS-STIRFRY', '荷塘小炒', 11.00, 'VEGETABLE', 'SIDE', '莲藕、荷兰豆、木耳与胡萝卜清炒。', ARRAY['清淡','清脆'], ARRAY['莲藕','荷兰豆','木耳','胡萝卜'], 'LOW','LOW','MEDIUM','LOW', ARRAY[]::text[], 'NONE','LARGE', ARRAY['素食','低脂','多样蔬菜'], 'YES'),
    ('FOOD-TOMATO-BEEF-SOUP', '番茄牛腩汤', 12.00, 'SOUP', 'SOUP_DRINK', '番茄与牛腩慢炖，汤汁酸香浓郁。', ARRAY['酸香','浓郁'], ARRAY['番茄','牛肉'], 'MEDIUM','HIGH','LOW','MEDIUM', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['热食','高蛋白'], 'YES'),
    ('FOOD-MUSHROOM-SOUP', '什锦菌菇汤', 6.00, 'SOUP', 'SOUP_DRINK', '多种菌菇清煮，突出自然鲜味。', ARRAY['鲜香','清淡'], ARRAY['香菇','白玉菇','金针菇'], 'LOW','LOW','LOW','LOW', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['素食','清淡','热食'], 'NO'),
    ('FOOD-MUNG-SOUP', '冰镇绿豆汤', 4.00, 'SOUP', 'SOUP_DRINK', '绿豆熬煮后冰镇，清甜解暑。', ARRAY['清甜','清爽'], ARRAY['绿豆','糖'], 'MEDIUM','LOW','MEDIUM','LOW', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['解暑','甜汤'], 'NO'),
    ('FOOD-MILK', '纯牛奶', 5.00, 'DRINK', 'SOUP_DRINK', '盒装纯牛奶，适合作为早餐或加餐搭配。', ARRAY['奶香'], ARRAY['牛奶'], 'MEDIUM','MEDIUM','LOW','MEDIUM', ARRAY['奶类'], 'NONE','STANDARD', ARRAY['早餐','蛋白质'], 'YES'),
    ('FOOD-ORANGE-JUICE', '鲜橙汁', 7.00, 'DRINK', 'SOUP_DRINK', '鲜橙榨汁，酸甜清爽。', ARRAY['酸甜','果香'], ARRAY['橙子'], 'MEDIUM','LOW','MEDIUM','LOW', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['果汁','清爽'], 'YES'),
    ('FOOD-OOLONG-TEA', '无糖乌龙茶', 4.00, 'DRINK', 'SOUP_DRINK', '乌龙茶冷泡，不额外加糖。', ARRAY['茶香','清爽'], ARRAY['乌龙茶','水'], 'LOW','LOW','LOW','LOW', ARRAY[]::text[], 'NONE','STANDARD', ARRAY['无糖','解腻'], 'NO'),
    ('FOOD-TEA-EGG', '五香茶叶蛋', 2.00, 'SNACK', 'EXTRA', '鸡蛋以茶叶和香料卤制。', ARRAY['卤香','咸鲜'], ARRAY['鸡蛋','茶叶','香料'], 'MEDIUM','MEDIUM','LOW','MEDIUM', ARRAY['蛋类'], 'NONE','SMALL', ARRAY['早餐','加餐'], 'YES'),
    ('FOOD-CORN-CAKE', '香煎玉米饼', 5.00, 'SNACK', 'EXTRA', '玉米面饼小火煎制，外香内软。', ARRAY['谷香','微甜'], ARRAY['玉米面','牛奶'], 'MEDIUM','LOW','HIGH','MEDIUM', ARRAY['奶类'], 'NONE','SMALL', ARRAY['粗粮','加餐'], 'NO')
)
INSERT INTO dish(code, name, payload, source, created_by, updated_by)
SELECT code, name,
       jsonb_build_object(
           'price', price, 'category', category, 'mealRole', meal_role,
           'description', description,
           'imageUrl', CASE category
               WHEN 'STAPLE' THEN '/foods/rice.svg'
               WHEN 'MEAT' THEN '/foods/beef.svg'
               WHEN 'VEGETABLE' THEN '/foods/greens.svg'
               WHEN 'SOUP' THEN '/foods/soup.svg'
               WHEN 'DRINK' THEN '/foods/yogurt.svg'
               ELSE '/foods/noodles.svg' END,
           'tastes', to_jsonb(tastes), 'ingredients', to_jsonb(ingredients),
           'energyLevel', energy_level, 'proteinLevel', protein_level,
           'carbLevel', carb_level, 'oilLevel', oil_level,
           'allergens', to_jsonb(allergens), 'spiceLevel', spice_level,
           'portionSize', portion_size, 'suitableTags', to_jsonb(suitable_tags),
           'availabilityStatus', 'AVAILABLE', 'featured', featured
       ),
       '智能食堂扩展测试菜单',
       '20000000-0000-0000-0000-000000000001',
       '20000000-0000-0000-0000-000000000001'
FROM menu
ON CONFLICT DO NOTHING;
