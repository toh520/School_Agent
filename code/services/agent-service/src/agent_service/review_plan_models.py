"""Validated API models for exam-linked review-plan versions."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from agent_service.learning_models import AgentModel


class ReviewPlanCreateRequest(AgentModel):
    """Inputs controlled by the student; exam facts are loaded from the database."""

    exam_ids: list[UUID] = Field(
        min_length=1, max_length=12, validation_alias="examIds", serialization_alias="examIds"
    )
    daily_minutes: int = Field(
        ge=15, le=720, validation_alias="dailyMinutes", serialization_alias="dailyMinutes"
    )
    target: str = Field(min_length=1, max_length=300)
    constraints: str = Field(default="", max_length=1000)

    @field_validator("exam_ids")
    @classmethod
    def unique_exams(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("请勿重复选择同一场考试")
        return value

    @field_validator("target", "constraints", mode="before")
    @classmethod
    def trim_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class ReviewPlanStageView(AgentModel):
    id: UUID
    stage_index: int = Field(validation_alias="stageIndex", serialization_alias="stageIndex")
    name: str
    phase: str
    start_date: date = Field(validation_alias="startDate", serialization_alias="startDate")
    end_date: date = Field(validation_alias="endDate", serialization_alias="endDate")
    subject: str
    knowledge_points: list[str] = Field(
        validation_alias="knowledgePoints", serialization_alias="knowledgePoints"
    )
    objective: str
    suggested_minutes: int = Field(
        validation_alias="suggestedMinutes", serialization_alias="suggestedMinutes"
    )
    method: str
    rationale: str


class ReviewPlanExamView(AgentModel):
    id: UUID
    subject: str
    exam_date: date = Field(validation_alias="examDate", serialization_alias="examDate")
    start_time: str = Field(validation_alias="startTime", serialization_alias="startTime")
    location: str
    priority_score: float = Field(
        validation_alias="priorityScore", serialization_alias="priorityScore"
    )
    allocated_minutes: int = Field(
        validation_alias="allocatedMinutes", serialization_alias="allocatedMinutes"
    )


class ReviewPlanView(AgentModel):
    id: UUID
    plan_group_id: UUID = Field(validation_alias="planGroupId", serialization_alias="planGroupId")
    version_number: int = Field(
        validation_alias="versionNumber", serialization_alias="versionNumber"
    )
    is_current: bool = Field(validation_alias="isCurrent", serialization_alias="isCurrent")
    title: str
    status: str
    target: str
    constraints: str
    input_snapshot: dict[str, Any] = Field(
        validation_alias="inputSnapshot", serialization_alias="inputSnapshot"
    )
    priority_explanation: str = Field(
        validation_alias="priorityExplanation", serialization_alias="priorityExplanation"
    )
    assumptions: list[str]
    limitations: list[str]
    total_minutes: int = Field(validation_alias="totalMinutes", serialization_alias="totalMinutes")
    model_name: str | None = Field(validation_alias="modelName", serialization_alias="modelName")
    data_as_of: datetime = Field(validation_alias="dataAsOf", serialization_alias="dataAsOf")
    created_at: datetime = Field(validation_alias="createdAt", serialization_alias="createdAt")
    stale: bool
    exams: list[ReviewPlanExamView] = Field(default_factory=list)
    stages: list[ReviewPlanStageView] = Field(default_factory=list)


class MistakeMasteryRequest(AgentModel):
    mastered: bool
