"""Boundary regressions use controlled model outputs without external data transfer."""

import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agent_service.learning_checks import visible_draft
from agent_service.learning_models import (
    LearningRequest,
    PracticeAttemptRequest,
    PracticeGenerateRequest,
    ReviewPlanRequest,
)
from agent_service.learning_service import LearningAssistantService, _practice_payloads, _test_cases
from test_learning_service import FakeMaterials, FakeModel, FakeRepository

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_selftest_with_answer_in_question_is_withheld():
    class Model(FakeModel):
        async def complete_json(self, system, user):
            return {"selfTestQuestion": "AI生成：已知先序遍历序列为ABDEC，请求前序遍历结果。"}

    result = await LearningAssistantService(Model(), FakeMaterials(), FakeRepository()).answer(
        uuid4(),
        LearningRequest(
            mode="EXPLAIN", course="数据结构", prompt="只给一道前序遍历自测题，不要给答案"
        ),
    )
    assert result.validation_status == "NEEDS_CLARIFICATION"
    assert "ABDEC" not in result.model_dump_json()


async def test_question_only_redacts_reviewer_solution_too():
    class Model(FakeModel):
        async def complete_json(self, system, user):
            if "答案质量审查器" in system:
                review = await super().complete_json(system, user)
                return {**review, "verification": "答案是BAC", "issues": ["答案BAC已核对"]}
            return {"selfTestQuestion": "AI生成：A根B左C右，求中序？", "steps": ["BAC"]}

    result = await LearningAssistantService(Model(), FakeMaterials(), FakeRepository()).answer(
        uuid4(),
        LearningRequest(mode="SOLVE", course="数据结构", prompt="只给一道自测题，不要给答案"),
    )
    assert "BAC" not in result.model_dump_json()
    assert result.steps == []


async def test_structurally_invalid_answer_repairs_before_persistence():
    class Model(FakeModel):
        drafts = 0

        async def complete_json(self, system, user):
            if "答案质量审查器" not in system:
                self.drafts += 1
                if self.drafts == 1:
                    return {"answer": "草稿", "conclusion": "草稿结论", "steps": [" ", {}]}
            return await super().complete_json(system, user)

    repository = FakeRepository()
    model = Model()
    result = await LearningAssistantService(model, FakeMaterials(), repository).answer(
        uuid4(), LearningRequest(mode="SOLVE", course="数据结构", prompt="求树高度")
    )
    assert model.drafts == 2
    assert len(repository.activities) == 1
    assert len(result.steps) == 2


async def test_no_mastery_consent_does_not_record_answer():
    repository = FakeRepository()
    await LearningAssistantService(FakeModel(), FakeMaterials(), repository).answer(
        uuid4(),
        LearningRequest(mode="EXPLAIN", course="数据结构", prompt="解释树"),
        record_activity=False,
    )
    assert repository.activities == []


@pytest.mark.parametrize(
    "kind,answer,options",
    [
        ("CHOICE", "A", ["A. 正确", "B. 错误", "C. 错误"]),
        ("PROOF", "结论成立，证明略。", []),
    ],
)
def test_incomplete_proof_and_duplicate_distractors_rejected(kind, answer, options):
    request = PracticeGenerateRequest(
        course="数据结构", knowledgePoint="树", questionTypes=[kind], count=1
    )
    with pytest.raises(ValueError):
        _practice_payloads(
            {
                "items": [
                    dict(
                        questionType=kind,
                        prompt="测试题",
                        standardAnswer=answer,
                        stepAnalysis="解析",
                        options=options,
                    )
                ]
            },
            request,
            [],
        )


def plan_input():
    return dict(
        exams=[
            dict(
                id=str(uuid4()),
                subject="数据结构",
                examDate="2026-12-20",
                difficulty=3,
                mastery=50,
                scope="树",
            )
        ],
        totalMinutes=60,
        goal="复习树",
    )


async def test_plan_serializes_uuid_and_preserves_total():
    class Model:
        model_name = "fake"

        async def complete_json(self, system, user):
            payload = json.loads(user)
            assert isinstance(payload["exams"][0]["id"], str)
            return {"stages": []}

    class Repository(FakeRepository):
        def save_plan(self, user_id, request, plan, model_name):
            return plan

    result = await LearningAssistantService(Model(), FakeMaterials(), Repository()).create_plan(
        uuid4(), ReviewPlanRequest(**plan_input())
    )
    assert sum(stage["suggestedMinutes"] for stage in result.stages) == 60


@pytest.mark.parametrize("field,value", [("course", "  "), ("prompt", "  ")])
def test_whitespace_is_not_valid_question(field, value):
    payload = dict(mode="EXPLAIN", course="数据结构", prompt="解释树")
    payload[field] = value
    with pytest.raises(ValidationError):
        LearningRequest(**payload)


@pytest.mark.parametrize("invalid_date", ["tomorrow", "2026-02-30"])
def test_invalid_plan_date_rejected_at_boundary(invalid_date):
    payload = plan_input()
    payload["exams"][0]["examDate"] = invalid_date
    with pytest.raises(ValidationError):
        ReviewPlanRequest(**payload)


def test_duplicate_exam_rejected():
    payload = plan_input()
    payload["exams"] *= 2
    with pytest.raises(ValidationError):
        ReviewPlanRequest(**payload)


async def test_attachment_is_present_in_review():
    class Repository(FakeRepository):
        def attachment_texts(self, user_id, ids):
            return ["附件题干：A为根，B左C右"]

    class Model(FakeModel):
        async def complete_json(self, system, user):
            if "答案质量审查器" in system:
                assert "A为根" in json.loads(user)["attachmentText"][0]
            return await super().complete_json(system, user)

    result = await LearningAssistantService(Model(), FakeMaterials(), Repository()).answer(
        uuid4(),
        LearningRequest(
            mode="SOLVE", course="数据结构", prompt="解析附件", attachmentIds=[uuid4()]
        ),
    )
    assert result.validation_status == "MATERIAL_SUPPORTED"


async def test_invalid_second_practice_does_not_save_first():
    class Model:
        async def complete_json(self, system, user):
            return {
                "items": [
                    dict(
                        questionType="CHOICE",
                        prompt="问题",
                        standardAnswer="A",
                        stepAnalysis="解析",
                        options=["A. 一", "B. 二"],
                    ),
                    dict(questionType="FILL"),
                ]
            }

    class Repository(FakeRepository):
        def save_practices(self, *args):
            self.activities.append(args)

    repository = Repository()
    with pytest.raises(ValueError):
        await LearningAssistantService(Model(), FakeMaterials(), repository).generate_practice(
            uuid4(),
            PracticeGenerateRequest(
                course="数据结构", knowledgePoint="树", questionTypes=["CHOICE", "FILL"], count=2
            ),
        )
    assert repository.activities == []


@pytest.mark.parametrize(
    "evaluation",
    [
        {"correct": "false", "score": 0},
        {"correct": True, "score": float("nan")},
        {"correct": False, "score": 101},
        {"correct": False},
        {"correct": True, "score": 10},
    ],
)
async def test_invalid_evaluation_never_updates_mastery(evaluation):
    class Model:
        async def complete_json(self, system, user):
            return evaluation

    class Repository(FakeRepository):
        def practice(self, *args):
            return dict(prompt="问题", standard_answer="答案", step_analysis="过程")

        def save_attempt(self, *args):
            self.activities.append(args)

    repository = Repository()
    with pytest.raises(ValueError):
        await LearningAssistantService(Model(), FakeMaterials(), repository).evaluate_attempt(
            uuid4(), PracticeAttemptRequest(practiceId=uuid4(), workProcess="完整的作答过程")
        )
    assert repository.activities == []


def test_programming_cases_preserve_empty_input_and_zero_output():
    assert _test_cases([{"input": "", "expectedOutput": 0}]) == [
        {"input": "", "expectedOutput": "0"}
    ]


async def test_review_outage_withholds_answer_and_keeps_history_readable():
    class Model(FakeModel):
        async def complete_json(self, system, user):
            if "答案质量审查器" in system:
                raise TimeoutError("test timeout")
            return await super().complete_json(system, user)

    class Repository(FakeRepository):
        def overview(self, user_id):
            return {"activities": ["existing"]}

    repository = Repository()
    service = LearningAssistantService(Model(), FakeMaterials(), repository)
    result = await service.answer(
        uuid4(), LearningRequest(mode="EXPLAIN", course="数据结构", prompt="解释树")
    )
    assert result.validation_status == "NEEDS_CLARIFICATION"
    assert repository.activities == []
    assert (await service.overview(uuid4()))["activities"] == ["existing"]


def test_question_only_never_displays_solution_fields():
    request = LearningRequest(
        mode="EXPLAIN", course="数据结构", prompt="只给一道自测题，不要给答案"
    )
    result = visible_draft(
        request,
        {
            "selfTestQuestion": "AI生成：A根B左C右，求前序？",
            "steps": ["答案ABC"],
            "conclusion": "ABC",
            "verification": "ABC正确",
        },
    )
    assert "ABC" not in json.dumps(result, ensure_ascii=False)
    assert result["steps"] == []


@pytest.mark.parametrize("value", [None, 42, [], {}, " "])
def test_invalid_prompt_types_are_validation_errors(value):
    with pytest.raises(ValidationError):
        LearningRequest(mode="EXPLAIN", course="数据结构", prompt=value)


def test_whitespace_attempt_is_not_complete_work():
    with pytest.raises(ValidationError):
        PracticeAttemptRequest(practiceId=uuid4(), workProcess="      ")


async def test_unavailable_attachment_never_invokes_model():
    class Model:
        async def complete_json(self, *args):
            pytest.fail("model must not receive a question whose attachment is unavailable")

    with pytest.raises(ValueError, match="附件不可用"):
        await LearningAssistantService(Model(), FakeMaterials(), FakeRepository()).answer(
            uuid4(),
            LearningRequest(
                mode="SOLVE", course="数据结构", prompt="解答附件", attachmentIds=[uuid4()]
            ),
        )


@pytest.mark.parametrize("kind", ["CHOICE", "FILL", "CALCULATION", "PROOF", "PROGRAMMING"])
async def test_all_practice_types_require_review_before_saving(kind):
    events = []

    class Model:
        async def complete_json(self, system, user):
            if "练习质量审查器" in system:
                events.append("review")
                return {"valid": True}
            return {
                "items": [
                    dict(
                        questionType=kind,
                        prompt="测试题",
                        standardAnswer="A",
                        options=["A. 一", "B. 二"],
                        stepAnalysis=["第一步", "第二步"],
                        testCases=[
                            dict(input="", expectedOutput="0"),
                            dict(input="1", expectedOutput="1"),
                        ],
                    )
                ]
            }

    class Repository(FakeRepository):
        def save_practices(self, user_id, items):
            item = items[0]
            events.append("save")
            assert item["stepAnalysis"] == "第一步\n第二步"
            if kind == "CHOICE":
                assert "A. 一" in item["prompt"]
            return items

    await LearningAssistantService(Model(), FakeMaterials(), Repository()).generate_practice(
        uuid4(),
        PracticeGenerateRequest(
            course="数据结构", knowledgePoint="树", questionTypes=[kind], count=1
        ),
    )
    assert events == ["review", "save"]


async def test_failed_practice_review_does_not_save():
    class Model:
        async def complete_json(self, system, user):
            if "练习质量审查器" in system:
                return {"valid": False, "issues": ["题目条件歧义"]}
            return {
                "items": [
                    dict(
                        questionType="FILL", prompt="问题", standardAnswer="A", stepAnalysis="解析"
                    )
                ]
            }

    class Repository(FakeRepository):
        def save_practices(self, *args):
            self.activities.append(args)

    repository = Repository()
    with pytest.raises(ValueError, match="质量审查"):
        await LearningAssistantService(Model(), FakeMaterials(), repository).generate_practice(
            uuid4(),
            PracticeGenerateRequest(
                course="数据结构", knowledgePoint="树", questionTypes=["FILL"], count=1
            ),
        )
    assert repository.activities == []
