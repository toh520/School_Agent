-- Replace misleading precise nutrition numbers with optional qualitative levels.
UPDATE dish
SET payload = payload
    - 'nutritionKcal'
    - 'nutritionProtein'
    - 'nutritionCarbs'
    - 'nutritionFat'
    || jsonb_build_object(
        'energyLevel', CASE code
            WHEN 'FOOD-GREENS' THEN 'LOW'
            WHEN 'FOOD-SOUP' THEN 'LOW'
            WHEN 'FOOD-NOODLES' THEN 'HIGH'
            ELSE 'MEDIUM'
        END,
        'proteinLevel', CASE code
            WHEN 'FOOD-CHICKEN' THEN 'HIGH'
            WHEN 'FOOD-BEEF' THEN 'HIGH'
            WHEN 'FOOD-NOODLES' THEN 'MEDIUM'
            ELSE 'LOW'
        END,
        'carbLevel', CASE code
            WHEN 'FOOD-RICE' THEN 'HIGH'
            WHEN 'FOOD-NOODLES' THEN 'HIGH'
            WHEN 'FOOD-BEEF' THEN 'MEDIUM'
            ELSE 'LOW'
        END,
        'oilLevel', CASE code
            WHEN 'FOOD-CHICKEN' THEN 'HIGH'
            WHEN 'FOOD-BEEF' THEN 'MEDIUM'
            WHEN 'FOOD-NOODLES' THEN 'MEDIUM'
            ELSE 'LOW'
        END
    )
WHERE deleted_at IS NULL;
