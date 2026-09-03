-- Smart canteen demo: one shared menu, persistent cart, and immutable order snapshots.
CREATE TABLE canteen_cart_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    dish_id UUID NOT NULL REFERENCES dish(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, dish_id)
);

CREATE TABLE canteen_order (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(32) NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    status VARCHAR(16) NOT NULL DEFAULT 'PLACED' CHECK (status IN ('PLACED')),
    total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE canteen_order_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES canteen_order(id) ON DELETE CASCADE,
    dish_id UUID REFERENCES dish(id) ON DELETE SET NULL,
    dish_name VARCHAR(120) NOT NULL,
    image_url TEXT,
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);

CREATE INDEX idx_canteen_cart_user ON canteen_cart_item(user_id, updated_at DESC);
CREATE INDEX idx_canteen_order_user ON canteen_order(user_id, created_at DESC);

-- Replace the old hierarchy-based sample with a single-canteen menu used by the demo.
UPDATE dish
SET parent_code = NULL,
    name = '番茄炒蛋',
    payload = '{"price":10.00,"category":"VEGETABLE","description":"酸甜番茄与嫩炒鸡蛋，适合搭配主食。","imageUrl":"/foods/tomato-egg.svg","tastes":["酸甜","家常"],"ingredients":["番茄","鸡蛋"],"nutritionKcal":180,"allergens":["蛋类"],"spiceLevel":"NONE","availabilityStatus":"AVAILABLE","featured":"YES"}'::jsonb,
    source = '智能食堂演示菜单', updated_at = CURRENT_TIMESTAMP
WHERE code = 'DISH-TOMATO-EGG';

INSERT INTO dish(code, name, payload, source, created_by, updated_by)
VALUES
('FOOD-RICE', '香软米饭', '{"price":2.00,"category":"STAPLE","description":"当日蒸制的东北大米，口感松软。","imageUrl":"/foods/rice.svg","tastes":["清淡"],"ingredients":["大米"],"nutritionKcal":230,"allergens":[],"spiceLevel":"NONE","availabilityStatus":"AVAILABLE","featured":"NO"}', '智能食堂演示菜单', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001'),
('FOOD-CHICKEN', '宫保鸡丁', '{"price":14.00,"category":"MEAT","description":"鸡丁配黄瓜与花生快炒，咸鲜微辣。","imageUrl":"/foods/chicken.svg","tastes":["咸鲜","微辣"],"ingredients":["鸡肉","黄瓜","花生"],"nutritionKcal":360,"allergens":["花生"],"spiceLevel":"MILD","availabilityStatus":"AVAILABLE","featured":"YES"}', '智能食堂演示菜单', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001'),
('FOOD-BEEF', '土豆烧牛肉', '{"price":16.00,"category":"MEAT","description":"慢炖牛肉搭配软糯土豆，浓香下饭。","imageUrl":"/foods/beef.svg","tastes":["浓香","咸鲜"],"ingredients":["牛肉","土豆","胡萝卜"],"nutritionKcal":410,"allergens":[],"spiceLevel":"NONE","availabilityStatus":"AVAILABLE","featured":"YES"}', '智能食堂演示菜单', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001'),
('FOOD-GREENS', '蒜蓉时蔬', '{"price":7.00,"category":"VEGETABLE","description":"时令青菜大火快炒，保留清脆口感。","imageUrl":"/foods/greens.svg","tastes":["清淡","蒜香"],"ingredients":["时令青菜","蒜"],"nutritionKcal":95,"allergens":[],"spiceLevel":"NONE","availabilityStatus":"AVAILABLE","featured":"NO"}', '智能食堂演示菜单', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001'),
('FOOD-SOUP', '紫菜蛋花汤', '{"price":4.00,"category":"SOUP","description":"紫菜与蛋花现煮，清爽暖胃。","imageUrl":"/foods/soup.svg","tastes":["清淡","鲜香"],"ingredients":["紫菜","鸡蛋"],"nutritionKcal":75,"allergens":["蛋类"],"spiceLevel":"NONE","availabilityStatus":"AVAILABLE","featured":"NO"}', '智能食堂演示菜单', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001'),
('FOOD-NOODLES', '红烧牛肉面', '{"price":13.00,"category":"STAPLE","description":"筋道面条配红烧牛肉与青菜，一碗即一餐。","imageUrl":"/foods/noodles.svg","tastes":["浓香","微辣"],"ingredients":["小麦","牛肉","青菜"],"nutritionKcal":520,"allergens":["麸质"],"spiceLevel":"MILD","availabilityStatus":"AVAILABLE","featured":"YES"}', '智能食堂演示菜单', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001'),
('FOOD-YOGURT', '原味酸奶', '{"price":5.00,"category":"DRINK","description":"低温原味酸奶，适合作为餐后搭配。","imageUrl":"/foods/yogurt.svg","tastes":["酸甜"],"ingredients":["牛奶"],"nutritionKcal":120,"allergens":["奶类"],"spiceLevel":"NONE","availabilityStatus":"AVAILABLE","featured":"NO"}', '智能食堂演示菜单', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;
