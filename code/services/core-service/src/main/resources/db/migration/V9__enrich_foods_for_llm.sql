-- Add consistent reasoning fields to the existing demo menu without changing table shape.
UPDATE dish
SET payload = payload || jsonb_build_object(
    'mealRole', CASE payload->>'category'
        WHEN 'STAPLE' THEN 'STAPLE'
        WHEN 'MEAT' THEN 'MAIN'
        WHEN 'VEGETABLE' THEN 'SIDE'
        WHEN 'SOUP' THEN 'SOUP_DRINK'
        WHEN 'DRINK' THEN 'SOUP_DRINK'
        ELSE 'EXTRA'
    END,
    'portionSize', 'STANDARD',
    'nutritionProtein', COALESCE((payload->>'nutritionProtein')::numeric, 0),
    'nutritionCarbs', COALESCE((payload->>'nutritionCarbs')::numeric, 0),
    'nutritionFat', COALESCE((payload->>'nutritionFat')::numeric, 0),
    'suitableTags', CASE payload->>'category'
        WHEN 'STAPLE' THEN '["饱腹"]'::jsonb
        WHEN 'MEAT' THEN '["高蛋白","饱腹"]'::jsonb
        WHEN 'VEGETABLE' THEN '["清淡","素食"]'::jsonb
        WHEN 'SOUP' THEN '["清淡","热食"]'::jsonb
        WHEN 'DRINK' THEN '["加餐"]'::jsonb
        ELSE '[]'::jsonb
    END
)
WHERE deleted_at IS NULL;

UPDATE dish SET payload = payload || '{"nutritionProtein":4.8,"nutritionCarbs":12.0,"nutritionFat":9.0}'::jsonb WHERE code = 'DISH-TOMATO-EGG';
UPDATE dish SET payload = payload || '{"nutritionProtein":4.0,"nutritionCarbs":50.0,"nutritionFat":0.5}'::jsonb WHERE code = 'FOOD-RICE';
UPDATE dish SET payload = payload || '{"nutritionProtein":25.0,"nutritionCarbs":18.0,"nutritionFat":19.0}'::jsonb WHERE code = 'FOOD-CHICKEN';
UPDATE dish SET payload = payload || '{"nutritionProtein":28.0,"nutritionCarbs":25.0,"nutritionFat":18.0}'::jsonb WHERE code = 'FOOD-BEEF';
UPDATE dish SET payload = payload || '{"nutritionProtein":3.0,"nutritionCarbs":9.0,"nutritionFat":5.0}'::jsonb WHERE code = 'FOOD-GREENS';
UPDATE dish SET payload = payload || '{"nutritionProtein":5.0,"nutritionCarbs":6.0,"nutritionFat":3.0}'::jsonb WHERE code = 'FOOD-SOUP';
UPDATE dish SET payload = payload || '{"nutritionProtein":24.0,"nutritionCarbs":68.0,"nutritionFat":17.0}'::jsonb WHERE code = 'FOOD-NOODLES';
UPDATE dish SET payload = payload || '{"nutritionProtein":5.0,"nutritionCarbs":15.0,"nutritionFat":4.0}'::jsonb WHERE code = 'FOOD-YOGURT';
