"""Regressions for the special-case audit, with no external service calls."""

import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

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
)
from agent_service.learning_service import (
    LearningAssistantService,
    LearningRepository,
    _correction_reteach_issues,
    _learning_section_issues,
    _practice_payloads,
    _public_review_issues,
    _validated_answer,
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
        "agent_service.learning_repository.psycopg.connect", lambda **kwargs: connection
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


@pytest.mark.parametrize("count", [0, 5, None])
def test_rule_verification_uses_program_count_instead_of_model_field(count):
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
    assert "最终文字结论与规则一致" in result["verification"]
    assert result["binarySearchWorstComparisons"] == 0


@pytest.mark.parametrize(
    "conclusion",
    [
        "最坏情况下需要比较5次。",
        "最坏比较次数为5次。",
        "最坏需要5次比较。",
    ],
)
def test_binary_count_accepts_common_chinese_word_orders(conclusion):
    request = LearningRequest(mode="SOLVE", course="算法", prompt="长度为17的二分查找")
    assert not check_generated_counts(
        dict(binarySearchWorstComparisons=5, conclusion=conclusion), reference_checks(request)
    )


def test_binary_count_rejects_wrong_authoritative_conclusion():
    request = LearningRequest(
        mode="CORRECT",
        course="算法",
        prompt="长度为17的二分查找",
        previousAnswer="5次",
        correction="用长度为8的数组再讲一遍",
    )
    issues = check_generated_counts(
        dict(
            binarySearchWorstComparisons=4,
            answer="例题最坏需要比较4次。",
            conclusion="长度为17时最坏情况需要比较5次。",
        ),
        reference_checks(request),
    )
    assert issues


def test_binary_diagnosis_gets_program_verified_error_reason():
    request = LearningRequest(
        mode="DIAGNOSE",
        course="算法",
        prompt="长度为17的二分查找最坏比较几次",
        workProcess="我连续减半了四次，所以认为是4次",
        finalAnswer="4次",
    )
    result = visible_draft(
        request,
        {
            "answer": "最坏需要比较5次。",
            "steps": ["确定区间", "计入最后的单元素区间"],
            "conclusion": "最坏需要比较5次。",
            "diagnosis": [],
            "correctedPoints": [],
        },
    )

    assert any("减半次数" in item for item in result["diagnosis"])
    assert any("正确结果为5次" in item for item in result["correctedPoints"])


async def test_diagnosis_without_a_diagnostic_result_is_repaired():
    calls = 0

    class RepairingModel:
        async def complete_json(self, system, user):
            nonlocal calls
            if "答案质量审查器" in system:
                return {
                    "valid": True,
                    "taskSatisfied": True,
                    "attributionCorrect": True,
                    "evidenceAligned": True,
                    "issues": [],
                    "verification": "已核对",
                }
            calls += 1
            return {
                "answer": "逐步核对作答过程。",
                "steps": ["核对减半过程", "核对最后一个元素"],
                "conclusion": "最后一个元素仍需比较。",
                "diagnosis": [] if calls == 1 else ["将减半次数误当成了比较次数"],
                "correctedPoints": ["计入最后一次比较"],
            }

    result = await LearningAssistantService(
        RepairingModel(), FakeMaterials(), FakeRepository()
    ).answer(
        uuid4(),
        LearningRequest(
            mode="DIAGNOSE",
            course="算法",
            prompt="检查二分查找次数",
            workProcess="我只计算了数组连续减半到长度为1的次数",
        ),
    )

    assert calls == 2
    assert result.diagnosis == ["将减半次数误当成了比较次数"]


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


def test_validated_answer_hides_internal_review_notes_and_deduplicates_diagnosis():
    request = LearningRequest(
        mode="DIAGNOSE", course="算法", prompt="检查作答", workProcess="这是完整的作答步骤"
    )
    result = _validated_answer(
        request,
        {
            "answer": "已核对。",
            "steps": ["检查第一步", "检查第二步"],
            "conclusion": "第二步出错。",
            "diagnosis": ["概念混淆", "概念混淆"],
            "correctedPoints": ["补充边界", "补充边界"],
        },
        FakeMaterials().search("算法", "检查作答"),
        {
            "valid": True,
            "evidenceAligned": True,
            "issues": ["keyClaims sourceIndexes内部核对信息"],
            "verification": "已核对",
        },
    )

    assert result.diagnosis == ["概念混淆"]
    assert result.corrected_points == ["补充边界"]
    assert result.limitations == []


def test_internal_reviewer_vocabulary_never_reaches_failure_message():
    result = _public_review_issues(
        [
            "候选答案的keyClaims均标记为AI_SUPPLEMENT，且evidenceAligned=false。",
            "diagnosis与correctedPoints的错因归属不一致。",
        ]
    )

    assert result == [
        "部分关键结论的资料依据未通过核对。",
        "错因定位或修正点未通过核对，请确认作答过程是否完整。",
    ]


def test_reteach_correction_cannot_keep_the_previous_conclusion():
    request = LearningRequest(
        mode="CORRECT",
        course="数据结构",
        prompt="请解释后序遍历",
        previousAnswer=json.dumps({"conclusion": "原题后序为DEBFCA"}, ensure_ascii=False),
        correction="请换一个例子再讲一遍",
    )
    issues = _correction_reteach_issues(
        request,
        {"workedExample": "新例子为A→B→C", "conclusion": "原题后序为DEBFCA"},
    )

    assert issues and "旧题结论" in issues[0]


def test_deep_explanation_requires_every_visible_learning_layer():
    request = LearningRequest(
        mode="EXPLAIN",
        course="计算机网络",
        prompt="解释拥塞避免",
        learningGoal="DEEP",
        familiarity="REVIEW",
    )
    generated = {
        "steps": ["定义拥塞窗口", "分析加性增大"],
        "keyConcepts": ["加性增大"],
        "commonMistakes": ["与慢开始混淆"],
        "memoryTip": "慢慢试探",
        "selfTestQuestion": "拥塞窗口如何增长？",
        "workedExample": "窗口每轮增加1。",
        "prerequisiteKnowledge": [],
    }

    assert _learning_section_issues(request, generated) == ["考试复习或深入掌握模式缺少前置知识"]


def test_quick_explanation_can_omit_prerequisites_and_worked_example():
    request = LearningRequest(
        mode="EXPLAIN",
        course="计算机网络",
        prompt="解释拥塞避免",
        learningGoal="QUICK",
        familiarity="BEGINNER",
    )
    generated = {
        "steps": ["先慢速增加窗口", "再观察网络反馈"],
        "keyConcepts": ["加性增大"],
        "commonMistakes": ["误以为仍指数增长"],
        "memoryTip": "接近容量后慢慢试",
        "selfTestQuestion": "为什么不继续翻倍？",
        "prerequisiteKnowledge": [],
        "workedExample": "",
    }

    assert _learning_section_issues(request, generated) == []


async def test_deep_explanation_supplements_a_missing_section_before_review():
    class Model:
        async def complete_json(self, system, user):
            if "教学讲义结构补全器" in system:
                assert json.loads(user)["missingFields"] == ["prerequisiteKnowledge"]
                return {"prerequisiteKnowledge": ["理解拥塞窗口与往返时延"]}
            if "答案质量审查器" in system:
                return {
                    "valid": True,
                    "taskSatisfied": True,
                    "attributionCorrect": True,
                    "evidenceAligned": True,
                    "issues": [],
                    "verification": "已核对",
                }
            return {
                "answer": "拥塞避免采用加性增大。",
                "steps": ["观察拥塞窗口", "根据反馈线性调整"],
                "conclusion": "它通过渐进增长降低再次拥塞的风险。",
                "keyConcepts": ["加性增大"],
                "keyClaims": [],
                "workedExample": "窗口可按轮次逐步增加。",
                "commonMistakes": ["误认为仍按指数增长"],
                "memoryTip": "接近容量后慢慢试探。",
                "selfTestQuestion": "拥塞避免阶段窗口如何变化？",
                "prerequisiteKnowledge": [],
            }

    result = await LearningAssistantService(Model(), FakeMaterials(), FakeRepository()).answer(
        uuid4(),
        LearningRequest(
            mode="EXPLAIN",
            course="计算机网络",
            prompt="深入讲解拥塞避免",
            learningGoal="DEEP",
            familiarity="REVIEW",
        ),
    )

    assert result.validation_status == "MATERIAL_SUPPORTED"
    assert result.prerequisite_knowledge == ["理解拥塞窗口与往返时延"]


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


def test_question_only_scrubs_all_structured_solution_fields():
    request = LearningRequest(
        mode="EXPLAIN", course="数据结构", prompt="出一道自测题，不要提供答案"
    )
    result = visible_draft(
        request,
        {
            "selfTestQuestion": "AI生成：请写出该树的前序遍历。",
            "selfTestAnswer": "ABC",
            "steps": ["先访问A"],
            "keyConcepts": ["答案是ABC"],
            "keyClaims": [{"text": "答案是ABC", "origin": "AI_SUPPLEMENT"}],
            "workedExample": "同一棵树的答案是ABC",
            "memoryTip": "记住ABC",
        },
    )

    assert result["answer"].startswith("AI生成")
    assert result["selfTestAnswer"] == ""
    assert result["steps"] == []
    assert result["keyConcepts"] == []
    assert result["keyClaims"] == []
    assert result["workedExample"] == ""
    assert result["memoryTip"] == ""
