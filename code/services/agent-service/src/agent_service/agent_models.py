"""Validated public and internal contracts for the M04 Agent platform."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class FoodCandidate(AgentModel):
    """Current in-stock food supplied by Core; recommendations cannot invent menu items."""

    id: UUID
    name: str
    price: float = Field(ge=0)
    category: str
    meal_role: str = Field(default="", validation_alias="mealRole", serialization_alias="mealRole")
    tastes: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    spice_level: str = Field(validation_alias="spiceLevel", serialization_alias="spiceLevel")
    energy_level: str = Field(
        default="UNKNOWN", validation_alias="energyLevel", serialization_alias="energyLevel"
    )
    protein_level: str = Field(
        default="UNKNOWN", validation_alias="proteinLevel", serialization_alias="proteinLevel"
    )
    carb_level: str = Field(
        default="UNKNOWN", validation_alias="carbLevel", serialization_alias="carbLevel"
    )
    oil_level: str = Field(
        default="UNKNOWN", validation_alias="oilLevel", serialization_alias="oilLevel"
    )
    portion_size: str = Field(
        default="", validation_alias="portionSize", serialization_alias="portionSize"
    )
    suitable_tags: list[str] = Field(
        default_factory=list,
        validation_alias="suitableTags",
        serialization_alias="suitableTags",
    )


class MealRecommendationRequest(AgentModel):
    """Transient constraints for one meal; none of these choices become profile data."""

    foods: list[FoodCandidate] = Field(min_length=1, max_length=200)
    allergens: list[str] = Field(default_factory=list)
    avoidances: list[str] = Field(default_factory=list)
    budget: float = Field(gt=0, le=500)
    diner_count: int = Field(
        default=1,
        ge=1,
        le=20,
        validation_alias="dinerCount",
        serialization_alias="dinerCount",
    )
    tastes: list[str] = Field(default_factory=list)
    spice_level: str | None = Field(
        default=None, validation_alias="spiceLevel", serialization_alias="spiceLevel"
    )
    goals: list[str] = Field(default_factory=list)
    preferred_ingredients: list[str] = Field(
        default_factory=list,
        validation_alias="preferredIngredients",
        serialization_alias="preferredIngredients",
    )
    excluded_ingredients: list[str] = Field(
        default_factory=list,
        validation_alias="excludedIngredients",
        serialization_alias="excludedIngredients",
    )
    meal_scale: str = Field(
        default="", validation_alias="mealScale", serialization_alias="mealScale"
    )
    extra_requirements: str = Field(
        default="",
        validation_alias="extraRequirements",
        serialization_alias="extraRequirements",
        max_length=500,
    )
    excluded_combinations: list[str] = Field(
        default_factory=list,
        validation_alias="excludedCombinations",
        serialization_alias="excludedCombinations",
    )


class MealCombination(AgentModel):
    key: str
    title: str
    food_ids: list[UUID] = Field(serialization_alias="foodIds")
    quantities: dict[str, int] = Field(default_factory=dict)
    total_price: float = Field(serialization_alias="totalPrice")
    reason: str
    matched_requirements: list[str] = Field(
        default_factory=list, serialization_alias="matchedRequirements"
    )
    limitations: list[str] = Field(default_factory=list)


class LibraryBookCandidate(AgentModel):
    """A real current holding supplied by the library catalog."""

    id: UUID
    name: str
    isbn: str = ""
    authors: list[str] = Field(default_factory=list)
    publisher: str = ""
    edition: str = ""
    published_year: int | None = Field(
        default=None, validation_alias="publishedYear", serialization_alias="publishedYear"
    )
    language: str = ""
    category: str = ""
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    cover_image: str = Field(
        default="", validation_alias="coverImage", serialization_alias="coverImage"
    )
    call_number: str = Field(
        default="", validation_alias="callNumber", serialization_alias="callNumber"
    )
    location: str = ""
    total_count: int = Field(
        default=0, ge=0, validation_alias="totalCount", serialization_alias="totalCount"
    )
    available_count: int = Field(
        default=0, ge=0, validation_alias="availableCount", serialization_alias="availableCount"
    )
    available: bool = False


class LibraryRecommendationRequest(AgentModel):
    requirement: str = Field(min_length=5, max_length=500)
    books: list[LibraryBookCandidate] = Field(min_length=1, max_length=300)

    @field_validator("requirement")
    @classmethod
    def normalize_requirement(cls, value: str) -> str:
        return value.strip()


class LibraryRecommendationItem(AgentModel):
    key: str
    source_type: str = Field(serialization_alias="sourceType")
    score: int = Field(ge=0, le=100)
    featured: bool
    reason: str
    book_id: UUID | None = Field(default=None, serialization_alias="bookId")
    name: str
    isbn: str = ""
    authors: list[str] = Field(default_factory=list)
    publisher: str = ""
    published_year: int | None = Field(default=None, serialization_alias="publishedYear")
    language: str = ""
    category: str = ""
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    cover_image: str = Field(default="", serialization_alias="coverImage")
    external_url: str = Field(default="", serialization_alias="externalUrl")
    queried_at: datetime | None = Field(default=None, serialization_alias="queriedAt")


class Intent(StrEnum):
    FOOD = "FOOD"
    EXAM = "EXAM"
    BOOK = "BOOK"
    CAMPUS_QA = "CAMPUS_QA"
    UNKNOWN = "UNKNOWN"


class TaskStatus(StrEnum):
    RUNNING = "RUNNING"
    NEEDS_INPUT = "NEEDS_INPUT"
    COMPLETED = "COMPLETED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class FeedbackCategory(StrEnum):
    HELPFUL = "HELPFUL"
    UNHELPFUL = "UNHELPFUL"
    INCORRECT = "INCORRECT"
    OUTDATED = "OUTDATED"


class IdentityContext(AgentModel):
    user_id: UUID
    role: str
    authorizations: dict[str, bool] = Field(default_factory=dict)


class ConversationCreate(AgentModel):
    title: str = Field(default="新会话", min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return value.strip()


class MessageCreate(AgentModel):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        return value.strip()


class FeedbackCreate(AgentModel):
    category: FeedbackCategory
    comment: str | None = Field(default=None, max_length=500)


class MemoryCreate(AgentModel):
    data_scope: str = Field(alias="dataScope")
    content_summary: str = Field(min_length=1, max_length=500, alias="contentSummary")
    confirmed: bool


class MemoryUpdate(AgentModel):
    content_summary: str = Field(min_length=1, max_length=500, alias="contentSummary")
    confirmed: bool


class MemoryView(AgentModel):
    id: UUID
    data_scope: str = Field(alias="dataScope")
    content_summary: str = Field(alias="contentSummary")
    created_at: datetime = Field(alias="createdAt")


class ConversationSummary(AgentModel):
    id: UUID
    title: str
    current_intent: Intent | None = Field(alias="currentIntent")
    updated_at: datetime = Field(alias="updatedAt")


class MessageView(AgentModel):
    id: UUID
    role: str
    content: str
    sequence_number: int = Field(alias="sequenceNumber")
    result_version_id: UUID | None = Field(default=None, alias="resultVersionId")
    task_id: UUID | None = Field(default=None, alias="taskId")
    intent: Intent | None = None
    fallback_used: bool = Field(default=False, alias="fallbackUsed")
    basis: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(alias="createdAt")


class ConversationDetail(ConversationSummary):
    messages: list[MessageView]


class ToolCallTrace(AgentModel):
    tool_name: str = Field(alias="toolName")
    tool_version: str = Field(alias="toolVersion")
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    status: str
    error_type: str | None = Field(default=None, alias="errorType")
    duration_ms: int = Field(alias="durationMs")


class WorkflowResult(AgentModel):
    intent: Intent
    status: TaskStatus
    missing_fields: list[str] = Field(default_factory=list, alias="missingFields")
    content: str = ""
    structured_result: dict[str, Any] = Field(default_factory=dict, alias="structuredResult")
    basis: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCallTrace] = Field(default_factory=list, alias="toolCalls")
    model_name: str | None = Field(default=None, alias="modelName")
    fallback_used: bool = Field(default=False, alias="fallbackUsed")


class PersistedTurn(AgentModel):
    task_id: UUID = Field(alias="taskId")
    message_id: UUID = Field(alias="messageId")
    result_version_id: UUID = Field(alias="resultVersionId")
    result: WorkflowResult
