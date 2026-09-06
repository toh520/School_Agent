import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agent_service.learning_models import LearningMode, LearningRequest, PracticeGenerateRequest
from agent_service.learning_service import (
    LearningAssistantService,
    _bounded_attachment_text,
    _test_cases,
)
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
        payload = json.loads(user)
        corrected_points = ["按最新纠正要求补充说明"] if payload.get("correction") else []
        return {
            "answer": "根据树的定义进行分析。",
            "steps": ["确认节点关系", "递归计算子树高度"],
            "conclusion": "根节点高度为 3。",
            "prerequisiteKnowledge": ["递归"],
            "keyConcepts": ["子树高度"],
            "keyClaims": [
                {"text": "高度由子树决定", "origin": "COURSE_MATERIAL", "sourceIndexes": [0]}
            ],
            "workedExample": "叶节点的两棵子树均为空。",
            "commonMistakes": ["遗漏空树边界"],
            "memoryTip": "先子树，后根节点。",
            "selfTestQuestion": "只有根节点时高度是多少？",
            "selfTestAnswer": "按层计数时为 1。",
            "diagnosis": [],
            "correctedPoints": corrected_points,
            "verification": "与教材定义一致",
            "limitations": [],
        }


class FakeMaterials:
    def search(self, course, query):
        return [StudyMatch("material-1", course, "数据结构.pdf", "第 2 页", "树的高度定义", 0.9)]

    def search_for_practice(self, course, knowledge_point):
        return self.search(course, knowledge_point)


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
    assert result.sources[0].snippet == "树的高度定义"
    assert result.prerequisite_knowledge == ["递归"]
    assert result.key_claims[0].origin == "COURSE_MATERIAL"
    assert result.key_claims[0].sources[0].locator == "第 2 页"
    assert len(repository.activities) == 1


async def test_practice_uses_exam_material_for_style_without_exposing_file_trace() -> None:
    systems = []

    class Model:
        async def complete_json(self, system, user):
            del user
            if "练习质量审查器" in system:
                return {"valid": True, "issues": []}
            systems.append(system)
            return {
                "items": [
                    {
                        "questionType": "FILL",
                        "prompt": "根据给定树结构填写前序遍历。",
                        "standardAnswer": "ABDCE",
                        "stepAnalysis": "先访问根，再递归访问左、右子树。",
                        "testCases": [],
                    }
                ]
            }

    class ExamMaterials(FakeMaterials):
        def search_for_practice(self, course, knowledge_point):
            del knowledge_point
            return [
                StudyMatch(
                    "exam-1", course, "2023数据结构A.pdf", "第2页", "填写树的遍历序列", 0.92, True
                ),
                StudyMatch("book-1", course, "教材.pdf", "第5页", "前序遍历为根左右", 0.95),
            ]

    class Repository(FakeRepository):
        def save_practices(self, user_id, items):
            del user_id
            self.saved = items
            return items

    repository = Repository()
    await LearningAssistantService(Model(), ExamMaterials(), repository).generate_practice(
        uuid4(),
        PracticeGenerateRequest(
            course="数据结构", knowledgePoint="二叉树遍历", questionTypes=["FILL"], count=1
        ),
    )

    assert '"usage": "EXAM_PATTERN"' in systems[0]
    assert "不得直接复制原题" in systems[0]
    assert repository.saved[0]["sourceLabel"] == "AI 生成（参考课程考试题型）"
    assert "2023数据结构A.pdf" not in repository.saved[0]["sourceLabel"]


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


async def test_learning_profile_and_diagnosis_context_reach_model() -> None:
    captured = []

    class CapturingModel(FakeModel):
        async def complete_json(self, system, user):
            if "高校考试学习助手" in system:
                captured.append(json.loads(user))
            return await super().complete_json(system, user)

    request = LearningRequest(
        mode="DIAGNOSE",
        course="数据结构",
        prompt="检查我的二分查找分析",
        workProcess="我把长度连续除以二直到一",
        finalAnswer="3次",
        confusion="比较次数是否包含最后一个元素",
        learningGoal="DEEP",
        familiarity="REVIEW",
    )
    await LearningAssistantService(CapturingModel(), FakeMaterials(), FakeRepository()).answer(
        uuid4(), request
    )

    assert captured[0]["finalAnswer"] == "3次"
    assert captured[0]["confusion"] == "比较次数是否包含最后一个元素"
    assert captured[0]["learningGoal"] == "DEEP"
    assert captured[0]["familiarity"] == "REVIEW"


async def test_untrusted_material_claim_is_downgraded_without_evidence() -> None:
    class EmptyMaterials:
        def search(self, course, query):
            return []

    result = await LearningAssistantService(FakeModel(), EmptyMaterials(), FakeRepository()).answer(
        uuid4(), LearningRequest(mode="EXPLAIN", course="数据结构", prompt="解释树高")
    )

    assert result.validation_status == "UNVERIFIED"
    assert result.key_claims[0].origin == "AI_SUPPLEMENT"
    assert result.key_claims[0].sources == []
    assert any("课程资料未命中" in item for item in result.limitations)


async def test_invalid_source_index_cannot_be_displayed_as_material_evidence() -> None:
    class InvalidClaimModel(FakeModel):
        async def complete_json(self, system, user):
            generated = await super().complete_json(system, user)
            if "高校考试学习助手" in system:
                generated["keyClaims"] = [
                    {
                        "text": "伪造来源的结论",
                        "origin": "COURSE_MATERIAL",
                        "sourceIndexes": [99],
                    }
                ]
            return generated

    result = await LearningAssistantService(
        InvalidClaimModel(), FakeMaterials(), FakeRepository()
    ).answer(uuid4(), LearningRequest(mode="EXPLAIN", course="数据结构", prompt="解释树高"))

    assert result.key_claims[0].origin == "AI_SUPPLEMENT"
    assert result.key_claims[0].sources == []


async def test_attachment_claim_requires_an_accessible_attachment() -> None:
    class AttachmentClaimModel(FakeModel):
        async def complete_json(self, system, user):
            generated = await super().complete_json(system, user)
            if "高校考试学习助手" in system:
                generated["keyClaims"] = [
                    {"text": "来自附件", "origin": "USER_ATTACHMENT", "sourceIndexes": []}
                ]
            return generated

    result = await LearningAssistantService(
        AttachmentClaimModel(), FakeMaterials(), FakeRepository()
    ).answer(uuid4(), LearningRequest(mode="EXPLAIN", course="数据结构", prompt="解释附件"))

    assert result.key_claims[0].origin == "AI_SUPPLEMENT"


async def test_internal_review_terms_and_duplicate_step_numbers_are_not_displayed() -> None:
    class VerboseReviewModel(FakeModel):
        async def complete_json(self, system, user):
            generated = await super().complete_json(system, user)
            if "高校考试学习助手" in system:
                generated["steps"] = ["1. 读取根节点", "步骤2：递归左右子树"]
            elif "答案质量审查器" in system:
                generated["verification"] = (
                    "candidate中的keyClaims已逐项引用evidence[0]且AI_SUPPLEMENT归因正确。"
                )
            return generated

    result = await LearningAssistantService(
        VerboseReviewModel(), FakeMaterials(), FakeRepository()
    ).answer(uuid4(), LearningRequest(mode="SOLVE", course="数据结构", prompt="求二叉树高度"))

    assert result.steps == ["读取根节点", "递归左右子树"]
    assert result.verification == "已核对回答结构、关键结论与课程资料的一致性。"


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


def test_duplicate_attachment_ids_are_rejected() -> None:
    attachment_id = uuid4()
    with pytest.raises(ValidationError, match="重复提交"):
        LearningRequest(
            mode="EXPLAIN",
            course="数据结构",
            prompt="解释队列",
            attachmentIds=[attachment_id, attachment_id],
        )


def test_attachment_context_is_bounded_and_keeps_each_file() -> None:
    result = _bounded_attachment_text(["甲" * 10000, "乙" * 10000, "丙" * 10000], 12)

    assert result == ["甲" * 4, "乙" * 4, "丙" * 4]
    assert sum(map(len, result)) == 12


async def test_attachment_claim_never_reuses_course_material_citation() -> None:
    attachment_id = uuid4()

    class Repository(FakeRepository):
        def attachment_texts(self, user_id, attachment_ids):
            return ["这是用户课堂笔记"]

    class Model(FakeModel):
        async def complete_json(self, system, user):
            generated = await super().complete_json(system, user)
            if "高校考试学习助手" in system:
                generated["keyClaims"] = [
                    {
                        "text": "来自课堂笔记的结论",
                        "origin": "USER_ATTACHMENT",
                        "sourceIndexes": [0],
                    }
                ]
            return generated

    result = await LearningAssistantService(Model(), FakeMaterials(), Repository()).answer(
        uuid4(),
        LearningRequest(
            mode="EXPLAIN",
            course="数据结构",
            prompt="解释课堂笔记",
            attachmentIds=[attachment_id],
        ),
    )

    assert result.key_claims[0].origin == "USER_ATTACHMENT"
    assert result.key_claims[0].sources == []
