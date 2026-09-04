import json
from datetime import date, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agent_service.learning_models import LearningMode, LearningRequest, ReviewPlanRequest
from agent_service.learning_service import LearningAssistantService, _test_cases, allocate_minutes
from agent_service.study_materials import StudyMatch

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakeModel:
    async def complete_json(self, system, user):
        if "答案质量审查器" in system:
            return {
                "valid": True,
                "taskSatisfied": True,
                "attributionCorrect": True,
                "evidenceAligned": True,
                "issues": [],
                "verification": "关键结论与教材定义一致",
            }
        return {
            "answer": "根据树的定义进行分析。",
            "steps": ["确认节点关系", "递归计算子树高度"],
            "conclusion": "根节点高度为 3。",
            "diagnosis": [],
            "correctedPoints": [],
            "verification": "与教材定义一致",
            "limitations": [],
        }


class FakeMaterials:
    def search(self, course, query):
        return [StudyMatch("material-1", course, "数据结构.pdf", "第 2 页", "树的高度定义", 0.9)]


class FakeRepository:
    def __init__(self):
        self.activities = []

    def attachment_texts(self, user_id, attachment_ids):
        return []

    def save_activity(self, *args):
        self.activities.append(args)


async def test_answer_is_marked_material_supported_and_recorded() -> None:
    repository = FakeRepository()
    service = LearningAssistantService(FakeModel(), FakeMaterials(), repository)
    request = LearningRequest(mode="SOLVE", course="数据结构", prompt="求二叉树高度")

    result = await service.answer(uuid4(), request)

    assert result.validation_status == "MATERIAL_SUPPORTED"
    assert result.sources[0].file_name == "数据结构.pdf"
    assert len(repository.activities) == 1


async def test_review_receives_latest_request_and_conversation() -> None:
    captured = []

    class CapturingModel(FakeModel):
        async def complete_json(self, system, user):
            if "答案质量审查器" in system:
                captured.append(json.loads(user))
            return await super().complete_json(system, user)

    request = LearningRequest(
        mode="CORRECT",
        course="数据结构",
        prompt="解释前序遍历",
        previousAnswer="前序是根左右",
        correction="请对比中序并出自测题",
        workProcess="我的理解是先根后左再右",
        history=[{"role": "user", "content": "A为根，B左C右"}],
    )
    await LearningAssistantService(CapturingModel(), FakeMaterials(), FakeRepository()).answer(
        uuid4(), request
    )
    assert captured[0]["correction"] == request.correction
    assert captured[0]["previousAnswer"] == request.previous_answer
    assert captured[0]["workProcess"] == request.work_process
    assert captured[0]["history"][0]["content"] == "A为根，B左C右"


async def test_rejected_draft_is_repaired_once_then_withheld() -> None:
    class RejectingModel(FakeModel):
        def __init__(self):
            self.calls = 0

        async def complete_json(self, system, user):
            self.calls += 1
            if "答案质量审查器" in system:
                return {"valid": False, "issues": ["编造上一题网络参数"]}
            return await super().complete_json(system, user)

    model = RejectingModel()
    repository = FakeRepository()
    result = await LearningAssistantService(model, FakeMaterials(), repository).answer(
        uuid4(), LearningRequest(mode="EXPLAIN", course="计算机网络", prompt="刚才的广播地址呢")
    )
    assert model.calls == 4
    assert result.validation_status == "NEEDS_CLARIFICATION"
    assert result.sources == []
    assert "根节点高度" not in result.answer
    assert repository.activities == []


async def test_followup_history_is_used_for_retrieval() -> None:
    class CapturingMaterials(FakeMaterials):
        def search(self, course, query):
            assert "192.168.10.64/26" in query
            return super().search(course, query)

    request = LearningRequest(
        mode="EXPLAIN",
        course="计算机网络",
        prompt="刚才的广播地址呢",
        history=[{"role": "user", "content": "网络192.168.10.64/26"}],
    )
    await LearningAssistantService(FakeModel(), CapturingMaterials(), FakeRepository()).answer(
        uuid4(), request
    )


def test_diagnosis_requires_complete_work_process() -> None:
    with pytest.raises(ValidationError, match="完整作答过程"):
        LearningRequest(mode=LearningMode.DIAGNOSE, course="数据结构", prompt="请诊断")


def test_plan_allocation_never_exceeds_available_time() -> None:
    request = ReviewPlanRequest.model_validate(
        {
            "exams": [
                {
                    "id": str(uuid4()),
                    "subject": "数据结构",
                    "examDate": str(date.today() + timedelta(days=2)),
                    "difficulty": 5,
                    "mastery": 30,
                    "scope": "树与图",
                },
                {
                    "id": str(uuid4()),
                    "subject": "计算机网络",
                    "examDate": str(date.today() + timedelta(days=8)),
                    "difficulty": 3,
                    "mastery": 70,
                    "scope": "传输层",
                },
            ],
            "totalMinutes": 601,
            "goal": "掌握主要题型",
        }
    )

    allocations = allocate_minutes(request)

    assert sum(allocations.values()) == 601
    assert all(value > 0 for value in allocations.values())


def test_programming_test_cases_require_input_and_expected_output() -> None:
    cases = _test_cases(
        [
            {"input": "3\n1 2 3", "expectedOutput": "6"},
            {"input": "", "expectedOutput": "0"},
            {"input": "1\n-2", "expectedOutput": "-2"},
        ]
    )

    assert cases == [
        {"input": "3\n1 2 3", "expectedOutput": "6"},
        {"input": "", "expectedOutput": "0"},
        {"input": "1\n-2", "expectedOutput": "-2"},
    ]
