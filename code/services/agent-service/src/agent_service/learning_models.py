"""Validated contracts for M06 tutoring, practice generation, and review plans."""

from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from agent_service.agent_models import AgentModel


class LearningMode(StrEnum):
    EXPLAIN = "EXPLAIN"
    SOLVE = "SOLVE"
    DIAGNOSE = "DIAGNOSE"
    CORRECT = "CORRECT"


class LearningGoal(StrEnum):
    QUICK = "QUICK"
    EXAM = "EXAM"
    DEEP = "DEEP"


class LearningFamiliarity(StrEnum):
    BEGINNER = "BEGINNER"
    BASIC = "BASIC"
    REVIEW = "REVIEW"


class LearningTurn(AgentModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)

    @field_validator("content", mode="before")
    @classmethod
    def trim_content(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class LearningRequest(AgentModel):
    mode: LearningMode
    course: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=2, max_length=12000)
    work_process: str = Field(default="", max_length=12000, alias="workProcess")
    final_answer: str = Field(default="", max_length=4000, alias="finalAnswer")
    confusion: str = Field(default="", max_length=4000)
    learning_goal: LearningGoal = Field(default=LearningGoal.EXAM, alias="learningGoal")
    familiarity: LearningFamiliarity = LearningFamiliarity.BASIC
    previous_answer: str = Field(default="", max_length=12000, alias="previousAnswer")
    correction: str = Field(default="", max_length=4000)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=5, alias="attachmentIds")
    history: list[LearningTurn] = Field(default_factory=list, max_length=12)

    @field_validator(
        "course",
        "prompt",
        "work_process",
        "final_answer",
        "confusion",
        "previous_answer",
        "correction",
        mode="before",
    )
    @classmethod
    def trim_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("attachment_ids")
    @classmethod
    def unique_attachments(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("请勿重复提交同一附件")
        return value

    @model_validator(mode="after")
    def require_mode_context(self) -> "LearningRequest":
        if self.mode == LearningMode.DIAGNOSE and len(self.work_process) < 5:
            raise ValueError("错因诊断需要提供完整作答过程")
        if self.mode == LearningMode.CORRECT and (
            len(self.previous_answer) < 2 or len(self.correction) < 2
        ):
            raise ValueError("纠错需要提供原回答和质疑内容")
        return self


class LearningSource(AgentModel):
    material_id: str = Field(alias="materialId")
    file_name: str = Field(alias="fileName")
    locator: str
    snippet: str = ""


class LearningClaim(AgentModel):
    """A displayable conclusion whose provenance has been validated by the service."""

    text: str
    origin: Literal["COURSE_MATERIAL", "USER_ATTACHMENT", "AI_SUPPLEMENT"]
    sources: list[LearningSource] = Field(default_factory=list)


class LearningAnswer(AgentModel):
    mode: LearningMode
    course: str
    answer: str
    steps: list[str]
    conclusion: str
    diagnosis: list[str] = Field(default_factory=list)
    corrected_points: list[str] = Field(default_factory=list, alias="correctedPoints")
    verification: str
    validation_status: str = Field(alias="validationStatus")
    sources: list[LearningSource] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    prerequisite_knowledge: list[str] = Field(default_factory=list, alias="prerequisiteKnowledge")
    key_concepts: list[str] = Field(default_factory=list, alias="keyConcepts")
    key_claims: list[LearningClaim] = Field(default_factory=list, alias="keyClaims")
    worked_example: str = Field(default="", alias="workedExample")
    common_mistakes: list[str] = Field(default_factory=list, alias="commonMistakes")
    memory_tip: str = Field(default="", alias="memoryTip")
    self_test_question: str = Field(default="", alias="selfTestQuestion")
    self_test_answer: str = Field(default="", alias="selfTestAnswer")
    evidence_conflicts: list[str] = Field(default_factory=list, alias="evidenceConflicts")


class PracticeGenerateRequest(AgentModel):
    course: str = Field(min_length=1, max_length=120)
    knowledge_point: str = Field(min_length=1, max_length=160, alias="knowledgePoint")
    question_types: list[str] = Field(min_length=1, max_length=5, alias="questionTypes")
    difficulty: str = Field(default="MEDIUM", pattern="^(BASIC|MEDIUM|HARD)$")
    count: int = Field(default=3, ge=1, le=10)

    @field_validator("course", "knowledge_point", mode="before")
    @classmethod
    def trim_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("question_types")
    @classmethod
    def validate_types(cls, values: list[str]) -> list[str]:
        allowed = {"CHOICE", "FILL", "CALCULATION", "PROOF", "PROGRAMMING"}
        normalized = [value.upper() for value in values]
        if any(value not in allowed for value in normalized):
            raise ValueError("不支持的题型")
        return normalized


class PracticeItemView(AgentModel):
    id: UUID
    course: str
    knowledge_point: str = Field(alias="knowledgePoint")
    question_type: str = Field(alias="questionType")
    difficulty: str
    prompt: str
    standard_answer: str = Field(alias="standardAnswer")
    step_analysis: str = Field(alias="stepAnalysis")
    test_cases: list[dict[str, str]] = Field(default_factory=list, alias="testCases")
    source_type: str = Field(alias="sourceType")
    source_label: str = Field(alias="sourceLabel")
    validation_status: str = Field(alias="validationStatus")


class PracticeAttemptRequest(AgentModel):
    practice_id: UUID = Field(alias="practiceId")
    work_process: str = Field(min_length=5, max_length=12000, alias="workProcess")
    final_answer: str = Field(default="", max_length=4000, alias="finalAnswer")
    duration_seconds: int | None = Field(default=None, ge=0, le=86400, alias="durationSeconds")

    @field_validator("work_process", "final_answer", mode="before")
    @classmethod
    def trim_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class PracticeAttemptView(AgentModel):
    id: UUID
    practice_id: UUID = Field(alias="practiceId")
    correct: bool
    score: float = Field(ge=0, le=100)
    diagnosis: list[str]
    cause_type: str = Field(alias="causeType")
    corrected_conclusion: str = Field(alias="correctedConclusion")
    review_suggestion: str = Field(alias="reviewSuggestion")


class AttachmentView(AgentModel):
    id: UUID
    original_name: str = Field(alias="originalName")
    media_type: str = Field(alias="mediaType")
    parse_status: str = Field(alias="parseStatus")
    extracted_preview: str = Field(alias="extractedPreview")


class LearningOverview(AgentModel):
    attempts: list[dict[str, Any]] = Field(default_factory=list)
    activities: list[dict[str, Any]]
    mistakes: list[dict[str, Any]]
    practices: list[dict[str, Any]]
