"""Authenticated endpoints for review-plan versions and mistake mastery."""

import asyncio
from uuid import UUID

from fastapi import APIRouter, Request, status

from agent_service.agent_routes import Actor
from agent_service.learning_repository import LearningRepository
from agent_service.middleware import request_id_context
from agent_service.review_plan_models import (
    MistakeMasteryRequest,
    ReviewPlanCreateRequest,
    ReviewPlanView,
)
from agent_service.review_plan_service import ReviewPlanService
from agent_service.schemas import ApiResponse

router = APIRouter(prefix="/agent-api/v1/learning", tags=["review-plan"])


def _require(actor: Actor, scope: str) -> None:
    if not actor.authorizations.get(scope, False):
        raise PermissionError("DATA_SCOPE_DENIED")


@router.post("/review-plans", response_model=ApiResponse[ReviewPlanView])
async def create_review_plan(
    payload: ReviewPlanCreateRequest, request: Request, actor: Actor
) -> ApiResponse[ReviewPlanView]:
    """Create a new plan from owned exams and currently authorized learning evidence."""

    _require(actor, "EXAMS")
    service: ReviewPlanService = request.app.state.review_plans
    plan = await service.create(
        actor.user_id, payload, use_mastery=actor.authorizations.get("MASTERY", False)
    )
    return ApiResponse.ok(plan, request_id_context.get())


@router.get("/review-plans", response_model=ApiResponse[list[ReviewPlanView]])
async def list_review_plans(request: Request, actor: Actor) -> ApiResponse[list[ReviewPlanView]]:
    _require(actor, "EXAMS")
    service: ReviewPlanService = request.app.state.review_plans
    plans = await service.list(actor.user_id)
    return ApiResponse.ok(plans, request_id_context.get())


@router.get("/review-plans/{plan_id}", response_model=ApiResponse[ReviewPlanView])
async def get_review_plan(
    plan_id: UUID, request: Request, actor: Actor
) -> ApiResponse[ReviewPlanView]:
    _require(actor, "EXAMS")
    service: ReviewPlanService = request.app.state.review_plans
    plan = await service.get(actor.user_id, plan_id)
    return ApiResponse.ok(plan, request_id_context.get())


@router.post("/review-plans/{plan_id}/regenerate", response_model=ApiResponse[ReviewPlanView])
async def regenerate_review_plan(
    plan_id: UUID, request: Request, actor: Actor
) -> ApiResponse[ReviewPlanView]:
    """Create a new current version without overwriting the previous plan."""

    _require(actor, "EXAMS")
    service: ReviewPlanService = request.app.state.review_plans
    plan = await service.regenerate(
        actor.user_id, plan_id, use_mastery=actor.authorizations.get("MASTERY", False)
    )
    return ApiResponse.ok(plan, request_id_context.get())


@router.delete("/review-plans/{plan_id}", status_code=status.HTTP_200_OK)
async def delete_review_plan(plan_id: UUID, request: Request, actor: Actor) -> ApiResponse[dict]:
    """Delete the selected plan and all versions in its version group."""

    _require(actor, "EXAMS")
    service: ReviewPlanService = request.app.state.review_plans
    await service.delete(actor.user_id, plan_id)
    return ApiResponse.ok({"deleted": True}, request_id_context.get())


@router.patch("/mistakes/{mistake_id}/mastery")
async def update_mistake_mastery(
    mistake_id: UUID, payload: MistakeMasteryRequest, request: Request, actor: Actor
) -> ApiResponse[dict]:
    """Let the student close or reopen an owned mistake after a deliberate review."""

    _require(actor, "MASTERY")
    repository: LearningRepository = request.app.state.learning_repository
    updated = await asyncio.to_thread(
        repository.set_mistake_mastery, actor.user_id, mistake_id, payload.mastered
    )
    if not updated:
        raise ValueError("错题记录不存在")
    return ApiResponse.ok({"mastered": payload.mastered}, request_id_context.get())
