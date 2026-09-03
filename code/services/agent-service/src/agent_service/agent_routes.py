"""Authenticated HTTP and SSE routes for the M04 student conversation workspace."""

import json
import logging
import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from agent_service.agent_models import (
    ConversationCreate,
    FeedbackCreate,
    FoodCandidate,
    IdentityContext,
    LibraryRecommendationItem,
    LibraryRecommendationRequest,
    MealCombination,
    MealRecommendationRequest,
    MemoryCreate,
    MemoryUpdate,
    MessageCreate,
)
from agent_service.agent_repository import AgentRepository
from agent_service.agent_service import AgentOrchestrator
from agent_service.identity import CoreIdentityClient
from agent_service.library_recommendation import recommend_books
from agent_service.llm import OpenAICompatibleModel
from agent_service.middleware import request_id_context
from agent_service.schemas import ApiResponse
from agent_service.tools import ToolRegistry

router = APIRouter(prefix="/agent-api/v1", tags=["agent"])
LOGGER = logging.getLogger(__name__)
_TARGET_RECOMMENDATION_COUNT = 3
_MODEL_CANDIDATE_COUNT = 5
_MAX_SUPPLEMENTAL_ATTEMPTS = 2


async def identity(
    request: Request, authorization: Annotated[str | None, Header()] = None
) -> IdentityContext:
    client: CoreIdentityClient = request.app.state.identity_client
    return await client.resolve(authorization, request_id_context.get())


Actor = Annotated[IdentityContext, Depends(identity)]


@router.post("/library/recommendations")
async def library_recommendations(
    payload: LibraryRecommendationRequest, request: Request, actor: Actor
) -> ApiResponse[list[LibraryRecommendationItem]]:
    """Recommend real holdings first, using Open Library only when needed."""

    del actor
    model: OpenAICompatibleModel = request.app.state.model
    result = await recommend_books(payload, model)
    return ApiResponse.ok(result, request_id_context.get())


@router.post("/canteen/recommendations")
async def meal_recommendations(
    payload: MealRecommendationRequest, request: Request, actor: Actor
) -> ApiResponse[list[MealCombination]]:
    """Generate recommendations and reject or repair output that contradicts the user."""

    del actor
    safe_foods = _safe_candidates(payload)
    if not safe_foods:
        return ApiResponse.ok([], request_id_context.get())
    model: OpenAICompatibleModel = request.app.state.model
    system = (
        "你是智慧校园食堂的专业选餐助手。任务是从候选餐品中生成真实、可下单、安全、"
        "符合预算且搭配合理的套餐。只能引用candidateFoods中存在的food id，绝不编造、"
        "替换或修改餐品。请在内部完成比较和权衡，但不要输出思维过程。"
        "【约束优先级】第一优先级是安全与可用性：过敏原、忌口、排除食材、不辣要求和"
        "可用状态已经由程序预先过滤，绝不能尝试放宽或推荐被过滤餐品。第二优先级是总预算："
        "每套foodItems对应价格之和不得超过budget。第三优先级是用户明确要求，例如人数、"
        "明确餐品数量、rawUserRequirements中必须包含或不要包含的内容。第四优先级才是"
        "preferences中的口味、饮食目标、想吃食材和套餐规模等软偏好。约束冲突时按此顺序"
        "取舍，并在limitations中说明。"
        "【补充要求】rawUserRequirements是用户原始文字，不要因为它是自然语言就整体视为软偏好。"
        "其中‘不要、不吃、排除、不需要’是硬排除；‘要、来、加、包含、想吃、想喝’表达的具体"
        "食材、餐品或类别必须优先满足；‘最好、尽量、偏好、可以’才是软偏好。逐句检查其中每项"
        "要求，不能用‘无某食材’当作满足‘想吃某食材’的依据。"
        "用户同时列出多个餐品或食材（如‘红薯和水饺’）时必须全部包含；数量修饰词必须作用于"
        "对应对象，不能擅自套用到其他类别。"
        "【数量判断】结合dinerCount、budget、mealScale和extraRequirements自行判断合理的"
        "菜品数量，不设置固定数量。这里必须严格区分三类：STAPLE是主食，DRINK是饮品，"
        "只有MEAT、VEGETABLE、SOUP计入用户所说的‘几个菜’；SNACK是加餐，也不计入几个菜。"
        "例如用户要求8个菜，应选择8个互不相同的MEAT/VEGETABLE/SOUP，主食和饮品另算。"
        "单人避免无意义堆叠，多人应考虑可分享性和份量。补充说明明确要求菜品数量时，"
        "在预算与安全允许的情况下满足；无法满足时仍返回最佳可行组合，"
        "并准确写明目标数量、实际数量及预算不足或候选不足等原因。"
        "主食采用‘特殊要求覆盖默认’：明确不要主食时不得选择STAPLE；明确指定主食名称、种类"
        "或份数时严格按该要求选择和计数，不能再用默认值替换、截断或额外补其他主食；只有"
        "rawUserRequirements完全没有主食特殊说明时，才默认每人1份主食。‘不要米饭’只表示"
        "排除米饭，不表示不要主食，必须改选"
        "面食、馒头、玉米、粥等其他可用主食；其他单一主食的排除要求同理。"
        "饮品同样遵循特殊要求优先；没有饮品特殊说明时，是否需要饮品由你根据套餐、预算、"
        "人数和口味判断；"
        "如果选择DRINK餐品且用户没有明确饮品杯数，则所有饮品quantity总和必须等于"
        "dinerCount。共享菜可根据人数、份量和预算设置合理数量。单项quantity为1至20。"
        "【搭配原则】优先形成主食、主菜、配菜、汤饮之间结构合理的组合，避免全是主食、"
        "全是饮品、口味高度重复或主要食材重复。高蛋白目标优先选择proteinLevel为HIGH的"
        "餐品并兼顾蔬菜和主食；清淡或低热量目标优先LOW等级与清蒸、白灼等特征；多人丰富"
        "套餐应增加角色和口味多样性。想吃食材是优先项，但不能牺牲更高优先级约束。"
        "【营养信息】LOW、MEDIUM、HIGH只是定性等级。UNKNOWN时可结合名称、主要食材、介绍"
        "和一般食品常识进行谨慎的定性判断，但必须在limitations声明属于常识推测而非食堂"
        "实测；禁止编造千卡、克数、医学功效或精确营养结论。"
        "【多方案差异】尽量返回5套真正有差异的候选组合，供程序校验后选出3套。方案之间应在"
        "主菜、价格、口味或丰富度上有明显区别，不能只改标题或理由。只有确实不存在足够的"
        "安全、预算内可行搭配时才可以少于5套。"
        "【真实性】matchedRequirements只能写实际满足且能由输入和foodIds验证的内容；"
        "任何未满足、部分满足、不确定或依赖常识推测的内容必须写入limitations。"
        "【输出前自检】逐项核对：所有硬排除均未出现；所有明确指定的餐品、食材、类别和数量均"
        "已满足；主食和饮品默认值没有覆盖特殊说明；菜品数量不含主食、饮品、小吃；按quantity"
        "重算总价不超预算；每条matchedRequirements都有foodItems或输入字段作为证据。任一项"
        "不成立就先修正方案，不要输出自相矛盾的标签。"
        '返回JSON对象，结构为{"combinations":[{"title":字符串,"foodItems":'
        '[{"foodId":字符串,"quantity":整数}],'
        '"reason":字符串,"matchedRequirements":[字符串],"limitations":[字符串]}]}。'
        "返回最多5套互不相同的候选组合；title不超过12字，reason不超过80字，"
        "matchedRequirements最多6项，limitations最多3项，每项不超过40字。"
        "不输出思维过程或JSON以外内容。"
    )
    user = json.dumps(
        {
            "budget": payload.budget,
            "dinerCount": payload.diner_count,
            "explicitDishCount": _explicit_dish_count(payload.extra_requirements),
            "countingRules": {
                "dishCategories": ["MEAT", "VEGETABLE", "SOUP"],
                "excludedFromDishCount": ["STAPLE", "DRINK", "SNACK"],
            },
            "preferences": {
                "tastes": payload.tastes,
                "spiceLevel": payload.spice_level,
                "goals": payload.goals,
                "preferredIngredients": payload.preferred_ingredients,
                "mealScale": payload.meal_scale,
            },
            "rawUserRequirements": payload.extra_requirements,
            "excludedCombinations": payload.excluded_combinations,
            "candidateFoods": [food.model_dump(mode="json", by_alias=True) for food in safe_foods],
        },
        ensure_ascii=False,
    )
    raw = await model.complete_json(system, user)
    result = _validate_combinations(raw, safe_foods, payload)
    for _ in range(_MAX_SUPPLEMENTAL_ATTEMPTS):
        if len(result) >= _TARGET_RECOMMENDATION_COUNT:
            break
        accepted_keys = [combination.key for combination in result]
        retry_payload = payload.model_copy(
            update={
                "excluded_combinations": [
                    *payload.excluded_combinations,
                    *accepted_keys,
                ]
            }
        )
        retry_user = json.dumps(
            {
                "originalRequest": json.loads(user),
                "missingCombinationCount": _TARGET_RECOMMENDATION_COUNT - len(result),
                "alreadyAcceptedCombinations": [
                    {
                        "foodIds": [str(food_id) for food_id in combination.food_ids],
                        "totalPrice": combination.total_price,
                    }
                    for combination in result
                ],
                "validationFeedback": (
                    "当前通过校验的方案不足3套。请生成与alreadyAcceptedCombinations不同的新候选；"
                    "逐项满足rawUserRequirements，并在加入默认主食和所有quantity后重新计算总价，"
                    "确保每套不超过budget。特别检查必须包含或排除的餐品、类别和食材。"
                ),
            },
            ensure_ascii=False,
        )
        raw = await model.complete_json(system, retry_user)
        supplements = _validate_combinations(raw, safe_foods, retry_payload)
        result.extend(supplements[: _TARGET_RECOMMENDATION_COUNT - len(result)])
    return ApiResponse.ok(result[:_TARGET_RECOMMENDATION_COUNT], request_id_context.get())


def _safe_candidates(payload: MealRecommendationRequest) -> list[FoodCandidate]:
    """Apply user-controlled hard constraints before any menu data reaches the model."""

    blocked_allergens = {item.strip().lower() for item in payload.allergens}
    blocked_terms = {
        item.strip().lower()
        for item in [*payload.avoidances, *payload.excluded_ingredients]
        if item.strip()
    }
    natural_blocked_terms = _excluded_food_terms(payload, payload.foods)
    rejects_spice = payload.spice_level == "NONE" or _requests_no_spice(payload.extra_requirements)
    result = []
    for food in payload.foods:
        searchable = {food.name.lower(), *(item.lower() for item in food.ingredients)}
        if blocked_allergens.intersection(item.lower() for item in food.allergens):
            continue
        if any(term in text or text in term for term in blocked_terms for text in searchable):
            continue
        if any(_food_matches_term(food, term) for term in natural_blocked_terms):
            continue
        if _excluded_by_extra_requirement(food, payload.extra_requirements):
            continue
        if rejects_spice and food.spice_level != "NONE":
            continue
        if food.price <= payload.budget:
            result.append(food)
    return result


def _validate_combinations(
    raw: dict, safe_foods: list[FoodCandidate], payload: MealRecommendationRequest
) -> list[MealCombination]:
    """Reject invented, repeated, unsafe, or over-budget model output and recompute totals."""

    available = {str(food.id): food for food in safe_foods}
    seen = set(payload.excluded_combinations)
    result: list[MealCombination] = []
    for candidate in raw.get("combinations", [])[:_MODEL_CANDIDATE_COUNT]:
        if not isinstance(candidate, dict):
            continue
        raw_items = candidate.get("foodItems", [])
        if not isinstance(raw_items, list):
            LOGGER.warning("Rejected meal combination: foodItems is not a list")
            continue
        if not raw_items and isinstance(candidate.get("foodIds"), list):
            raw_items = [{"foodId": value, "quantity": 1} for value in candidate.get("foodIds", [])]
        requested_quantities: dict[str, int] = {}
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            food_id = str(item.get("foodId", ""))
            try:
                quantity = int(item.get("quantity", 1))
            except (TypeError, ValueError):
                continue
            if food_id and 1 <= quantity <= 20:
                requested_quantities[food_id] = quantity
        food_ids = list(requested_quantities)
        if not food_ids or any(value not in available for value in food_ids):
            LOGGER.warning("Rejected meal combination: missing or unknown food id")
            continue
        foods = [available[value] for value in food_ids]
        normalized = _normalize_default_servings(foods, requested_quantities, safe_foods, payload)
        if normalized is None:
            LOGGER.warning("Rejected meal combination: no eligible staple is available")
            continue
        foods, quantities = normalized
        requested_count = _explicit_dish_count(payload.extra_requirements)
        foods, quantities = _normalize_requested_dish_count(
            foods, quantities, safe_foods, payload, requested_count
        )
        enforced = _enforce_explicit_requirements(foods, quantities, safe_foods, payload)
        if enforced is None:
            LOGGER.warning("Rejected meal combination: explicit user requirements are infeasible")
            continue
        foods, quantities = enforced
        repaired = False
        if _combination_total(foods, quantities) > payload.budget:
            repaired_result = _repair_to_budget(
                foods, quantities, safe_foods, payload, requested_count
            )
            if repaired_result is None:
                LOGGER.warning(
                    "Rejected meal combination: no feasible budget repair budget=%.2f",
                    payload.budget,
                )
                continue
            foods, quantities = repaired_result
            repaired = True
        if not _explicit_requirements_satisfied(foods, quantities, payload, safe_foods):
            LOGGER.warning(
                "Rejected meal combination: explicit user requirements are not satisfied"
            )
            continue
        food_ids = [str(food.id) for food in foods]
        key = ":".join(sorted(food_ids))
        total = _combination_total(foods, quantities)
        if key in seen or total > payload.budget:
            LOGGER.warning(
                "Rejected meal combination: duplicate=%s total=%.2f budget=%.2f items=%d",
                key in seen,
                total,
                payload.budget,
                len(foods),
            )
            continue
        seen.add(key)
        matched_requirements, limitations = _verified_notes(candidate, foods, quantities, payload)
        if repaired:
            limitations.append("模型原方案超出预算，已替换为预算内可行搭配")
        dish_count = _dish_count(foods)
        if requested_count is not None and dish_count < requested_count:
            feasibility = _dish_count_feasibility(safe_foods, payload, requested_count)
            cause = {
                "CANDIDATES": "符合限制的可选菜品不足",
                "BUDGET": "预算不足",
                "MODEL": "本方案未完全满足数量要求",
            }[feasibility]
            limitations.append(f"{cause}，实际{dish_count}个菜，目标{requested_count}个菜")
        result.append(
            MealCombination(
                key=key,
                title=_validated_title(candidate.get("title"), foods, payload.foods),
                food_ids=[food.id for food in foods],
                quantities=quantities,
                total_price=total,
                reason=_verified_reason(foods),
                matched_requirements=matched_requirements,
                limitations=limitations[:8],
            )
        )
        if len(result) >= _TARGET_RECOMMENDATION_COUNT:
            break
    return result


def _normalize_default_servings(
    foods: list[FoodCandidate],
    quantities: dict[str, int],
    safe_foods: list[FoodCandidate],
    payload: MealRecommendationRequest,
) -> tuple[list[FoodCandidate], dict[str, int]] | None:
    """Enforce per-person staple and optional drink servings unless explicitly overridden."""

    selected = list(foods)
    result = dict(quantities)
    requirements = payload.extra_requirements
    requested_staples = _required_terms_for_category(payload, safe_foods, "STAPLE")
    if _waives_staple(requirements):
        selected, result = _remove_category(selected, result, "STAPLE")
    elif requested_staples:
        selected, result = _keep_requested_category_items(
            selected, result, "STAPLE", requested_staples
        )
    else:
        target = _explicit_role_quantity(requirements, "staple") or payload.diner_count
        staples = [food for food in selected if food.category == "STAPLE"]
        if not staples:
            alternatives = [food for food in safe_foods if food.category == "STAPLE"]
            if not alternatives:
                return None
            staple = min(alternatives, key=lambda food: food.price)
            selected.append(staple)
            result[str(staple.id)] = target
            staples = [staple]
        selected, result = _set_role_total(selected, result, staples, target)
    requested_drinks = _required_terms_for_category(payload, safe_foods, "DRINK")
    if _waives_drink(requirements):
        selected, result = _remove_category(selected, result, "DRINK")
    elif requested_drinks:
        selected, result = _keep_requested_category_items(
            selected, result, "DRINK", requested_drinks
        )
    else:
        drinks = [food for food in selected if food.category == "DRINK"]
        if drinks:
            target = _explicit_role_quantity(requirements, "drink") or payload.diner_count
            selected, result = _set_role_total(selected, result, drinks, target)
    return selected, result


def _keep_requested_category_items(
    foods: list[FoodCandidate],
    quantities: dict[str, int],
    category: str,
    requested_terms: list[str],
) -> tuple[list[FoodCandidate], dict[str, int]]:
    """Suppress default role choices once the user names concrete alternatives."""

    removed = {
        str(food.id)
        for food in foods
        if food.category == category
        and not any(_food_matches_term(food, term) for term in requested_terms)
    }
    return (
        [food for food in foods if str(food.id) not in removed],
        {food_id: quantity for food_id, quantity in quantities.items() if food_id not in removed},
    )


def _remove_category(
    foods: list[FoodCandidate], quantities: dict[str, int], category: str
) -> tuple[list[FoodCandidate], dict[str, int]]:
    """Remove a category explicitly waived by the user, including model-selected items."""

    removed = {str(food.id) for food in foods if food.category == category}
    return (
        [food for food in foods if str(food.id) not in removed],
        {food_id: quantity for food_id, quantity in quantities.items() if food_id not in removed},
    )


def _enforce_explicit_requirements(
    foods: list[FoodCandidate],
    quantities: dict[str, int],
    safe_foods: list[FoodCandidate],
    payload: MealRecommendationRequest,
) -> tuple[list[FoodCandidate], dict[str, int]] | None:
    """Add explicitly requested foods/categories and remove optional items to stay in budget."""

    required_terms = _required_food_terms(payload, safe_foods)
    required_categories = _required_categories(payload.extra_requirements)
    if not required_terms and not required_categories:
        return foods, quantities

    selected = list(foods)
    result = dict(quantities)
    selected_ids = {str(food.id) for food in selected}

    for term in required_terms:
        if any(_food_matches_term(food, term) for food in selected):
            continue
        alternatives = sorted(
            (food for food in safe_foods if _food_matches_term(food, term)),
            key=lambda food: food.price,
        )
        if not alternatives:
            return None
        choice = alternatives[0]
        if str(choice.id) not in selected_ids:
            selected.append(choice)
            selected_ids.add(str(choice.id))
            result[str(choice.id)] = 1

    for category in required_categories:
        if any(food.category == category for food in selected):
            continue
        alternatives = sorted(
            (food for food in safe_foods if food.category == category), key=lambda food: food.price
        )
        if not alternatives:
            return None
        choice = alternatives[0]
        if str(choice.id) not in selected_ids:
            selected.append(choice)
            selected_ids.add(str(choice.id))
            result[str(choice.id)] = 1

    for term in required_terms:
        target = _explicit_food_quantity(payload.extra_requirements, term)
        matches = sorted(
            (food for food in selected if _food_matches_term(food, term)),
            key=lambda food: food.price,
        )
        if target is not None and matches:
            result[str(matches[0].id)] = target
    for category in required_categories:
        target = _explicit_category_quantity(payload.extra_requirements, category)
        role_foods = [food for food in selected if food.category == category]
        if target is not None and role_foods and len(role_foods) <= target:
            selected, result = _set_role_total(selected, result, role_foods, target)

    protected_ids: set[str] = set()
    for term in required_terms:
        matches = sorted(
            (food for food in selected if _food_matches_term(food, term)),
            key=lambda food: food.price,
        )
        if matches:
            protected_ids.add(str(matches[0].id))
    for category in required_categories:
        matches = sorted(
            (food for food in selected if food.category == category), key=lambda food: food.price
        )
        if matches:
            protected_ids.add(str(matches[0].id))
    if not _waives_staple(payload.extra_requirements):
        protected_ids.update(str(food.id) for food in selected if food.category == "STAPLE")
    requested_count = _explicit_dish_count(payload.extra_requirements)
    if requested_count is not None:
        removable_dishes = sorted(
            (
                food
                for food in selected
                if food.category in _DISH_CATEGORIES and str(food.id) not in protected_ids
            ),
            key=lambda food: food.price,
            reverse=True,
        )
        while _dish_count(selected) > requested_count and removable_dishes:
            removed = removable_dishes.pop(0)
            selected = [food for food in selected if food.id != removed.id]
            result.pop(str(removed.id), None)
    optional = sorted(
        (food for food in selected if str(food.id) not in protected_ids),
        key=lambda food: food.price * result[str(food.id)],
        reverse=True,
    )
    while _combination_total(selected, result) > payload.budget and optional:
        removed = optional.pop(0)
        selected = [food for food in selected if food.id != removed.id]
        result.pop(str(removed.id), None)
    if not selected or _combination_total(selected, result) > payload.budget:
        minimum = _minimum_explicit_combination(
            safe_foods, payload, required_terms, required_categories
        )
        if minimum is None:
            return None
        selected, result = minimum
    return selected, result


def _minimum_explicit_combination(
    safe_foods: list[FoodCandidate],
    payload: MealRecommendationRequest,
    required_terms: list[str],
    required_categories: set[str],
) -> tuple[list[FoodCandidate], dict[str, int]] | None:
    """Build the cheapest valid fallback when a model chose expensive requirement variants."""

    selected: list[FoodCandidate] = []
    quantities: dict[str, int] = {}

    def add(food: FoodCandidate, quantity: int = 1) -> None:
        if str(food.id) not in quantities:
            selected.append(food)
            quantities[str(food.id)] = quantity

    for term in required_terms:
        if any(_food_matches_term(food, term) for food in selected):
            continue
        alternatives = sorted(
            (food for food in safe_foods if _food_matches_term(food, term)),
            key=lambda food: food.price,
        )
        if not alternatives:
            return None
        add(alternatives[0], _explicit_food_quantity(payload.extra_requirements, term) or 1)
    for category in required_categories:
        if any(food.category == category for food in selected):
            continue
        alternatives = sorted(
            (food for food in safe_foods if food.category == category), key=lambda food: food.price
        )
        if not alternatives:
            return None
        quantity = _explicit_category_quantity(payload.extra_requirements, category) or 1
        if category in {"STAPLE", "DRINK"} and quantity == 1:
            quantity = payload.diner_count
        add(alternatives[0], quantity)
    if not _waives_staple(payload.extra_requirements) and not any(
        food.category == "STAPLE" for food in selected
    ):
        staples = sorted(
            (food for food in safe_foods if food.category == "STAPLE"), key=lambda food: food.price
        )
        if not staples:
            return None
        servings = (
            _explicit_role_quantity(payload.extra_requirements, "staple") or payload.diner_count
        )
        add(staples[0], servings)
    requested_count = _explicit_dish_count(payload.extra_requirements)
    if requested_count is not None:
        alternatives = sorted(
            (
                food
                for food in safe_foods
                if food.category in _DISH_CATEGORIES and str(food.id) not in quantities
            ),
            key=lambda food: food.price,
        )
        while _dish_count(selected) < requested_count and alternatives:
            add(alternatives.pop(0))
        if _dish_count(selected) < requested_count:
            return None
    if not selected or _combination_total(selected, quantities) > payload.budget:
        return None
    return selected, quantities


def _explicit_requirements_satisfied(
    foods: list[FoodCandidate],
    quantities: dict[str, int],
    payload: MealRecommendationRequest,
    safe_foods: list[FoodCandidate],
) -> bool:
    """Final gate for requirements that can be proven from menu data."""

    if _waives_staple(payload.extra_requirements) and any(
        food.category == "STAPLE" for food in foods
    ):
        return False
    if _waives_drink(payload.extra_requirements) and any(
        food.category == "DRINK" for food in foods
    ):
        return False
    if any(
        not any(_food_matches_term(food, term) for food in foods)
        for term in _required_food_terms(payload, safe_foods)
    ):
        return False
    if not all(
        any(food.category == category for food in foods)
        for category in _required_categories(payload.extra_requirements)
    ):
        return False
    for term in _required_food_terms(payload, safe_foods):
        target = _explicit_food_quantity(payload.extra_requirements, term)
        actual = sum(quantities[str(food.id)] for food in foods if _food_matches_term(food, term))
        if target is not None and actual != target:
            return False
    for category in _required_categories(payload.extra_requirements):
        target = _explicit_category_quantity(payload.extra_requirements, category)
        actual = sum(quantities[str(food.id)] for food in foods if food.category == category)
        if target is not None and actual != target:
            return False
    return True


def _normalize_requested_dish_count(
    foods: list[FoodCandidate],
    quantities: dict[str, int],
    safe_foods: list[FoodCandidate],
    payload: MealRecommendationRequest,
    target: int | None,
) -> tuple[list[FoodCandidate], dict[str, int]]:
    """Treat an explicit dish count as distinct dishes, with one portion of each by default."""

    if target is None or _dish_count_feasibility(safe_foods, payload, target) != "MODEL":
        return foods, quantities
    dishes = [food for food in foods if food.category in _DISH_CATEGORIES][:target]
    selected_ids = {str(food.id) for food in dishes}
    alternatives = sorted(
        (
            food
            for food in safe_foods
            if food.category in _DISH_CATEGORIES and str(food.id) not in selected_ids
        ),
        key=lambda food: food.price,
    )
    dishes.extend(alternatives[: max(0, target - len(dishes))])
    kept_dish_ids = {str(food.id) for food in dishes}
    others = [food for food in foods if food.category not in _DISH_CATEGORIES]
    normalized_foods = [*dishes, *others]
    normalized_quantities = {
        str(food.id): (1 if str(food.id) in kept_dish_ids else quantities[str(food.id)])
        for food in normalized_foods
    }
    return normalized_foods, normalized_quantities


def _combination_total(foods: list[FoodCandidate], quantities: dict[str, int]) -> float:
    return round(sum(food.price * quantities[str(food.id)] for food in foods), 2)


def _repair_to_budget(
    foods: list[FoodCandidate],
    quantities: dict[str, int],
    safe_foods: list[FoodCandidate],
    payload: MealRecommendationRequest,
    requested_count: int | None,
) -> tuple[list[FoodCandidate], dict[str, int]] | None:
    """Repair model arithmetic while preserving explicit dish and staple requirements."""

    if requested_count is None:
        return None
    dishes = sorted(
        (food for food in safe_foods if food.category in _DISH_CATEGORIES),
        key=lambda food: food.price,
    )[:requested_count]
    if len(dishes) < requested_count:
        return None
    repaired_foods = list(dishes)
    repaired_quantities = {str(food.id): 1 for food in dishes}
    if not _waives_staple(payload.extra_requirements):
        staples = [food for food in safe_foods if food.category == "STAPLE"]
        if not staples:
            return None
        staple = min(staples, key=lambda food: food.price)
        servings = (
            _explicit_role_quantity(payload.extra_requirements, "staple") or payload.diner_count
        )
        repaired_foods.append(staple)
        repaired_quantities[str(staple.id)] = servings
    if _combination_total(repaired_foods, repaired_quantities) > payload.budget:
        return None
    return repaired_foods, repaired_quantities


def _set_role_total(
    foods: list[FoodCandidate],
    quantities: dict[str, int],
    role_foods: list[FoodCandidate],
    target: int,
) -> tuple[list[FoodCandidate], dict[str, int]]:
    """Distribute a serving total across selected alternatives without exceeding target."""

    kept = role_foods[:target]
    removed_ids = {str(food.id) for food in role_foods[target:]}
    foods = [food for food in foods if str(food.id) not in removed_ids]
    for food_id in removed_ids:
        quantities.pop(food_id, None)
    for food in kept:
        quantities[str(food.id)] = 1
    if kept:
        quantities[str(kept[0].id)] += target - len(kept)
    return foods, quantities


def _waives_staple(requirements: str) -> bool:
    compact = re.sub(r"\s+", "", requirements)
    return bool(re.search(r"(?:不要|不吃|无需|不需要|不想要|免)(?:任何)?主食", compact))


def _waives_drink(requirements: str) -> bool:
    compact = re.sub(r"\s+", "", requirements)
    return bool(re.search(r"(?:不要|不喝|无需|不需要|不想要)(?:任何)?(?:饮品|饮料)", compact))


def _explicit_role_quantity(requirements: str, role: str) -> int | None:
    terms = r"主食|米饭|面食|馒头|粥|玉米" if role == "staple" else r"饮品|饮料|豆浆|奶茶|水"
    number = r"([1-9]|1\d|20|[一二两三四五六七八九十])"
    unit = r"份" if role == "staple" else r"杯"
    match = re.search(rf"(?:{terms})\s*(?:要|共|来)?\s*{number}\s*{unit}", requirements)
    if match is None:
        match = re.search(rf"{number}\s*{unit}\s*(?:{terms})", requirements)
    if match is None:
        return None
    raw = match.group(1)
    return int(raw) if raw.isdigit() else _CHINESE_NUMBERS.get(raw)


def _explicit_food_quantity(requirements: str, term: str) -> int | None:
    aliases = [term, *(alias for alias, canonical in _FOOD_ALIASES.items() if canonical == term)]
    return _explicit_quantity_for_terms(requirements, aliases)


def _explicit_category_quantity(requirements: str, category: str) -> int | None:
    if category == "STAPLE":
        return _explicit_role_quantity(requirements, "staple")
    if category == "DRINK":
        return _explicit_role_quantity(requirements, "drink")
    return _explicit_quantity_for_terms(requirements, list(_CATEGORY_REQUIREMENTS[category]))


def _explicit_quantity_for_terms(requirements: str, terms: list[str]) -> int | None:
    joined = "|".join(re.escape(term) for term in terms)
    number = r"([1-9]|1\d|20|[一二两三四五六七八九十])"
    unit = r"份|个|碗|杯|盘"
    compact = re.sub(r"\s+", "", requirements)
    match = re.search(rf"(?:{joined})(?:要|来|共|各)?{number}(?:{unit})", compact)
    if match is None:
        match = re.search(rf"{number}(?:{unit})(?:的)?(?:{joined})", compact)
    if match is None:
        return None
    raw = match.group(1)
    return int(raw) if raw.isdigit() else _CHINESE_NUMBERS.get(raw)


_DISH_CATEGORIES = {"MEAT", "VEGETABLE", "SOUP"}
_GENERIC_FOOD_TERMS = {"食材", "香料", "调料", "盐", "糖", "油", "水", "菜"}
_CATEGORY_REQUIREMENTS = {
    "SNACK": ("小吃", "点心", "零食", "加餐"),
    "SOUP": ("汤品", "汤"),
    "DRINK": ("饮品", "饮料"),
    "STAPLE": ("主食",),
    "MEAT": ("荤菜", "肉菜"),
    "VEGETABLE": ("素菜", "蔬菜"),
}
_NEGATIVE_CUES = r"不要|不吃|不喝|不想吃|不想喝|排除|去掉|别放|无需|不需要|免"
_POSITIVE_CUES = (
    r"(?<!不)想吃|(?<!不)想喝|(?<!不)需要|(?<!不)(?<!需)要|来|加|配|包含|"
    r"必须有|一定要|希望有|给我|再来"
)
_FOOD_ALIASES = {
    "地瓜": "红薯",
    "红薯": "红薯",
    "水饺": "水饺",
    "饺子": "水饺",
    "面条": "面条",
    "米饭": "米饭",
    "白米饭": "米饭",
    "馒头": "馒头",
    "包子": "鲜肉包",
}


def _dish_count(foods: list[FoodCandidate]) -> int:
    """Count shared dishes without treating staples, drinks, or snacks as dishes."""

    return sum(food.category in _DISH_CATEGORIES for food in foods)


def _food_matches_term(food: FoodCandidate, term: str) -> bool:
    normalized = term.strip().lower()
    if normalized == "面条":
        return food.category == "STAPLE" and (
            "面" in food.name or any("面条" in value for value in food.ingredients)
        )
    if normalized == "米饭":
        return food.category == "STAPLE" and (
            "饭" in food.name or any(value == "大米" for value in food.ingredients)
        )
    return bool(normalized) and any(
        normalized in value.lower() or value.lower() in normalized
        for value in [food.name, *food.ingredients]
        if len(value.strip()) >= 2
    )


def _term_is_negated(requirements: str, term: str) -> bool:
    normalized = re.sub(r"\s+", "", requirements).lower()
    for clause in re.split(r"[，。；,;]", normalized):
        position = clause.find(term.lower())
        if position < 0:
            continue
        prefix = clause[:position]
        negative = [match.start() for match in re.finditer(_NEGATIVE_CUES, prefix)]
        positive = [match.start() for match in re.finditer(_POSITIVE_CUES, prefix)]
        if negative and (not positive or negative[-1] > positive[-1]):
            return True
    return False


def _term_is_explicitly_requested(requirements: str, term: str) -> bool:
    normalized = re.sub(r"\s+", "", requirements).lower()
    for clause in re.split(r"[，。；,;]", normalized):
        position = clause.find(term.lower())
        if position < 0:
            continue
        prefix = clause[:position]
        positive = [match.start() for match in re.finditer(_POSITIVE_CUES, prefix)]
        negative = [match.start() for match in re.finditer(_NEGATIVE_CUES, prefix)]
        if positive and (not negative or positive[-1] > negative[-1]):
            return True
    return False


def _required_food_terms(
    payload: MealRecommendationRequest, safe_foods: list[FoodCandidate]
) -> list[str]:
    """Find explicit positive references to real menu names or ingredients."""

    catalog_terms = {
        value.strip()
        for food in safe_foods
        for value in [food.name, *food.ingredients]
        if len(value.strip()) >= 2 and value.strip() not in _GENERIC_FOOD_TERMS
    }
    requested = {
        term
        for term in catalog_terms
        if _term_is_explicitly_requested(payload.extra_requirements, term)
    }
    for alias, canonical in _FOOD_ALIASES.items():
        if _term_is_explicitly_requested(payload.extra_requirements, alias) and any(
            _food_matches_term(food, canonical) for food in safe_foods
        ):
            requested.add(canonical)
    for term in payload.preferred_ingredients:
        normalized = term.strip()
        if normalized and any(_food_matches_term(food, normalized) for food in safe_foods):
            requested.add(normalized)
    return sorted(requested, key=lambda value: (-len(value), value))


def _excluded_food_terms(
    payload: MealRecommendationRequest, foods: list[FoodCandidate]
) -> set[str]:
    """Resolve coordinated natural-language exclusions against the actual menu catalog."""

    catalog_terms = {
        value.strip()
        for food in foods
        for value in [food.name, *food.ingredients]
        if len(value.strip()) >= 2 and value.strip() not in _GENERIC_FOOD_TERMS
    }
    excluded = {
        term for term in catalog_terms if _term_is_negated(payload.extra_requirements, term)
    }
    for alias, canonical in _FOOD_ALIASES.items():
        if _term_is_negated(payload.extra_requirements, alias):
            excluded.add(canonical)
    return excluded


def _requests_no_spice(requirements: str) -> bool:
    compact = re.sub(r"\s+", "", requirements)
    return bool(
        re.search(
            r"(?:不要|不吃|不想吃|不能吃|拒绝|忌)(?:任何)?(?:辣|辣椒|辣味)|"
            r"(?:完全|一点都)?不(?:能)?吃辣",
            compact,
        )
    )


def _required_terms_for_category(
    payload: MealRecommendationRequest,
    safe_foods: list[FoodCandidate],
    category: str,
) -> list[str]:
    """Return named food requirements that resolve to a specific menu category."""

    return [
        term
        for term in _required_food_terms(payload, safe_foods)
        if any(food.category == category and _food_matches_term(food, term) for food in safe_foods)
    ]


def _required_categories(requirements: str) -> set[str]:
    """Extract explicitly requested menu roles without treating '最好' as mandatory."""

    result = set()
    for category, terms in _CATEGORY_REQUIREMENTS.items():
        if any(_term_is_explicitly_requested(requirements, term) for term in terms):
            result.add(category)
    return result


def _verified_reason(foods: list[FoodCandidate]) -> str:
    """Build a short explanation from selected rows instead of trusting model prose."""

    names = [food.name for food in foods]
    preview = "、".join(names[:4]) + ("等" if len(names) > 4 else "")
    return f"选择{preview}，已按本餐预算、人数和明确要求完成校验。"


def _validated_title(
    model_title: object,
    foods: list[FoodCandidate],
    catalog_foods: list[FoodCandidate],
) -> str:
    """Keep an accurate model title, otherwise name the final validated combination."""

    title = str(model_title or "").strip()
    if title and len(title) <= 40 and _title_matches_foods(title, foods, catalog_foods):
        return title

    return _generated_title(foods)


def _title_matches_foods(
    title: str,
    foods: list[FoodCandidate],
    catalog_foods: list[FoodCandidate],
) -> bool:
    """Reject concrete food claims in a title that the final selected rows cannot prove."""

    compact_title = re.sub(r"[\s·・,，、/\\（）()\-—_]", "", title).lower()
    selected_names = {food.name.lower() for food in foods}

    # A title may use the exact name of a menu item. If that item exists in the
    # catalog, it must also exist in the final combination.
    for food in catalog_foods:
        name = food.name.strip().lower()
        if len(name) >= 2 and name in compact_title and name not in selected_names:
            return False

    # Ingredient and taste words are also factual claims (for example "羊肉风味").
    # Only terms known by the current menu are checked; creative generic titles
    # such as "校园暖心套餐" remain valid model output.
    selected_terms = {
        term.strip().lower()
        for food in foods
        for term in [food.name, *food.ingredients, *food.tastes]
        if len(term.strip()) >= 2
    }
    catalog_terms = {
        term.strip().lower()
        for food in catalog_foods
        for term in [*food.ingredients, *food.tastes]
        if len(term.strip()) >= 2
    }
    for term in catalog_terms:
        if term in compact_title and not any(
            term in selected_term or selected_term in term for selected_term in selected_terms
        ):
            return False

    category_claims = {
        "汤": "SOUP",
        "主食": "STAPLE",
        "饮品": "DRINK",
        "饮料": "DRINK",
        "小吃": "SNACK",
    }
    selected_categories = {food.category for food in foods}
    if any(
        claim in compact_title and category not in selected_categories
        for claim, category in category_claims.items()
    ):
        return False
    return not (
        ("素食" in compact_title or "全素" in compact_title)
        and any(food.category == "MEAT" for food in foods)
    )


def _generated_title(foods: list[FoodCandidate]) -> str:
    """Generate a fallback title from a real final selected row."""

    category_priority = {
        "MEAT": 0,
        "VEGETABLE": 1,
        "SOUP": 2,
        "STAPLE": 3,
        "SNACK": 4,
        "DRINK": 5,
    }
    primary = min(
        foods,
        key=lambda food: (
            0 if food.meal_role == "MAIN" else 1,
            category_priority.get(food.category, 9),
            food.name,
        ),
    )
    return f"{primary.name}套餐"[:40]


def _verified_notes(
    candidate: dict,
    foods: list[FoodCandidate],
    quantities: dict[str, int],
    payload: MealRecommendationRequest,
) -> tuple[list[str], list[str]]:
    """Replace objective LLM claims with facts recomputed from the selected foods."""

    del candidate
    matched: list[str] = []
    limitations: list[str] = []
    matched.extend(["预算内", f"适合{payload.diner_count}人用餐"])

    for term in _required_food_terms(payload, payload.foods):
        if any(_food_matches_term(food, term) for food in foods):
            matched.append(f"包含{term}")
    category_labels = {
        "SNACK": "小吃",
        "SOUP": "汤品",
        "DRINK": "饮品",
        "STAPLE": "主食",
        "MEAT": "荤菜",
        "VEGETABLE": "素菜",
    }
    for category in sorted(_required_categories(payload.extra_requirements)):
        if any(food.category == category for food in foods):
            matched.append(f"包含{category_labels[category]}")

    requested_count = _explicit_dish_count(payload.extra_requirements)
    actual_count = _dish_count(foods)
    if requested_count is not None and actual_count >= requested_count:
        matched.append(f"包含{requested_count}个菜")

    staples = [food for food in foods if food.category == "STAPLE"]
    staple_total = sum(quantities[str(food.id)] for food in staples)
    if staples:
        matched.append(f"主食共{staple_total}份")
    elif _waives_staple(payload.extra_requirements):
        matched.append("按要求不含主食")

    drinks = [food for food in foods if food.category == "DRINK"]
    if drinks:
        drink_total = sum(quantities[str(food.id)] for food in drinks)
        matched.append(f"饮品共{drink_total}杯")
    elif _waives_drink(payload.extra_requirements):
        matched.append("按要求不含饮品")

    if _requests_no_rice(payload.extra_requirements) and not any(
        _is_rice_food(food) for food in foods
    ):
        matched.append("已排除米饭")
    if _requests_no_spice(payload.extra_requirements) and all(
        food.spice_level == "NONE" for food in foods
    ):
        matched.append("按要求不辣")
    return list(dict.fromkeys(matched))[:8], list(dict.fromkeys(limitations))[:8]


def _dish_count_feasibility(
    safe_foods: list[FoodCandidate], payload: MealRecommendationRequest, target: int
) -> str:
    """Explain a verified quantity shortfall without trusting the model's budget claim."""

    dishes = sorted(food.price for food in safe_foods if food.category in _DISH_CATEGORIES)
    if len(dishes) < target:
        return "CANDIDATES"
    minimum = sum(dishes[:target])
    if not _waives_staple(payload.extra_requirements):
        staples = [food.price for food in safe_foods if food.category == "STAPLE"]
        if not staples:
            return "CANDIDATES"
        servings = (
            _explicit_role_quantity(payload.extra_requirements, "staple") or payload.diner_count
        )
        minimum += min(staples) * servings
    return "BUDGET" if minimum > payload.budget else "MODEL"


def _requests_no_rice(requirements: str) -> bool:
    compact = re.sub(r"\s+", "", requirements)
    return bool(re.search(r"(?:不要|不吃|不想吃|排除|去掉|别放)(?:米饭|大米)", compact))


def _is_rice_food(food: FoodCandidate) -> bool:
    terms = [food.name, *food.ingredients]
    return any("米饭" in term or "大米" in term for term in terms)


def _excluded_by_extra_requirement(food: FoodCandidate, requirements: str) -> bool:
    """Apply only explicit natural-language exclusions, without broad semantic guessing."""

    compact = re.sub(r"\s+", "", requirements).lower()
    terms = {food.name.lower(), *(item.lower() for item in food.ingredients)}
    if _requests_no_rice(requirements) and _is_rice_food(food):
        return True
    if re.search(r"(?:不要|不吃|不想吃|排除)面条", compact) and _food_matches_term(food, "面条"):
        return True
    if (
        re.search(r"(?:不要|不吃|不想吃|排除)面食", compact)
        and food.category == "STAPLE"
        and any(marker in text for text in terms for marker in ("面", "小麦", "馒头", "包"))
    ):
        return True
    prefixes = ("不要", "不吃", "不想吃", "排除", "去掉", "别放")
    return any(f"{prefix}{term}" in compact for prefix in prefixes for term in terms if term)


_CHINESE_NUMBERS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def _explicit_dish_count(requirements: str) -> int | None:
    """Extract an explicitly stated dish count for post-LLM truth checking only."""

    match = re.search(
        r"([1-9]|1\d|20|[一二两三四五六七八九十])\s*(?:个|道|份)\s*(?:菜|餐品)", requirements
    )
    if match is None:
        return None
    raw = match.group(1)
    return int(raw) if raw.isdigit() else _CHINESE_NUMBERS.get(raw)


def _claims_dish_count(text: str, requested_count: int) -> bool:
    """Identify an LLM-generated matched tag that falsely claims the requested count."""

    detected = _explicit_dish_count(text)
    return detected == requested_count


@router.get("/conversations")
async def conversations(request: Request, actor: Actor) -> ApiResponse[list]:
    repository: AgentRepository = request.app.state.agent_repository
    result = await run_in_threadpool(repository.list_conversations, actor.user_id)
    return ApiResponse.ok(result, request_id_context.get())


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate, request: Request, actor: Actor
) -> ApiResponse:
    repository: AgentRepository = request.app.state.agent_repository
    result = await run_in_threadpool(repository.create_conversation, actor.user_id, payload.title)
    return ApiResponse.ok(result, request_id_context.get())


@router.get("/conversations/{conversation_id}")
async def conversation(conversation_id: UUID, request: Request, actor: Actor) -> ApiResponse:
    repository: AgentRepository = request.app.state.agent_repository
    result = await run_in_threadpool(repository.conversation, actor.user_id, conversation_id)
    return ApiResponse.ok(result, request_id_context.get())


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: UUID, request: Request, actor: Actor) -> None:
    repository: AgentRepository = request.app.state.agent_repository
    await run_in_threadpool(repository.delete_conversation, actor.user_id, conversation_id)


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID, payload: MessageCreate, request: Request, actor: Actor
) -> StreamingResponse:
    orchestrator: AgentOrchestrator = request.app.state.agent_orchestrator
    stream = await orchestrator.start(
        actor, conversation_id, payload.content, request_id_context.get()
    )
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/tasks/{task_id}/regenerate")
async def regenerate(task_id: UUID, request: Request, actor: Actor) -> StreamingResponse:
    orchestrator: AgentOrchestrator = request.app.state.agent_orchestrator
    stream = await orchestrator.regenerate(actor, task_id, request_id_context.get())
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.put("/results/{result_id}/feedback")
async def feedback(
    result_id: UUID, payload: FeedbackCreate, request: Request, actor: Actor
) -> ApiResponse[dict]:
    repository: AgentRepository = request.app.state.agent_repository
    await run_in_threadpool(repository.save_feedback, actor, result_id, payload)
    return ApiResponse.ok({"saved": True}, request_id_context.get())


@router.post("/memories", status_code=status.HTTP_201_CREATED)
async def save_memory(payload: MemoryCreate, request: Request, actor: Actor) -> ApiResponse[dict]:
    if not payload.confirmed:
        raise PermissionError("MEMORY_CONFIRMATION_REQUIRED")
    repository: AgentRepository = request.app.state.agent_repository
    memory_id = await run_in_threadpool(
        repository.save_memory, actor, payload.data_scope, payload.content_summary
    )
    return ApiResponse.ok({"id": memory_id}, request_id_context.get())


@router.get("/memories")
async def memories(request: Request, actor: Actor) -> ApiResponse[list]:
    repository: AgentRepository = request.app.state.agent_repository
    result = await run_in_threadpool(repository.list_memories, actor.user_id)
    return ApiResponse.ok(result, request_id_context.get())


@router.put("/memories/{memory_id}")
async def update_memory(
    memory_id: UUID, payload: MemoryUpdate, request: Request, actor: Actor
) -> ApiResponse[dict]:
    if not payload.confirmed:
        raise PermissionError("MEMORY_CONFIRMATION_REQUIRED")
    repository: AgentRepository = request.app.state.agent_repository
    await run_in_threadpool(
        repository.update_memory, actor.user_id, memory_id, payload.content_summary
    )
    return ApiResponse.ok({"saved": True}, request_id_context.get())


@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: UUID, request: Request, actor: Actor) -> None:
    repository: AgentRepository = request.app.state.agent_repository
    await run_in_threadpool(repository.delete_memory, actor.user_id, memory_id)


@router.get("/tools")
async def tools(request: Request, actor: Actor) -> ApiResponse[list]:
    del actor
    registry: ToolRegistry = request.app.state.tool_registry
    return ApiResponse.ok(registry.public_contracts(), request_id_context.get())
