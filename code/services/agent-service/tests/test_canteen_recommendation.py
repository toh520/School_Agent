import asyncio
from types import SimpleNamespace
from uuid import UUID

from agent_service.agent_models import FoodCandidate, MealRecommendationRequest
from agent_service.agent_routes import (
    _safe_candidates,
    _validate_combinations,
    meal_recommendations,
)


def food(
    identifier: str,
    name: str,
    price: float,
    spice: str,
    ingredients: list[str],
    allergens: list[str],
    category: str = "MEAT",
) -> FoodCandidate:
    return FoodCandidate(
        id=UUID(identifier),
        name=name,
        price=price,
        category=category,
        mealRole="MAIN",
        tastes=[],
        ingredients=ingredients,
        allergens=allergens,
        spiceLevel=spice,
        energyLevel="UNKNOWN",
    )


def test_hard_filters_run_before_llm() -> None:
    safe = food(
        "00000000-0000-0000-0000-000000000001", "土豆牛肉", 15, "NONE", ["牛肉", "土豆"], []
    )
    spicy = food("00000000-0000-0000-0000-000000000002", "辣子鸡", 16, "HOT", ["鸡肉", "辣椒"], [])
    allergy = food(
        "00000000-0000-0000-0000-000000000003", "花生鸡丁", 14, "NONE", ["鸡肉", "花生"], ["花生"]
    )
    payload = MealRecommendationRequest(
        foods=[safe, spicy, allergy],
        allergens=["花生"],
        budget=20,
        spiceLevel="NONE",
        excludedIngredients=["香菜"],
    )

    assert _safe_candidates(payload) == [safe]


def test_model_output_is_repriced_and_invented_ids_are_rejected() -> None:
    candidate = food("00000000-0000-0000-0000-000000000001", "土豆牛肉", 15, "NONE", ["牛肉"], [])
    staple = food(
        "00000000-0000-0000-0000-000000000002",
        "米饭",
        2,
        "NONE",
        ["大米"],
        [],
        "STAPLE",
    )
    payload = MealRecommendationRequest(foods=[candidate, staple], budget=20)
    raw = {
        "combinations": [
            {
                "title": "可靠组合",
                "foodIds": [str(candidate.id), str(staple.id)],
                "reason": "符合预算",
            },
            {"title": "虚构组合", "foodIds": ["00000000-0000-0000-0000-000000000099"]},
        ]
    }

    result = _validate_combinations(raw, [candidate, staple], payload)

    assert len(result) == 1
    assert result[0].total_price == 17


def test_explicit_dish_count_is_verified_instead_of_trusting_model_tag() -> None:
    candidates = [
        food(
            f"00000000-0000-0000-0000-{index:012d}",
            f"餐品{index}",
            20,
            "NONE",
            ["测试食材"],
            [],
        )
        for index in range(1, 7)
    ]
    candidates.append(
        food(
            "00000000-0000-0000-0000-000000000010",
            "米饭",
            2,
            "NONE",
            ["大米"],
            [],
            "STAPLE",
        )
    )
    payload = MealRecommendationRequest(
        foods=candidates,
        budget=50,
        dinerCount=3,
        extraRequirements="来六个菜",
    )
    selected = [*candidates[:2], candidates[-1]]
    raw = {
        "combinations": [
            {
                "title": "预算内组合",
                "foodIds": [str(item.id) for item in selected],
                "reason": "尽量搭配",
                "matchedRequirements": ["三人用餐", "六个菜"],
                "limitations": [],
            }
        ]
    }

    result = _validate_combinations(raw, candidates, payload)

    assert len(result) == 1
    assert "六个菜" not in result[0].matched_requirements
    assert "预算内" in result[0].matched_requirements
    assert "适合3人用餐" in result[0].matched_requirements
    assert "预算不足" in result[0].limitations[0]
    assert "实际2个菜" in result[0].limitations[0]


def test_default_staple_and_selected_drink_quantities_follow_diner_count() -> None:
    staple = food("00000000-0000-0000-0000-000000000001", "米饭", 2, "NONE", ["大米"], [], "STAPLE")
    main = food("00000000-0000-0000-0000-000000000002", "牛肉", 12, "NONE", ["牛肉"], [])
    drink = food("00000000-0000-0000-0000-000000000003", "豆浆", 3, "NONE", ["黄豆"], [], "DRINK")
    payload = MealRecommendationRequest(foods=[staple, main, drink], budget=80, dinerCount=3)
    raw = {
        "combinations": [
            {
                "title": "三人套餐",
                "foodItems": [
                    {"foodId": str(staple.id), "quantity": 1},
                    {"foodId": str(main.id), "quantity": 1},
                    {"foodId": str(drink.id), "quantity": 1},
                ],
            }
        ]
    }

    result = _validate_combinations(raw, [staple, main, drink], payload)

    assert result[0].quantities[str(staple.id)] == 3
    assert result[0].quantities[str(drink.id)] == 3
    assert result[0].total_price == 27


def test_dish_count_excludes_staples_drinks_and_snacks() -> None:
    dishes = [
        food(
            f"00000000-0000-0000-0000-{index:012d}",
            f"菜{index}",
            6,
            "NONE",
            ["食材"],
            [],
            "MEAT" if index == 1 else "VEGETABLE",
        )
        for index in range(1, 3)
    ]
    staple = food("00000000-0000-0000-0000-000000000010", "米饭", 2, "NONE", ["大米"], [], "STAPLE")
    drink = food("00000000-0000-0000-0000-000000000011", "豆浆", 3, "NONE", ["黄豆"], [], "DRINK")
    payload = MealRecommendationRequest(
        foods=[*dishes, staple, drink], budget=30, extraRequirements="要两个菜"
    )
    raw = {
        "combinations": [
            {
                "foodItems": [
                    {"foodId": str(item.id), "quantity": 1} for item in [*dishes, staple, drink]
                ],
                "matchedRequirements": ["四个菜"],
            }
        ]
    }

    result = _validate_combinations(raw, [*dishes, staple, drink], payload)

    assert "包含2个菜" in result[0].matched_requirements
    assert "四个菜" not in result[0].matched_requirements


def test_no_rice_keeps_staple_requirement_and_uses_alternative() -> None:
    rice = food("00000000-0000-0000-0000-000000000001", "米饭", 2, "NONE", ["大米"], [], "STAPLE")
    bun = food("00000000-0000-0000-0000-000000000002", "馒头", 2, "NONE", ["小麦"], [], "STAPLE")
    dish = food("00000000-0000-0000-0000-000000000003", "青菜", 6, "NONE", ["青菜"], [])
    payload = MealRecommendationRequest(
        foods=[rice, bun, dish], budget=30, dinerCount=2, extraRequirements="不要米饭，要1个菜"
    )
    safe = _safe_candidates(payload)
    raw = {"combinations": [{"foodIds": [str(dish.id)]}]}

    result = _validate_combinations(raw, safe, payload)

    assert rice not in safe
    assert bun in safe
    assert str(bun.id) in result[0].quantities
    assert result[0].quantities[str(bun.id)] == 2
    assert "已排除米饭" in result[0].matched_requirements


def test_budget_limitation_is_recomputed_from_actual_minimum_cost() -> None:
    dishes = [
        food(
            f"00000000-0000-0000-0000-{index:012d}",
            f"菜{index}",
            5,
            "NONE",
            ["食材"],
            [],
        )
        for index in range(1, 9)
    ]
    staple = food("00000000-0000-0000-0000-000000000010", "米饭", 2, "NONE", ["大米"], [], "STAPLE")
    payload = MealRecommendationRequest(
        foods=[*dishes, staple], budget=100, extraRequirements="要八个菜"
    )
    raw = {
        "combinations": [
            {
                "foodIds": [str(dishes[0].id), str(dishes[1].id), str(staple.id)],
                "limitations": ["预算不足，无法组成八个菜"],
            }
        ]
    }

    result = _validate_combinations(raw, [*dishes, staple], payload)

    assert all("预算不足" not in item for item in result[0].limitations)
    assert "包含8个菜" in result[0].matched_requirements
    assert len(result[0].food_ids) == 9


def test_explicit_duck_snack_and_no_staple_are_enforced_and_verified() -> None:
    duck = food(
        "00000000-0000-0000-0000-000000000001",
        "盐水鸭",
        18,
        "NONE",
        ["鸭肉", "盐"],
        [],
    )
    snack = food(
        "00000000-0000-0000-0000-000000000002",
        "五香茶叶蛋",
        2,
        "NONE",
        ["鸡蛋", "茶叶"],
        [],
        "SNACK",
    )
    expensive_snack = food(
        "00000000-0000-0000-0000-000000000005",
        "酸奶水果杯",
        8,
        "NONE",
        ["酸奶", "水果"],
        [],
        "SNACK",
    )
    rice = food(
        "00000000-0000-0000-0000-000000000003",
        "五谷杂粮饭",
        3,
        "NONE",
        ["大米", "杂粮"],
        [],
        "STAPLE",
    )
    tofu = food(
        "00000000-0000-0000-0000-000000000004",
        "家常豆腐",
        7,
        "NONE",
        ["豆腐"],
        [],
        "VEGETABLE",
    )
    payload = MealRecommendationRequest(
        foods=[duck, snack, expensive_snack, rice, tofu],
        budget=25,
        extraRequirements="想吃鸭肉，再来个小吃，不要主食",
    )
    raw = {
        "combinations": [
            {
                "title": "错误的素食套餐",
                "foodIds": [str(rice.id), str(tofu.id), str(expensive_snack.id)],
                "matchedRequirements": ["无鸭肉", "无小吃", "主食共2份"],
                "reason": "模型错误说明",
            }
        ]
    }

    result = _validate_combinations(raw, [duck, snack, expensive_snack, rice, tofu], payload)

    assert len(result) == 1
    assert str(duck.id) in result[0].quantities
    assert str(snack.id) in result[0].quantities
    assert str(expensive_snack.id) not in result[0].quantities
    assert str(rice.id) not in result[0].quantities
    assert result[0].total_price <= 25
    assert "包含鸭肉" in result[0].matched_requirements
    assert "包含小吃" in result[0].matched_requirements
    assert "按要求不含主食" in result[0].matched_requirements
    assert all("无鸭肉" not in note for note in result[0].matched_requirements)
    assert result[0].title == "盐水鸭套餐"
    assert "模型错误说明" not in result[0].reason


def test_incorrect_model_title_is_replaced_with_a_name_from_the_final_foods() -> None:
    beef = food(
        "00000000-0000-0000-0000-000000000001",
        "土豆烧牛肉",
        16,
        "NONE",
        ["牛肉", "土豆"],
        [],
    )
    rice = food(
        "00000000-0000-0000-0000-000000000002",
        "香软米饭",
        2,
        "NONE",
        ["大米"],
        [],
        "STAPLE",
    )
    lamb = food(
        "00000000-0000-0000-0000-000000000003",
        "孜然羊肉",
        20,
        "MILD",
        ["羊肉", "孜然"],
        [],
    )
    payload = MealRecommendationRequest(foods=[beef, rice, lamb], budget=25)
    raw = {"combinations": [{"title": "羊肉风味套餐", "foodIds": [str(beef.id), str(rice.id)]}]}

    result = _validate_combinations(raw, [beef, rice], payload)

    assert result[0].title == "土豆烧牛肉套餐"
    assert "羊肉" not in result[0].title


def test_accurate_model_title_is_preserved() -> None:
    beef = food(
        "00000000-0000-0000-0000-000000000001",
        "土豆烧牛肉",
        16,
        "NONE",
        ["牛肉", "土豆"],
        [],
    )
    rice = food(
        "00000000-0000-0000-0000-000000000002",
        "香软米饭",
        2,
        "NONE",
        ["大米"],
        [],
        "STAPLE",
    )
    payload = MealRecommendationRequest(foods=[beef, rice], budget=25)
    raw = {"combinations": [{"title": "牛肉暖心套餐", "foodIds": [str(beef.id), str(rice.id)]}]}

    result = _validate_combinations(raw, [beef, rice], payload)

    assert result[0].title == "牛肉暖心套餐"


def test_creative_model_title_without_false_food_claims_is_preserved() -> None:
    beef = food(
        "00000000-0000-0000-0000-000000000001",
        "土豆烧牛肉",
        16,
        "NONE",
        ["牛肉", "土豆"],
        [],
    )
    rice = food(
        "00000000-0000-0000-0000-000000000002",
        "香软米饭",
        2,
        "NONE",
        ["大米"],
        [],
        "STAPLE",
    )
    payload = MealRecommendationRequest(foods=[beef, rice], budget=25)
    raw = {"combinations": [{"title": "校园暖心套餐", "foodIds": [str(beef.id), str(rice.id)]}]}

    result = _validate_combinations(raw, [beef, rice], payload)

    assert result[0].title == "校园暖心套餐"


def test_recommendation_endpoint_supplements_results_until_three_are_collected() -> None:
    meats = [
        food(
            f"00000000-0000-0000-0000-00000000000{index}",
            name,
            10,
            "NONE",
            [name],
            [],
        )
        for index, name in enumerate(["牛肉", "鸡肉", "鱼肉"], start=1)
    ]
    rice = food(
        "00000000-0000-0000-0000-000000000004",
        "香软米饭",
        2,
        "NONE",
        ["大米"],
        [],
        "STAPLE",
    )

    class SequenceModel:
        def __init__(self) -> None:
            self.calls = 0
            self.responses = [
                {
                    "combinations": [
                        {"title": "牛肉套餐", "foodIds": [str(meats[0].id), str(rice.id)]},
                        {"title": "鸡肉套餐", "foodIds": [str(meats[1].id), str(rice.id)]},
                    ]
                },
                {
                    "combinations": [
                        {"title": "重复套餐", "foodIds": [str(meats[0].id), str(rice.id)]},
                        {"title": "鱼肉套餐", "foodIds": [str(meats[2].id), str(rice.id)]},
                    ]
                },
            ]

        async def complete_json(self, system: str, user: str) -> dict:
            del system, user
            response = self.responses[self.calls]
            self.calls += 1
            return response

    model = SequenceModel()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(model=model)))
    payload = MealRecommendationRequest(foods=[*meats, rice], budget=20)

    response = asyncio.run(meal_recommendations(payload, request, None))

    assert response.data is not None
    assert len(response.data) == 3
    assert len({combination.key for combination in response.data}) == 3
    assert model.calls == 2


def test_soft_best_effort_wording_is_not_forced_as_a_hard_category() -> None:
    dish = food(
        "00000000-0000-0000-0000-000000000001", "清炒时蔬", 8, "NONE", ["青菜"], [], "VEGETABLE"
    )
    staple = food("00000000-0000-0000-0000-000000000002", "米饭", 2, "NONE", ["大米"], [], "STAPLE")
    soup = food("00000000-0000-0000-0000-000000000003", "菌菇汤", 6, "NONE", ["菌菇"], [], "SOUP")
    payload = MealRecommendationRequest(
        foods=[dish, staple, soup], budget=10, extraRequirements="最好有一份汤"
    )
    raw = {"combinations": [{"foodIds": [str(dish.id), str(staple.id)]}]}

    result = _validate_combinations(raw, [dish, staple, soup], payload)

    assert len(result) == 1
    assert str(soup.id) not in result[0].quantities


def test_all_safe_menu_rows_remain_available_to_the_model_layer() -> None:
    candidates = [
        food(
            f"00000000-0000-0000-0000-{index:012d}",
            f"测试餐品{index}",
            5,
            "NONE",
            [f"食材{index}"],
            [],
        )
        for index in range(1, 59)
    ]
    payload = MealRecommendationRequest(foods=candidates, budget=25)

    assert len(_safe_candidates(payload)) == 58


def test_explicit_two_staple_servings_override_one_person_default() -> None:
    rice = food(
        "00000000-0000-0000-0000-000000000001",
        "香软米饭",
        2,
        "NONE",
        ["大米"],
        [],
        "STAPLE",
    )
    dish = food(
        "00000000-0000-0000-0000-000000000002",
        "清炒时蔬",
        8,
        "NONE",
        ["青菜"],
        [],
        "VEGETABLE",
    )
    payload = MealRecommendationRequest(
        foods=[rice, dish], budget=20, dinerCount=1, extraRequirements="我要两份主食"
    )
    raw = {"combinations": [{"foodIds": [str(rice.id), str(dish.id)]}]}

    result = _validate_combinations(raw, [rice, dish], payload)

    assert result[0].quantities[str(rice.id)] == 2
    assert "主食共2份" in result[0].matched_requirements


def test_named_staples_override_default_and_support_synonym_coordination() -> None:
    rice = food(
        "00000000-0000-0000-0000-000000000001",
        "香软米饭",
        2,
        "NONE",
        ["大米"],
        [],
        "STAPLE",
    )
    sweet_potato = food(
        "00000000-0000-0000-0000-000000000002",
        "蒸红薯",
        3,
        "NONE",
        ["红薯"],
        [],
        "STAPLE",
    )
    dumpling = food(
        "00000000-0000-0000-0000-000000000003",
        "牛肉水饺",
        12,
        "NONE",
        ["牛肉", "小麦面粉"],
        [],
        "STAPLE",
    )
    payload = MealRecommendationRequest(
        foods=[rice, sweet_potato, dumpling],
        budget=27,
        dinerCount=1,
        extraRequirements="我要吃地瓜和水饺",
    )
    raw = {"combinations": [{"foodIds": [str(dumpling.id), str(rice.id)]}]}

    result = _validate_combinations(raw, [rice, sweet_potato, dumpling], payload)

    assert len(result) == 1
    assert str(sweet_potato.id) in result[0].quantities
    assert str(dumpling.id) in result[0].quantities
    assert str(rice.id) not in result[0].quantities
    assert result[0].quantities[str(sweet_potato.id)] == 1
    assert result[0].quantities[str(dumpling.id)] == 1
    assert "包含红薯" in result[0].matched_requirements
    assert "包含水饺" in result[0].matched_requirements
    assert "主食共2份" in result[0].matched_requirements


def test_named_noodle_replaces_the_default_staple() -> None:
    rice = food(
        "00000000-0000-0000-0000-000000000001",
        "香软米饭",
        2,
        "NONE",
        ["大米"],
        [],
        "STAPLE",
    )
    noodles = food(
        "00000000-0000-0000-0000-000000000002",
        "红烧牛肉面",
        13,
        "NONE",
        ["小麦", "牛肉", "青菜"],
        [],
        "STAPLE",
    )
    dish = food(
        "00000000-0000-0000-0000-000000000003",
        "清炒时蔬",
        8,
        "NONE",
        ["青菜"],
        [],
        "VEGETABLE",
    )
    payload = MealRecommendationRequest(
        foods=[rice, noodles, dish], budget=25, extraRequirements="我要吃面条"
    )
    raw = {"combinations": [{"foodIds": [str(rice.id), str(dish.id)]}]}

    result = _validate_combinations(raw, [rice, noodles, dish], payload)

    assert str(noodles.id) in result[0].quantities
    assert str(rice.id) not in result[0].quantities
    assert "包含面条" in result[0].matched_requirements


def test_natural_language_no_spice_is_a_hard_filter() -> None:
    plain = food("00000000-0000-0000-0000-000000000001", "白切鸡", 15, "NONE", ["鸡肉"], [])
    spicy = food("00000000-0000-0000-0000-000000000002", "辣子鸡", 15, "HOT", ["鸡肉", "辣椒"], [])
    payload = MealRecommendationRequest(
        foods=[plain, spicy], budget=30, extraRequirements="我一点都不能吃辣"
    )

    assert _safe_candidates(payload) == [plain]


def test_coordinated_exclusions_remove_every_named_ingredient() -> None:
    beef = food("00000000-0000-0000-0000-000000000001", "黑椒牛柳", 18, "NONE", ["牛肉"], [])
    chicken = food("00000000-0000-0000-0000-000000000002", "香菇滑鸡", 15, "NONE", ["鸡肉"], [])
    vegetable = food(
        "00000000-0000-0000-0000-000000000003", "清炒时蔬", 8, "NONE", ["青菜"], [], "VEGETABLE"
    )
    payload = MealRecommendationRequest(
        foods=[beef, chicken, vegetable], budget=30, extraRequirements="不要牛肉和鸡肉"
    )

    assert _safe_candidates(payload) == [vegetable]


def test_excluding_noodles_does_not_exclude_other_wheat_staples() -> None:
    noodles = food(
        "00000000-0000-0000-0000-000000000001",
        "红烧牛肉面",
        13,
        "NONE",
        ["小麦", "牛肉"],
        [],
        "STAPLE",
    )
    dumpling = food(
        "00000000-0000-0000-0000-000000000002",
        "牛肉水饺",
        12,
        "NONE",
        ["小麦面粉", "牛肉"],
        [],
        "STAPLE",
    )
    payload = MealRecommendationRequest(
        foods=[noodles, dumpling], budget=20, extraRequirements="不要面条"
    )

    assert _safe_candidates(payload) == [dumpling]


def test_specific_food_quantity_overrides_default_role_quantity() -> None:
    rice = food(
        "00000000-0000-0000-0000-000000000001", "香软米饭", 2, "NONE", ["大米"], [], "STAPLE"
    )
    bun = food(
        "00000000-0000-0000-0000-000000000002",
        "奶香馒头",
        1.5,
        "NONE",
        ["小麦面粉", "牛奶"],
        [],
        "STAPLE",
    )
    dish = food(
        "00000000-0000-0000-0000-000000000003", "清炒时蔬", 8, "NONE", ["青菜"], [], "VEGETABLE"
    )
    payload = MealRecommendationRequest(
        foods=[rice, bun, dish], budget=20, dinerCount=1, extraRequirements="我要两个馒头"
    )
    raw = {"combinations": [{"foodIds": [str(rice.id), str(dish.id)]}]}

    result = _validate_combinations(raw, [rice, bun, dish], payload)

    assert result[0].quantities[str(bun.id)] == 2
    assert str(rice.id) not in result[0].quantities
    assert "主食共2份" in result[0].matched_requirements
