"""Regressions for the special-case audit, with no external service calls."""

import json
from datetime import date, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agent_service.learning_checks import (
    check_generated_counts,
    question_only,
    reference_checks,
    traversal_practice_issues,
    traversal_sample_issues,
    visible_draft,
)
from agent_service.learning_models import (
    LearningRequest,
    PracticeAttemptRequest,
    PracticeGenerateRequest,
    ReviewPlanRequest,
)
from agent_service.learning_service import (
    LearningAssistantService,
    LearningRepository,
    _practice_payloads,
    _validated_answer,
    allocate_minutes,
)
from test_learning_service import FakeMaterials, FakeRepository

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.parametrize(
    "prompt",
    [
        "只给一道自测题，不要给答案",
        "出一道自测题，先别告诉我答案",
        "仅提供一道练习，暂时隐藏解答",
        "Give me a practice question without the answer.",
    ],
)
def test_selftest_synonyms(prompt):
    assert question_only(LearningRequest(mode="EXPLAIN", course="数据结构", prompt=prompt))


@pytest.mark.parametrize(
    "correction,expected",
    [("数组长度为32", 6), ("把数组大小改为32", 6), ("现在改成空数组", 0), ("改成64", 7)],
)
def test_current_binary_conditions(correction, expected):
    result = reference_checks(
        LearningRequest(
            mode="CORRECT",
            course="算法设计与分析",
            prompt="长度为16的二分查找",
            previousAnswer="最多5次",
            correction=correction,
        )
    )
    assert result["binarySearch"]["worstComparisons"] == expected


@pytest.mark.parametrize("answer", ["后序遍历序列为DEBCFA", "DEBCFA", "后序为DEBCFA"])
def test_traversal_answer_wording(answer):
    assert traversal_practice_issues(
        dict(
            questionType="PROOF",
            prompt="先序遍历序列为ABDECF，中序遍历序列为DBEAFC，求后序。",
            standardAnswer=answer,
        )
    )


@pytest.mark.parametrize(
    "options,answer", [(["A. 1", "A. 2"], "A"), (["1", "2"], "A"), (["A. 1", "B. 2"], "Z")]
)
def test_choice_labels(options, answer):
    with pytest.raises(ValueError):
        _practice_payloads(
            {
                "items": [
                    dict(
                        questionType="CHOICE",
                        prompt="1+1等于几",
                        standardAnswer=answer,
                        stepAnalysis="相加",
                        options=options,
                    )
                ]
            },
            PracticeGenerateRequest(
                course="数据结构", knowledgePoint="树", questionTypes=["CHOICE"], count=1
            ),
            [],
        )


def plan_payload():
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
        totalMinutes=30,
        goal="复习树",
    )


@pytest.mark.parametrize("field", ["goal", "subject", "scope"])
def test_plan_blanks(field):
    payload = plan_payload()
    (payload if field == "goal" else payload["exams"][0])[field] = " "
    with pytest.raises(ValidationError):
        ReviewPlanRequest(**payload)


@pytest.mark.parametrize("count", [1, 3, 10])
@pytest.mark.parametrize("minutes", [30, 61, 100000])
def test_all_exams_have_positive_exact_allocation(count, minutes):
    exams = [
        dict(
            id=str(uuid4()),
            subject="树",
            examDate=str(date.today() + timedelta(days=1 if i else 365)),
            difficulty=5 if i else 1,
            mastery=0 if i else 100,
            scope="树",
        )
        for i in range(count)
    ]
    result = allocate_minutes(ReviewPlanRequest(exams=exams, totalMinutes=minutes, goal="复习树"))
    assert min(result.values()) > 0
    assert sum(result.values()) == minutes


async def test_missing_reasoning_clarifies_without_model_or_record():
    class Model:
        async def complete_json(self, *args):
            pytest.fail("must not infer missing reasoning")

    repo = FakeRepository()
    result = await LearningAssistantService(Model(), FakeMaterials(), repo).answer(
        uuid4(),
        LearningRequest(
            mode="DIAGNOSE",
            course="数据结构",
            prompt="根A左B右C求前序",
            workProcess="我只记得最后写了BAC，其他过程完全没有写，也不记得怎么想的",
        ),
    )
    assert result.validation_status == "NEEDS_CLARIFICATION"
    assert not result.diagnosis and not repo.activities


async def test_plan_caps_stage_count_and_restores_subject_content():
    class Model:
        model_name = "fake"

        async def complete_json(self, system, user):
            exam = json.loads(user)["exams"][0]["id"]
            return {
                "stages": [
                    dict(examId=exam, subject="错课", content="", objective="", suggestedMinutes=0)
                ]
                * 100
            }

    class Repo:
        def save_plan(self, user, request, plan, model):
            return plan

    plan = await LearningAssistantService(Model(), FakeMaterials(), Repo()).create_plan(
        uuid4(), ReviewPlanRequest(**plan_payload())
    )
    assert len(plan.stages) <= 5
    assert sum(s["suggestedMinutes"] for s in plan.stages) == 30
    assert all(
        s["subject"] == "数据结构" and s["content"] and s["objective"] and s["suggestedMinutes"] > 0
        for s in plan.stages
    )


@pytest.mark.parametrize(
    "evaluation",
    [
        dict(correct=False, score=100),
        dict(correct=True, score=100, causeType="INVALID"),
        dict(correct=False, score=0, causeType="OTHER", diagnosis=[]),
        dict(correct=False, score=0, causeType=[], diagnosis=["错误步骤"]),
        dict(correct=False, score=0, causeType={}, diagnosis=["错误步骤"]),
    ],
)
async def test_invalid_grading_never_saved(evaluation):
    class Model:
        async def complete_json(self, system, user):
            assert json.loads(user)["testCases"] == [dict(input="1", expectedOutput="1")]
            return evaluation

    class Repo:
        def practice(self, *args):
            return dict(
                prompt="test",
                standard_answer="1",
                step_analysis="steps",
                test_cases=[dict(input="1", expectedOutput="1")],
            )

        def save_attempt(self, *args):
            pytest.fail("invalid grading must not be saved")

    with pytest.raises(ValueError):
        await LearningAssistantService(Model(), FakeMaterials(), Repo()).evaluate_attempt(
            uuid4(), PracticeAttemptRequest(practiceId=uuid4(), workProcess="这是我的完整作答过程")
        )


def test_practice_transaction_exits_with_failure_before_activity(monkeypatch):
    repo = object.__new__(LearningRepository)
    repo._connect = {}
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    connection.__enter__.return_value = connection
    monkeypatch.setattr(
        "agent_service.learning_service.psycopg.connect", lambda **kwargs: connection
    )
    repo._insert_practice = MagicMock(side_effect=[object(), RuntimeError("second insert failed")])
    with pytest.raises(RuntimeError):
        repo.save_practices(uuid4(), [{}, {}])
    assert connection.__exit__.call_args.args[0] is RuntimeError
    connection.commit.assert_not_called()
    cursor.execute.assert_not_called()


async def test_bare_traversal_answer_cannot_contradict_conclusion():
    service = LearningAssistantService(None, FakeMaterials(), FakeRepository())
    review = await service._review_answer(
        LearningRequest(mode="SOLVE", course="数据结构", prompt="根A左B右C的前序遍历"),
        dict(answer="BAC", conclusion="前序遍历为ABC", steps=["访问根", "访问左右"]),
        [],
        [],
    )
    assert review["valid"] is False


@pytest.mark.parametrize("count,passed", [(0, True), (5, False), (None, False)])
def test_rule_verification_is_program_owned_without_hiding_wrong_counts(count, passed):
    request = LearningRequest(mode="EXPLAIN", course="算法设计", prompt="二分查找空数组比较几次？")
    result = visible_draft(
        request,
        dict(
            answer="空数组0次",
            conclusion="空数组0次",
            binarySearchWorstComparisons=count,
            verification="trustedChecks.fakeField已经通过全部验证",
        ),
    )
    assert "fakeField" not in result["verification"]
    assert ("候选次数与规则一致" in result["verification"]) is passed
    assert result["binarySearchWorstComparisons"] == count


@pytest.mark.parametrize("output,valid", [("ABCDE", False), ("ABDCE", True)])
def test_program_sample_checks_non_balanced_tree(output, valid):
    issues = traversal_sample_issues(
        dict(questionType="PROGRAMMING", prompt="第二行先序遍历。第三行中序遍历。输出层序"),
        [dict(input="5\nABCDE\nCBADE", expectedOutput=output)],
    )
    assert bool(issues) is not valid


def test_recursive_tree_practice_rejects_oversized_domain():
    assert traversal_sample_issues(
        dict(questionType="PROGRAMMING", prompt="1≤n≤1000，第二行先序。第三行中序。输出层序"),
        [dict(input="1\nA\nA", expectedOutput="A")],
    )


def test_reviewer_cannot_replace_program_owned_verification():
    request = LearningRequest(mode="EXPLAIN", course="算法", prompt="二分查找空数组")
    generated = visible_draft(
        request, dict(answer="0次", conclusion="0次", binarySearchWorstComparisons=0)
    )
    result = _validated_answer(request, generated, [], dict(valid=True, verification="虚构字段"))
    assert result.verification == generated["verification"]


def test_correct_count_does_not_excuse_false_empty_array_precondition():
    request = LearningRequest(mode="EXPLAIN", course="算法", prompt="二分查找空数组")
    assert check_generated_counts(
        dict(
            answer="0次",
            conclusion="0次",
            binarySearchWorstComparisons=0,
            steps=["标准闭区间二分查找要求数组非空"],
        ),
        reference_checks(request),
    )
